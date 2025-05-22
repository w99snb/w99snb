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
    globalThis.get_network_topology_from_python = null; 
    // globalThis.run_basic_simulation_from_python = null; // If simulation button is re-added
    globalThis.cy_instance = null;

    async function initializePyodideAndApp() {
        outputDiv.innerText = "Initializing Pyodide and EPANET tools...";
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
            
            // Import the specific function for topology
            globalThis.pyodide.runPython('from main_poc import get_network_topology_for_js');
            globalThis.get_network_topology_from_python = globalThis.pyodide.globals.get('get_network_topology_for_js');
            // If simulation is needed later:
            // pyodide.runPython('from main_poc import run_basic_simulation_for_js');
            // globalThis.run_basic_simulation_from_python = pyodide.globals.get('run_basic_simulation_for_js');

            outputDiv.innerText = "Ready to load .INP file.";
            console.log("JS: Python environment and functions ready.");

        } catch (error) {
            console.error("JS: Error during initialization:", error);
            outputDiv.innerText = `Initialization Error: ${error.message}. Check console.`;
            if(loadInpBtn) loadInpBtn.disabled = true;
        }
    }

    async function displayNetworkTopology(inp_content_str) {
        if (!globalThis.get_network_topology_from_python) {
            outputDiv.innerText = "Error: Topology function not loaded from Python.";
            console.error("JS: get_network_topology_from_python is not available.");
            return;
        }
        
        outputDiv.innerText = "Processing INP file and extracting topology...";
        console.log("JS: Calling Python to get network topology...");

        try {
            let topology_js_proxy = await globalThis.get_network_topology_from_python(inp_content_str);
            let topology = topology_js_proxy.toJs({ dict_converter: Object.fromEntries });
            topology_js_proxy.destroy();
            console.log("JS: Topology received from Python:", topology);

            if (!topology || !topology.nodes || !topology.links) {
                throw new Error("Invalid or empty topology data received from Python.");
            }

            if (globalThis.cy_instance) {
                globalThis.cy_instance.destroy();
                console.log("JS: Destroyed existing Cytoscape instance.");
            }

            const elements = [];
            const nodePositions = {}; // For preset layout

            topology.nodes.forEach(node => {
                elements.push({ 
                    data: { id: node.id, type: node.type, type_code: node.type_code },
                    // Cytoscape expects position at the top level of the node object for preset layout
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
                style: [
                    { selector: 'node', style: { 
                        'background-color': '#666', 'label': 'data(id)', 
                        'width': '25px', 'height': '25px', 
                        'font-size': '10px', 'color': '#333',
                        'text-valign': 'bottom', 'text-halign': 'center',
                        'text-outline-width': 1, 'text-outline-color': '#fff'
                    }},
                    { selector: 'node[type="junction"]', style: { 
                        'background-color': '#808080', /* Grey for junctions */
                        'shape': 'ellipse' 
                    }},
                    { selector: 'node[type="tank"]', style: { 
                        'background-color': '#add8e6', /* Light Blue for tanks */
                        'shape': 'rectangle', 
                        'width': '30px', 'height': '40px' 
                    }},
                    { selector: 'node[type="reservoir"]', style: { 
                        'background-color': '#90ee90', /* Light Green for reservoirs */
                        'shape': 'diamond', 
                        'width': '35px', 'height': '35px' 
                    }},
                    { selector: 'edge', style: { 
                        'width': 2.5, 
                        'line-color': '#b0c4de', /* Light Steel Blue for pipes */
                        'target-arrow-shape': 'none', 
                        'curve-style': 'haystack' // Changed from bezier for simplicity with preset
                    }}
                ],
                layout: { 
                    name: 'preset',
                    // 'positions' field is implicitly used by preset layout from node objects
                },
                zoom: 1,
                pan: { x: 0, y: 0 },
                minZoom: 0.1,
                maxZoom: 4
            });
            
            globalThis.cy_instance.center();
            globalThis.cy_instance.fit(null, 30); // Fit with 30px padding
            console.log("JS: Cytoscape network rendered.");
            outputDiv.innerText = `Network displayed: ${topology.nodes.length} nodes, ${topology.links.length} links.`;

        } catch (error) {
            console.error("JS: Error in displayNetworkTopology:", error);
            let errorMsg = error.message || String(error);
            if (error.pyError) { errorMsg = error.message; }
            outputDiv.innerText = `Error displaying topology: ${errorMsg}. Check console.`;
            // Clear Cytoscape container on error
            if (globalThis.cy_instance) globalThis.cy_instance.destroy();
            cyContainer.innerHTML = '<p style="text-align:center; color:red;">Could not render network.</p>';
        }
    }

    if (loadInpBtn) {
        loadInpBtn.addEventListener('click', () => {
            if (inpFileElement) inpFileElement.click();
        });
    }

    if (inpFileElement) {
        inpFileElement.addEventListener('change', (event) => {
            const file = event.target.files[0];
            if (file) {
                if (file.name.toLowerCase().endsWith('.inp')) {
                    if(fileNameDisplay) fileNameDisplay.textContent = `Selected: ${file.name}`;
                    outputDiv.innerText = `Reading file: ${file.name}...`;
                    
                    const reader = new FileReader();
                    reader.onload = async (e) => {
                        const inp_content_str = e.target.result;
                        await displayNetworkTopology(inp_content_str);
                    };
                    reader.onerror = () => {
                        console.error("JS: FileReader error.");
                        outputDiv.innerText = "Error reading file.";
                        if(fileNameDisplay) fileNameDisplay.textContent = "Error reading file.";
                    };
                    reader.readAsText(file);
                } else {
                    alert("Please select a valid .INP file.");
                    outputDiv.innerText = "Invalid file type. Please select an .INP file.";
                    if(fileNameDisplay) fileNameDisplay.textContent = "No file selected.";
                    inpFileElement.value = ''; // Reset file input
                }
            } else {
                 if(fileNameDisplay) fileNameDisplay.textContent = "No file selected.";
            }
        });
    }

    // Initialize the application
    initializePyodideAndApp();
});
