import epanetapi_shim # This will be the epanetapi_shim.py file we created

class epanet:
    def __init__(self, inp_content_str, version=2.2, ph=False, loadfile=False, customlib=None, display_msg=True, display_warnings=True):
        """
        Initializes the EPANET simulation object.

        Args:
            inp_content_str (str): The full content of the INP file as a string.
            version (float, optional): EPANET version. Defaults to 2.2. Not strictly used by the shim.
            ph (bool, optional): Placeholder for Prolog/Headless mode. Defaults to False. Not used.
            loadfile (bool, optional): Placeholder. Defaults to False. The shim expects content directly.
            customlib (str, optional): Placeholder for custom library path. Defaults to None. Not used.
            display_msg (bool, optional): Placeholder. Defaults to True. Not used.
            display_warnings (bool, optional): Placeholder. Defaults to True. Not used.
        """
        # print("Python: epanet_shim: __init__ called.")
        if not isinstance(inp_content_str, str):
            raise TypeError("inp_content_str must be a string containing the INP file data.")
        
        self.InputFileContent = inp_content_str
        self._version = version # Store for getVersion, though it's fixed for the shim
        
        # print("Python: epanet_shim: Initializing epanetapi_shim.epanetapi...")
        self.api = epanetapi_shim.epanetapi(version=version, ph=ph, customlib=customlib)
        
        if self.api.errcode != 0:
            # print("Python: epanet_shim: Error during epanetapi_shim initialization.")
            # Propagate error or handle, for now, let's assume an error message is sufficient
            # Or raise an exception here.
            raise RuntimeError(f"Failed to initialize epanetapi_shim: {self.api.ENgeterror(self.api.errcode)}")

        # print("Python: epanet_shim: Calling self.api.ENopen with INP content.")
        # The first argument to ENopen in the shim is the INP content string directly
        ret = self.api.ENopen(self.InputFileContent, "report.rpt", "out.bin")
        if ret != 0:
            # print(f"Python: epanet_shim: ENopen failed with code {ret}. Error: {self.api.ENgeterror(ret)}")
            raise RuntimeError(f"EPANET ENopen failed: {self.api.ENgeterror(ret)}")
        # print("Python: epanet_shim: __init__ completed successfully.")

    def getNodeCount(self):
        """
        Gets the number of nodes in the network.
        """
        # print("Python: epanet_shim: getNodeCount called.")
        count = self.api.ENgetcount(epanetapi_shim.epanetapi.EN_NODECOUNT)
        if self.api.errcode != 0:
            # print(f"Python: epanet_shim: Error in ENgetcount for nodes. Code: {self.api.errcode}")
            raise RuntimeError(f"Error getting node count: {self.api.ENgeterror(self.api.errcode)}")
        return count

    def getLinkCount(self):
        """
        Gets the number of links in the network.
        """
        # print("Python: epanet_shim: getLinkCount called.")
        count = self.api.ENgetcount(epanetapi_shim.epanetapi.EN_LINKCOUNT)
        if self.api.errcode != 0:
            # print(f"Python: epanet_shim: Error in ENgetcount for links. Code: {self.api.errcode}")
            raise RuntimeError(f"Error getting link count: {self.api.ENgeterror(self.api.errcode)}")
        return count

    def solveCompleteHydraulics(self):
        """
        Runs a complete hydraulic simulation.
        """
        # print("Python: epanet_shim: solveCompleteHydraulics called.")
        ret = self.api.ENsolveH()
        if ret != 0:
            # print(f"Python: epanet_shim: ENsolveH failed with code {ret}. Error: {self.api.ENgeterror(ret)}")
            raise RuntimeError(f"EPANET ENsolveH failed: {self.api.ENgeterror(ret)}")
        # print("Python: epanet_shim: solveCompleteHydraulics completed.")
        return ret # Should be 0 on success

    def closeNetwork(self):
        """
        Closes the EPANET network.
        """
        # print("Python: epanet_shim: closeNetwork called.")
        ret = self.api.ENclose()
        if ret != 0:
            # print(f"Python: epanet_shim: ENclose failed with code {ret}. Error: {self.api.ENgeterror(ret)}")
            # It might be better not to raise an error on close failure if EPyT doesn't,
            # but for debugging, it's useful.
            raise RuntimeError(f"EPANET ENclose failed: {self.api.ENgeterror(ret)}")
        # print("Python: epanet_shim: closeNetwork completed.")
        return ret # Should be 0 on success

    def getVersion(self):
        """
        Returns the (shimmed) EPANET version.
        """
        # print("Python: epanet_shim: getVersion called.")
        return f"{self._version} (shimmed for epanet-js)"

    # Add other EPyT methods here as needed, calling self.api methods.
    # For example:
    # def getNodePressure(self, node_index):
    #     # This would require ENgetnodevalue in epanetapi_shim
    #     # value = self.api.ENgetnodevalue(node_index, epanetapi_shim.epanetapi.EN_PRESSURE)
    #     # Check self.api.errcode
    #     # return value
    #     pass

    # def saveInputFile(self, filename):
    #     # This would require ENsaveinpfile in epanetapi_shim
    #     # ret = self.api.ENsaveinpfile(filename)
    #     # Check self.api.errcode
    #     pass

