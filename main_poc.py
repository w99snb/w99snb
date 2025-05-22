from epanet_shim import epanet # Assuming epanet_shim.py is in the same Pyodide FS path
from js import console # For logging to browser console

# Global variable to hold the current EPANET instance
epanet_instance_py = None

def create_epanet_instance_from_inp(inp_content_str):
    """
    Creates or re-creates the global epanet_instance_py with new INP content.
    This instance is then used by other functions.
    """
    global epanet_instance_py
    console.log("Python (main_poc.py): create_epanet_instance_from_inp called.")
    
    if epanet_instance_py is not None:
        try:
            console.log("Python: Closing existing EPANET instance...")
            if hasattr(epanet_instance_py, 'api') and epanet_instance_py.api is not None:
                try:
                    epanet_instance_py.closeQualityAnalysis() # Close quality first
                    console.log("Python: Closed quality analysis of existing instance (if open).")
                except Exception as e_close_q:
                    console.log(f"Python: Info - No active quality analysis to close or error closing: {str(e_close_q)}")
                try:
                    epanet_instance_py.closeHydraulicAnalysis()
                    console.log("Python: Closed hydraulic analysis of existing instance (if open).")
                except Exception as e_close_h:
                    console.log(f"Python: Info - No active hydraulic analysis to close or error closing: {str(e_close_h)}")
            
            epanet_instance_py.closeNetwork() 
            console.log("Python: Closed network of existing instance.")
        except Exception as e_close_old:
            console.log(f"Python: Error closing existing EPANET instance: {str(e_close_old)}")
        finally:
            epanet_instance_py = None 

    if not inp_content_str or not inp_content_str.strip():
        raise ValueError("INP file content for instance creation is empty.")
    
    console.log("Python: Initializing new epanet_shim.epanet instance...")
    epanet_instance_py = epanet(inp_content_str=inp_content_str)
    console.log(f"Python: New EPANET instance created. Version: {epanet_instance_py.getVersion()}")
    return "Python: EPANET instance created successfully."

def get_network_topology_js():
    global epanet_instance_py
    console.log("Python (main_poc.py): get_network_topology_js called.")
    if epanet_instance_py is None:
        raise RuntimeError("EPANET instance not initialized. Load INP file first.")
    topology = epanet_instance_py.get_network_topology()
    console.log("Python: Topology extracted from current instance.")
    return topology

def open_hydraulic_analysis_js():
    global epanet_instance_py
    if epanet_instance_py is None: raise RuntimeError("EPANET instance not initialized.")
    epanet_instance_py.openHydraulicAnalysis()
    # Also open quality analysis here if a quality type is set
    # This logic might be better placed in initialize_hydraulic_analysis_js
    # or handled by a dedicated "initialize_full_simulation_js"
    try:
        epanet_instance_py.openQualityAnalysis()
        console.log("Python: Quality analysis opened during hydraulic open.")
    except Exception as e_open_q:
        console.log(f"Python: Info - Could not open quality analysis during hydraulic open: {str(e_open_q)}")
    return "Hydraulic analysis opened."

def initialize_hydraulic_analysis_js(save_flag=0):
    global epanet_instance_py
    if epanet_instance_py is None: raise RuntimeError("EPANET instance not initialized.")
    epanet_instance_py.initializeHydraulicAnalysis(save_flag)
    # Initialize quality analysis as well
    try:
        epanet_instance_py.initializeQualityAnalysis(save_flag) # Use same save_flag for now
        console.log(f"Python: Quality analysis initialized (save_flag={save_flag}).")
        return f"Hydraulic and Quality analyses initialized (save_flag={save_flag})."
    except Exception as e_init_q:
        console.log(f"Python: Error initializing quality analysis: {str(e_init_q)}")
        return f"Hydraulic analysis initialized (save_flag={save_flag}). Quality init failed: {str(e_init_q)}"


def run_single_hydraulic_step_js(node_id_to_get_pressure, link_id_to_get_flow):
    global epanet_instance_py
    if epanet_instance_py is None: raise RuntimeError("EPANET instance not initialized.")
    results = epanet_instance_py.run_single_hydraulic_step_for_js(
        str(node_id_to_get_pressure), 
        str(link_id_to_get_flow)
    )
    return results

def close_hydraulic_analysis_js():
    global epanet_instance_py
    if epanet_instance_py is None: return "No instance to close hydraulics for."
    try:
        epanet_instance_py.closeHydraulicAnalysis()
        # Also close quality analysis
        try:
            epanet_instance_py.closeQualityAnalysis()
            console.log("Python: Quality analysis closed during hydraulic close.")
        except Exception as e_close_q:
            console.log(f"Python: Info - No active quality analysis to close or error closing: {str(e_close_q)}")
        return "Hydraulic and Quality analyses closed."
    except Exception as e:
        return f"Error closing hydraulic analysis: {str(e)}"

