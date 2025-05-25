print("Python: main_poc.py script started")
from epanet_shim import epanet # Assuming epanet_shim.py is in the same Pyodide FS path
from js import console # For logging to browser console
# Import actual version strings from the shim files
from epanetapi_shim import __epanetapi_shim_version__
from epanet_shim import __epanet_shim_version__

MAIN_POC_PY_VERSION = "v_main_1"

# This Python script (`main_poc.py`) serves as the bridge between the JavaScript UI
# and the Python EPANET simulation logic (provided by `epanet_shim.py` and `epanetapi_shim.py`).
# It defines functions that are directly callable from JavaScript via Pyodide.
# These functions manage a global instance of the `epanet_shim.epanet` class,
# allowing for persistent state of the EPANET model across multiple JS calls.

# Global variable to hold the current EPANET simulation instance.
# This instance is created/updated when a new INP file is loaded.
epanet_instance_py = None

# In main_poc.py

# Define actual versions of your Python files
# These should be updated whenever you change a file
# __epanetapi_shim_version__ = "1.0.0" # Now imported
# __epanet_shim_version__ = "1.0.1" # Now imported
__main_poc_version__ = "1.0.3" # Example version for main_poc.py
print(f"Python: main_poc.py version {__main_poc_version__} loaded.")

def get_epanetapi_shim_version_actual():
    return __epanetapi_shim_version__

def get_epanet_shim_version_actual():
    return __epanet_shim_version__

def get_main_poc_version_actual():
    return __main_poc_version__

# Make sure to include these in the 'export_functions' if you have such a mechanism,
# or ensure they are in the global scope if using pyodide.globals.get directly on them.
# For the provided script.js structure, they need to be importable.

def create_epanet_instance_from_inp(inp_content_str):
    """
    (Called from JavaScript)
    Creates or re-creates the global EPANET simulation instance (`epanet_instance_py`)
    using the provided INP file content. If an instance already exists, it's closed first.
    Args:
        inp_content_str (str): The full content of the .INP file as a string.
    Returns:
        str: A success or error message string.
    """
    global epanet_instance_py
    print(f"Python [Phase 1]: Received INP (first 300 chars): {inp_content_str[:300]}")
    console.log("Python (main_poc.py): create_epanet_instance_from_inp called.")
    
    # Gracefully close any existing instance and its analyses
    if epanet_instance_py is not None:
        try:
            console.log("Python: Closing existing EPANET instance...")
            if hasattr(epanet_instance_py, 'api') and epanet_instance_py.api is not None: # Check if instance was properly initialized
                try:
                    epanet_instance_py.closeQualityAnalysis() 
                    console.log("Python: Closed quality analysis of existing instance (if open).")
                except Exception as e_close_q:
                    console.log(f"Python: Info - No active quality analysis to close or error: {str(e_close_q)}")
                try:
                    epanet_instance_py.closeHydraulicAnalysis()
                    console.log("Python: Closed hydraulic analysis of existing instance (if open).")
                except Exception as e_close_h:
                    console.log(f"Python: Info - No active hydraulic analysis to close or error: {str(e_close_h)}")
            epanet_instance_py.closeNetwork() # Should close the EPANET project via shim
            console.log("Python: Closed network of existing instance.")
        except Exception as e_close_old:
            console.log(f"Python: Error closing existing EPANET instance: {str(e_close_old)}")
        finally:
            epanet_instance_py = None # Ensure it's cleared

    if not inp_content_str or not inp_content_str.strip():
        raise ValueError("INP file content for instance creation is empty.")
    
    # inp_content_str = "[TITLE]\nMinimal Test\n[JUNCTIONS]\nJ1 0 0\n[PIPES]\n[END]"
    print(f"Main POC: inp_content_str (first 500 chars): {inp_content_str[:500]}")
    console.log("Python: Initializing new epanet_shim.epanet instance...")
    epanet_instance_py = epanet(inp_content_str=inp_content_str) # Creates and opens the model
    if epanet_instance_py:
        print(f"Python [Phase 1]: epanet_instance_py created successfully. Version: {epanet_instance_py.getVersion()}")
    else:
        print("Python [Phase 1]: ERROR - epanet_instance_py is None after creation attempt.")
    console.log(f"Python: New EPANET instance created. Version: {epanet_instance_py.getVersion()}")
    return "Python: EPANET instance created successfully."