# Example of how constants would be accessed if defined in epanetapi_shim
# NODE_COUNT_CONSTANT = epanetapi_shim.epanetapi.EN_NODECOUNT
# LINK_COUNT_CONSTANT = epanetapi_shim.epanetapi.EN_LINKCOUNT
# (These are used internally by the methods above)

    def get_network_topology(self):
        """
        Extracts the network topology (nodes and links) from the loaded INP file.
        Returns a dictionary suitable for Cytoscape.js.
        """
        # print("Python: epanet_shim: get_network_topology called.")
        if not self.api or self.api.errcode != 0:
            # print("Python: epanet_shim: API not initialized or in error state.")
            raise RuntimeError("EPANET API not initialized or in error state before getting topology.")

        # EPyT uses ToolkitConstants for these, so we use the shim's constants
        node_count = self.api.ENgetcount(epanetapi_shim.epanetapi.EN_NODECOUNT)
        if self.api.errcode != 0:
            raise RuntimeError(f"Error getting node count: {self.api.ENgeterror(self.api.errcode)}")
        
        link_count = self.api.ENgetcount(epanetapi_shim.epanetapi.EN_LINKCOUNT)
        if self.api.errcode != 0:
            raise RuntimeError(f"Error getting link count: {self.api.ENgeterror(self.api.errcode)}")

        # print(f"Python: epanet_shim: Node count: {node_count}, Link count: {link_count}")

        nodes_data = []
        node_id_map = {} # To map 1-based index to ID for link creation

        for i in range(1, node_count + 1): # EPANET indices are 1-based
            node_id = self.api.ENgetnodeid(i)
            if self.api.errcode != 0:
                raise RuntimeError(f"Error getting ID for node index {i}: {self.api.ENgeterror(self.api.errcode)}")
            
            coords = self.api.ENgetcoord(i) # Returns (x, y)
            if self.api.errcode != 0:
                raise RuntimeError(f"Error getting coordinates for node {node_id} (index {i}): {self.api.ENgeterror(self.api.errcode)}")
            
            node_type_code = self.api.ENgetnodetype(i)
            if self.api.errcode != 0:
                raise RuntimeError(f"Error getting type for node {node_id} (index {i}): {self.api.ENgeterror(self.api.errcode)}")

            node_id_map[i] = node_id
            
            # Map EPANET type codes to string types for Cytoscape
            node_type_str = "junction" # Default
            if node_type_code == epanetapi_shim.epanetapi.EN_TANK:
                node_type_str = "tank"
            elif node_type_code == epanetapi_shim.epanetapi.EN_RESERVOIR:
                node_type_str = "reservoir"
            # Add other types if needed

            nodes_data.append({
                'id': node_id,
                'x': coords[0],
                'y': coords[1],
                'type_code': node_type_code, # Keep original code if needed
                'type': node_type_str # For Cytoscape styling
            })
        
        links_data = []
        for i in range(1, link_count + 1): # EPANET indices are 1-based
            link_id = self.api.ENgetlinkid(i)
            if self.api.errcode != 0:
                raise RuntimeError(f"Error getting ID for link index {i}: {self.api.ENgeterror(self.api.errcode)}")
            
            from_node_idx, to_node_idx = self.api.ENgetlinknodes(i)
            if self.api.errcode != 0:
                raise RuntimeError(f"Error getting nodes for link {link_id} (index {i}): {self.api.ENgeterror(self.api.errcode)}")

            if from_node_idx == 0 or to_node_idx == 0: # Error from ENgetlinknodes
                 raise RuntimeError(f"Invalid node indices (0) returned for link {link_id} (index {i}).")

            source_node_id = node_id_map.get(from_node_idx)
            target_node_id = node_id_map.get(to_node_idx)

            if not source_node_id or not target_node_id:
                raise RuntimeError(f"Could not map node indices ({from_node_idx}, {to_node_idx}) to IDs for link {link_id}.")

            links_data.append({
                'id': link_id,
                'source': source_node_id,
                'target': target_node_id
            })
            
        # print(f"Python: epanet_shim: Topology extraction complete. Nodes: {len(nodes_data)}, Links: {len(links_data)}")
        return {'nodes': nodes_data, 'links': links_data}

    def setNodeEmitterCoeff(self, node_index, emitter_coeff):
        """
        Sets the emitter coefficient for a given node.
        node_index is 1-based.
        """
        # print(f"Python: epanet_shim: setNodeEmitterCoeff called for node index {node_index} with coeff {emitter_coeff}")
        ret = self.api.ENsetnodevalue(node_index, epanetapi_shim.epanetapi.EN_EMITTER, float(emitter_coeff))
        if ret != 0: # ENsetnodevalue returns errcode
            raise RuntimeError(f"EPANET ENsetnodevalue for emitter failed (node {node_index}, coeff {emitter_coeff}): {self.api.ENgeterror(ret)}")
        # print(f"Python: epanet_shim: Emitter coefficient for node index {node_index} set to {emitter_coeff}")
        return ret # Should be 0 on success

    def setDemandModel(self, type_str, pmin_float, preq_float, pexp_float):
        """
        Sets the demand model and its parameters.
        type_str: "DDA" or "PDA"
        pmin_float, preq_float, pexp_float: PDD parameters
        """
        # print(f"Python: epanet_shim: setDemandModel called with type: {type_str}, Pmin: {pmin_float}, Preq: {preq_float}, Pexp: {pexp_float}")
        model_type_int = 1 if type_str.upper() == "PDA" else 0 # 0 for DDA, 1 for PDA
        
        ret = self.api.ENsetdemandmodel(model_type_int, float(pmin_float), float(preq_float), float(pexp_float))
        if ret != 0: # ENsetdemandmodel returns errcode
            raise RuntimeError(f"EPANET ENsetdemandmodel failed (type {type_str}, params {pmin_float},{preq_float},{pexp_float}): {self.api.ENgeterror(ret)}")
        # print(f"Python: epanet_shim: Demand model set to {type_str}.")
        return ret # Should be 0 on success

    def setQualityType(self, type_str, chemName_str="", chemUnits_str="", traceNode_id_str=""):
        # print(f"Python: epanet_shim: setQualityType called with type: {type_str}, traceNode: '{traceNode_id_str}'")
        qualcode_int = epanetapi_shim.epanetapi.EN_NONE # Default
        type_upper = type_str.upper()
        if type_upper == "AGE":
            qualcode_int = epanetapi_shim.epanetapi.EN_AGE
        elif type_upper == "TRACE":
            qualcode_int = epanetapi_shim.epanetapi.EN_TRACE
        elif type_upper == "CHEM": # Basic support, though not fully configurable via UI in this PoC
            qualcode_int = epanetapi_shim.epanetapi.EN_CHEM
        
        # For TRACE, traceNode_id_str must be a valid Node ID. If not TRACE, it's ignored by API.
        api_trace_node_id = traceNode_id_str if type_upper == 'TRACE' and traceNode_id_str else ""

        ret = self.api.ENsetqualtype(qualcode_int, chemName_str, chemUnits_str, api_trace_node_id)
        if ret != 0:
            raise RuntimeError(f"EPANET ENsetqualtype failed (type {type_str}, trace {api_trace_node_id}): {self.api.ENgeterror(ret)}")
        # print(f"Python: epanet_shim: Quality type set to {type_str} with trace node '{api_trace_node_id}'.")
        return ret

    def openQualityAnalysis(self):
        ret = self.api.ENopenQ()
        if ret != 0: raise RuntimeError(f"EPANET ENopenQ failed: {self.api.ENgeterror(ret)}")
        return ret

    def initializeQualityAnalysis(self, save_flag=0):
        ret = self.api.ENinitQ(save_flag) # save_flag: 0 for NOSAVE, 1 for SAVE
        if ret != 0: raise RuntimeError(f"EPANET ENinitQ failed: {self.api.ENgeterror(ret)}")
        return ret

    def runQualityAnalysis(self):
        current_q_time = self.api.ENrunQ()
        if self.api.errcode != 0:
            raise RuntimeError(f"EPANET ENrunQ failed: {self.api.ENgeterror(self.api.errcode)}")
        return current_q_time

    def nextQualityAnalysisStep(self):
        time_to_next_q_event = self.api.ENnextQ()
        if self.api.errcode != 0:
            raise RuntimeError(f"EPANET ENnextQ failed: {self.api.ENgeterror(self.api.errcode)}")
        return time_to_next_q_event

    def closeQualityAnalysis(self):
        ret = self.api.ENcloseQ()
        if ret != 0: raise RuntimeError(f"EPANET ENcloseQ failed: {self.api.ENgeterror(ret)}")
        return ret

    def getNodeActualQuality(self, node_index):
        # In EPyT, getNodeActualQuality returns a list (usually one value for non-CHEM)
        # ENgetnodevalue in our shim returns a float directly
        # For consistency with potential EPyT usage, we wrap it in a list
        # Note: EN_QUALITY (2) in epanetapi_shim maps to JS_NODEPROP_QUALITY (2)
        quality_val = self.api.ENgetnodevalue(node_index, epanetapi_shim.epanetapi.EN_QUALITY)
        if self.api.errcode != 0:
            raise RuntimeError(f"Error getting quality for node index {node_index}: {self.api.ENgeterror(self.api.errcode)}")
        return [quality_val] # Return as a list

    def run_single_quality_step_for_js(self, node_id_to_get_quality):
        # print(f"Python: epanet_shim: run_single_quality_step_for_js for node ID: {node_id_to_get_quality}")
        try:
            current_q_time = self.runQualityAnalysis()
            
            node_idx_list = self.getNodeIndex([str(node_id_to_get_quality)])
            node_idx = node_idx_list[0]
            
            quality_val_array = self.getNodeActualQuality(node_idx) # Returns a list
            quality_val = quality_val_array[0] if quality_val_array else 0.0 # Default if empty for some reason

            time_to_next_q_event = self.nextQualityAnalysisStep()
            
            return {
                'currentTime': current_q_time,
                'nodeId': str(node_id_to_get_quality),
                'quality': quality_val,
                'nextQualityEventTime': time_to_next_q_event,
                'error': None
            }
        except Exception as e:
            # import traceback
            # traceback.print_exc()
            return {
                'currentTime': -1,
                'nodeId': str(node_id_to_get_quality),
                'quality': 0.0,
                'nextQualityEventTime': 0,
                'error': str(e)
            }

    def openHydraulicAnalysis(self):
        # print("Python: epanet_shim: openHydraulicAnalysis called.")
        ret = self.api.ENopenH()
        if ret != 0:
            raise RuntimeError(f"EPANET ENopenH failed: {self.api.ENgeterror(ret)}")
        return ret

    def initializeHydraulicAnalysis(self, save_flag=0):
        # print(f"Python: epanet_shim: initializeHydraulicAnalysis called with save_flag: {save_flag}")
        # Default save_flag = 0 (NOSAVE). EPANET API: 0=NOSAVE, 1=SAVE
        ret = self.api.ENinitH(save_flag)
        if ret != 0:
            raise RuntimeError(f"EPANET ENinitH failed: {self.api.ENgeterror(ret)}")
        return ret

    def runHydraulicAnalysis(self):
        # print("Python: epanet_shim: runHydraulicAnalysis called.")
        current_time = self.api.ENrunH()
        if self.api.errcode != 0: # ENrunH returns time, error is checked via self.api.errcode
            raise RuntimeError(f"EPANET ENrunH failed: {self.api.ENgeterror(self.api.errcode)}")
        return current_time

    def nextHydraulicAnalysisStep(self):
        # print("Python: epanet_shim: nextHydraulicAnalysisStep called.")
        time_to_next_event = self.api.ENnextH()
        if self.api.errcode != 0: # ENnextH returns time, error is checked via self.api.errcode
            raise RuntimeError(f"EPANET ENnextH failed: {self.api.ENgeterror(self.api.errcode)}")
        return time_to_next_event

    def closeHydraulicAnalysis(self):
        # print("Python: epanet_shim: closeHydraulicAnalysis called.")
        ret = self.api.ENcloseH()
        if ret != 0:
            raise RuntimeError(f"EPANET ENcloseH failed: {self.api.ENgeterror(ret)}")
        return ret

    def getNodePressure(self, node_index):
        # print(f"Python: epanet_shim: getNodePressure called for index {node_index}.")
        pressure = self.api.ENgetnodevalue(node_index, epanetapi_shim.epanetapi.EN_PRESSURE)
        if self.api.errcode != 0:
            raise RuntimeError(f"Error getting pressure for node index {node_index}: {self.api.ENgeterror(self.api.errcode)}")
        return pressure

    def getLinkFlows(self, link_index): # Note: EPyT calls this getLinkFlows (plural)
        # print(f"Python: epanet_shim: getLinkFlows called for index {link_index}.")
        flow = self.api.ENgetlinkvalue(link_index, epanetapi_shim.epanetapi.EN_FLOW)
        if self.api.errcode != 0:
            raise RuntimeError(f"Error getting flow for link index {link_index}: {self.api.ENgeterror(self.api.errcode)}")
        return flow

    def getNodeIndex(self, node_ids_list):
        """
        Helper to get node indices from IDs. EPyT has this.
        For simplicity, this shim version assumes self.api.ENgetnodeindex exists
        or we implement a basic version if ENgetnodeid is already available.
        This is a simplified version. A robust one would build a map or iterate.
        """
        # print(f"Python: epanet_shim: getNodeIndex for IDs: {node_ids_list}")
        # This is a placeholder implementation. A real one would map IDs to indices.
        # For this PoC, we assume the epanet-js layer or a full ENgetnodeindex isn't directly shimmed yet
        # for ID to Index conversion. We'll iterate using ENgetnodeid.
        # This is inefficient but works for a PoC.
        node_indices = []
        if not hasattr(self, '_node_id_to_index_map') or not self._node_id_to_index_map:
            self._node_id_to_index_map = {}
            node_count = self.api.ENgetcount(epanetapi_shim.epanetapi.EN_NODECOUNT)
            if self.api.errcode != 0: raise RuntimeError("Failed to get node count for ID mapping")
            for i in range(1, node_count + 1):
                node_id = self.api.ENgetnodeid(i)
                if self.api.errcode != 0: raise RuntimeError(f"Failed to get node ID for index {i}")
                self._node_id_to_index_map[node_id] = i
        
        for node_id_str in node_ids_list:
            idx = self._node_id_to_index_map.get(str(node_id_str)) # Ensure string comparison
            if idx is None:
                raise ValueError(f"Node ID '{node_id_str}' not found in network.")
            node_indices.append(idx)
        return node_indices


    def getLinkIndex(self, link_ids_list):
        """
        Helper to get link indices from IDs. EPyT has this.
        Similar to getNodeIndex, this is a simplified placeholder.
        """
        # print(f"Python: epanet_shim: getLinkIndex for IDs: {link_ids_list}")
        link_indices = []
        if not hasattr(self, '_link_id_to_index_map') or not self._link_id_to_index_map:
            self._link_id_to_index_map = {}
            link_count = self.api.ENgetcount(epanetapi_shim.epanetapi.EN_LINKCOUNT)
            if self.api.errcode != 0: raise RuntimeError("Failed to get link count for ID mapping")
            for i in range(1, link_count + 1):
                link_id = self.api.ENgetlinkid(i)
                if self.api.errcode != 0: raise RuntimeError(f"Failed to get link ID for index {i}")
                self._link_id_to_index_map[link_id] = i

        for link_id_str in link_ids_list:
            idx = self._link_id_to_index_map.get(str(link_id_str))
            if idx is None:
                raise ValueError(f"Link ID '{link_id_str}' not found in network.")
            link_indices.append(idx)
        return link_indices

    def run_single_hydraulic_step_for_js(self, node_id_to_get_pressure, link_id_to_get_flow):
        # print(f"Python: epanet_shim: run_single_hydraulic_step_for_js called with node_id: {node_id_to_get_pressure}, link_id: {link_id_to_get_flow}")
        try:
            current_time = self.runHydraulicAnalysis()
            
            # Get Node Index from ID
            # getNodeIndex expects a list and returns a list
            node_idx_list = self.getNodeIndex([str(node_id_to_get_pressure)]) 
            node_idx = node_idx_list[0]
            pressure = self.getNodePressure(node_idx)
            
            # Get Link Index from ID
            link_idx_list = self.getLinkIndex([str(link_id_to_get_flow)])
            link_idx = link_idx_list[0]
            flow = self.getLinkFlows(link_idx)
            
            time_to_next_event = self.nextHydraulicAnalysisStep()
            
            return {
                'currentTime': current_time,
                'nodeId': str(node_id_to_get_pressure), # Ensure string
                'pressure': pressure,
                'linkId': str(link_id_to_get_flow),   # Ensure string
                'flow': flow,
                'nextEventTime': time_to_next_event,
                'error': None # No error
            }
        except Exception as e:
            # print(f"Python: Error in run_single_hydraulic_step_for_js: {str(e)}")
            # import traceback
            # traceback.print_exc()
            return {
                'currentTime': -1,
                'nodeId': str(node_id_to_get_pressure),
                'pressure': 0.0,
                'linkId': str(link_id_to_get_flow),
                'flow': 0.0,
                'nextEventTime': 0,
                'error': str(e)
            }

# Note: The original EPyT library has extensive error checking and handling,
# including specific exception types. This shim is simplified for the PoC.
pass
