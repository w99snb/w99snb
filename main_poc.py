from epanet_shim import epanet # Assuming epanet_shim.py is in the same Pyodide FS path
from js import console # For logging to browser console

# This global variable will hold the epanet instance if we want to persist it
# For now, functions will create their own instance.
# current_epanet_instance = None

def get_network_topology_for_js(inp_content_str):
    """
    Creates an epanet instance, gets topology, closes, and returns topology.
    """
    console.log("Python (main_poc.py): get_network_topology_for_js called.")
    d = None  # Initialize d to None for the finally block
    try:
        if not inp_content_str or not inp_content_str.strip():
            raise ValueError("INP file content for topology extraction is empty.")
        
        console.log("Python: Initializing epanet_shim.epanet for topology...")
        d = epanet(inp_content_str=inp_content_str)
        console.log(f"Python: EPANET shim version: {d.getVersion()}")
        
        console.log("Python: Calling get_network_topology()...")
        topology = d.get_network_topology() # This is the new method in epanet_shim
        # The topology is already a Python dict. Pyodide will convert it to a JsProxy.
        # JavaScript will need to convert JsProxy to a JS object.
        console.log("Python: Topology extracted.")
        return topology
    except Exception as e:
        error_msg = f"Python Error in get_network_topology_for_js: {str(e)}"
        console.log(error_msg)
        # Potentially raise it so JS can catch it via Pyodide's error handling,
        # or return a specific error structure. For now, log and let it propagate.
        raise # Re-raise the exception to be caught by Pyodide/JS
    finally:
        if d:
            try:
                console.log("Python: Closing network (topology)...")
                d.closeNetwork() # Ensure network is closed
            except Exception as e_close:
                console.log(f"Python: Error closing network in topology: {str(e_close)}")


def run_basic_simulation_for_js(inp_content_str):
    """
    Creates an epanet instance, runs full hydraulics, closes, and returns status.
    """
    console.log("Python (main_poc.py): run_basic_simulation_for_js called.")
    d = None # Initialize d to None
    try:
        if not inp_content_str or not inp_content_str.strip():
            raise ValueError("INP file content for simulation is empty.")

        console.log("Python: Initializing epanet_shim.epanet for simulation...")
        d = epanet(inp_content_str=inp_content_str)
        console.log(f"Python: EPANET shim version: {d.getVersion()}")

        node_count = d.getNodeCount()
        link_count = d.getLinkCount()
        console.log(f"Python: Node count: {node_count}, Link count: {link_count}")

        if node_count <= 0: # Links can be 0 for a network with only nodes
             console.log("Python: Warning - Node count is zero or negative. Cannot run simulation.")
             return "Simulation cannot run: Node count is zero or negative."


        console.log("Python: Running full hydraulics via solveCompleteHydraulics()...")
        simulation_result_code = d.solveCompleteHydraulics()
        
        results_str = ""
        if simulation_result_code == 0:
            console.log(f"Python: Simulation successful (ENsolveH returned {simulation_result_code}).")
            results_str = f"Simulation successful! Nodes: {node_count}, Links: {link_count}. Hydraulics solved."
        else:
            error_message = d.api.ENgeterror(simulation_result_code) # Accessing lower-level shim for error
            console.log(f"Python: Simulation failed. ENsolveH returned code {simulation_result_code}. Error: {error_message}")
            results_str = f"Simulation failed. EPANET error code: {simulation_result_code}. Message: {error_message}"
        
        return results_str
    except Exception as e:
        error_msg = f"Python Error in run_basic_simulation_for_js: {str(e)}"
        console.log(error_msg)
        raise # Re-raise
    finally:
        if d:
            try:
                console.log("Python: Closing network (simulation)...")
                d.closeNetwork()
            except Exception as e_close:
                console.log(f"Python: Error closing network in simulation: {str(e_close)}")


# The old main execution block (if any) from the original main_poc.py can be removed
# if this file is now primarily for defining functions to be called from JS.
# If you still want to run a default action if this script is run directly by Pyodide (not typical for this setup):
# if __name__ == "__main__":
#   console.log("Python: main_poc.py executed directly (not typical for library use).")
#   # perhaps run a default test if inp_file_content_from_js is somehow available
#   # default_inp = "..."
#   # result_topo = get_network_topology_for_js(default_inp)
#   # console.log(f"Default topo result: {result_topo}")
#   # result_sim = run_basic_simulation_for_js(default_inp)
#   # console.log(f"Default sim result: {result_sim}")
#   pass
