from js import globalThis, Object, Error # Import Error for explicit error construction
import js # Ensure full js module is available

__epanetapi_shim_version__ = "1.0.4"

# Low-level Python shim for epanet-js library, mimicking EPANET C API function calls.
# This class directly interacts with the epanet-js objects (epanetJsProject, epanetJsWorkspace)
# made available on the global JavaScript scope (globalThis).
# It handles:
#   - Translation of EPANET C API style calls to epanet-js method calls.
#   - Basic error code management (self.errcode).
#   - Conversion of 1-based indices (common in EPANET C API) to 0-based indices (used by epanet-js).
#   - Mapping of EPANET constants (e.g., for node properties, link properties, quality types)
#     to the corresponding integer codes expected by epanet-js, where they differ.
class epanetapi:
    # --- EPANET Object Counts (match EPANET Toolkit codes) ---
    EN_NODECOUNT = 0      # Number of nodes
    EN_TANKCOUNT = 1      # Number of tanks and reservoirs
    EN_LINKCOUNT = 2      # Number of links
    EN_PATCOUNT = 3       # Number of patterns
    EN_CURVECOUNT = 4     # Number of curves
    EN_CONTROLCOUNT = 5   # Number of controls

    # --- Node Types (match EPANET Toolkit codes, and epanet-js NodeType enum) ---
    EN_JUNCTION = 0
    EN_RESERVOIR = 1
    EN_TANK = 2
    
    # --- Node Properties ---
    # These constants represent EPANET Toolkit codes (used by EPyT).
    # The shim translates these to the codes expected by epanet-js if they differ.
    # Comments indicate the epanet-js NodeProperty enum value for clarity.
    EN_ELEVATION = 0    # Node elevation (epanet-js NodeProperty.Elevation = 0)
    EN_BASEDEMAND = 1   # Node base demand (epanet-js NodeProperty.BaseDemand = 1)
    # EN_PATTERN = 2      # Index of demand pattern (epanet-js NodeProperty.DemandPattern = 2)
    EN_EMITTER = 3      # Emitter coefficient (epanet-js NodeProperty.EmitterCoeff = 12)
    EN_INITQUAL = 4     # Node initial quality (epanet-js NodeProperty.InitialQuality = 3)
    # EN_SOURCEQUAL = 5   # Source quality (epanet-js NodeProperty.SourceQuality = 4)
    # EN_SOURCEPAT = 6    # Source pattern index (epanet-js NodeProperty.SourcePattern = 5)
    # EN_SOURCETYPE = 7   # Source type (epanet-js NodeProperty.SourceType = 6)
    # EN_TANKLEVEL = 8    # Tank initial water level (epanet-js NodeProperty.InitialWaterLevel = 8)

    # For retrieving simulation results (actual computed values):
    # Note: EPyT uses some of the same constant values for base properties and computed results.
    # The mapping to specific epanet-js codes is crucial.
    EN_DEMAND = 0       # Actual computed demand (epanet-js NodeProperty.ActualDemand = 9). EPyT uses 0.
    EN_HEAD = 1         # Actual computed hydraulic head (epanet-js NodeProperty.Head = 10). EPyT uses 1.
    EN_PRESSURE = 11    # Actual computed pressure (epanet-js NodeProperty.Pressure = 11). EPyT uses 11.
    EN_QUALITY = 2      # Actual computed water quality (epanet-js NodeProperty.ActualQuality = 7). EPyT uses 2.

    # Internal mapping for epanet-js NodeProperty codes (used directly in API calls to epanet-js)
    JS_NODEPROP_ELEVATION = 0
    JS_NODEPROP_BASEDEMAND = 1
    JS_NODEPROP_DEMANDPATTERN = 2 
    JS_NODEPROP_INITIALQUALITY = 3
    JS_NODEPROP_SOURCEQUALITY = 4
    JS_NODEPROP_SOURCEPATTERN = 5 
    JS_NODEPROP_SOURCETYPE = 6    
    JS_NODEPROP_ACTUALQUALITY = 7 
    JS_NODEPROP_INITIALWATERLEVEL = 8
    JS_NODEPROP_ACTUALDEMAND = 9  
    JS_NODEPROP_HEAD = 10         
    JS_NODEPROP_PRESSURE = 11     
    JS_NODEPROP_EMITTER = 12      
    
    # --- Quality Types (match EPANET and epanet-js integer codes for QualityType) ---
    EN_NONE = 0
    EN_CHEM = 1 
    EN_AGE = 2
    EN_TRACE = 3

    # --- Link Properties ---
    # These constants represent EPANET Toolkit codes (used by EPyT).
    EN_DIAMETER = 0         # Link Diameter (epanet-js LinkProperty.Diameter = 0)
    EN_LENGTH = 1           # Link Length (epanet-js LinkProperty.Length = 1)
    EN_ROUGHNESS = 2        # Link Roughness (epanet-js LinkProperty.Roughness = 2)
    EN_MINORLOSS = 3        # Link Minor Loss Coeff (epanet-js LinkProperty.MinorLoss = 4)
    # EN_INITSTATUS = 4     # Initial status (epanet-js LinkProperty.InitialStatus = 3)
    # EN_INITSETTING = 5    # Initial setting (epanet-js LinkProperty.InitialSetting = 5)
    EN_STATUS = 10          # Actual Link Status (epanet-js LinkProperty.ActualStatus = 6). EPyT uses 10.
    EN_FLOW = 8             # Actual Link Flow (epanet-js LinkProperty.Flow = 8). EPyT uses 8.

    # Internal mapping for epanet-js LinkProperty codes
    JS_LINKPROP_DIAMETER = 0
    JS_LINKPROP_LENGTH = 1
    JS_LINKPROP_ROUGHNESS = 2
    JS_LINKPROP_INITIALSTATUS = 3 
    JS_LINKPROP_MINORLOSS = 4
    JS_LINKPROP_INITIALSETTING = 5 
    JS_LINKPROP_ACTUALSTATUS = 6   
    JS_LINKPROP_SETTING = 7      
    JS_LINKPROP_FLOW = 8         
    JS_LINKPROP_VELOCITY = 9     
    JS_LINKPROP_HEADLOSS = 10    
    
    # --- Time Parameters (match EPANET Toolkit codes) ---
    EN_DURATION = 0     # Simulation duration (seconds)
    EN_HYDSTEP = 1      # Hydraulic time step (seconds)
    EN_QUALSTEP = 2     # Water quality time step (seconds)
    EN_REPORTSTEP = 4   # Reporting time step (seconds)
    EN_STATISTIC = 8    # Type of simulation statistic (used with ENgetstatistic)

    def __init__(self, version=2.2, ph=False, customlib=None):
        """
        Initializes the epanetapi shim.
        Connects to the epanet-js Project and Workspace objects expected on globalThis.
        Args:
            version (float, optional): Placeholder for EPANET version. Defaults to 2.2. Not actively used.
            ph (bool, optional): Placeholder for Prolog/Headless mode. Defaults to False. Not actively used.
            customlib (str, optional): Placeholder for custom library path. Defaults to None. Not actively used.
        """
        self.errcode = 0
        self.epanet_js_obj = None # Will hold globalThis.epanetJsProject
        self.epanet_js_workspace = None # Will hold globalThis.epanetJsWorkspace
        
        try:
            if hasattr(globalThis, 'epanetJsProject') and hasattr(globalThis, 'epanetJsWorkspace'):
                self.epanet_js_obj = globalThis.epanetJsProject
                self.epanet_js_workspace = globalThis.epanetJsWorkspace
            else:
                self.errcode = -1 # Indicate an initialization error
        except Exception as e:
            self.errcode = -1 
            # print(f"Python: epanetapi_shim: Error during __init__: {str(e)}")

    def ENopen(self, inpfile_content_str, rptfile_path_str="report.rpt", binfile_path_str="out.bin"):
        """
        Opens an EPANET input file and prepares for simulation.
        Writes inpfile_content_str to a temporary file in Pyodide's virtual FS, then calls epanet-js open().
        Args:
            inpfile_content_str (str): Full content of the INP file.
            rptfile_path_str (str): Path for the report file (used by epanet-js).
            binfile_path_str (str): Path for the binary output file (used by epanet-js).
        Returns:
            int: Error code (0 if successful).
        """
        if self.epanet_js_workspace is None:
            self.errcode = 101 # Custom error code for missing workspace
            # print("Python: epanetapi_shim: ENopen error: epanetJsWorkspace is None")
            return self.errcode
        if self.epanet_js_obj is None:
            self.errcode = 102 # Custom error code for missing project object
            # print("Python: epanetapi_shim: ENopen error: epanetJsProject (self.epanet_js_obj) is None")
            return self.errcode
        try:
            inp_content_uint8array = js.TextEncoder.new().encode(inpfile_content_str)
            print("Python [ENopen]: Attempting self.epanet_js_workspace.writeFile...")
            self.epanet_js_workspace.writeFile("temp_model.inp", inp_content_uint8array)
            print("Python [ENopen]: self.epanet_js_workspace.writeFile successful.")
            try:
                written_content = self.epanet_js_workspace.readFile("temp_model.inp")
                print(f"Python [ENopen Investigation]: Content read back from virtual file (first 300 chars): {written_content[:300]}")
                # Optional: Compare written_content with inpfile_content_str.decode('utf-8')
                # if written_content != inpfile_content_str.decode('utf-8'):
                #     print("Python [ENopen Investigation]: WARNING - Content read back differs from content written!")
            except Exception as e_read:
                print(f"Python [ENopen Investigation]: ERROR reading back temp_model.inp: {str(e_read)}")
            print("Python [ENopen]: Attempting self.epanet_js_obj.open...")
            self.epanet_js_obj.open("temp_model.inp", rptfile_path_str, binfile_path_str)
            print("Python [ENopen]: self.epanet_js_obj.open successful.")
            self.errcode = 0
        except Exception as e:
            print(f"Python [ENopen]: Exception caught in ENopen: {type(e).__name__}: {str(e)}")
            self.errcode = 1 # General error during open/write
        return self.errcode

    def ENsolveH(self):
        """
        Runs a complete hydraulic simulation (solveH in epanet-js).
        Returns:
            int: Error code from epanet-js (0 if successful).
        """
        if self.epanet_js_obj is None: self.errcode = 1; return self.errcode
        try:
            error_code = self.epanet_js_obj.solveH() 
            self.errcode = error_code
        except Exception as e:
            self.errcode = 1
        return self.errcode

    def ENclose(self):
        """
        Closes the EPANET simulation, freeing resources used by epanet-js.
        Returns:
            int: Error code from epanet-js (0 if successful).
        """
        if self.epanet_js_obj is None: self.errcode = 1; return self.errcode
        try:
            error_code = self.epanet_js_obj.close() 
            self.errcode = error_code
        except Exception as e:
            self.errcode = 1
        return self.errcode

    def ENgetcount(self, countcode_int):
        """
        Retrieves the number of specified EPANET components.
        Args:
            countcode_int (int): EPANET constant for the component type (e.g., EN_NODECOUNT).
        Returns:
            int: Number of components, or -1 on error.
        """
        if self.epanet_js_obj is None: self.errcode = 1; return -1
        value = -1
        try:
            if countcode_int == self.EN_NODECOUNT: value = self.epanet_js_obj.getNodeCount()
            elif countcode_int == self.EN_LINKCOUNT: value = self.epanet_js_obj.getLinkCount()
            elif countcode_int == self.EN_TANKCOUNT: value = self.epanet_js_obj.getTankCount() 
            elif countcode_int == self.EN_PATCOUNT: value = self.epanet_js_obj.getPatternCount()
            elif countcode_int == self.EN_CURVECOUNT: value = self.epanet_js_obj.getCurveCount()
            # EN_CONTROLCOUNT may not be directly available in epanet-js Project API, might need parsing.
            else: self.errcode = 1; return -1 # Unknown or unsupported countcode
            self.errcode = 0
        except Exception as e:
            self.errcode = 1; value = -1
        return value

    def ENgeterror(self, errcode_val_int, max_len_int=80):
        """
        Retrieves the error message for a given error code. Simplified for this shim.
        Args:
            errcode_val_int (int): The error code from a previous API call.
            max_len_int (int): Max length of the message buffer (ignored).
        Returns:
            str: Error message.
        """
        current_err_to_report = self.errcode if self.errcode !=0 else errcode_val_int
        if current_err_to_report == 0: return "No error."
        if current_err_to_report == -1: return "EPANET Shim: Initialization failed (Python-side epanet-js objects not found)."
        if current_err_to_report == 1: return f"EPANET Shim: Error (code 1). This may be due to an issue writing or opening the temporary INP file, potentially an invalid INP format or content encoding problem."
        if current_err_to_report == 101: return "EPANET Shim: Critical error - epanetJsWorkspace (JS) is not available to the Python shim."
        if current_err_to_report == 102: return "EPANET Shim: Critical error - epanetJsProject (JS) is not available to the Python shim."
        # epanet-js usually throws JS Errors, direct EPANET error codes might not be set often from the wasm lib itself.
        # Other error codes are typically from the epanet-js library directly.
        return f"EPANET Shim: An epanet-js related error occurred (code {current_err_to_report}). Operation may have failed."

    def ENgetnodeid(self, node_index_1_based):
        """
        Retrieves the ID string of a node by its 1-based index.
        Args:
            node_index_1_based (int): 1-based index of the node.
        Returns:
            str: Node ID string, or empty string on error.
        """
        if self.epanet_js_obj is None: self.errcode = 1; return ""
        try:
            node_id_str = self.epanet_js_obj.getNodeId(node_index_1_based - 1) # 0-based for epanet-js
            print(f"Python [Phase 1 - epanetapi_shim]: ENgetnodeid for 0-based index {node_index_1_based - 1}. JS returned ID: {node_id_str}")
            self.errcode = 0
            return node_id_str
        except Exception as e:
            self.errcode = 1; return ""

    def ENgetcoord(self, node_index_1_based):
        """
        Retrieves X and Y coordinates for a node by its 1-based index.
        Args:
            node_index_1_based (int): 1-based index of the node.
        Returns:
            tuple: (float, float) for (x, y), or (0.0, 0.0) on error.
        """
        if self.epanet_js_obj is None: self.errcode = 1; return (0.0, 0.0)
        try:
            coords_obj = self.epanet_js_obj.getNodeCoordinates(node_index_1_based - 1) # 0-based
            print(f"Python [Phase 1 - epanetapi_shim]: ENgetcoord for 0-based index {node_index_1_based - 1}. JS returned: x={coords_obj.x if coords_obj else 'N/A'}, y={coords_obj.y if coords_obj else 'N/A'}")
            if coords_obj and hasattr(coords_obj, 'x') and hasattr(coords_obj, 'y'):
                self.errcode = 0
                return (float(coords_obj.x), float(coords_obj.y))
            else:
                self.errcode = 1; return (0.0, 0.0)
        except Exception as e:
            self.errcode = 1; return (0.0, 0.0)

    def ENgetnodetype(self, node_index_1_based):
        """
        Retrieves the type of a node (e.g., EN_JUNCTION) by its 1-based index.
        Args:
            node_index_1_based (int): 1-based index of the node.
        Returns:
            int: Node type code (matching EN_JUNCTION, etc.), or -1 on error.
        """
        if self.epanet_js_obj is None: self.errcode = 1; return -1
        try:
            node_type_code_int = self.epanet_js_obj.getNodeType(node_index_1_based - 1) # 0-based
            self.errcode = 0
            return int(node_type_code_int) # epanet-js NodeType enum matches EPANET codes
        except Exception as e:
            self.errcode = 1; return -1

    def ENgetlinkid(self, link_index_1_based):
        """
        Retrieves the ID string of a link by its 1-based index.
        Args:
            link_index_1_based (int): 1-based index of the link.
        Returns:
            str: Link ID string, or empty string on error.
        """
        if self.epanet_js_obj is None: self.errcode = 1; return ""
        try:
            link_id_str = self.epanet_js_obj.getLinkId(link_index_1_based - 1) # 0-based
            self.errcode = 0
            return link_id_str
        except Exception as e:
            self.errcode = 1; return ""

    def ENgetlinknodes(self, link_index_1_based):
        """
        Retrieves the 1-based indices of the start and end nodes of a link.
        Args:
            link_index_1_based (int): 1-based index of the link.
        Returns:
            tuple: (int, int) for (start_node_idx_1_based, end_node_idx_1_based), or (0,0) on error.
        """
        if self.epanet_js_obj is None: self.errcode = 1; return (0,0)
        try:
            nodes_array_js = self.epanet_js_obj.getLinkNodes(link_index_1_based - 1) # 0-based link, 0-based node indices
            if nodes_array_js and hasattr(nodes_array_js, 'length') and nodes_array_js.length == 2:
                from_node_idx_1_based = int(nodes_array_js[0]) + 1
                to_node_idx_1_based = int(nodes_array_js[1]) + 1
                self.errcode = 0
                return (from_node_idx_1_based, to_node_idx_1_based)
            else:
                self.errcode = 1; return (0,0)
        except Exception as e:
            self.errcode = 1; return (0,0)

    # --- Hydraulic Simulation Functions ---
    def ENopenH(self):
        """Opens the hydraulic analysis system."""
        if self.epanet_js_obj is None: self.errcode = 1; return self.errcode
        try: self.epanet_js_obj.openH(); self.errcode = 0
        except Exception as e: self.errcode = 1; 
        return self.errcode

    def ENinitH(self, save_flag_int):
        """
        Initializes hydraulic analysis.
        Args:
            save_flag_int (int): 0 (NOSAVE) or 1 (SAVE results).
                                 (EPANET's 2 for SAVE_AND_INIT is treated as SAVE for hydraulics).
        """
        if self.epanet_js_obj is None: self.errcode = 1; return self.errcode
        try:
            js_save_flag = True if save_flag_int == 1 else False 
            self.epanet_js_obj.initH(js_save_flag)
            self.errcode = 0
        except Exception as e: self.errcode = 1; 
        return self.errcode

    def ENrunH(self):
        """
        Runs a single hydraulic step, advancing simulation time.
        Returns:
            float: Current simulation time in seconds, or -1 on error.
        """
        if self.epanet_js_obj is None: self.errcode = 1; return -1 
        try:
            current_time_sec = self.epanet_js_obj.runH()
            self.errcode = 0
            return current_time_sec 
        except Exception as e: self.errcode = 1; return -1 

    def ENnextH(self):
        """
        Determines the time until the next hydraulic event.
        Returns:
            float: Time to next event in seconds, or 0 if no more events or error.
        """
        if self.epanet_js_obj is None: self.errcode = 1; return 0 
        try:
            time_to_next_event_sec = self.epanet_js_obj.nextH()
            self.errcode = 0
            return time_to_next_event_sec
        except Exception as e: self.errcode = 1; return 0 
            
    def ENcloseH(self):
        """Closes the hydraulic analysis system."""
        if self.epanet_js_obj is None: self.errcode = 1; return self.errcode
        try: self.epanet_js_obj.closeH(); self.errcode = 0
        except Exception as e: self.errcode = 1; 
        return self.errcode

    def ENgetnodevalue(self, node_index_1_based, param_code_epyt):
        """
        Retrieves the value of a specific node parameter using EPyT/Toolkit param codes.
        Handles mapping EPyT codes to epanet-js NodeProperty codes.
        Args:
            node_index_1_based (int): 1-based index of the node.
            param_code_epyt (int): EPANET Toolkit constant for the parameter.
        Returns:
            float: Value of the parameter, or 0.0 on error.
        """
        if self.epanet_js_obj is None: self.errcode = 1; return 0.0
        
        js_param_code = -1 
        if param_code_epyt == self.EN_PRESSURE: js_param_code = self.JS_NODEPROP_PRESSURE
        elif param_code_epyt == self.EN_HEAD: js_param_code = self.JS_NODEPROP_HEAD
        elif param_code_epyt == self.EN_QUALITY: js_param_code = self.JS_NODEPROP_ACTUALQUALITY 
        elif param_code_epyt == self.EN_DEMAND: js_param_code = self.JS_NODEPROP_ACTUALDEMAND 
        elif param_code_epyt == self.EN_ELEVATION: js_param_code = self.JS_NODEPROP_ELEVATION
        elif param_code_epyt == self.EN_BASEDEMAND: js_param_code = self.JS_NODEPROP_BASEDEMAND
        elif param_code_epyt == self.EN_EMITTER: js_param_code = self.JS_NODEPROP_EMITTER # For getting emitter coeff, not typical
        # Add other EPyT to epanet-js mappings here as needed
        else: self.errcode = 1; return 0.0 # Unsupported param_code for getting

        try:
            value_float = self.epanet_js_obj.getNodeValue(node_index_1_based - 1, js_param_code) # 0-based index
            self.errcode = 0
            return float(value_float)
        except Exception as e:
            self.errcode = 1; return 0.0

    def ENsetnodevalue(self, node_index_1_based, param_code_epyt, value_float):
        """
        Sets the value of a specific node parameter using EPyT/Toolkit param codes.
        Handles mapping EPyT codes to epanet-js NodeProperty codes for settable parameters.
        Args:
            node_index_1_based (int): 1-based index of the node.
            param_code_epyt (int): EPANET Toolkit constant for the parameter.
            value_float (float): Value to set.
        Returns:
            int: Error code (0 if successful).
        """
        if self.epanet_js_obj is None: self.errcode = 1; return self.errcode
        
        js_param_code = -1 
        if param_code_epyt == self.EN_EMITTER: js_param_code = self.JS_NODEPROP_EMITTER 
        elif param_code_epyt == self.EN_BASEDEMAND: js_param_code = self.JS_NODEPROP_BASEDEMAND
        elif param_code_epyt == self.EN_ELEVATION: js_param_code = self.JS_NODEPROP_ELEVATION
        # Add other mappings for settable parameters
        else: self.errcode = 1; return self.errcode # Unsupported param_code for setting

        try:
            self.epanet_js_obj.setNodeValue(node_index_1_based - 1, js_param_code, float(value_float)) # 0-based index
            self.errcode = 0
        except Exception as e:
            self.errcode = 1
        return self.errcode

    def ENgetlinkvalue(self, link_index_1_based, param_code_epyt):
        """
        Retrieves the value of a specific link parameter using EPyT/Toolkit param codes.
        Handles mapping EPyT codes to epanet-js LinkProperty codes.
        Args:
            link_index_1_based (int): 1-based index of the link.
            param_code_epyt (int): EPANET Toolkit constant for the parameter.
        Returns:
            float: Value of the parameter, or 0.0 on error.
        """
        if self.epanet_js_obj is None: self.errcode = 1; return 0.0

        js_param_code = -1 
        if param_code_epyt == self.EN_FLOW: js_param_code = self.JS_LINKPROP_FLOW # EPyT EN_FLOW is 8
        elif param_code_epyt == self.EN_STATUS: js_param_code = self.JS_LINKPROP_ACTUALSTATUS # EPyT EN_STATUS is 10
        # Add other mappings
        else: self.errcode = 1; return 0.0 
        
        try:
            value_float = self.epanet_js_obj.getLinkValue(link_index_1_based - 1, js_param_code) # 0-based index
            self.errcode = 0
            return float(value_float)
        except Exception as e:
            self.errcode = 1; return 0.0

    def ENsetdemandmodel(self, model_type_int, pmin_float, preq_float, pexp_float):
        """Sets the pressure-dependent demand (PDD) model and its parameters."""
        if self.epanet_js_obj is None: self.errcode = 1; return self.errcode
        try:
            # epanet-js setDemandModel(model: number (0=DDA, 1=PDA), minPressure, reqPressure, exponent)
            self.epanet_js_obj.setDemandModel(int(model_type_int), float(pmin_float), float(preq_float), float(pexp_float))
            self.errcode = 0
        except Exception as e: self.errcode = 1; 
        return self.errcode

    # --- Water Quality Simulation Functions ---
    def ENsetqualtype(self, qualcode_int, chemname_str, chemunits_str, tracenode_id_str):
        """
        Sets the type of water quality analysis.
        Args:
            qualcode_int (int): Quality type code (EN_NONE, EN_AGE, EN_TRACE, EN_CHEM).
            chemname_str (str): Name of the chemical (if qualcode is EN_CHEM).
            chemunits_str (str): Units of the chemical (if qualcode is EN_CHEM).
            tracenode_id_str (str): ID of the trace node (if qualcode is EN_TRACE).
        """
        if self.epanet_js_obj is None: self.errcode = 1; return self.errcode
        try:
            effective_tracenode_id_str = tracenode_id_str if qualcode_int == self.EN_TRACE and tracenode_id_str else ""
            self.epanet_js_obj.setQualityType(int(qualcode_int), str(chemname_str), str(chemunits_str), str(effective_tracenode_id_str))
            self.errcode = 0
        except Exception as e: self.errcode = 1; 
        return self.errcode

    def ENopenQ(self):
        """Opens the water quality analysis system."""
        if self.epanet_js_obj is None: self.errcode = 1; return self.errcode
        try: self.epanet_js_obj.openQ(); self.errcode = 0
        except Exception as e: self.errcode = 1; 
        return self.errcode

    def ENinitQ(self, saveflag_int):
        """
        Initializes water quality analysis.
        Args:
            saveflag_int (int): 0 (NOSAVE) or 1 (SAVE results).
        """
        if self.epanet_js_obj is None: self.errcode = 1; return self.errcode
        try: 
            js_save_flag = True if saveflag_int == 1 else False 
            self.epanet_js_obj.initQ(js_save_flag)
            self.errcode = 0
        except Exception as e: self.errcode = 1; 
        return self.errcode

    def ENrunQ(self):
        """
        Runs a single water quality step, advancing quality simulation time.
        Returns:
            float: Current simulation time in seconds for quality, or -1 on error.
        """
        if self.epanet_js_obj is None: self.errcode = 1; return -1 
        try: 
            current_q_time_sec = self.epanet_js_obj.runQ()
            self.errcode = 0
            return current_q_time_sec
        except Exception as e: self.errcode = 1; return -1 
        
    def ENnextQ(self):
        """
        Determines the time until the next quality event.
        Returns:
            float: Time to next quality event in seconds, or 0 if no more events or error.
        """
        if self.epanet_js_obj is None: self.errcode = 1; return 0 
        try: 
            time_to_next_q_event_sec = self.epanet_js_obj.nextQ()
            self.errcode = 0
            return time_to_next_q_event_sec
        except Exception as e: self.errcode = 1; return 0 

    def ENcloseQ(self):
        """Closes the water quality analysis system."""
        if self.epanet_js_obj is None: self.errcode = 1; return self.errcode
        try: self.epanet_js_obj.closeQ(); self.errcode = 0
        except Exception as e: self.errcode = 1; 
        return self.errcode

    # The `ph` (Prolog/Headless) and `customlib` parameters are not used in this shim
    # as epanet-js is the only "library" we're interacting with.
    # Version is also informational for this shim.
pass