def set_emitter_coefficient_js(node_id_str, emitter_coeff_float):
    global epanet_instance_py
    console.log(f"Python: set_emitter_coefficient_js called for Node ID: {node_id_str}, Coeff: {emitter_coeff_float}")
    if epanet_instance_py:
        try:
            node_idx_list = epanet_instance_py.getNodeIndex([str(node_id_str)]) 
            if not node_idx_list: raise ValueError(f"Node ID '{node_id_str}' not found.")
            node_idx = node_idx_list[0]
            epanet_instance_py.setNodeEmitterCoeff(node_idx, float(emitter_coeff_float))
            success_msg = f"Python: Emitter coefficient for node {node_id_str} (index {node_idx}) set to {emitter_coeff_float}."
            console.log(success_msg)
            return f"Leak applied to Node {node_id_str} with coefficient {emitter_coeff_float}. Ready for next step."
        except Exception as e:
            error_message = f"Python: Error setting emitter coefficient for Node ID '{node_id_str}': {str(e)}"
            console.log(error_message)
            return error_message 
    return "Error: EPANET instance not available in Python."

def set_pdd_options_js(enable_pdd_bool, pmin_float, preq_float, pexp_float):
    global epanet_instance_py
    console.log(f"Python: set_pdd_options_js called with Enable: {enable_pdd_bool}, Pmin: {pmin_float}, Preq: {preq_float}, Pexp: {pexp_float}")
    if epanet_instance_py:
        try:
            model_str = "PDA" if enable_pdd_bool else "DDA"
            epanet_instance_py.setDemandModel(model_str, float(pmin_float), float(preq_float), float(pexp_float))
            success_msg = f"Python: PDD model set to {model_str} with Pmin={pmin_float}, Preq={preq_float}, Pexp={pexp_float}."
            console.log(success_msg)
            return f"PDD model set to {model_str}. Please Re-initialize Step Simulation."
        except Exception as e:
            error_message = f"Python: Error setting PDD options: {str(e)}"
            console.log(error_message)
            return error_message 
    return "Error: EPANET instance not available in Python. Load INP first."

def set_quality_type_js(quality_type_str, trace_node_id_str=""):
    global epanet_instance_py
    console.log(f"Python: set_quality_type_js called with Type: {quality_type_str}, Trace Node: '{trace_node_id_str}'")
    if epanet_instance_py:
        try:
            # The shim's setQualityType handles the logic for empty/non-empty traceNode_id_str based on type
            # and converts quality_type_str.upper() to the correct integer code.
            epanet_instance_py.setQualityType(quality_type_str, traceNode_id_str=trace_node_id_str)
            
            # Close existing quality analysis to force re-open/re-init in the simulation step initialization
            try:
                epanet_instance_py.closeQualityAnalysis() 
                console.log("Python: Closed existing quality analysis due to quality type change (if it was open).")
            except Exception as e_close_q:
                console.log(f"Python: Info - No active quality analysis to close or error closing: {str(e_close_q)}")

            return f"Quality type set to {quality_type_str}. Please Re-initialize Step Simulation."
        except Exception as e:
            error_msg = f"Python: Error setting quality type: {str(e)}"
            console.log(error_msg)
            return error_msg 
    return "Error: EPANET instance not available."

def run_quality_step_js(node_id_to_get_quality):
    global epanet_instance_py
    if epanet_instance_py:
        try:
            results = epanet_instance_py.run_single_quality_step_for_js(str(node_id_to_get_quality))
            if not isinstance(results, dict): # Should be a dict from the shim
                return {'error': str(results), 'currentTime': -1, 'quality': 0.0, 'nextQualityEventTime': 0, 'nodeId': str(node_id_to_get_quality)}
            return results
        except Exception as e:
            error_msg = f"Python: Error in run_quality_step_js: {str(e)}"
            console.log(error_msg)
            return {'error': error_msg, 'currentTime': -1, 'quality': 0.0, 'nextQualityEventTime': 0, 'nodeId': str(node_id_to_get_quality)}
    return {'error': "EPANET instance not available for quality step.", 'currentTime': -1, 'quality': 0.0, 'nextQualityEventTime': 0, 'nodeId': str(node_id_to_get_quality)}

console.log("Python: main_poc.py loaded and all functions defined, including quality simulation.")
