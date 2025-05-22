document.addEventListener('DOMContentLoaded', async () => {
    const loadInpBtn = document.getElementById('loadInpBtn');
    const inpFileElement = document.getElementById('inpFile');
    const fileNameDisplay = document.getElementById('fileNameDisplay');
    const outputDiv = document.getElementById('output');
    const cyContainer = document.getElementById('cy');

    // Global instances
    globalThis.pyodide = null;
    globalThis.epanetJsWorkspace = null;
    globalThis.epanetJsProject = null;
    
    // Python function proxies from main_poc.py
    globalThis.py_create_epanet_instance = null;
    globalThis.py_get_network_topology = null;
    globalThis.py_open_hydraulic_analysis = null;
    globalThis.py_initialize_hydraulic_analysis = null;
    globalThis.py_run_single_hydraulic_step = null;
    globalThis.py_close_hydraulic_analysis = null;
    globalThis.py_set_emitter_coefficient = null;
    globalThis.py_set_pdd_options = null; 
    globalThis.py_set_quality_type = null; // For Quality settings
    globalThis.py_run_quality_step = null; // For Quality settings

    globalThis.cy_instance = null; // Cytoscape instance

    // UI elements
    const initStepSimBtn = document.getElementById('initStepSimBtn');
    const runNextStepBtn = document.getElementById('runNextStepBtn');
    const applyLeakBtn = document.getElementById('applyLeakBtn');
    const leakNodeIdInput = document.getElementById('leakNodeIdInput');
    const emitterCoeffInput = document.getElementById('emitterCoeffInput');
    const leakStatusDisplayDiv = document.getElementById('leakStatusDisplay');
    
    // PDD UI Elements
    const pddEnableSwitch = document.getElementById('pddEnableSwitch');
    const pddPminInput = document.getElementById('pddPminInput');
    const pddPreqInput = document.getElementById('pddPreqInput');
    const pddPexpInput = document.getElementById('pddPexpInput');
    const applyPddSettingsBtn = document.getElementById('applyPddSettingsBtn');
    const pddStatusDisplayDiv = document.getElementById('pddStatusDisplay');

    // Quality UI Elements
    const qualityTypeNoneRadio = document.getElementById('qualityTypeNone');
    const qualityTypeAgeRadio = document.getElementById('qualityTypeAge');
    const qualityTypeTraceRadio = document.getElementById('qualityTypeTrace');
    const traceNodeIdInput = document.getElementById('traceNodeIdInput');
    const applyQualitySettingsBtn = document.getElementById('applyQualitySettingsBtn');
    const qualityStatusDisplayDiv = document.getElementById('qualityStatusDisplay');
    const nodeQualityDisplayDiv = document.getElementById('nodeQualityDisplay');
    
    const simulationStatusDiv = document.getElementById('simulationStatus');
    const currentTimeDisplayDiv = document.getElementById('currentTimeDisplay');
    const nodePressureDisplayDiv = document.getElementById('nodePressureDisplay');
    const linkFlowDisplayDiv = document.getElementById('linkFlowDisplay');

    // Default node/link IDs to monitor - these will be updated if not found in the loaded INP.
    let node_to_monitor = "J1"; 
    let link_to_monitor = "P1";

    async function initializePyodideAndApp() {
        simulationStatusDiv.textContent = "Status: Initializing Pyodide and EPANET tools...";
        try {
            globalThis.pyodide = await loadPyodide();
            console.log("JS: Pyodide initialized.");

            if (typeof epanetjs !== 'undefined' && epanetjs.Workspace && epanetjs.Project) {
                globalThis.epanetJsWorkspace = new epanetjs.Workspace();
                globalThis.epanetJsProject = new epanetjs.Project(globalThis.epanetJsWorkspace);
                console.log("JS: epanet-js Workspace and Project initialized.");
            } else {
                throw new Error("epanet-js is not loaded or does not have Workspace/Project.");
            }

            const scriptsToLoad = ['epanetapi_shim.py', 'epanet_shim.py', 'main_poc.py'];
            for (const scriptName of scriptsToLoad) {
                const scriptContent = await (await fetch(scriptName)).text();
                globalThis.pyodide.FS.writeFile(scriptName, scriptContent);
                console.log(`JS: Loaded ${scriptName} into Pyodide FS.`);
            }
            
            // Import the functions from main_poc.py
            // These functions operate on the global epanet_instance_py in Python
            globalThis.pyodide.runPython(`
from main_poc import (
    create_epanet_instance_from_inp,
    get_network_topology_js,
    open_hydraulic_analysis_js,
    initialize_hydraulic_analysis_js,
    run_single_hydraulic_step_js,
    close_hydraulic_analysis_js 
    # close_network_js is available but not critical for this step-by-step UI yet
)
            `);
            globalThis.py_create_epanet_instance = globalThis.pyodide.globals.get('create_epanet_instance_from_inp');
            globalThis.py_get_network_topology = globalThis.pyodide.globals.get('get_network_topology_js');
            globalThis.py_open_hydraulic_analysis = globalThis.pyodide.globals.get('open_hydraulic_analysis_js');
            globalThis.py_initialize_hydraulic_analysis = globalThis.pyodide.globals.get('initialize_hydraulic_analysis_js');
            globalThis.py_run_single_hydraulic_step = globalThis.pyodide.globals.get('run_single_hydraulic_step_js');
            globalThis.py_close_hydraulic_analysis = globalThis.pyodide.globals.get('close_hydraulic_analysis_js');
    globalThis.py_set_emitter_coefficient = globalThis.pyodide.globals.get('set_emitter_coefficient_js');
    globalThis.py_set_pdd_options = globalThis.pyodide.globals.get('set_pdd_options_js');
    globalThis.py_set_quality_type = globalThis.pyodide.globals.get('set_quality_type_js');
    globalThis.py_run_quality_step = globalThis.pyodide.globals.get('run_quality_step_js');
            
            simulationStatusDiv.textContent = "Status: Ready to load .INP file.";
            outputDiv.innerText = "Pyodide, Python scripts, and epanet-js ready."; // General status for other messages
            console.log("JS: Python environment and functions ready.");

        } catch (error) {
            console.error("JS: Error during initialization:", error);
            simulationStatusDiv.textContent = `Status: Initialization Error. Check console.`;
            outputDiv.innerText = `Initialization Error: ${error.message}.`;
            if(loadInpBtn) loadInpBtn.disabled = true;
        }
    }

    async function displayNetworkTopology(inp_content_str) {
        if (!globalThis.py_create_epanet_instance || !globalThis.py_get_network_topology) {
            simulationStatusDiv.textContent = "Status: Error - Core Python functions not loaded.";
            outputDiv.innerText = "Error: Core Python functions not loaded.";
            console.error("JS: Python instance or topology functions are not available.");
            return;
        }
        
        simulationStatusDiv.textContent = "Status: Processing INP file...";
        outputDiv.innerText = "Creating EPANET instance and extracting topology...";
        console.log("JS: Calling Python to create instance and get network topology...");

        try {
            // Create/Re-create the EPANET instance in Python
            // This call handles closing previous instance/hydraulics if any.
            let instance_msg_proxy = globalThis.py_create_epanet_instance(inp_content_str);
            let instance_msg = instance_msg_proxy.toString();
            instance_msg_proxy.destroy();
            console.log(`JS: Python create_epanet_instance says: ${instance_msg}`);

            // Now get topology from the newly created instance
            let topology_js_proxy = globalThis.py_get_network_topology();
            let topology = topology_js_proxy.toJs({ dict_converter: Object.fromEntries });
            topology_js_proxy.destroy();
            console.log("JS: Topology received from Python:", topology);

            if (!topology || !topology.nodes || !topology.links) {
                throw new Error("Invalid or empty topology data received from Python.");
            }
            
             // Update monitored elements if they exist in the new network, or set to N/A
            if (topology.nodes.length > 0) {
                const nodeExists = topology.nodes.some(n => n.id === node_to_monitor);
                if (!nodeExists) node_to_monitor = topology.nodes[0].id; // Fallback to first node
            } else { node_to_monitor = "N/A"; } // No nodes in network

            if (topology.links.length > 0) {
                const linkExists = topology.links.some(l => l.id === link_to_monitor);
                if (!linkExists) link_to_monitor = topology.links[0].id; // Fallback to first link
            } else { link_to_monitor = "N/A"; } // No links in network
            }


            if (globalThis.cy_instance) {
                globalThis.cy_instance.destroy();
                console.log("JS: Destroyed existing Cytoscape instance.");
            }

            const elements = [];
            // nodePositions map is not needed if positions are part of node data for cytoscape preset layout
            topology.nodes.forEach(node => {
                elements.push({ 
                    data: { id: node.id, type: node.type, type_code: node.type_code },
                    position: { x: parseFloat(node.x) || 0, y: parseFloat(node.y) || 0 } 
                });
            });

            topology.links.forEach(link => {
                elements.push({ 
                    data: { id: link.id, source: link.source, target: link.target } 
                });
            });
            
            outputDiv.innerText = `Rendering network: ${topology.nodes.length} nodes, ${topology.links.length} links.`;

            globalThis.cy_instance = cytoscape({
                container: cyContainer,
                elements: elements,
                style: [ // Same style as before, can be refactored
                    { selector: 'node', style: { 'background-color': '#666', 'label': 'data(id)', 'width': '25px', 'height': '25px', 'font-size': '10px', 'color': '#333', 'text-valign': 'bottom', 'text-halign': 'center', 'text-outline-width': 1, 'text-outline-color': '#fff' }},
                    { selector: 'node[type="junction"]', style: { 'background-color': '#808080', 'shape': 'ellipse' }},
                    { selector: 'node[type="tank"]', style: { 'background-color': '#add8e6', 'shape': 'rectangle', 'width': '30px', 'height': '40px' }},
                    { selector: 'node[type="reservoir"]', style: { 'background-color': '#90ee90', 'shape': 'diamond', 'width': '35px', 'height': '35px' }},
                    { selector: 'edge', style: { 'width': 2.5, 'line-color': '#b0c4de', 'target-arrow-shape': 'none', 'curve-style': 'haystack' }}
                ],
                layout: { name: 'preset' },
                zoom: 1, pan: { x: 0, y: 0 }, minZoom: 0.1, maxZoom: 4
            });
            
            globalThis.cy_instance.center();
            globalThis.cy_instance.fit(null, 30);
            console.log("JS: Cytoscape network rendered.");
            
            // Enable init button, disable run next step
            initStepSimBtn.disabled = false;
            runNextStepBtn.disabled = true;
            simulationStatusDiv.textContent = 'Status: Network loaded. Ready to initialize step simulation.';
            outputDiv.innerText = `Network displayed: ${topology.nodes.length} nodes, ${topology.links.length} links.`; // General message
            currentTimeDisplayDiv.textContent = 'Current Time: -';
            nodePressureDisplayDiv.textContent = `Node Pressure (${node_to_monitor}): -`;
            linkFlowDisplayDiv.textContent = `Link Flow (${link_to_monitor}): -`;


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

    loadInpBtn.addEventListener('click', () => {
        if (inpFileElement) inpFileElement.click();
    });

    inpFileElement.addEventListener('change', (event) => {
        const file = event.target.files[0];
        if (file) {
            if (file.name.toLowerCase().endsWith('.inp')) {
                fileNameDisplay.textContent = `Selected: ${file.name}`;
                simulationStatusDiv.textContent = `Status: Reading file ${file.name}...`;
                outputDiv.innerText = `Reading file: ${file.name}...`; // General message
                
                const reader = new FileReader();
                reader.onload = async (e) => {
                    const inp_content_str = e.target.result;
                    // No need to store in globalThis.current_inp_content if Python instance management is robust
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
                alert("Please select a valid .INP file.");
                simulationStatusDiv.textContent = "Status: Invalid file type.";
                outputDiv.innerText = "Invalid file type. Please select an .INP file.";
                fileNameDisplay.textContent = "No file selected.";
                inpFileElement.value = ''; 
            }
        } else {
             fileNameDisplay.textContent = "No file selected.";
        }
    });

    initStepSimBtn.addEventListener('click', async () => {
        if (!globalThis.py_open_hydraulic_analysis || !globalThis.py_initialize_hydraulic_analysis) {
            simulationStatusDiv.textContent = "Status: Error - Python simulation functions not loaded.";
            outputDiv.innerText = "Error: Python simulation functions not loaded."; // General message
            return;
        }
        simulationStatusDiv.textContent = 'Status: Initializing step simulation...';
        try {
            let msg_proxy_open = globalThis.py_open_hydraulic_analysis();
            console.log("JS: py_open_hydraulic_analysis: " + msg_proxy_open.toString());
            msg_proxy_open.destroy();

            // Parameter 0 for NOSAVE, 1 for SAVE. EPyT uses 0 for NOSAVE.
            let msg_proxy_init = globalThis.py_initialize_hydraulic_analysis(0); 
            console.log("JS: py_initialize_hydraulic_analysis: " + msg_proxy_init.toString());
            msg_proxy_init.destroy();
            
            runNextStepBtn.disabled = false;
            initStepSimBtn.disabled = true;
            simulationStatusDiv.textContent = 'Status: Step simulation initialized. Ready for next step.';
            currentTimeDisplayDiv.textContent = 'Current Time: 0.00 hrs';
            nodePressureDisplayDiv.textContent = `Node Pressure (${node_to_monitor}): -`; 
            linkFlowDisplayDiv.textContent = `Link Flow (${link_to_monitor}): -`;    
        } catch (error) {
            console.error("JS: Error initializing step simulation:", error);
            simulationStatusDiv.textContent = 'Status: Error initializing simulation.';
            let errorMsg = error.message || String(error);
            if (error.pyError && error.message) { errorMsg = error.message; }
            outputDiv.innerText = `Error: ${errorMsg}`; // General message
            runNextStepBtn.disabled = true; 
        }
    });

    runNextStepBtn.addEventListener('click', async () => {
        if (!globalThis.py_run_single_hydraulic_step) {
            simulationStatusDiv.textContent = "Status: Error - Python run step function not loaded.";
            outputDiv.innerText = "Error: Python run step function not loaded."; // General message
            return;
        }
        simulationStatusDiv.textContent = 'Status: Running next hydraulic step...';
        try {
            // Use the globally maintained node_to_monitor and link_to_monitor
            if (node_to_monitor === "N/A" || link_to_monitor === "N/A") {
                 throw new Error("Cannot run step: Monitored node/link is N/A. Load a valid network.");
            }

            let results_proxy = globalThis.py_run_single_hydraulic_step(node_to_monitor, link_to_monitor);
            let results = results_proxy.toJs({ dict_converter: Object.fromEntries });
            results_proxy.destroy();

            if (results.error) {
                throw new Error(results.error); // Propagate Python error
            }

            currentTimeDisplayDiv.textContent = `Current Time: ${(results.currentTime / 3600).toFixed(2)} hrs`;
            nodePressureDisplayDiv.textContent = `Node Pressure (${results.nodeId}): ${results.pressure.toFixed(2)}`;
            linkFlowDisplayDiv.textContent = `Link Flow (${results.linkId}): ${results.flow.toFixed(2)}`;

            if (results.nextEventTime <= 0) {
                runNextStepBtn.disabled = true;
                initStepSimBtn.disabled = false; // Allow re-initialization
                simulationStatusDiv.textContent = 'Status: Hydraulic simulation ended.';
                outputDiv.innerText = "Simulation ended. Initialize again or load new INP."; // General message
            } else {
                simulationStatusDiv.textContent = 'Status: Ready for next step.';
            }
        } catch (error) {
            console.error("JS: Error running next hydraulic step:", error);
            simulationStatusDiv.textContent = 'Status: Error during step execution.';
            let errorMsg = error.message || String(error);
            outputDiv.innerText = `Error: ${errorMsg}`; // General message
            runNextStepBtn.disabled = true; 
            initStepSimBtn.disabled = false; // Allow re-initialization on error
        }
    });

    // Global state for current quality simulation
    let currentQualityType = "NONE";
    let currentTraceNodeId = "";

    initializePyodideAndApp();

    // Event listener for quality type radio buttons
    document.querySelectorAll('input[name="qualityType"]').forEach(radio => {
        radio.addEventListener('change', (event) => {
            traceNodeIdInput.disabled = (event.target.value !== "TRACE");
            if (event.target.value !== "TRACE") {
                traceNodeIdInput.value = ""; // Clear if not TRACE
            }
        });
    });

    applyQualitySettingsBtn.addEventListener('click', async () => {
        if (!globalThis.py_set_quality_type) {
            qualityStatusDisplayDiv.textContent = "Quality Status: Error - Python function not loaded.";
            return;
        }
        if (!globalThis.pyodide.globals.get('epanet_instance_py')) {
            qualityStatusDisplayDiv.textContent = "Quality Status: EPANET model not loaded.";
            return;
        }

        const selectedTypeRadio = document.querySelector('input[name="qualityType"]:checked');
        currentQualityType = selectedTypeRadio ? selectedTypeRadio.value : "NONE";
        currentTraceNodeId = (currentQualityType === "TRACE") ? traceNodeIdInput.value.trim() : "";

        if (currentQualityType === "TRACE" && !currentTraceNodeId) {
            qualityStatusDisplayDiv.textContent = "Quality Status: Trace Node ID is required for TRACE analysis.";
            return;
        }
        
        qualityStatusDisplayDiv.textContent = `Quality Status: Applying ${currentQualityType}...`;
        try {
            let message_proxy = globalThis.py_set_quality_type(currentQualityType, currentTraceNodeId);
            let message = message_proxy.toString();
            message_proxy.destroy();

            qualityStatusDisplayDiv.textContent = `Quality Status: ${message}`;
            simulationStatusDiv.textContent = "Status: Quality settings applied. Please Re-initialize Step Simulation.";
            initStepSimBtn.disabled = false; // Allow re-initialization
            runNextStepBtn.disabled = true;  // Force re-initialization
            nodeQualityDisplayDiv.textContent = 'Node Quality (-): -'; // Reset display
        } catch (error) {
            let errorMsg = error.message || String(error);
            if (error.pyError && error.message) { errorMsg = error.message; }
            qualityStatusDisplayDiv.textContent = `Quality Status: Error - ${errorMsg}`;
        }
    });


    // Modify initStepSimBtn listener
    initStepSimBtn.addEventListener('click', async () => {
        if (!globalThis.py_open_hydraulic_analysis || !globalThis.py_initialize_hydraulic_analysis) {
            simulationStatusDiv.textContent = "Status: Error - Python simulation functions not loaded.";
            return;
        }
        simulationStatusDiv.textContent = 'Status: Initializing step simulation...';
        try {
            let msg_proxy_open_h = globalThis.py_open_hydraulic_analysis(); // This now also calls openQ in Python
            console.log("JS: py_open_hydraulic_analysis: " + msg_proxy_open_h.toString());
            msg_proxy_open_h.destroy();

            // Parameter 0 for NOSAVE, 1 for SAVE.
            let msg_proxy_init_h = globalThis.py_initialize_hydraulic_analysis(0); // This now also calls initQ in Python
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

    // Modify runNextStepBtn listener
    runNextStepBtn.addEventListener('click', async () => {
        if (!globalThis.py_run_single_hydraulic_step) {
            simulationStatusDiv.textContent = "Status: Error - Python run step function not loaded.";
            return;
        }
        simulationStatusDiv.textContent = 'Status: Running next hydraulic step...';
        try {
            let node_to_check_pressure = node_to_monitor;
            let link_to_check_flow = link_to_monitor;
            let node_for_quality_val = node_to_monitor; // Use the same node for quality for simplicity

            if (globalThis.cy_instance) { // Fallbacks if default elements don't exist
                 if (node_to_monitor === "N/A" && globalThis.cy_instance.nodes().length > 0) {
                    node_to_check_pressure = globalThis.cy_instance.nodes()[0].id(); 
                    node_for_quality_val = node_to_check_pressure;
                    node_to_monitor = node_to_check_pressure;
                 } else if (node_to_monitor === "N/A") { node_to_check_pressure = "N/A"; node_for_quality_val = "N/A"; }
                 
                 if (link_to_monitor === "N/A" && globalThis.cy_instance.edges().length > 0) {
                    link_to_check_flow = globalThis.cy_instance.edges()[0].id(); 
                    link_to_monitor = link_to_check_flow;
                 } else if (link_to_monitor === "N/A") { link_to_check_flow = "N/A"; }
            }
            if (node_to_check_pressure === "N/A" || link_to_check_flow === "N/A") {
                 throw new Error("Cannot run step: Monitored node/link is N/A. Load a valid network.");
            }

            let results_proxy = globalThis.py_run_single_hydraulic_step(node_to_check_pressure, link_to_check_flow);
            let results = results_proxy.toJs({ dict_converter: Object.fromEntries });
            results_proxy.destroy();

            if (results.error) { throw new Error(results.error); }

            currentTimeDisplayDiv.textContent = `Current Time: ${(results.currentTime / 3600).toFixed(2)} hrs`;
            nodePressureDisplayDiv.textContent = `Node Pressure (${results.nodeId}): ${results.pressure.toFixed(2)}`;
            linkFlowDisplayDiv.textContent = `Link Flow (${results.linkId}): ${results.flow.toFixed(2)}`;

            // Run quality step if enabled
            if (currentQualityType !== "NONE" && globalThis.py_run_quality_step) {
                if(node_for_quality_val === "N/A") {
                    nodeQualityDisplayDiv.textContent = `Node Quality (${currentQualityType}): N/A (No valid node)`;
                } else {
                    simulationStatusDiv.textContent = 'Status: Running quality step...';
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

            if (results.nextEventTime <= 0) { // End of simulation (hydraulics)
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


    applyLeakBtn.addEventListener('click', async () => {
        if (!globalThis.py_set_emitter_coefficient) {
            leakStatusDisplayDiv.textContent = "Leak Status: Error - Python function for setting leak not loaded.";
            console.error("JS: py_set_emitter_coefficient is not available.");
            return;
        }
        if (!globalThis.pyodide.globals.get('epanet_instance_py')) { 
            leakStatusDisplayDiv.textContent = "Leak Status: EPANET model not loaded/initialized in Python.";
            simulationStatusDiv.textContent = "Status: Error - Load INP and initialize simulation first.";
            return;
        }

        const nodeId = leakNodeIdInput.value.trim();
        const coeff = parseFloat(emitterCoeffInput.value);

        if (nodeId && !isNaN(coeff) && coeff >= 0) {
            leakStatusDisplayDiv.textContent = `Leak Status: Attempting to apply leak to Node ${nodeId} with coeff ${coeff}...`;
            try {
                let message_proxy = globalThis.py_set_emitter_coefficient(nodeId, coeff);
                let message = message_proxy.toString();
                message_proxy.destroy();
                
                leakStatusDisplayDiv.textContent = `Leak Status: ${message}`;
                // simulationStatusDiv.textContent = "Status: Leak parameter applied. Run next step to see effect.";
                // The message from Python already guides the user.
                console.log("JavaScript: Attempted to set leak. Python responded:", message);
            } catch (error) {
                console.error("JS: Error calling py_set_emitter_coefficient:", error);
                let errorMsg = error.message || String(error);
                if (error.pyError && error.message) { errorMsg = error.message; }
                leakStatusDisplayDiv.textContent = `Leak Status: Error - ${errorMsg}`;
                // simulationStatusDiv.textContent = "Status: Error applying leak parameter.";
            }
        } else {
            leakStatusDisplayDiv.textContent = "Leak Status: Error - Invalid Node ID or Coefficient value.";
            // simulationStatusDiv.textContent = "Status: Invalid input for leak parameter.";
        }
    });

    applyPddSettingsBtn.addEventListener('click', async () => {
        if (!globalThis.py_set_pdd_options) {
            pddStatusDisplayDiv.textContent = "PDD Status: Error - Python function for PDD not loaded.";
            console.error("JS: py_set_pdd_options is not available.");
            return;
        }
         if (!globalThis.pyodide.globals.get('epanet_instance_py')) { 
            pddStatusDisplayDiv.textContent = "PDD Status: EPANET model not loaded/initialized in Python.";
            simulationStatusDiv.textContent = "Status: Error - Load INP first.";
            return;
        }

        const enabled = pddEnableSwitch.checked;
        const pmin = parseFloat(pddPminInput.value);
        const preq = parseFloat(pddPreqInput.value);
        const pexp = parseFloat(pddPexpInput.value);

        if (!isNaN(pmin) && !isNaN(preq) && !isNaN(pexp)) {
            pddStatusDisplayDiv.textContent = `PDD Status: Applying settings (Enabled: ${enabled}, Pmin: ${pmin}, Preq: ${preq}, Pexp: ${pexp})...`;
            try {
                let message_proxy = globalThis.py_set_pdd_options(enabled, pmin, preq, pexp);
                let message = message_proxy.toString();
                message_proxy.destroy();

                pddStatusDisplayDiv.textContent = `PDD Status: ${message}`;
                simulationStatusDiv.textContent = "Status: PDD settings applied. Please Initialize/Re-initialize Step Simulation.";
                initStepSimBtn.disabled = false; // Allow re-initialization
                runNextStepBtn.disabled = true;  // Force re-initialization
                console.log("JavaScript: Attempted to set PDD options. Python responded:", message);
            } catch (error) {
                console.error("JS: Error calling py_set_pdd_options:", error);
                let errorMsg = error.message || String(error);
                if (error.pyError && error.message) { errorMsg = error.message; }
                pddStatusDisplayDiv.textContent = `PDD Status: Error - ${errorMsg}`;
                simulationStatusDiv.textContent = "Status: Error applying PDD settings.";
            }
        } else {
            pddStatusDisplayDiv.textContent = "PDD Status: Error - Invalid PDD parameter values.";
            simulationStatusDiv.textContent = "Status: Invalid input for PDD parameters.";
        }
    });
});
});
