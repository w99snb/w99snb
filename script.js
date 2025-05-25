// Main JavaScript file for the EPANET Web Simulator PoC
import { Workspace, Project } from 'https://cdn.jsdelivr.net/npm/epanet-js@0.8.0-alpha.5/+esm';

// Event listener for when the DOM is fully loaded.
// Initializes Pyodide, epanet-js, UI elements, and event handlers.
document.addEventListener('DOMContentLoaded', async () => {
    // --- UI Element References ---
    const loadInpBtn = document.getElementById('loadInpBtn'); // Button to trigger file input
    const inpFileElement = document.getElementById('inpFile');    // Hidden file input for .INP files
    const fileNameDisplay = document.getElementById('fileNameDisplay'); // Span to show selected file name
    const outputDiv = document.getElementById('output');          // General messages and non-critical errors
    const cyContainer = document.getElementById('cy');            // Div container for Cytoscape.js graph
    // *** NEW: Reference to the file versions display div ***
    const fileVersionsDiv = document.getElementById('fileVersions');

    // --- Global Pyodide & EPANET-JS Instances ---
    globalThis.pyodide = null;
    // globalThis.epanetJsWorkspace = null; // Initialized in initializePyodideAndApp
    // globalThis.epanetJsProject = null;   // Initialized in initializePyodideAndApp

    // --- Proxies for Python functions defined in main_poc.py ---
    globalThis.py_create_epanet_instance = null;
    globalThis.py_get_network_topology = null;
    globalThis.py_open_hydraulic_analysis = null;
    globalThis.py_initialize_hydraulic_analysis = null;
    globalThis.py_run_hydraulic_step_all_results = null; // For getting all node/link results
    globalThis.py_close_hydraulic_analysis = null;
    globalThis.py_set_emitter_coefficient = null;
    globalThis.py_set_pdd_options = null;
    globalThis.py_set_quality_type = null;
    globalThis.py_run_quality_step = null;
    // *** NEW: Proxies for Python version getter functions ***
    globalThis.py_get_epanetapi_shim_version = null;
    globalThis.py_get_epanet_shim_version = null;
    globalThis.py_get_main_poc_version = null;


    // --- Cytoscape Instance ---
    globalThis.cy_instance = null; // Holds the Cytoscape graph instance

    // --- Simulation Control UI Elements ---
    const initStepSimBtn = document.getElementById('initStepSimBtn');
    const runNextStepBtn = document.getElementById('runNextStepBtn');

    // --- Leak (Emitter) UI Elements ---
    const applyLeakBtn = document.getElementById('applyLeakBtn');
    const leakNodeIdInput = document.getElementById('leakNodeIdInput');
    const emitterCoeffInput = document.getElementById('emitterCoeffInput');
    const leakStatusDisplayDiv = document.getElementById('leakStatusDisplay');

    // --- PDD UI Elements ---
    const pddEnableSwitch = document.getElementById('pddEnableSwitch');
    const pddPminInput = document.getElementById('pddPminInput');
    const pddPreqInput = document.getElementById('pddPreqInput');
    const pddPexpInput = document.getElementById('pddPexpInput');
    const applyPddSettingsBtn = document.getElementById('applyPddSettingsBtn');
    const pddStatusDisplayDiv = document.getElementById('pddStatusDisplay');

    // --- Water Quality UI Elements ---
    const qualityTypeNoneRadio = document.getElementById('qualityTypeNone');
    const qualityTypeAgeRadio = document.getElementById('qualityTypeAge');
    const qualityTypeTraceRadio = document.getElementById('qualityTypeTrace');
    const traceNodeIdInput = document.getElementById('traceNodeIdInput');
    const applyQualitySettingsBtn = document.getElementById('applyQualitySettingsBtn');
    const qualityStatusDisplayDiv = document.getElementById('qualityStatusDisplay');
    const nodeQualityDisplayDiv = document.getElementById('nodeQualityDisplay');

    // --- Status and Result Display UI Elements ---
    const simulationStatusDiv = document.getElementById('simulationStatus');
    const currentTimeDisplayDiv = document.getElementById('currentTimeDisplay');
    const nodePressureDisplayDiv = document.getElementById('nodePressureDisplay');
    const linkFlowDisplayDiv = document.getElementById('linkFlowDisplay');

    // --- Global JS State Variables ---
    let node_to_monitor = "J1";
    let link_to_monitor = "P1";
    let currentQualityType = "NONE";
    let currentTraceNodeId = "";

    // *** NEW: Expected versions for Python files ***
    // These are the versions you expect to be loaded.
    // You might update these as you deploy new versions of your Python files.
    const expectedFileVersions = {
        'epanetapi_shim.py': '1.0.5',
        'epanet_shim.py': '1.0.3',
        'main_poc.py': '1.0.4'
    };

    /**
     * Initializes Pyodide, loads Python scripts into its virtual file system,
     * sets up epanet-js, and imports Python functions into the global JavaScript scope.
     */
    async function initializePyodideAndApp() {
        console.log("JS: Entered initializePyodideAndApp function.");
        simulationStatusDiv.textContent = "Status: Initializing Pyodide and EPANET tools...";
        if(fileVersionsDiv) fileVersionsDiv.innerHTML = "Checking file versions...";

        try {
            console.log("JS: Attempting to load Pyodide...");
            globalThis.pyodide = await loadPyodide();
            console.log("JS: Pyodide initialized successfully.");

            // console.log("JS: Attempting to initialize epanet-js Workspace and Project..."); // Old log
            console.log("JS: Attempting to initialize epanet-js Workspace...");
            try {
                globalThis.epanetJsWorkspace = new Workspace();
                console.log("JS: epanet-js Workspace instantiated. Attempting to load WASM module...");
                
                // Load the EPANET WASM module
                await globalThis.epanetJsWorkspace.loadModule(); // This is the new crucial line
                console.log("JS: epanet-js WASM module loaded successfully.");

                // Now that the module is loaded, initialize the Project
                console.log("JS: Attempting to initialize epanet-js Project...");
                globalThis.epanetJsProject = new Project(globalThis.epanetJsWorkspace);
                console.log("JS: epanet-js Project initialized successfully using the workspace.");
            } catch (error) {
                console.error("JS: Critical Error initializing epanet-js Workspace/Project:", error);
                if(simulationStatusDiv) {
                    simulationStatusDiv.textContent = 'Fatal Error: Could not initialize epanet-js libraries. ' + error.toString();
                }
                if(loadInpBtn) loadInpBtn.disabled = true;
                throw error;
            }

            console.log("JS: Preparing to load Python scripts into Pyodide FS...");
            const scriptsToLoad = ['epanetapi_shim.py', 'epanet_shim.py', 'main_poc.py'];
            // *** MODIFIED: Added cache-busting parameter to fetch URLs ***
            const cacheBustParam = `v=${Date.now()}`;
            for (const scriptName of scriptsToLoad) {
                // Append a unique query parameter to prevent caching
                const response = await fetch(`${scriptName}?${cacheBustParam}`);
                if (!response.ok) {
                    throw new Error(`Failed to fetch ${scriptName}: ${response.statusText}`);
                }
                const scriptContent = await response.text();
                globalThis.pyodide.FS.writeFile(scriptName, scriptContent);
                console.log(`JS: Loaded ${scriptName} into Pyodide FS.`);
            }
            console.log("JS: All Python scripts loaded into Pyodide FS.");

            console.log("JS: Attempting to run Python code to import main_poc.py functions...");
            // *** MODIFIED: Added new version getter functions to the import list ***
            globalThis.pyodide.runPython(`
from main_poc import (
    create_epanet_instance_from_inp,
    get_network_topology_js,
    open_hydraulic_analysis_js,
    initialize_hydraulic_analysis_js,
    py_run_hydraulic_step_and_get_all_results,
    close_hydraulic_analysis_js,
    set_emitter_coefficient_js,
    set_pdd_options_js,
    set_quality_type_js,
    run_quality_step_js,
    get_epanetapi_shim_version_actual,  # New
    get_epanet_shim_version_actual,    # New
    get_main_poc_version_actual        # New
)
            `);
            globalThis.py_create_epanet_instance = globalThis.pyodide.globals.get('create_epanet_instance_from_inp');
            globalThis.py_get_network_topology = globalThis.pyodide.globals.get('get_network_topology_js');
            globalThis.py_open_hydraulic_analysis = globalThis.pyodide.globals.get('open_hydraulic_analysis_js');
            globalThis.py_initialize_hydraulic_analysis = globalThis.pyodide.globals.get('initialize_hydraulic_analysis_js');
            globalThis.py_run_hydraulic_step_all_results = globalThis.pyodide.globals.get('py_run_hydraulic_step_and_get_all_results');
            globalThis.py_close_hydraulic_analysis = globalThis.pyodide.globals.get('close_hydraulic_analysis_js');
            globalThis.py_set_emitter_coefficient = globalThis.pyodide.globals.get('set_emitter_coefficient_js');
            globalThis.py_set_pdd_options = globalThis.pyodide.globals.get('set_pdd_options_js');
            globalThis.py_set_quality_type = globalThis.pyodide.globals.get('set_quality_type_js');
            globalThis.py_run_quality_step = globalThis.pyodide.globals.get('run_quality_step_js');
            // *** NEW: Get references to Python version getter functions ***
            globalThis.py_get_epanetapi_shim_version = globalThis.pyodide.globals.get('get_epanetapi_shim_version_actual');
            globalThis.py_get_epanet_shim_version = globalThis.pyodide.globals.get('get_epanet_shim_version_actual');
            globalThis.py_get_main_poc_version = globalThis.pyodide.globals.get('get_main_poc_version_actual');
            console.log("JS: Python functions from main_poc.py imported into global JS scope.");

            // *** NEW: Display Python file versions ***
            if (fileVersionsDiv) {
                let versionsHTML = "<strong>Python File Versions:</strong><ul>";
                let allMatch = true;

                for (const scriptName of scriptsToLoad) {
                    let actualVersion = "N/A";
                    let versionGetter;
                    let expectedVersion = expectedFileVersions[scriptName] || "Not specified";

                    try {
                        if (scriptName === 'epanetapi_shim.py' && globalThis.py_get_epanetapi_shim_version) {
                            versionGetter = globalThis.py_get_epanetapi_shim_version;
                        } else if (scriptName === 'epanet_shim.py' && globalThis.py_get_epanet_shim_version) {
                            versionGetter = globalThis.py_get_epanet_shim_version;
                        } else if (scriptName === 'main_poc.py' && globalThis.py_get_main_poc_version) {
                            versionGetter = globalThis.py_get_main_poc_version;
                        }

                        if (versionGetter) {
                            let versionProxy = versionGetter();
                            actualVersion = versionProxy.toString();
                            // versionProxy.destroy(); // Clean up proxy - Removed as direct string returns don't need it
                        } else {
                             console.warn(`JS: Version getter for ${scriptName} not found or not imported.`);
                             actualVersion = "Getter N/A";
                        }
                    } catch (e) {
                        console.error(`JS: Error getting version for ${scriptName}:`, e);
                        actualVersion = "Error";
                    }

                    const match = actualVersion === expectedVersion;
                    if (!match && actualVersion !== "Error" && actualVersion !== "Getter N/A") allMatch = false;
                    versionsHTML += `<li>${scriptName}: Expected ${expectedVersion}, Actual: ${actualVersion} ${match ? '✅' : '❌'}</li>`;
                }
                versionsHTML += "</ul>";
                if (!allMatch) {
                    versionsHTML += "<p style='color:red;'><strong>Warning: Version mismatch detected!</strong></p>";
                } else {
                     versionsHTML += "<p style='color:green;'>All Python file versions match expected.</p>";
                }
                fileVersionsDiv.innerHTML = versionsHTML;
            }

            simulationStatusDiv.textContent = "Status: Ready to load .INP file.";
            outputDiv.innerText = "Pyodide, Python scripts, and epanet-js ready.";
            console.log("JS: initializePyodideAndApp completed successfully.");

        } catch (error) {
            console.error("JS: Error during initializePyodideAndApp:", error);
            if(simulationStatusDiv) simulationStatusDiv.textContent = `Status: Initialization Error. Check console.`;
            if(outputDiv) outputDiv.innerText = `Initialization Error: ${error.message}.`;
            if(fileVersionsDiv) fileVersionsDiv.innerHTML = `<span style="color:red;">Error initializing app: ${error.message}</span>`;
            if(loadInpBtn) {
                console.log("JS: Disabling loadInpBtn due to initialization error.");
                loadInpBtn.disabled = true;
            }
        }
    }

    /**
     * Processes the INP file content, calls Python to create an EPANET instance and get topology,
     * then renders the network using Cytoscape.js.
     * @param {string} inp_content_str - The string content of the .INP file.
     */
    async function displayNetworkTopology(inp_content_str) {
        if (!globalThis.py_create_epanet_instance || !globalThis.py_get_network_topology) {
            simulationStatusDiv.textContent = "Status: Error - Core Python functions not loaded.";
            outputDiv.innerText = "Error: Core Python functions not loaded.";
            return;
        }
        
        simulationStatusDiv.textContent = "Status: Processing INP file...";
        outputDiv.innerText = "Creating EPANET instance and extracting topology...";

        try {
            console.log('JS [Phase 1]: Raw INP content being sent to Python:', inp_content_str);
            let instance_msg_proxy = globalThis.py_create_epanet_instance(inp_content_str);
            if (instance_msg_proxy && typeof instance_msg_proxy.toString === 'function') {
                console.log(`JS: Python create_epanet_instance says: ${instance_msg_proxy.toString()}`);
            }
            if (instance_msg_proxy && typeof instance_msg_proxy.destroy === 'function') {
                instance_msg_proxy.destroy();
            }

            let topology_js_proxy = globalThis.py_get_network_topology();
            let topology = topology_js_proxy.toJs({ dict_converter: Object.fromEntries }); 
            console.log('JS [Phase 1]: Topology object received from Python:', JSON.stringify(topology, null, 2));
            topology_js_proxy.destroy();
            console.log("JS: Topology received from Python:", topology);

            if (!topology || !topology.nodes || !topology.links) {
                throw new Error("Invalid or empty topology data received from Python.");
            }
            
            if (topology.nodes.length > 0) {
                const nodeExists = topology.nodes.some(n => n.id === node_to_monitor);
                if (!nodeExists) node_to_monitor = topology.nodes[0].id; 
            } else { node_to_monitor = "N/A"; }

            if (topology.links.length > 0) {
                const linkExists = topology.links.some(l => l.id === link_to_monitor);
                if (!linkExists) link_to_monitor = topology.links[0].id; 
            } else { link_to_monitor = "N/A"; }

            if (globalThis.cy_instance) globalThis.cy_instance.destroy();

            const elements = [];
            topology.nodes.forEach(node => {
                const xVal = parseFloat(node.x);
                const yVal = parseFloat(node.y);
                console.log(`JS [Phase 1]: Node ${node.id} coords from Python: x=${node.x}, y=${node.y}. Parsed: x=${xVal}, y=${yVal}`);
                elements.push({ 
                    data: { id: node.id, type: node.type, type_code: node.type_code }, 
                    position: { x: xVal || 0, y: yVal || 0 } 
                });
            });
            topology.links.forEach(link => {
                elements.push({ data: { id: link.id, source: link.source, target: link.target } });
            });
            
            outputDiv.innerText = `Rendering network: ${topology.nodes.length} nodes, ${topology.links.length} links.`;

            globalThis.cy_instance = cytoscape({
                container: cyContainer,
                elements: elements,
                style: [ 
                    { selector: 'node', style: { 'background-color': '#666', 'label': 'data(id)', 'width': '25px', 'height': '25px', 'font-size': '10px', 'color': '#333', 'text-valign': 'bottom', 'text-halign': 'center', 'text-outline-width': 1, 'text-outline-color': '#fff' }},
                    { selector: 'node[type="junction"]', style: { 'background-color': '#808080', 'shape': 'ellipse' }},
                    { selector: 'node[type="tank"]', style: { 'background-color': '#add8e6', 'shape': 'rectangle', 'width': '30px', 'height': '40px' }},
                    { selector: 'node[type="reservoir"]', style: { 'background-color': '#90ee90', 'shape': 'diamond', 'width': '35px', 'height': '35px' }},
                    { selector: 'edge', style: { 'width': 2.5, 'line-color': '#b0c4de', 'target-arrow-shape': 'none', 'curve-style': 'haystack' }}
                ],
                layout: { name: 'preset' },
            });
            
            globalThis.cy_instance.center(); 
            globalThis.cy_instance.fit(null, 30); 
            console.log("JS: Cytoscape network rendered.");
            
            initStepSimBtn.disabled = false; 
            runNextStepBtn.disabled = true;  
            simulationStatusDiv.textContent = 'Status: Network loaded. Ready to initialize step simulation.';
            outputDiv.innerText = `Network displayed: ${topology.nodes.length} nodes, ${topology.links.length} links.`;
            currentTimeDisplayDiv.textContent = 'Current Time: -';
            nodePressureDisplayDiv.textContent = `Node Pressure (${node_to_monitor}): -`;
            linkFlowDisplayDiv.textContent = `Link Flow (${link_to_monitor}): -`;
            nodeQualityDisplayDiv.textContent = `Node Quality (${currentQualityType !== "NONE" ? currentQualityType : "-"}): -`;

        } catch (error) { 
            console.error("JS: Error in displayNetworkTopology:", error);
            let errorMsg = error.message || String(error);
            if (error.pyError && error.message) { errorMsg = error.message; } 
            simulationStatusDiv.textContent = `Status: Error loading network.`;
            outputDiv.innerText = `Error displaying topology: ${errorMsg}. Check console.`;
            if (globalThis.cy_instance) globalThis.cy_instance.destroy(); 
            cyContainer.innerHTML = '<p style="text-align:center; color:red;">Could not render network.</p>';
            initStepSimBtn.disabled = true; 
            runNextStepBtn.disabled = true;
        }
    }

    // --- Event Listeners for File Loading ---
    loadInpBtn.addEventListener('click', () => {
        console.log("JS: loadInpBtn clicked.");
        if (inpFileElement) {
            console.log("JS: Triggering click on inpFileElement.");
            inpFileElement.click();
        } else {
            console.error("JS: inpFileElement not found.");
        }
    });

    inpFileElement.addEventListener('change', (event) => {
        console.log("JS: inpFileElement change event triggered.");
        const file = event.target.files[0];
        if (file) {
            console.log(`JS: File selected: ${file.name}, type: ${file.type}, size: ${file.size} bytes.`);
            if (file.name.toLowerCase().endsWith('.inp')) {
                fileNameDisplay.textContent = `Selected: ${file.name}`;
                simulationStatusDiv.textContent = `Status: Reading file ${file.name}...`;
                outputDiv.innerText = `Reading file: ${file.name}...`;
                console.log(`JS: Reading file ${file.name} as text.`);
                
                const reader = new FileReader();
                reader.onload = async (e) => {
                    console.log("JS: FileReader onload event triggered.");
                    const inp_content_str = e.target.result;
                    console.log("JS: File content read successfully. Length:", inp_content_str.length);
                    await displayNetworkTopology(inp_content_str); 
                };
                reader.onerror = (e_reader) => {
                    console.error("JS: FileReader error:", e_reader);
                    simulationStatusDiv.textContent = "Status: Error reading file.";
                    outputDiv.innerText = "Error reading file.";
                    fileNameDisplay.textContent = "Error reading file.";
                };
                reader.readAsText(file);
            } else {
                console.warn(`JS: Invalid file type selected: ${file.name}. Expected .inp file.`);
                alert("Please select a valid .INP file.");
                simulationStatusDiv.textContent = "Status: Invalid file type.";
                outputDiv.innerText = "Invalid file type. Please select an .INP file.";
                fileNameDisplay.textContent = "No file selected.";
                if (inpFileElement) inpFileElement.value = ''; 
            }
        } else {
             console.log("JS: No file selected after change event (e.g., dialog cancelled).");
             fileNameDisplay.textContent = "No file selected."; 
        }
    });

    // --- Event Listener for "Initialize Step Simulation" Button ---
    initStepSimBtn.addEventListener('click', async () => {
        if (!globalThis.py_open_hydraulic_analysis || !globalThis.py_initialize_hydraulic_analysis) {
            simulationStatusDiv.textContent = "Status: Error - Python simulation functions not loaded.";
            return;
        }
        simulationStatusDiv.textContent = 'Status: Initializing step simulation...';
        try {
            let msg_proxy_open_h = globalThis.py_open_hydraulic_analysis(); 
            console.log("JS: py_open_hydraulic_analysis: " + msg_proxy_open_h.toString());
            msg_proxy_open_h.destroy();

            let msg_proxy_init_h = globalThis.py_initialize_hydraulic_analysis(0); // 0 for NOSAVE
            console.log("JS: py_initialize_hydraulic_analysis: " + msg_proxy_init_h.toString());
            msg_proxy_init_h.destroy();
            
            runNextStepBtn.disabled = false;
            initStepSimBtn.disabled = true;
            simulationStatusDiv.textContent = 'Status: Step simulation initialized. Ready for next step.';
            currentTimeDisplayDiv.textContent = 'Current Time: 0.00 hrs';
            nodePressureDisplayDiv.textContent = `Node Pressure (${node_to_monitor}): -`; 
            linkFlowDisplayDiv.textContent = `Link Flow (${link_to_monitor}): -`;      
            nodeQualityDisplayDiv.textContent = `Node Quality (${currentQualityType !== "NONE" ? currentQualityType : "-"}): -`;
        } catch (error) {
            console.error("JS: Error initializing step simulation:", error);
            simulationStatusDiv.textContent = 'Status: Error initializing simulation.';
            let errorMsg = error.message || String(error);
            if (error.pyError && error.message) { errorMsg = error.message; }
            outputDiv.innerText = `Error: ${errorMsg}`; 
            runNextStepBtn.disabled = true;
        }
    });
    
    // --- Helper functions for dynamic Cytoscape styling ---
    function getNodePressureColor(pressure, minP = 0, maxP = 50) {
        if (pressure < minP) return 'rgb(128,0,128)';
        if (pressure < (minP + (maxP - minP) * 0.1)) return 'rgb(255,0,0)'; 
        const ratio = Math.max(0, Math.min(1, (pressure - minP) / (maxP - minP)));
        if (ratio < 0.5) { 
            return `rgb(255, ${Math.round(255 * ratio * 2)}, 0)`;
        } else { 
            return `rgb(${Math.round(255 * (1 - (ratio - 0.5) * 2))}, 255, 0)`;
        }
    }

    function getLinkFlowWidth(flow, minF = 0, maxF = 1000, baseWidth = 1.5, maxWidth = 8) {
        const absFlow = Math.abs(flow); 
        if (absFlow <= minF) return `${baseWidth}px`;
        const range = maxF - minF;
        const flowRatio = Math.max(0, Math.min(1, (absFlow - minF) / (range === 0 ? 1 : range) ));
        const width = baseWidth + flowRatio * (maxWidth - baseWidth);
        return `${Math.round(width * 2) / 2}px`; 
    }

    // --- Event Listener for "Run Next Hydraulic Step" Button ---
    runNextStepBtn.addEventListener('click', async () => {
        if (!globalThis.py_run_hydraulic_step_all_results) {
            simulationStatusDiv.textContent = "Status: Error - Python run step function not loaded.";
            return;
        }
        simulationStatusDiv.textContent = 'Status: Running next hydraulic step...';
        try {
            let results_proxy = globalThis.py_run_hydraulic_step_all_results(); 
            let results = results_proxy.toJs({ dict_converter: Object.fromEntries });
            results_proxy.destroy();

            if (results.error) { throw new Error(results.error); }

            currentTimeDisplayDiv.textContent = `Current Time: ${(results.currentTime / 3600).toFixed(2)} hrs`;

            if (globalThis.cy_instance) {
                const minP = 0, maxP = 50; 
                const minF = 0, maxF = 1000; 

                results.nodeResults.forEach(node_data => {
                    let cy_node = globalThis.cy_instance.$id(node_data.id);
                    if (cy_node.length > 0) {
                        let color = getNodePressureColor(node_data.pressure, minP, maxP);
                        cy_node.style('background-color', color);
                    }
                });
                results.linkResults.forEach(link_data => {
                    let cy_link = globalThis.cy_instance.$id(link_data.id);
                    if (cy_link.length > 0) {
                        let width = getLinkFlowWidth(link_data.flow, minF, maxF);
                        cy_link.style('width', width);
                    }
                });

                const monitoredNodeResult = results.nodeResults.find(nr => nr.id === node_to_monitor);
                if (monitoredNodeResult) nodePressureDisplayDiv.textContent = `Node Pressure (${node_to_monitor}): ${monitoredNodeResult.pressure.toFixed(2)}`;
                else if (node_to_monitor !== "N/A") nodePressureDisplayDiv.textContent = `Node Pressure (${node_to_monitor}): Not found`;
                
                const monitoredLinkResult = results.linkResults.find(lr => lr.id === link_to_monitor);
                if (monitoredLinkResult) linkFlowDisplayDiv.textContent = `Link Flow (${link_to_monitor}): ${monitoredLinkResult.flow.toFixed(2)}`;
                else if (link_to_monitor !== "N/A") linkFlowDisplayDiv.textContent = `Link Flow (${link_to_monitor}): Not found`;
            }

            if (currentQualityType !== "NONE" && globalThis.py_run_quality_step) {
                 let node_for_quality_val = node_to_monitor; 
                 if (node_to_monitor === "N/A" && results.nodeResults.length > 0) node_for_quality_val = results.nodeResults[0].id;

                if(node_for_quality_val === "N/A") {
                    nodeQualityDisplayDiv.textContent = `Node Quality (${currentQualityType}): N/A (No valid node)`;
                } else {
                    let quality_results_proxy = globalThis.py_run_quality_step(node_for_quality_val);
                    let quality_results = quality_results_proxy.toJs({ dict_converter: Object.fromEntries });
                    quality_results_proxy.destroy();

                    if (quality_results.error) {
                        console.error("JS: Quality step error:", quality_results.error);
                        nodeQualityDisplayDiv.textContent = `Node Quality (${currentQualityType}): Error`;
                    } else {
                        nodeQualityDisplayDiv.textContent = `Node Quality (${quality_results.nodeId} - ${currentQualityType}): ${quality_results.quality.toFixed(2)}`;
                    }
                }
            } else {
                nodeQualityDisplayDiv.textContent = 'Node Quality (-): - (Quality Sim Disabled)';
            }

            if (results.nextEventTime <= 0) { 
                runNextStepBtn.disabled = true; 
                initStepSimBtn.disabled = false; 
                simulationStatusDiv.textContent = 'Status: Hydraulic simulation ended.';
            } else {
                simulationStatusDiv.textContent = 'Status: Ready for next step.';
            }
        } catch (error) {
            console.error("JS: Error running next step:", error);
            simulationStatusDiv.textContent = 'Status: Error during step execution.';
            let errorMsg = error.message || String(error);
            outputDiv.innerText = `Error: ${errorMsg}`; 
            runNextStepBtn.disabled = true; 
            initStepSimBtn.disabled = false; 
        }
    });

    // --- Event Listeners for Parameter Modification ---
    applyLeakBtn.addEventListener('click', async () => {
        if (!globalThis.py_set_emitter_coefficient) {
            leakStatusDisplayDiv.textContent = "Leak Status: Error - Python function not loaded."; return;
        }
        if (!globalThis.pyodide.globals.get('epanet_instance_py')) { 
            leakStatusDisplayDiv.textContent = "Leak Status: EPANET model not loaded."; return;
        }
        const nodeId = leakNodeIdInput.value.trim();
        const coeff = parseFloat(emitterCoeffInput.value);
        if (nodeId && !isNaN(coeff) && coeff >= 0) {
            leakStatusDisplayDiv.textContent = `Leak Status: Applying to Node ${nodeId}...`;
            try {
                let message_proxy = globalThis.py_set_emitter_coefficient(nodeId, coeff);
                leakStatusDisplayDiv.textContent = `Leak Status: ${message_proxy.toString()}`;
                message_proxy.destroy();
            } catch (error) {
                let errorMsg = error.message || String(error);
                if (error.pyError && error.message) { errorMsg = error.message; }
                leakStatusDisplayDiv.textContent = `Leak Status: Error - ${errorMsg}`;
            }
        } else {
            leakStatusDisplayDiv.textContent = "Leak Status: Error - Invalid Node ID or Coefficient.";
        }
    });

    applyPddSettingsBtn.addEventListener('click', async () => {
        if (!globalThis.py_set_pdd_options) {
            pddStatusDisplayDiv.textContent = "PDD Status: Error - Python function not loaded."; return;
        }
         if (!globalThis.pyodide.globals.get('epanet_instance_py')) { 
            pddStatusDisplayDiv.textContent = "PDD Status: EPANET model not loaded."; return;
        }
        const enabled = pddEnableSwitch.checked;
        const pmin = parseFloat(pddPminInput.value);
        const preq = parseFloat(pddPreqInput.value);
        const pexp = parseFloat(pddPexpInput.value);
        if (!isNaN(pmin) && !isNaN(preq) && !isNaN(pexp)) {
            pddStatusDisplayDiv.textContent = `PDD Status: Applying...`;
            try {
                let message_proxy = globalThis.py_set_pdd_options(enabled, pmin, preq, pexp);
                pddStatusDisplayDiv.textContent = `PDD Status: ${message_proxy.toString()}`;
                message_proxy.destroy();
                simulationStatusDiv.textContent = "Status: PDD settings applied. Please Re-initialize Step Simulation.";
                initStepSimBtn.disabled = false; 
                runNextStepBtn.disabled = true;  
            } catch (error) {
                let errorMsg = error.message || String(error);
                if (error.pyError && error.message) { errorMsg = error.message; }
                pddStatusDisplayDiv.textContent = `PDD Status: Error - ${errorMsg}`;
            }
        } else {
            pddStatusDisplayDiv.textContent = "PDD Status: Error - Invalid PDD parameter values.";
        }
    });
    
    document.querySelectorAll('input[name="qualityType"]').forEach(radio => {
        radio.addEventListener('change', (event) => {
            traceNodeIdInput.disabled = (event.target.value !== "TRACE");
            if (event.target.value !== "TRACE") traceNodeIdInput.value = ""; 
        });
    });

    applyQualitySettingsBtn.addEventListener('click', async () => {
        if (!globalThis.py_set_quality_type) {
            qualityStatusDisplayDiv.textContent = "Quality Status: Error - Python function not loaded."; return;
        }
        if (!globalThis.pyodide.globals.get('epanet_instance_py')) {
            qualityStatusDisplayDiv.textContent = "Quality Status: EPANET model not loaded."; return;
        }
        const selectedTypeRadio = document.querySelector('input[name="qualityType"]:checked');
        currentQualityType = selectedTypeRadio ? selectedTypeRadio.value : "NONE"; 
        currentTraceNodeId = (currentQualityType === "TRACE") ? traceNodeIdInput.value.trim() : ""; 

        if (currentQualityType === "TRACE" && !currentTraceNodeId) {
            qualityStatusDisplayDiv.textContent = "Quality Status: Trace Node ID is required for TRACE analysis."; return;
        }
        
        qualityStatusDisplayDiv.textContent = `Quality Status: Applying ${currentQualityType}...`;
        try {
            let message_proxy = globalThis.py_set_quality_type(currentQualityType, currentTraceNodeId);
            qualityStatusDisplayDiv.textContent = `Quality Status: ${message_proxy.toString()}`;
            message_proxy.destroy();
            simulationStatusDiv.textContent = "Status: Quality settings applied. Please Re-initialize Step Simulation.";
            initStepSimBtn.disabled = false; 
            runNextStepBtn.disabled = true;  
            nodeQualityDisplayDiv.textContent = 'Node Quality (-): -'; 
        } catch (error) {
            let errorMsg = error.message || String(error);
            if (error.pyError && error.message) { errorMsg = error.message; }
            qualityStatusDisplayDiv.textContent = `Quality Status: Error - ${errorMsg}`;
        }
    });

    // Initialize the application
    initializePyodideAndApp();
});
