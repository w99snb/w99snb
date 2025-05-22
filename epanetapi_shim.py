from js import globalThis, Object, Error # Import Error for explicit error construction

class epanetapi:
    # Define constants (as used in EPyT)
    EN_NODECOUNT = 0
    EN_TANKCOUNT = 1
    EN_LINKCOUNT = 2
    EN_PATCOUNT = 3
    EN_CURVECOUNT = 4
    EN_CONTROLCOUNT = 5

    # Node types
    EN_JUNCTION = 0
    EN_RESERVOIR = 1
    EN_TANK = 2
    
    # Node properties
    # EPANET C API Codes (used by EPyT) on the left, epanet-js NodeProperty enum values on the right for mapping
    # These are what EPyT expects. The shim will translate to epanet-js codes if different.
    EN_ELEVATION = 0    # Elevation -> epanet-js NodeProperty.Elevation (value 0)
    EN_BASEDEMAND = 1   # Base Demand -> epanet-js NodeProperty.BaseDemand (value 1)
    # EN_PATTERN = 2 (Index of time pattern)
    EN_EMITTER = 3      # Emitter Coeff -> epanet-js NodeProperty.EmitterCoeff (value 12)
    EN_INITQUAL = 4     # Initial Quality
    EN_SOURCEQUAL = 5   # Source Quality
    EN_SOURCEPAT = 6    # Source Pattern
    EN_SOURCETYPE = 7   # Source Type
    EN_TANKLEVEL = 8    # Initial Water Level in Tank
    # ... other EPyT codes

    # For getting values, we map EPyT codes to epanet-js codes if they differ
    # For setting values, we also need this mapping.
    # The param_code in ENgetnodevalue/ENsetnodevalue will be the EPyT code.
    
    # Subset of epanet-js NodeProperty enum for direct use when no EPyT code maps cleanly,
    # or for internal consistency with epanet-js.
    # These are what epanet-js expects for its get/set NodeValue functions.
    JS_NODEPROP_DEMAND = 0       # Net demand (ActualDemand in epanet-js)
    JS_NODEPROP_HEAD = 1         # Hydraulic head
    JS_NODEPROP_PRESSURE = 11    # Pressure
    EN_QUALITY = 2               # EPyT constant for getting quality (maps to JS_NODEPROP_QUALITY)
    JS_NODEPROP_QUALITY = 2      # Water quality (ActualQuality in epanet-js)
    JS_NODEPROP_EMITTER = 12     # Emitter Coefficient (EmitterCoeff in epanet-js)

    # Quality types (match EPANET and epanet-js integer codes)
    EN_NONE = 0
    EN_CHEM = 1 # Not fully implemented in this PoC for setting custom chem
    EN_AGE = 2
    EN_TRACE = 3

    # Link properties (from epanet-js LinkProperty)
    # EPyT codes for Link Properties
    EN_DIAMETER = 0         # -> epanet-js LinkProperty.Diameter (0)
    EN_LENGTH = 1           # -> epanet-js LinkProperty.Length (1)
    EN_ROUGHNESS = 2        # -> epanet-js LinkProperty.Roughness (2)
    EN_MINORLOSS = 3        # -> epanet-js LinkProperty.MinorLoss (3)
    # EN_INITSTATUS = 4 (Initial status)
    # EN_INITSETTING = 5 (Initial setting for pump, valve)
    # EN_KBULK = 6 (Bulk reaction coeff)
    # EN_KWALL = 7 (Wall reaction coeff)

    # Subset of epanet-js LinkProperty enum
    JS_LINKPROP_FLOW = 8         # Flow rate
    JS_LINKPROP_VELOCITY = 9     # Flow velocity
    JS_LINKPROP_HEADLOSS = 10    # Headloss per 1000 units
    JS_LINKPROP_STATUS = 3       # Link status (0-closed, 1-open) (maps to EPyT's EN_STATUS if that's 10)
                                 # Note: EPyT's EN_STATUS is 10. epanet-js LinkProperty.Status is 3.
                                 # This will require mapping in get/setLinkValue.

    # Time parameters
    EN_DURATION = 0     # Simulation duration
    EN_HYDSTEP = 1      # Hydraulic time step
    # ... other time parameters

    def __init__(self, version=2.2, ph=False, customlib=None):
        self.errcode = 0
        self.epanet_js_obj = None
        self.epanet_js_workspace = None
        
        try:
            if hasattr(globalThis, 'epanetJsProject') and hasattr(globalThis, 'epanetJsWorkspace'):
                self.epanet_js_obj = globalThis.epanetJsProject
                self.epanet_js_workspace = globalThis.epanetJsWorkspace
                # print("Python: epanetapi_shim: Successfully connected to epanetJsProject and epanetJsWorkspace.")
            else:
                # print("Python: epanetapi_shim: epanetJsProject or epanetJsWorkspace not found on globalThis.")
                # This case should ideally be handled more robustly,
                # maybe by raising an exception or setting a specific error code.
                self.errcode = -1 # Indicate an initialization error
        except Exception as e:
            # print(f"Python: epanetapi_shim: Error during __init__: {str(e)}")
            self.errcode = -1 # Indicate an initialization error


    def ENopen(self, inpfile_content, rptfile_path="report.rpt", binfile_path="out.bin"):
        # print(f"Python: ENopen called with rpt: {rptfile_path}, bin: {binfile_path}")
        if self.epanet_js_workspace is None or self.epanet_js_obj is None:
            # print("Python: ENopen: epanet-js objects not initialized.")
            self.errcode = 1 # Generic error code
            return self.errcode

        try:
            # epanet-js writeFile returns void, so no direct error check here other than exception
            self.epanet_js_workspace.writeFile("temp_model.inp", inpfile_content)
            # print("Python: ENopen: Successfully wrote to temp_model.inp")
            
            # epanet-js open method might return an error code or throw an exception
            # Based on epanet-js examples, it seems to throw errors or complete.
            # We'll assume direct calls and catch exceptions.
            # The open method in epanet-js Project class is just open(inp, rpt, out)
            self.epanet_js_obj.open("temp_model.inp", rptfile_path, binfile_path)
            # print("Python: ENopen: Model opened successfully.")
            self.errcode = 0
        except Exception as e:
            # print(f"Python: ENopen: Error during epanet-js operation: {str(e)}")
            # Try to get a more specific error code if possible, otherwise use a generic one
            # For now, a generic error code. epanet-js might not provide specific codes easily.
            self.errcode = 1 # Placeholder for error
        return self.errcode

    def ENsolveH(self):
        # print("Python: ENsolveH called")
        if self.epanet_js_obj is None:
            # print("Python: ENsolveH: epanet-js project not initialized.")
            self.errcode = 1
            return self.errcode
        try:
            # solveH in epanet-js project returns an error code or 0 for success.
            error_code = self.epanet_js_obj.solveH()
            self.errcode = error_code
            # print(f"Python: ENsolveH: Simulation solved. epanet-js returned code: {error_code}")
        except Exception as e:
            # print(f"Python: ENsolveH: Error during epanet-js solveH: {str(e)}")
            self.errcode = 1 # Placeholder for error
        return self.errcode

    def ENclose(self):
        # print("Python: ENclose called")
        if self.epanet_js_obj is None:
            # print("Python: ENclose: epanet-js project not initialized.")
            self.errcode = 1
            return self.errcode
        try:
            # close in epanet-js project returns an error code or 0.
            error_code = self.epanet_js_obj.close()
            self.errcode = error_code
            # print(f"Python: ENclose: Model closed. epanet-js returned code: {error_code}")
        except Exception as e:
            # print(f"Python: ENclose: Error during epanet-js close: {str(e)}")
            self.errcode = 1 # Placeholder for error
        return self.errcode

    def ENgetcount(self, countcode):
        # print(f"Python: ENgetcount called with code: {countcode}")
        if self.epanet_js_obj is None:
            # print("Python: ENgetcount: epanet-js project not initialized.")
            self.errcode = 1 
            return -1 # Return -1 for error as per EPyT's behavior for getcount

        value = -1 # Default error return
        try:
            if countcode == self.EN_NODECOUNT:
                value = self.epanet_js_obj.getNodeCount()
            elif countcode == self.EN_LINKCOUNT:
                value = self.epanet_js_obj.getLinkCount()
            # Add other count codes here if needed (e.g., EN_TANKCOUNT)
            # else:
                # print(f"Python: ENgetcount: Unknown countcode {countcode}")
                # self.errcode = 1 # Or a more specific error for invalid arg
                # return -1
            self.errcode = 0 # Success
            # print(f"Python: ENgetcount: Got value: {value} for code: {countcode}")
        except Exception as e:
            # print(f"Python: ENgetcount: Error during epanet-js call: {str(e)}")
            self.errcode = 1 # Placeholder for error
            value = -1
        return value

    def ENgeterror(self, errcode_val_from_epyt, max_len=80):
        # This is a simplified version. EPyT's ENgeterror retrieves a message
        # from the DLL. Here, we'll just return a generic message based on our internal errcode.
        # The errcode_val_from_epyt is the one EPyT passes, which might be different from self.errcode
        # For simplicity, we'll use self.errcode.
        # print(f"Python: ENgeterror called with errcode_val_from_epyt: {errcode_val_from_epyt}, self.errcode: {self.errcode}")

        if self.errcode == 0:
            return "No error."
        elif self.errcode == -1:
            return "EPANET Shim: Initialization failed (epanet-js objects not found)."
        # Add more specific messages if self.errcode is set more granularly
        else:
            # In a real scenario, you might try to fetch a more detailed error from epanet-js if available
            # or map epanet-js error codes to EPANET error messages.
            # For now, a generic error based on the internal code.
            return f"EPANET Shim: An error occurred (code {self.errcode}). Operation may have failed."

    def ENgetnodeid(self, node_index):
        # print(f"Python: ENgetnodeid called for index: {node_index}")
        if self.epanet_js_obj is None:
            self.errcode = 1
            return "" # Return empty string on error, EPyT might raise or return None
        try:
            # Assuming epanet-js has a method like getNodeId(index)
            # Note: epanet-js indices are typically 0-based, EPANET API is 1-based.
            # The epanet-js library's Project.getNodeId takes a 0-based index.
            node_id = self.epanet_js_obj.getNodeId(node_index - 1)
            self.errcode = 0
            # print(f"Python: ENgetnodeid: Got ID: {node_id}")
            return node_id
        except Exception as e:
            # print(f"Python: ENgetnodeid: Error: {str(e)}")
            self.errcode = 1
            return ""

    def ENgetcoord(self, node_index):
        # print(f"Python: ENgetcoord called for index: {node_index}")
        if self.epanet_js_obj is None:
            self.errcode = 1
            return (0.0, 0.0) # Return tuple (0,0) on error, EPyT might raise
        try:
            # Assuming epanet-js has getNodeCoordinates(index) returning {x: val, y: val}
            # The epanet-js library's Project.getNodeCoordinates takes a 0-based index.
            coords_obj = self.epanet_js_obj.getNodeCoordinates(node_index - 1)
            # Convert JS object to Python tuple
            # print(f"Python: ENgetcoord: Got JS coords_obj: {coords_obj}")
            # Check if coords_obj is not None and has x and y properties
            if coords_obj and hasattr(coords_obj, 'x') and hasattr(coords_obj, 'y'):
                self.errcode = 0
                return (float(coords_obj.x), float(coords_obj.y))
            else:
                # print(f"Python: ENgetcoord: Invalid coords_obj received: {coords_obj}")
                self.errcode = 1
                return (0.0, 0.0)
        except Exception as e:
            # print(f"Python: ENgetcoord: Error: {str(e)}")
            self.errcode = 1
            return (0.0, 0.0)

    def ENgetnodetype(self, node_index):
        # print(f"Python: ENgetnodetype called for index: {node_index}")
        if self.epanet_js_obj is None:
            self.errcode = 1
            return -1 # Return -1 for error, consistent with some EPANET API behaviors
        try:
            # Assuming epanet-js has getNodeType(index) returning an integer code
            # The epanet-js library's Project.getNodeType takes a 0-based index.
            node_type_code = self.epanet_js_obj.getNodeType(node_index - 1)
            self.errcode = 0
            # print(f"Python: ENgetnodetype: Got type code: {node_type_code}")
            return int(node_type_code) # Ensure it's an int
        except Exception as e:
            # print(f"Python: ENgetnodetype: Error: {str(e)}")
            self.errcode = 1
            return -1

    def ENgetlinkid(self, link_index):
        # print(f"Python: ENgetlinkid called for index: {link_index}")
        if self.epanet_js_obj is None:
            self.errcode = 1
            return ""
        try:
            # Assuming epanet-js has getLinkId(index)
            # The epanet-js library's Project.getLinkId takes a 0-based index.
            link_id = self.epanet_js_obj.getLinkId(link_index - 1)
            self.errcode = 0
            # print(f"Python: ENgetlinkid: Got ID: {link_id}")
            return link_id
        except Exception as e:
            # print(f"Python: ENgetlinkid: Error: {str(e)}")
            self.errcode = 1
            return ""

    def ENgetlinknodes(self, link_index):
        # print(f"Python: ENgetlinknodes called for index: {link_index}")
        if self.epanet_js_obj is None:
            self.errcode = 1
            return (0, 0) # Return (0,0) for error, EPANET API usually uses 0 for invalid index
        try:
            # Assuming epanet-js has getLinkNodes(index) returning [fromNodeIdx, toNodeIdx] (0-based)
            # The epanet-js library's Project.getLinkNodes takes a 0-based index.
            nodes_array = self.epanet_js_obj.getLinkNodes(link_index - 1)
            # Convert JS array to Python tuple, and adjust to 1-based indices for EPANET API consistency
            # print(f"Python: ENgetlinknodes: Got JS nodes_array: {nodes_array}")
            if nodes_array and hasattr(nodes_array, 'length') and nodes_array.length == 2:
                # Ensure elements are numbers before adding 1
                from_node_idx = int(nodes_array[0]) + 1
                to_node_idx = int(nodes_array[1]) + 1
                self.errcode = 0
                return (from_node_idx, to_node_idx)
            else:
                # print(f"Python: ENgetlinknodes: Invalid nodes_array received: {nodes_array}")
                self.errcode = 1
                return (0,0)
        except Exception as e:
            # print(f"Python: ENgetlinknodes: Error: {str(e)}")
            self.errcode = 1
            return (0, 0)

    def ENopenH(self):
        # print("Python: ENopenH called")
        if self.epanet_js_obj is None:
            self.errcode = 1; return self.errcode
        try:
            self.epanet_js_obj.openH()
            self.errcode = 0
        except Exception as e:
            # print(f"Python: ENopenH Error: {str(e)}")
            self.errcode = 1
        return self.errcode

    def ENinitH(self, save_flag):
        # print(f"Python: ENinitH called with save_flag: {save_flag}")
        # epanet-js initH expects a boolean: true to save results, false otherwise.
        # EPANET API: 0 = NOSAVE, 1 = SAVE, 2 = SAVE AND INIT (for quality)
        # We'll map 1 (SAVE) to true, others to false for simplicity here.
        js_save_flag = True if save_flag == 1 else False
        if self.epanet_js_obj is None:
            self.errcode = 1; return self.errcode
        try:
            self.epanet_js_obj.initH(js_save_flag)
            self.errcode = 0
        except Exception as e:
            # print(f"Python: ENinitH Error: {str(e)}")
            self.errcode = 1
        return self.errcode

    def ENrunH(self):
        # print("Python: ENrunH called")
        if self.epanet_js_obj is None:
            self.errcode = 1; return -1 # Return -1 for error, time is usually non-negative
        try:
            current_time = self.epanet_js_obj.runH()
            self.errcode = 0
            return current_time # Should be current simulation time in seconds
        except Exception as e:
            # print(f"Python: ENrunH Error: {str(e)}")
            self.errcode = 1
            return -1

    def ENnextH(self):
        # print("Python: ENnextH called")
        if self.epanet_js_obj is None:
            self.errcode = 1; return 0 # Return 0 for error, tstep is usually >0
        try:
            time_to_next_event = self.epanet_js_obj.nextH()
            self.errcode = 0
            return time_to_next_event # Should be time to next event in seconds
        except Exception as e:
            # print(f"Python: ENnextH Error: {str(e)}")
            self.errcode = 1
            return 0
            
    def ENcloseH(self):
        # print("Python: ENcloseH called")
        if self.epanet_js_obj is None:
            self.errcode = 1; return self.errcode
        try:
            self.epanet_js_obj.closeH()
            self.errcode = 0
        except Exception as e:
            # print(f"Python: ENcloseH Error: {str(e)}")
            self.errcode = 1
        return self.errcode

    def ENgetnodevalue(self, node_index, param_code):
        # print(f"Python: ENgetnodevalue called for node index: {node_index}, param: {param_code}")
        if self.epanet_js_obj is None:
            self.errcode = 1; return 0.0 # Return 0.0 for error
        try:
            # epanet-js uses 0-based indexing
            value = self.epanet_js_obj.getNodeValue(node_index - 1, param_code)
            self.errcode = 0
            return float(value)
        except Exception as e:
            # print(f"Python: ENgetnodevalue Error: {str(e)}")
            self.errcode = 1
            return 0.0

    def ENsetnodevalue(self, node_index, param_code, value):
        # print(f"Python: ENsetnodevalue called for node index: {node_index}, param: {param_code}, value: {value}")
        if self.epanet_js_obj is None:
            self.errcode = 1; return self.errcode
        
        js_param_code = param_code # Default if codes match
        if param_code == self.EN_EMITTER: # EPyT EN_EMITTER (3)
            js_param_code = self.JS_NODEPROP_EMITTER # epanet-js NodeProperty.EmitterCoeff (12)
        elif param_code == self.EN_BASEDEMAND: # EPyT EN_BASEDEMAND (1)
            js_param_code = 1 # epanet-js NodeProperty.BaseDemand (1) - same
        # Add other mappings as necessary for other settable EPyT codes
        # else:
            # Potentially raise error for unmapped/unsupported param_code for setting

        try:
            # epanet-js uses 0-based indexing
            self.epanet_js_obj.setNodeValue(node_index - 1, js_param_code, float(value))
            self.errcode = 0
        except Exception as e:
            # print(f"Python: ENsetnodevalue Error: {str(e)}")
            self.errcode = 1
        return self.errcode

    def ENgetlinkvalue(self, link_index, param_code):
        # print(f"Python: ENgetlinkvalue called for link index: {link_index}, param: {param_code}")
        if self.epanet_js_obj is None:
            self.errcode = 1; return 0.0

        js_param_code = param_code # Default if codes match
        if param_code == 8: # Assuming EPyT uses 8 for Flow, which matches JS_LINKPROP_FLOW
            js_param_code = self.JS_LINKPROP_FLOW
        # Add other mappings if EPyT codes differ from epanet-js codes for links
        # For example, if EPyT uses EN_STATUS = 10, map to JS_LINKPROP_STATUS = 3

        try:
            # epanet-js uses 0-based indexing
            value = self.epanet_js_obj.getLinkValue(link_index - 1, js_param_code)
            self.errcode = 0
            return float(value)
        except Exception as e:
            # print(f"Python: ENgetlinkvalue Error: {str(e)}")
            self.errcode = 1
            return 0.0

    # ENsetlinkvalue would follow a similar pattern to ENsetnodevalue with code mapping
    # def ENsetlinkvalue(self, link_index, param_code, value): ...

    def ENsetdemandmodel(self, model_type_int, pmin_float, preq_float, pexp_float):
        # print(f"Python: ENsetdemandmodel called with type: {model_type_int}, Pmin: {pmin_float}, Preq: {preq_float}, Pexp: {pexp_float}")
        if self.epanet_js_obj is None:
            self.errcode = 1; return self.errcode
        try:
            # epanet-js setDemandModel(model: number, minPressure: number, reqPressure: number, exponent: number)
            # model: 0 for DDA, 1 for PDA
            self.epanet_js_obj.setDemandModel(int(model_type_int), float(pmin_float), float(preq_float), float(pexp_float))
            self.errcode = 0
        except Exception as e:
            # print(f"Python: ENsetdemandmodel Error: {str(e)}")
            self.errcode = 1
        return self.errcode

    def ENsetqualtype(self, qualcode_int, chemname_str, chemunits_str, tracenode_str):
        # print(f"Python: ENsetqualtype called with qualcode: {qualcode_int}, chemname: '{chemname_str}', chemunits: '{chemunits_str}', tracenode: '{tracenode_str}'")
        if self.epanet_js_obj is None:
            self.errcode = 1; return self.errcode
        try:
            # Ensure tracenode_str is None if empty, as epanet-js might expect null/undefined for non-trace cases
            # However, epanet-js setQualityType expects a string for traceNodeId. If it's not TRACE, it might ignore it.
            # For safety, if qualcode is not TRACE, pass empty string, which epanet-js should handle.
            effective_tracenode_str = tracenode_str if qualcode_int == self.EN_TRACE and tracenode_str else ""

            self.epanet_js_obj.setQualityType(int(qualcode_int), str(chemname_str), str(chemunits_str), str(effective_tracenode_str))
            self.errcode = 0
        except Exception as e:
            # print(f"Python: ENsetqualtype Error: {str(e)}")
            self.errcode = 1
        return self.errcode

    def ENopenQ(self):
        if self.epanet_js_obj is None: self.errcode = 1; return self.errcode
        try: self.epanet_js_obj.openQ(); self.errcode = 0
        except Exception as e: self.errcode = 1; # print(f"ENopenQ Error: {e}")
        return self.errcode

    def ENinitQ(self, saveflag_int):
        if self.epanet_js_obj is None: self.errcode = 1; return self.errcode
        try: 
            # epanet-js initQ takes a boolean saveResults flag.
            # EPANET API: 0 for NOSAVE, 1 for SAVE.
            js_save_flag = True if saveflag_int == 1 else False
            self.epanet_js_obj.initQ(js_save_flag)
            self.errcode = 0
        except Exception as e: self.errcode = 1; # print(f"ENinitQ Error: {e}")
        return self.errcode

    def ENrunQ(self):
        if self.epanet_js_obj is None: self.errcode = 1; return -1 # error, time is non-negative
        try: 
            current_q_time = self.epanet_js_obj.runQ()
            self.errcode = 0
            return current_q_time
        except Exception as e: self.errcode = 1; # print(f"ENrunQ Error: {e}"); 
        return -1
        
    def ENnextQ(self):
        if self.epanet_js_obj is None: self.errcode = 1; return 0 # error, tstep usually >0
        try: 
            time_to_next_q_event = self.epanet_js_obj.nextQ()
            self.errcode = 0
            return time_to_next_q_event
        except Exception as e: self.errcode = 1; # print(f"ENnextQ Error: {e}"); 
        return 0

    def ENcloseQ(self):
        if self.epanet_js_obj is None: self.errcode = 1; return self.errcode
        try: self.epanet_js_obj.closeQ(); self.errcode = 0
        except Exception as e: self.errcode = 1; # print(f"ENcloseQ Error: {e}")
        return self.errcode

    # The `ph` (Prolog/Headless) and `customlib` parameters are not used in this shim
    # as epanet-js is the only "library" we're interacting with.
    # Version is also informational for this shim.
pass
