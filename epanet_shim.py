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


# Note: The original EPyT library has extensive error checking and handling,
# including specific exception types. This shim is simplified for the PoC.
pass
