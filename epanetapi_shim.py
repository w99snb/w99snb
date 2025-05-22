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
    # Other constants can be added as needed
    # Link types (for reference if ENgetlinktype is added later)
    # EN_CVPIPE = 0 (seems to be an error in some docs, usually 0 is for pipes if types are indexed)
    # EN_PIPE = 1 (EPyT uses 1 for Pipe)
    # EN_PUMP = 2
    # EN_PRV = 3
    # ... etc.

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

    # The `ph` (Prolog/Headless) and `customlib` parameters are not used in this shim
    # as epanet-js is the only "library" we're interacting with.
    # Version is also informational for this shim.
pass