def get_network_topology_js():
    """
    (Called from JavaScript)
    Uses the global `epanet_instance_py` to extract and return the network topology.
    Returns:
        dict: A dictionary containing nodes and links data, suitable for Cytoscape.js.
              Pyodide converts this to a JsProxy.
    Raises:
        RuntimeError: If the EPANET instance is not initialized.
    """
    global epanet_instance_py
    # console.log("Python (main_poc.py): get_network_topology_js called.")
    if epanet_instance_py is None: raise RuntimeError("EPANET instance not initialized. Load INP file first.")
    topology = epanet_instance_py.get_network_topology()
    # console.log("Python: Topology extracted from current instance.")
    return topology

def open_hydraulic_analysis_js():
    """
    (Called from JavaScript)
    Opens the hydraulic analysis system on the global `epanet_instance_py`.
    Also attempts to open quality analysis if a quality type is set.
    Returns:
        str: A status message.
    Raises:
        RuntimeError: If the EPANET instance is not initialized.
    """
    global epanet_instance_py
    if epanet_instance_py is None: raise RuntimeError("EPANET instance not initialized.")
    epanet_instance_py.openHydraulicAnalysis()
    try: 
        epanet_instance_py.openQualityAnalysis()
        # console.log("Python: Quality analysis opened during hydraulic open.")
    except Exception as e_open_q:
        console.log(f"Python: Info - Could not open quality analysis (likely no quality type set): {str(e_open_q)}")
    return "Hydraulic analysis opened (and attempted quality open)."

def initialize_hydraulic_analysis_js(save_flag=0):
    """
    (Called from JavaScript)
    Initializes the hydraulic analysis (and quality analysis if applicable) on the global `epanet_instance_py`.
    Args:
        save_flag (int, optional): 0 for NOSAVE, 1 for SAVE. Defaults to 0.
    Returns:
        str: A status message.
    Raises:
        RuntimeError: If the EPANET instance is not initialized.
    """
    global epanet_instance_py
    if epanet_instance_py is None: raise RuntimeError("EPANET instance not initialized.")
    epanet_instance_py.initializeHydraulicAnalysis(save_flag)
    try: 
        epanet_instance_py.initializeQualityAnalysis(save_flag)
        # console.log(f"Python: Quality analysis initialized (save_flag={save_flag}).")
        return f"Hydraulic and Quality analyses initialized (save_flag={save_flag})."
    except Exception as e_init_q:
        console.log(f"Python: Info - Could not initialize quality analysis: {str(e_init_q)}")
        return f"Hydraulic analysis initialized (save_flag={save_flag}). Quality not initialized: {str(e_init_q)}"

def py_run_hydraulic_step_and_get_all_results():
    """
    (Called from JavaScript, renamed from run_single_hydraulic_step_js)
    Runs a single hydraulic step using the global `epanet_instance_py` and fetches
    pressures for all nodes and flows for all links.
    Returns:
        dict: Simulation results including current time, node pressures, link flows,
              time to next event, and any error. Pyodide converts to JsProxy.
    """
    global epanet_instance_py
    if epanet_instance_py is None: 
        return {'currentTime': -1, 'nodeResults': [], 'linkResults': [], 'nextEventTime': 0, 'error': "EPANET instance not initialized."}
    try:
        results = epanet_instance_py.run_hydraulic_step_and_get_all_results()
        if not isinstance(results, dict): # Should be a dict from the shim
             return {'error': str(results), 'currentTime': -1, 'nodeResults': [], 'linkResults': [], 'nextEventTime': 0}
        return results
    except Exception as e:
        error_msg = f"Python: Error in py_run_hydraulic_step_and_get_all_results: {str(e)}"
        console.log(error_msg)
        return {'currentTime': -1, 'nodeResults': [], 'linkResults': [], 'nextEventTime': 0, 'error': error_msg}

def close_hydraulic_analysis_js():
    """
    (Called from JavaScript)
    Closes the hydraulic (and quality) analysis systems on the global `epanet_instance_py`.
    Returns:
        str: A status message.
    """
    global epanet_instance_py
    if epanet_instance_py is None: return "No instance to close hydraulics for."
    msg_h = ""
    msg_q = ""
    try:
        epanet_instance_py.closeHydraulicAnalysis()
        msg_h = "Hydraulic analysis closed."
    except Exception as e:
        msg_h = f"Error closing hydraulic analysis: {str(e)}"
    try:
        epanet_instance_py.closeQualityAnalysis()
        msg_q = "Quality analysis closed."
    except Exception as e_close_q:
        msg_q = f"Info - No active quality analysis to close: {str(e_close_q)}"
    return f"{msg_h} {msg_q}".strip()

