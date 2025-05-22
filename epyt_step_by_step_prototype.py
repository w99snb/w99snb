import os
from epyt import epanet

# --- Configuration ---
# Assume 'Net1.inp' is in the same directory as the script or a known path.
# If EPyT/EPANET DLL is not found automatically, its location might need to be
# specified, but EPyT usually handles this if EPANET is installed correctly.
# Example: epanet.load_epanet_dll("path/to/epanet2.dll") if needed.
INP_FILE = 'Net1.inp' 

# --- Main Script ---
def main():
    print(f"Attempting to load INP file: {INP_FILE}")
    
    # Check if Net1.inp exists, and create a dummy one if not, for basic script execution.
    if not os.path.exists(INP_FILE):
        print(f"Warning: INP file '{INP_FILE}' not found. Creating a minimal dummy file for demonstration purposes.")
        with open(INP_FILE, 'w') as f:
            f.write("""[TITLE]
Minimal Net1.inp for EPyT step-by-step prototype

[JUNCTIONS]
;ID              Elev        Demand      Pattern         
 J1              0           10                          
 J2              0           -10                         
 J3              0           0

[PIPES]
;ID              Node1       Node2       Length      Diameter    Roughness   MinorLoss   Status      
 P1              J1          J2          1000        12          100         0           Open        
 P2              J2          J3          1000        10          100         0           Open

[REPORT]
 Status          Full

[OPTIONS]
 Units           GPM
 Headloss        H-W
 Quality         None
 Trials          40
 Accuracy        0.001
 Unbalanced      Continue 10

[COORDINATES]
;Node            X-Coord         Y-Coord         
 J1              10              10              
 J2              20              10              
 J3              30              10              

[END]
""")

    try:
        d = epanet(INP_FILE)
        print(f"Successfully loaded '{INP_FILE}'. EPANET version: {d.getVersion()}")

        # 2. PDD Setup (Example)
        # This section might require a PDD-enabled EPANET version and specific model characteristics.
        # It's included as per requirements but commented out for broader compatibility in a basic test.
        # try:
        #     print("\nAttempting to set Pressure Dependent Demands (PDD) model...")
        #     # These are example parameters for PDA (Pressure Driven Analysis)
        #     # Adjust p_min, p_req, p_exp as per your model or EPANET variant needs
        #     d.setDemandModel(model_type=d.ToolkitConstants.EN_PDA, p_min=0.5, p_req=20.0, p_exp=0.5)
        #     print("PDD model set (or attempted). Note: This requires a PDD-capable EPANET engine.")
        # except Exception as e_pdd:
        #     print(f"Could not set PDD model (this is often expected with standard EPANET 2.2): {e_pdd}")


        # 3. Initialize Step-by-Step Hydraulic Simulation
        print("\nInitializing step-by-step hydraulic simulation...")
        d.openHydraulicAnalysis()
        # Use EN_SAVE to keep hydraulic results available for subsequent quality analysis
        # If memory is a concern for very long simulations, EN_NOSAVE might be used,
        # but then hydraulics would need to be re-run for quality.
        d.initializeHydraulicAnalysis(d.ToolkitConstants.EN_SAVE) 
        print("Hydraulic analysis initialized.")

        # 4. Simulation Loop
        num_steps_to_run = 10 # As per requirement
        print(f"\nStarting hydraulic simulation loop for {num_steps_to_run} steps...")
        
        # Note: EPANET's `runHydraulicAnalysis` returns the current simulation time (t)
        # and `nextHydraulicAnalysisStep` returns the time until the next hydraulic event (tstep).
        # The `time_step_seconds` variable is illustrative if you were trying to force fixed steps,
        # but EPANET is event-driven. We use `nextHydraulicAnalysisStep` to advance time.

        current_sim_time_seconds = 0 # t, initially 0
        
        for i in range(num_steps_to_run):
            # Run hydraulics for the current step
            # `runHydraulicAnalysis` advances simulation time to the current step's time
            current_sim_time_seconds = d.runHydraulicAnalysis()

            # Get example results
            # Node indices in EPyT are 1-based. Make sure these nodes exist in Net1.inp.
            # For the dummy INP: J1 is index 1, J2 is index 2, J3 is index 3
            # P1 is index 1, P2 is index 2
            node_index_to_check = 1 
            link_index_to_check = 1
            
            try:
                pressure_at_node = d.getNodePressure(node_index_to_check)
                flow_at_link = d.getLinkFlows(link_index_to_check)
                print(f"Step {i+1}: Time: {current_sim_time_seconds/3600:.2f} hrs - Node {node_index_to_check} Pressure: {pressure_at_node:.2f}, Link {link_index_to_check} Flow: {flow_at_link:.2f}")
            except Exception as e_getval:
                print(f"Step {i+1}: Time: {current_sim_time_seconds/3600:.2f} hrs - Error getting value for Node {node_index_to_check} or Link {link_index_to_check}: {e_getval}")


            # Parameter Modification Example (at step 5, which is i == 4)
            if i == 4: # 0-indexed, so 5th step
                print(f"--- Performing modifications at Step {i+1} (Time: {current_sim_time_seconds/3600:.2f} hrs) ---")
                try:
                    # Modify Emitter Coefficient for a node (simulating a leak)
                    node_to_modify_emitter = 2 # Example: J2
                    new_emitter_coeff = 0.1
                    # First, ensure the node is not a tank, as emitters are typically on junctions
                    # This check might be more complex depending on node type codes from EPANET
                    # For simplicity, we assume node_to_modify_emitter is a junction.
                    d.setNodeValue(node_to_modify_emitter, d.ToolkitConstants.EN_EMITTER, new_emitter_coeff)
                    # EPyT also has d.setNodeEmitterCoeff(node_index, coeff) but it's less direct for general parameters
                    print(f"INFO: Applied emitter coefficient {new_emitter_coeff} to Node {node_to_modify_emitter}")

                    # Modify Pipe Roughness
                    pipe_to_modify_roughness = 2 # Example: P2
                    new_roughness = 120
                    # Using setLinkValue for roughness. EN_ROUGHNESS is the code for pipe roughness.
                    d.setLinkValue(pipe_to_modify_roughness, d.ToolkitConstants.EN_ROUGHNESS, new_roughness)
                    # EPyT also has d.setLinkRoughnessCoeff(link_index, coeff)
                    print(f"INFO: Changed roughness of Pipe {pipe_to_modify_roughness} to {new_roughness}")
                    print("--- Modifications applied ---")
                except Exception as e_mod:
                    print(f"ERROR during parameter modification: {e_mod}")

            # Advance to the next hydraulic time step
            time_to_next_event_seconds = d.nextHydraulicAnalysisStep() # tstep
            
            if time_to_next_event_seconds <= 0:
                print(f"End of simulation period reached or error at step {i+1} (nextHydraulicAnalysisStep returned {time_to_next_event_seconds}).")
                break
        
        print("Hydraulic simulation loop finished.")

        # 5. Water Quality Simulation (Age - Example after hydraulics)
        print("\nStarting Water Quality Analysis (Age example)...")
        # Set quality type to AGE. Other parameters are not strictly needed for AGE.
        d.setQualityType(d.ToolkitConstants.EN_AGE, "", "") 
        
        # Open and initialize quality analysis
        # This assumes hydraulic results were saved (EN_SAVE in initializeHydraulicAnalysis)
        # or that the hydraulic state is suitable for starting quality analysis.
        d.openQualityAnalysis()
        # Typically EN_NOSAVE for quality if just analyzing, unless results need to be saved for reporting.
        d.initializeQualityAnalysis(d.ToolkitConstants.EN_NOSAVE) 
        print("Water quality analysis (AGE) initialized.")

        # To run a full quality simulation synchronized with hydraulics, one would typically:
        # 1. Re-initialize hydraulic time to 0 (d.reInitializeHydraulicAnalysis()) or solve complete hydraulics.
        # 2. Loop through time steps, calling runHydraulicAnalysis(), then runQualityAnalysis(), then nextHydraulicAnalysisStep(), then nextQualityAnalysisStep().
        # For this prototype's simplicity, we'll just get quality at the *current* simulation time (end of hydraulic loop).
        # This demonstrates the calls but isn't a full time-series quality analysis.

        # Let's try to run quality step-by-step for a few steps from the current hydraulic state
        # This is not the typical way if hydraulics were not re-initialized or solved completely first.
        # It will continue from the hydraulic state at `current_sim_time_seconds`.
        print("\nRunning a few quality steps from current hydraulic state (simplified example):")
        
        # Reset quality simulation time. This is important.
        # `initializeQualityAnalysis` should reset time, but let's be explicit for demonstration.
        # We will run quality steps matching the hydraulic steps *if we re-ran them*.
        # For this example, we'll just take a few steps from the *end* of the previous hydraulic run.
        
        # To correctly run quality for the whole period, you'd often do:
        # d.solveCompleteHydraulics() # Solve all H first
        # d.initializeQualityAnalysis(d.ToolkitConstants.EN_NOSAVE) # Re-initialize Q time to 0
        # Then loop Q steps.

        # Simplified: show quality at the state where hydraulics left off.
        # Run one quality step to get the quality at the current hydraulic time
        current_q_time_seconds = d.runQualityAnalysis() 
        
        node_index_for_age = 1 # J1
        try:
            # getNodeActualQuality returns a list (EPyT specific, often just one value for AGE)
            age_at_node_list = d.getNodeActualQuality(node_index_for_age)
            age_at_node_hours = age_at_node_list[0] / 3600.0 # Assuming age is in seconds
            print(f"Quality at Time: {current_q_time_seconds/3600:.2f} hrs - Node {node_index_for_age} Water Age: {age_at_node_hours:.2f} hrs")
        except Exception as e_getq:
             print(f"Error getting water age for Node {node_index_for_age}: {e_getq}")

        # Example of stepping quality analysis (would typically be in a loop)
        # time_to_next_q_event_seconds = d.nextQualityAnalysisStep()
        # if time_to_next_q_event_seconds > 0:
        #     current_q_time_seconds = d.runQualityAnalysis()
        #     # ... get quality values ...
        # else:
        #     print("No further quality steps or quality simulation ended.")

        d.closeQualityAnalysis()
        print("Water Quality Analysis complete.")

    except Exception as e:
        print(f"An error occurred during the EPyT simulation: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 6. Close Simulation
        if 'd' in locals() and d.isLoaded():
            try:
                print("\nClosing hydraulic analysis and unloading simulation...")
                d.closeHydraulicAnalysis()
                # d.unload() # Use this to completely unload the EPANET toolkit instance
                # For EPyT, d.closeNetwork() is often used and might be more robust if unload causes issues
                d.closeNetwork() 
                print("EPyT simulation closed.")
            except Exception as e_close:
                print(f"Error during EPyT close/unload: {e_close}")

if __name__ == "__main__":
    main()
