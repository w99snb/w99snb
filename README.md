# EPANET Web Simulator (Pyodide PoC)

## Description

A proof-of-concept web-based EPANET simulator using Python (via Pyodide and EPyT-like shims) and epanet-js for client-side hydraulic and water quality simulations. Features interactive controls and network visualization.

This application allows users to load standard EPANET .INP files, visualize the network topology, run step-by-step hydraulic and basic water quality simulations, modify certain parameters dynamically (like leaks and PDD settings), and see results reflected on the network map.

## Features Implemented

*   **INP File Loading:** Users can load local .INP files into the application.
*   **Network Visualization:** Displays the network topology using Cytoscape.js, rendering nodes at their specified coordinates with basic styling to differentiate junctions, tanks, and reservoirs.
*   **Step-by-Step Hydraulic Simulation:**
    *   Initialize hydraulic simulation.
    *   Run hydraulic simulation step-by-step.
    *   View current simulation time.
*   **Dynamic Network Map Styling:**
    *   Node colors change dynamically based on pressure (Red for low, Yellow for medium, Green for high).
    *   Link widths change dynamically based on flow rate.
*   **Dynamic Parameter Modification:**
    *   **Leaks:** Apply or modify emitter coefficients for specified nodes during the simulation.
    *   **PDD (Pressure Dependent Demand):** Enable/disable PDD and set Pmin, Preq, and Pexp parameters.
*   **Basic Water Quality Simulation:**
    *   Supports "Age" and "Trace" (with a specified trace node ID) quality simulations.
    *   Displays quality results for a monitored node after each step.
*   **Interactive UI:** Controls for loading files, initializing/stepping through simulations, and applying parameter changes. Status messages provide feedback to the user.

## Setup and Running

1.  **Local Web Server:** Requires a local web server to serve `index.html` and associated `.js` and `.py` files. This is necessary due to browser security policies (CORS) for loading Pyodide/WebAssembly and fetching local Python script files.
    *   A simple way to start a server is using Python: `python -m http.server` (Python 3) or `python -m SimpleHTTPServer` (Python 2) in the project's root directory.
    *   Then, open your browser to `http://localhost:8000` (or the port indicated by the server).
2.  **Browser:** Ensure JavaScript is enabled in your web browser. Modern browsers (Chrome, Firefox, Edge, Safari) are recommended.
3.  **Libraries:** All required JavaScript libraries (`Pyodide`, `epanet-js`, `@model-create/epanet-engine`, `Cytoscape.js`) are loaded via CDN (jsDelivr) in `index.html`, so no local installation of these libraries is needed beyond having an internet connection when first loading the page.

## File Structure

*   `index.html`: The main HTML file that structures the web page and includes all scripts and UI elements.
*   `script.js`: Handles all client-side UI logic, user interactions, Pyodide initialization, communication with Python functions, and Cytoscape.js graph rendering and updates.
*   `epanetapi_shim.py`: A low-level Python shim that emulates the EPANET C API. It translates these API calls into method calls for the `epanet-js` library (which runs in the JavaScript environment).
*   `epanet_shim.py`: A higher-level Python class that provides an EPyT-like interface, making it easier to work with EPANET models and simulations. It uses `epanetapi_shim.py` for its operations.
*   `main_poc.py`: Contains the Python functions that are directly called by JavaScript (via Pyodide). These functions manage the global EPANET simulation instance and orchestrate calls to `epanet_shim.py`.

## Known Issues/Limitations

*   **Error Handling:** Error handling is basic. More comprehensive error reporting and recovery mechanisms could be implemented.
*   **UI Styling:** The UI styling is functional and uses basic Material Design 3-inspired elements. A full MD3 component library or more detailed CSS work would enhance the visual polish.
*   **Performance:** For very large INP files or extremely long simulations, client-side performance might be a consideration, although `epanet-js` and Pyodide are generally efficient.
*   **Feature Completeness:** This is a proof-of-concept and does not implement the full range of EPANET features (e.g., complex controls, all report types, advanced quality modeling options, saving/exporting modified INP or results).
*   **Time-Series Plots:** Dynamic time-series plots for node/link results are not yet implemented.
*   **Monitored Elements:** Currently, only one node and one link are monitored for detailed display of pressure/flow/quality in the text area, though the map visualizes all elements. User selection of monitored elements could be added.

## Future Development Ideas

*   Implement user selection for monitored nodes/links.
*   Add time-series plotting of simulation results.
*   Support for saving modified INP files or simulation results.
*   More advanced UI for editing network components and parameters.
*   Integration with more comprehensive Material Design component libraries.
*   Further performance optimizations for larger networks.
*   Expanded water quality modeling options.
*   Support for running EPANET rules.

This PoC demonstrates the feasibility of a rich, interactive, client-side EPANET simulation environment.