def set_emitter_coefficient_js(node_id_str, emitter_coeff_float):
    """
    (Called from JavaScript)
    Sets the emitter coefficient for a specified node on the global `epanet_instance_py`.
    Args:
        node_id_str (str): The ID of the node to modify.
        emitter_coeff_float (float): The new emitter coefficient value.
    Returns:
        str: A status or error message.
    """
    global epanet_instance_py
    # console.log(f"Python: set_emitter_coefficient_js for Node ID: {node_id_str}, Coeff: {emitter_coeff_float}")
    if epanet_instance_py is None: return "Error: EPANET instance not available."
    try:
        node_idx_list = epanet_instance_py.getNodeIndex([str(node_id_str)]) 
        if not node_idx_list: raise ValueError(f"Node ID '{node_id_str}' not found.")
        epanet_instance_py.setNodeEmitterCoeff(node_idx_list[0], float(emitter_coeff_float))
        # console.log(f"Python: Emitter for node {node_id_str} set to {emitter_coeff_float}.")
        return f"Leak applied to Node {node_id_str} with coefficient {emitter_coeff_float}. Ready for next step."
    except Exception as e: return f"Python: Error setting emitter for Node ID '{node_id_str}': {str(e)}"

def set_pdd_options_js(enable_pdd_bool, pmin_float, preq_float, pexp_float):
    """
    (Called from JavaScript)
    Sets the Pressure Dependent Demand (PDD) model options on the global `epanet_instance_py`.
    Args:
        enable_pdd_bool (bool): True to enable PDA, False for DDA.
        pmin_float (float): Minimum pressure for PDD.
        preq_float (float): Required pressure for PDD.
        pexp_float (float): Pressure exponent for PDD.
    Returns:
        str: A status or error message.
    """
    global epanet_instance_py
    # console.log(f"Python: set_pdd_options_js with Enable: {enable_pdd_bool}, Pmin: {pmin_float}, Preq: {preq_float}, Pexp: {pexp_float}")
    if epanet_instance_py is None: return "Error: EPANET instance not available."
    try:
        model_str = "PDA" if enable_pdd_bool else "DDA"
        epanet_instance_py.setDemandModel(model_str, float(pmin_float), float(preq_float), float(pexp_float))
        # console.log(f"Python: PDD model set to {model_str}.")
        return f"PDD model set to {model_str}. Please Re-initialize Step Simulation."
    except Exception as e: return f"Python: Error setting PDD options: {str(e)}"

def set_quality_type_js(quality_type_str, trace_node_id_str=""):
    """
    (Called from JavaScript)
    Sets the water quality simulation type on the global `epanet_instance_py`.
    Args:
        quality_type_str (str): "NONE", "AGE", or "TRACE".
        trace_node_id_str (str, optional): Node ID for TRACE analysis. Defaults to "".
    Returns:
        str: A status or error message.
    """
    global epanet_instance_py
    # console.log(f"Python: set_quality_type_js with Type: {quality_type_str}, Trace Node: '{trace_node_id_str}'")
    if epanet_instance_py is None: return "Error: EPANET instance not available."
    try:
        epanet_instance_py.setQualityType(quality_type_str.upper(), traceNode_id_str=trace_node_id_str)
        try: epanet_instance_py.closeQualityAnalysis() # Ensure Q is re-opened/re-initialized
        except Exception: pass 
        # console.log(f"Python: Quality type set to {quality_type_str}.")
        return f"Quality type set to {quality_type_str}. Please Re-initialize Step Simulation."
    except Exception as e: return f"Python: Error setting quality type: {str(e)}"

def run_quality_step_js(node_id_to_get_quality):
    """
    (Called from JavaScript)
    Runs a single water quality step using the global `epanet_instance_py` and retrieves
    the quality for a specified node.
    Args:
        node_id_to_get_quality (str): The ID of the node for which to retrieve quality.
    Returns:
        dict: Results including current quality time, node ID, quality value,
              time to next quality event, and any error. Pyodide converts to JsProxy.
    """
    global epanet_instance_py
    if epanet_instance_py is None: 
        return {'error': "EPANET instance not available.", 'currentTime': -1, 'quality': 0.0, 'nextQualityEventTime': 0, 'nodeId': str(node_id_to_get_quality)}
    try:
        results = epanet_instance_py.run_single_quality_step_for_js(str(node_id_to_get_quality))
        if not isinstance(results, dict): # Should be a dict from the shim
            return {'error': str(results), 'currentTime': -1, 'quality': 0.0, 'nextQualityEventTime': 0, 'nodeId': str(node_id_to_get_quality)}
        return results
    except Exception as e:
        return {'error': f"Python: Error in run_quality_step_js: {str(e)}", 'currentTime': -1, 'quality': 0.0, 'nextQualityEventTime': 0, 'nodeId': str(node_id_to_get_quality)}

console.log("Python: main_poc.py loaded and all functions defined for JS interaction.")

def get_main_poc_version():
    return MAIN_POC_PY_VERSION
