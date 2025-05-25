print("Python: epanet_shim.py script started")
import epanetapi_shim # The low-level shim for epanet-js

__epanet_shim_version__ = "1.0.4"
EPANET_SHIM_PY_VERSION = "v_shim_1" #TODO: This seems like an old version string, consider removing or reconciling

# High-level Python class mimicking EPyT's `epanet` class interface.
# This class provides a more user-friendly API for EPANET operations and
# uses the `epanetapi_shim.epanetapi` class for actual interaction with epanet-js.
# It aims to abstract away the direct calls to the C-like API provided by the shim.
class epanet:
    def __init__(self, inp_content_str, version=2.2, ph=False, loadfile=False, customlib=None, display_msg=True, display_warnings=True):
        """
        Initializes the EPANET simulation object by loading an INP file content.
        Args:
            inp_content_str (str): The full content of the INP file as a string.
            version (float, optional): EPANET version. Placeholder, not strictly used by the shim.
            ph (bool, optional): Placeholder for Prolog/Headless mode. Not used.
            loadfile (bool, optional): Placeholder. The shim expects content directly. Not used.
            customlib (str, optional): Placeholder for custom library path. Not used.
            display_msg (bool, optional): Placeholder. Not used.
            display_warnings (bool, optional): Placeholder. Not used.
        Raises:
            TypeError: If inp_content_str is not a string.
            RuntimeError: If the underlying epanetapi_shim fails to initialize or open the INP file.
        """
        print(f"Python: epanet_shim.py version {__epanet_shim_version__} loaded.")
        # print("Python: epanet_shim: __init__ called.")
        if not isinstance(inp_content_str, str):
            raise TypeError("inp_content_str must be a string containing the INP file data.")
        
        self.InputFileContent = inp_content_str
        self._version = version # Store for getVersion, though it's fixed for this shim
        
        self.api = epanetapi_shim.epanetapi(version=version, ph=ph, customlib=customlib)
        
        if self.api.errcode != 0:
            raise RuntimeError(f"Failed to initialize epanetapi_shim: {self.api.ENgeterror(self.api.errcode)}")

        # Open the model using the provided INP content string.
        # The epanetapi_shim's ENopen expects byte strings.
        
        print(f"EPANET Shim: inp_content_str (first 500 chars): {inp_content_str[:500]}")
        
        # String cleaning logic removed as per request.
        
        self.rpt_file = "report.rpt"
        self.out_file = "out.bin"
        
        # Sanitize INP file content
        lines = inp_content_str.splitlines()
        sanitized_lines = []
        for line in lines:
            # Normalize line endings (already handled by splitlines, but good for clarity)
            # Trim leading/trailing whitespace from each line
            sanitized_line = line.strip()
            sanitized_lines.append(sanitized_line)
        # Reconstruct the content, ensuring newline characters are '\n'
        inp_content_str = "\n".join(sanitized_lines)

        # Add a print statement to log the sanitized content for verification (optional, for debugging)
        # print(f"EPANET Shim: Sanitized inp_content_str (first 500 chars): {inp_content_str[:500]}")
        
        # inp_content_str is already the sanitized string, ready for the shim
        # which now expects a string for inpfile_content_str.
        
        print("EPANET Shim: CALLING ENOPEN NOW")
        # Pass the INP content string directly, and self.rpt_file, self.out_file as strings.
        # The epanetapi_shim's ENopen now expects string paths for rpt and out files,
        # and will handle any necessary encoding or type conversion for inp_content_str itself.
        ret = self.api.ENopen(inp_content_str, self.rpt_file, self.out_file)
        print(f"EPANET Shim: ENOPEN RETURNED {ret}")
        if ret != 0:
            raise RuntimeError(f"EPANET ENopen failed with code {ret}: {self.api.ENgeterror(ret)}")
        
        # Initialize internal maps for ID to Index lookups (cached)
        self._node_id_to_index_map = {}
        self._link_id_to_index_map = {}
        self._build_id_to_index_maps()


    def _build_id_to_index_maps(self):
        """
        Internal helper to build or rebuild ID-to-index maps for nodes and links.
        This is called after loading a new INP file.
        """
        self._node_id_to_index_map.clear()
        node_count = self.api.ENgetcount(epanetapi_shim.epanetapi.EN_NODECOUNT)
        if self.api.errcode != 0: raise RuntimeError("Failed to get node count for ID mapping")
        for i in range(1, node_count + 1):
            node_id = self.api.ENgetnodeid(i)
            if self.api.errcode != 0: raise RuntimeError(f"Failed to get node ID for index {i} during map build")
            self._node_id_to_index_map[node_id] = i

        self._link_id_to_index_map.clear()
        link_count = self.api.ENgetcount(epanetapi_shim.epanetapi.EN_LINKCOUNT)
        if self.api.errcode != 0: raise RuntimeError("Failed to get link count for ID mapping")
        for i in range(1, link_count + 1):
            link_id = self.api.ENgetlinkid(i)
            if self.api.errcode != 0: raise RuntimeError(f"Failed to get link ID for index {i} during map build")
            self._link_id_to_index_map[link_id] = i


    def getNodeCount(self):
        """Gets the number of nodes in the network."""
        count = self.api.ENgetcount(epanetapi_shim.epanetapi.EN_NODECOUNT)
        if self.api.errcode != 0:
            raise RuntimeError(f"Error getting node count: {self.api.ENgeterror(self.api.errcode)}")
        return count

    def getLinkCount(self):
        """Gets the number of links in the network."""
        count = self.api.ENgetcount(epanetapi_shim.epanetapi.EN_LINKCOUNT)
        if self.api.errcode != 0:
            raise RuntimeError(f"Error getting link count: {self.api.ENgeterror(self.api.errcode)}")
        return count

    def solveCompleteHydraulics(self):
        """Runs a complete hydraulic simulation (equivalent to ENsolveH)."""
        ret = self.api.ENsolveH()
        if ret != 0:
            raise RuntimeError(f"EPANET ENsolveH failed: {self.api.ENgeterror(ret)}")
        return ret 

    def closeNetwork(self):
        """Closes the EPANET network (equivalent to ENclose)."""
        ret = self.api.ENclose()
        if ret != 0:
            raise RuntimeError(f"EPANET ENclose failed: {self.api.ENgeterror(ret)}")
        return ret 

    def getVersion(self):
        """Returns the (shimmed) EPANET version."""
        return f"{self._version} (shimmed for epanet-js)"

    def get_network_topology(self):
        """
        Extracts the network topology (nodes and links) from the loaded INP file.
        Returns a dictionary suitable for Cytoscape.js, including node IDs, coordinates, types,
        and link IDs with source/target node IDs.
        """
        if not self.api or self.api.errcode != 0:
            raise RuntimeError("EPANET API not initialized or in error state before getting topology.")

        node_count = self.getNodeCount() # Uses self method which handles errors
        link_count = self.getLinkCount() # Uses self method which handles errors

        nodes_data = []
        node_id_map_for_links = {} # Maps 1-based index to ID for link creation

        for i in range(1, node_count + 1): # EPANET indices are 1-based
            node_id = self.api.ENgetnodeid(i)
            if self.api.errcode != 0:
                raise RuntimeError(f"Error getting ID for node index {i}: {self.api.ENgeterror(self.api.errcode)}")
            
            coords = self.api.ENgetcoord(i) 
            if self.api.errcode != 0:
                raise RuntimeError(f"Error getting coordinates for node {node_id} (index {i}): {self.api.ENgeterror(self.api.errcode)}")
            
            node_type_code = self.api.ENgetnodetype(i)
            if self.api.errcode != 0:
                raise RuntimeError(f"Error getting type for node {node_id} (index {i}): {self.api.ENgeterror(self.api.errcode)}")

            node_id_map_for_links[i] = node_id # Store for resolving link connectivity
            
            node_type_str = "junction" # Default
            if node_type_code == epanetapi_shim.epanetapi.EN_TANK: node_type_str = "tank"
            elif node_type_code == epanetapi_shim.epanetapi.EN_RESERVOIR: node_type_str = "reservoir"

            nodes_data.append({
                'id': node_id, 'x': coords[0], 'y': coords[1],
                'type_code': node_type_code, 'type': node_type_str 
            })
        
        links_data = []
        for i in range(1, link_count + 1): 
            link_id = self.api.ENgetlinkid(i)
            if self.api.errcode != 0:
                raise RuntimeError(f"Error getting ID for link index {i}: {self.api.ENgeterror(self.api.errcode)}")
            
            from_node_idx, to_node_idx = self.api.ENgetlinknodes(i)
            if self.api.errcode != 0 or from_node_idx == 0 or to_node_idx == 0:
                 raise RuntimeError(f"Error getting nodes for link {link_id} (index {i}): {self.api.ENgeterror(self.api.errcode)}")

            source_node_id = node_id_map_for_links.get(from_node_idx)
            target_node_id = node_id_map_for_links.get(to_node_idx)

            if not source_node_id or not target_node_id:
                raise RuntimeError(f"Could not map node indices ({from_node_idx}, {to_node_idx}) to IDs for link {link_id}.")

            links_data.append({'id': link_id, 'source': source_node_id, 'target': target_node_id})
            
        print(f"Python [Phase 1 - epanet_shim]: Nodes data to be returned: {nodes_data}")
        print(f"Python [Phase 1 - epanet_shim]: Links data to be returned: {links_data}")
        return {'nodes': nodes_data, 'links': links_data}

    def setNodeEmitterCoeff(self, node_index_1_based, emitter_coeff_float):
        """
        Sets the emitter coefficient for a given node (1-based index).
        """
        ret = self.api.ENsetnodevalue(node_index_1_based, epanetapi_shim.epanetapi.EN_EMITTER, float(emitter_coeff_float))
        if ret != 0: 
            raise RuntimeError(f"EPANET ENsetnodevalue for emitter failed (node index {node_index_1_based}, coeff {emitter_coeff_float}): {self.api.ENgeterror(ret)}")
        return ret 

    def getNodeNameID(self, node_index_1_based):
        """
        Gets the ID of a node by its 1-based index.
        """
        node_id_str = self.api.ENgetnodeid(node_index_1_based)
        if self.api.errcode != 0:
            raise RuntimeError(f"Error getting ID for node index {node_index_1_based}: {self.api.ENgeterror(self.api.errcode)}")
        return node_id_str

    def getLinkNameID(self, link_index_1_based):
        """
        Gets the ID of a link by its 1-based index.
        """
        link_id_str = self.api.ENgetlinkid(link_index_1_based)
        if self.api.errcode != 0:
            raise RuntimeError(f"Error getting ID for link index {link_index_1_based}: {self.api.ENgeterror(self.api.errcode)}")
        return link_id_str

    def setDemandModel(self, type_str, pmin_float, preq_float, pexp_float):
        """
        Sets the demand model (DDA or PDA) and its parameters.
        """
        model_type_int = 1 if type_str.upper() == "PDA" else 0 # 0 for DDA, 1 for PDA
        ret = self.api.ENsetdemandmodel(model_type_int, float(pmin_float), float(preq_float), float(pexp_float))
        if ret != 0: 
            raise RuntimeError(f"EPANET ENsetdemandmodel failed: {self.api.ENgeterror(ret)}")
        return ret

    # --- Water Quality Simulation Methods ---
    def setQualityType(self, type_str, chemName_str="", chemUnits_str="", traceNode_id_str=""):
        """
        Sets the water quality simulation type (NONE, AGE, TRACE, or CHEM).
        Args:
            type_str (str): "NONE", "AGE", "TRACE", or "CHEM".
            chemName_str (str, optional): Name of the chemical for CHEM type.
            chemUnits_str (str, optional): Units of the chemical for CHEM type.
            traceNode_id_str (str, optional): Node ID for TRACE type.
        """
        qualcode_int = epanetapi_shim.epanetapi.EN_NONE # Default
        type_upper = type_str.upper()
        if type_upper == "AGE": qualcode_int = epanetapi_shim.epanetapi.EN_AGE
        elif type_upper == "TRACE": qualcode_int = epanetapi_shim.epanetapi.EN_TRACE
        elif type_upper == "CHEM": qualcode_int = epanetapi_shim.epanetapi.EN_CHEM
        
        api_trace_node_id = traceNode_id_str if type_upper == 'TRACE' and traceNode_id_str else ""

        ret = self.api.ENsetqualtype(qualcode_int, chemName_str, chemUnits_str, api_trace_node_id)
        if ret != 0:
            raise RuntimeError(f"EPANET ENsetqualtype failed: {self.api.ENgeterror(ret)}")
        return ret

    def openQualityAnalysis(self):
        """Opens the water quality analysis system."""
        ret = self.api.ENopenQ()
        if ret != 0: raise RuntimeError(f"EPANET ENopenQ failed: {self.api.ENgeterror(ret)}")
        return ret

    def initializeQualityAnalysis(self, save_flag=0):
        """Initializes water quality analysis. save_flag: 0 for NOSAVE, 1 for SAVE."""
        ret = self.api.ENinitQ(save_flag) 
        if ret != 0: raise RuntimeError(f"EPANET ENinitQ failed: {self.api.ENgeterror(ret)}")
        return ret

    def runQualityAnalysis(self):
        """Runs a single water quality step."""
        current_q_time = self.api.ENrunQ()
        if self.api.errcode != 0:
            raise RuntimeError(f"EPANET ENrunQ failed: {self.api.ENgeterror(self.api.errcode)}")
        return current_q_time

    def nextQualityAnalysisStep(self):
        """Determines time until the next quality event."""
        time_to_next_q_event = self.api.ENnextQ()
        if self.api.errcode != 0:
            raise RuntimeError(f"EPANET ENnextQ failed: {self.api.ENgeterror(self.api.errcode)}")
        return time_to_next_q_event

    def closeQualityAnalysis(self):
        """Closes the water quality analysis system."""
        ret = self.api.ENcloseQ()
        if ret != 0: raise RuntimeError(f"EPANET ENcloseQ failed: {self.api.ENgeterror(ret)}")
        return ret

    def getNodeActualQuality(self, node_index_1_based):
        """
        Retrieves the actual computed quality at a node (1-based index).
        Returns a list containing the quality value (consistent with EPyT).
        """
        # EN_QUALITY (2) in epanetapi_shim maps to JS_NODEPROP_ACTUALQUALITY (7)
        quality_val = self.api.ENgetnodevalue(node_index_1_based, epanetapi_shim.epanetapi.EN_QUALITY)
        if self.api.errcode != 0:
            raise RuntimeError(f"Error getting quality for node index {node_index_1_based}: {self.api.ENgeterror(self.api.errcode)}")
        return [quality_val] 

    # --- Step-by-Step Hydraulic Simulation Methods ---
    def openHydraulicAnalysis(self):
        """Opens the hydraulic analysis system (ENopenH)."""
        ret = self.api.ENopenH()
        if ret != 0:
            raise RuntimeError(f"EPANET ENopenH failed: {self.api.ENgeterror(ret)}")
        return ret

    def initializeHydraulicAnalysis(self, save_flag=0):
        """Initializes hydraulic analysis (ENinitH). save_flag: 0 for NOSAVE, 1 for SAVE."""
        ret = self.api.ENinitH(save_flag)
        if ret != 0:
            raise RuntimeError(f"EPANET ENinitH failed: {self.api.ENgeterror(ret)}")
        return ret

    def runHydraulicAnalysis(self):
        """Runs a single hydraulic analysis step (ENrunH). Returns current simulation time."""
        current_time = self.api.ENrunH()
        if self.api.errcode != 0: 
            raise RuntimeError(f"EPANET ENrunH failed: {self.api.ENgeterror(self.api.errcode)}")
        return current_time

    def nextHydraulicAnalysisStep(self):
        """Determines time until the next hydraulic event (ENnextH). Returns time step."""
        time_to_next_event = self.api.ENnextH()
        if self.api.errcode != 0: 
            raise RuntimeError(f"EPANET ENnextH failed: {self.api.ENgeterror(self.api.errcode)}")
        return time_to_next_event

    def closeHydraulicAnalysis(self):
        """Closes the hydraulic analysis system (ENcloseH)."""
        ret = self.api.ENcloseH()
        if ret != 0:
            raise RuntimeError(f"EPANET ENcloseH failed: {self.api.ENgeterror(ret)}")
        return ret

    def getNodePressure(self, node_index_1_based):
        """Retrieves computed pressure at a node (1-based index)."""
        # EN_PRESSURE (11) in epanetapi_shim maps to JS_NODEPROP_PRESSURE (11)
        pressure = self.api.ENgetnodevalue(node_index_1_based, epanetapi_shim.epanetapi.EN_PRESSURE)
        if self.api.errcode != 0:
            raise RuntimeError(f"Error getting pressure for node index {node_index_1_based}: {self.api.ENgeterror(self.api.errcode)}")
        return pressure

    def getLinkFlows(self, link_index_1_based): # EPyT uses plural "Flows"
        """Retrieves computed flow in a link (1-based index)."""
        # EN_FLOW (8) in epanetapi_shim maps to JS_LINKPROP_FLOW (8)
        flow = self.api.ENgetlinkvalue(link_index_1_based, epanetapi_shim.epanetapi.EN_FLOW)
        if self.api.errcode != 0:
            raise RuntimeError(f"Error getting flow for link index {link_index_1_based}: {self.api.ENgeterror(self.api.errcode)}")
        return flow

    def getNodeIndex(self, node_ids_list):
        """
        Gets 1-based node indices from a list of node ID strings.
        Uses a cached ID-to-index map for efficiency.
        """
        if not isinstance(node_ids_list, list): node_ids_list = [node_ids_list] # Allow single ID string
        node_indices = []
        for node_id_str in node_ids_list:
            idx = self._node_id_to_index_map.get(str(node_id_str)) 
            if idx is None:
                raise ValueError(f"Node ID '{node_id_str}' not found in network.")
            node_indices.append(idx)
        return node_indices


    def getLinkIndex(self, link_ids_list):
        """
        Gets 1-based link indices from a list of link ID strings.
        Uses a cached ID-to-index map for efficiency.
        """
        if not isinstance(link_ids_list, list): link_ids_list = [link_ids_list] # Allow single ID string
        link_indices = []
        for link_id_str in link_ids_list:
            idx = self._link_id_to_index_map.get(str(link_id_str))
            if idx is None:
                raise ValueError(f"Link ID '{link_id_str}' not found in network.")
            link_indices.append(idx)
        return link_indices

    # --- Orchestration Methods for JavaScript ---
    def run_hydraulic_step_and_get_all_results(self):
        """
        Runs a single hydraulic step and gathers all node pressures and link flows.
        This is intended for efficient data retrieval by JavaScript to update the UI map.
        Returns:
            dict: Contains current time, lists of node pressures, lists of link flows, 
                  time to next event, and any error message.
        """
        all_node_results = []
        all_link_results = []
        error_occurred = None
        current_time_sec = -1
        time_to_next_event_sec = 0

        try:
            current_time_sec = self.runHydraulicAnalysis() # ENrunH

            node_count = self.getNodeCount() 
            for i in range(1, node_count + 1):
                node_id = self.getNodeNameID(i) 
                pressure = self.getNodePressure(i) 
                all_node_results.append({'id': node_id, 'pressure': pressure})

            link_count = self.getLinkCount() 
            for i in range(1, link_count + 1):
                link_id = self.getLinkNameID(i) 
                flow = self.getLinkFlows(i) 
                all_link_results.append({'id': link_id, 'flow': flow})
            
            time_to_next_event_sec = self.nextHydraulicAnalysisStep() # ENnextH

        except Exception as e:
            error_occurred = str(e)
            # current_time_sec and time_to_next_event_sec will retain their last valid values or defaults

        return {
            'currentTime': current_time_sec,
            'nodeResults': all_node_results,
            'linkResults': all_link_results,
            'nextEventTime': time_to_next_event_sec,
            'error': error_occurred 
        }

    def run_single_quality_step_for_js(self, node_id_to_get_quality):
        """
        Runs a single quality step and retrieves quality for a specific node.
        This is intended for JavaScript calls.
        Args:
            node_id_to_get_quality (str): ID of the node for which to retrieve quality.
        Returns:
            dict: Contains current quality simulation time, node ID, quality value, 
                  time to next quality event, and any error message.
        """
        try:
            current_q_time_sec = self.runQualityAnalysis() # ENrunQ
            
            node_idx_list = self.getNodeIndex([str(node_id_to_get_quality)])
            node_idx = node_idx_list[0]
            
            quality_val_array = self.getNodeActualQuality(node_idx) 
            quality_val = quality_val_array[0] if quality_val_array else 0.0 

            time_to_next_q_event_sec = self.nextQualityAnalysisStep() # ENnextQ
            
            return {
                'currentTime': current_q_time_sec,
                'nodeId': str(node_id_to_get_quality),
                'quality': quality_val,
                'nextQualityEventTime': time_to_next_q_event_sec,
                'error': None
            }
        except Exception as e:
            return {
                'currentTime': -1, 'nodeId': str(node_id_to_get_quality), 'quality': 0.0,
                'nextQualityEventTime': 0, 'error': str(e)
            }

def get_epanet_shim_version():
    return EPANET_SHIM_PY_VERSION
