
import xml.etree.ElementTree as ET
import random

class NetworkBuilder:

    def __init__(self, start_id=1):
        #Begin counting devices from this value
        self.current_id = start_id

        # Prefix used for naming different types of networks 
        self.network_prefixes = {
            "SWITCH": "n",
            "HUB": "n",
            "WIRELESS_LAN": "wlan"
        }

        self.MIN_X = 32
        self.MAX_X = 970
        self.MIN_Y = 29
        self.MAX_Y = 719

        self.X_STEP = 160 
        self.Y_STEP = 140  
 
        # Tracks all devices created with their properties
        self.device_registry = {}

    def generate_network_tag(self, name, net_type, x, y, lat, lon):

        # Creates a <network> XML element with a <position> subelement
        network = ET.Element("network", {
            "id": str(self.current_id),
            "name": name,
            "icon": "",
            "canvas": "1",
            "type": net_type
        })
        ET.SubElement(network, "position", {
            "x": str(x),
            "y": str(y),
            "lat": str(lat),
            "lon": str(lon),
            "alt": "2.0"
        })
        return network

    def add_user_networks(self, networks_element, device_counts):

        # Adds network nodes like switches, routers, etc to the scenario
        for net_type in self.network_prefixes:
            count = device_counts.get(net_type, 0)
            prefix = self.network_prefixes[net_type]
            

            for _ in range(count):
                name = f"{prefix}{self.current_id}"

                x, y = self._get_bounded_position(self.current_id)
                
                lat, lon = self.get_lat_lon(self.current_id)

                # Create and append <network> element
                tag = self.generate_network_tag(name, net_type, x, y, lat, lon)
                networks_element.append(tag)

                # Save info to the registry
                self.device_registry[self.current_id] = {
                    "name": name,
                    "type": net_type,
                    "interfaces": 0
                }
                self.current_id += 1

    def add_user_devices(self, devices_element, device_counts):

        # Adds PC and router devices, and assigns services to them
        device_types = {
            "PC": ["DefaultRoute"],
            "router": ["OSPFv3", "OSPFv2", "IPForward", "zebra"],
            "mdr":["zebra", "IPForward", "OSPFv3MDR"]
        }

        for device_type, services in device_types.items():
            count = device_counts.get(device_type, 0)

            for _ in range(count):
                name = f"n{self.current_id}"

                device = ET.Element("device", {
                    "id": str(self.current_id),
                    "name": name,
                    "icon": "",
                    "canvas": "1",
                    "type": device_type,
                    "class": "",
                    "image": ""
                })

                x, y = self._get_bounded_position(self.current_id)
                lat, lon = self.get_lat_lon(self.current_id)

                # Add position info
                ET.SubElement(device, "position", {
                    "x": str(x),
                    "y": str(y),
                    "lat": str(lat),
                    "lon": str(lon),
                    "alt": "2.0"
                })

                # Add config services like routing protocols
                configservices = ET.SubElement(device, "configservices")
                for svc in services:
                    ET.SubElement(configservices, "service", {"name": svc})

                devices_element.append(device)

                # Save info to the registry
                self.device_registry[self.current_id] = {
                    "name": name,
                    "type": device_type,
                    "interfaces": 0
                }

                self.current_id += 1

    def generate_links(self, links_element, connections):
        subnet_counter = 1
        adjacency = {}
        for node1, node2 in connections:
            adjacency.setdefault(node1, []).append(node2)
            adjacency.setdefault(node2, []).append(node1)

        self.adjacency = adjacency

        linked_pairs = set()

        # Process connections: wireless and direct links
        for node1, node2 in connections:
            type1 = self.device_registry[node1]["type"].lower()
            type2 = self.device_registry[node2]["type"].lower()

            pair_key = tuple(sorted((node1, node2)))

            if "wireless_lan" in (type1, type2):
                link = self._create_wireless_link(node1, node2, subnet_counter)
                links_element.append(link)
                linked_pairs.add(pair_key)
                subnet_counter += 1

            elif self._is_direct_link(type1, type2):
                link = self._create_direct_link(node1, node2, subnet_counter)
                links_element.append(link)
                linked_pairs.add(pair_key)
                subnet_counter += 1

        # Process LAN links (switch/hub)
        for device_id, info in self.device_registry.items():
            device_type = info["type"].lower()
            if device_type in {"switch", "hub"} and device_id in adjacency:
                neighbors = adjacency[device_id]
                if neighbors:
                    link_group = self._create_lan_links(device_id, neighbors, subnet_counter)
                    for link in link_group:
                        # Extract node1 + node2 from link attributes
                        node1 = int(link.attrib["node1"])
                        node2 = int(link.attrib["node2"])
                        pair_key = tuple(sorted((node1, node2)))
                        if pair_key not in linked_pairs:
                            links_element.append(link)
                            linked_pairs.add(pair_key)
                    subnet_counter += 1



    def _is_direct_link(self, type1, type2):
        # Checks PCs and routers for direct links
        valid = {"router", "pc", "mdr"}
        return type1 in valid and type2 in valid
    
    def _create_direct_link(self, node1, node2, subnet_counter):
        # Create a link element between two devices, with IP interfaces
        ip4_prefix = f"10.0.{subnet_counter}." #TODO Change to be dynamic 
        ip6_prefix = f"2001::{subnet_counter}"

        iface1_id = self.device_registry[node1]["interfaces"]
        iface2_id = self.device_registry[node2]["interfaces"]

        # Build XML element
        link = ET.Element("link", {
            "node1": str(node1),
            "node2": str(node2)
        })

        iface1 = ET.Element("iface1", {
            "id": str(iface1_id),
            "name": f"eth{iface1_id}",
            "ip4": ip4_prefix + "1",
            "ip4_mask": "24",
            "ip6": ip6_prefix + "1",
            "ip6_mask": "64"
        })

        iface2 = ET.Element("iface2", {
            "id": str(iface2_id),
            "name": f"eth{iface2_id}",
            "ip4": ip4_prefix + "2",
            "ip4_mask": "24",
            "ip6": ip6_prefix + "2",
            "ip6_mask": "64"
        })

        options = ET.Element("options", {
            "delay": "0",
            "bandwidth": "0",
            "loss": "0.0",
            "dup": "0",
            "jitter": "0",
            "unidirectional": "0",
            "buffer": "0"
        })

        link.extend([iface1, iface2, options])

        # Increment interface counters for both devices
        self.device_registry[node1]["interfaces"] += 1
        self.device_registry[node2]["interfaces"] += 1

        return link
    
    def _create_lan_links(self, center_id, neighbors, subnet_counter):
        # Creates links between a switch/hub and all its neighbors using a shared subnet
        links = []
        ip4_prefix = f"10.0.{subnet_counter}."
        ip6_prefix = f"2001::{subnet_counter}"
        ip_host = 1  # Host counter for IP assignments

        # Find the router if any to use as reference
       
        router_id = None
        for neighbor_id in neighbors:
            neighbor_type = self.device_registry[neighbor_id]["type"].lower()
            if neighbor_type in {"router", "mdr"}:
                router_id = neighbor_id
                break

        if not router_id:
            return links  # skip if no router to base IPs on

        # Assign IP to router first
        for node_id in neighbors:
            if node_id == router_id:
                iface_id = self.device_registry[node_id]["interfaces"]
                link = ET.Element("link", {
                    "node1": str(center_id),
                    "node2": str(node_id)
                })

                iface = ET.Element("iface2", {
                    "id": str(iface_id),
                    "name": f"eth{iface_id}",
                    "ip4": ip4_prefix + str(ip_host),
                    "ip4_mask": "24",
                    "ip6": ip6_prefix + f":{ip_host}",
                    "ip6_mask": "64"
                })

                link.append(iface)
                link.append(ET.Element("options", {
                    "delay": "0", "bandwidth": "0", "loss": "0.0",
                    "dup": "0", "jitter": "0", "unidirectional": "0", "buffer": "0"
                }))
                links.append(link)
                self.device_registry[node_id]["interfaces"] += 1
                ip_host += 1

        # Connect remaining devices
        for node_id in neighbors:
            if node_id == router_id:
                continue

            iface_id = self.device_registry[node_id]["interfaces"]
            link = ET.Element("link", {
                "node1": str(center_id),
                "node2": str(node_id)
            })

            iface = ET.Element("iface2", {
                "id": str(iface_id),
                "name": f"eth{iface_id}",
                "ip4": ip4_prefix + str(ip_host),
                "ip4_mask": "24",
                "ip6": ip6_prefix + f":{ip_host}",
                "ip6_mask": "64"
            })

            link.append(iface)
            link.append(ET.Element("options", {
                "delay": "0", "bandwidth": "0", "loss": "0.0",
                "dup": "0", "jitter": "0", "unidirectional": "0", "buffer": "0"
            }))
            links.append(link)
            self.device_registry[node_id]["interfaces"] += 1
            ip_host += 1

        return links
    

    def _create_wireless_link(self, node1, node2, subnet_counter):
        # Ensure node1 is the wireless LAN node
        if self.device_registry[node1]["type"].upper() != "WIRELESS_LAN":
            node1, node2 = node2, node1

        iface_id = self.device_registry[node2]["interfaces"]

        link = ET.Element("link", {
            "node1": str(node1),
            "node2": str(node2)
        })

        # Check if node2 is a switch
        if self.device_registry[node2]["type"].lower() == "switch" or  self.device_registry[node2]["type"].lower() == "hub":
            # iface2 for switch + WLAN connection
            iface2 = ET.Element("iface2", {
                "id": str(iface_id),
                "name": f"veth{node1}.{node2}.1"
            })
        else:
            # iface2 for other connections
            ip4_prefix = f"10.0.{subnet_counter}."
            ip6_prefix = f"2001:0:0:{subnet_counter}::"

            iface2 = ET.Element("iface2", {
                "id": str(iface_id),
                "name": f"eth{iface_id}",
                "ip4": ip4_prefix + "1",
                "ip4_mask": "32",
                "ip6": f"{ip6_prefix}1",
                "ip6_mask": "128"
            })

        link.append(iface2)

        self.device_registry[node2]["interfaces"] += 1

        return link


    def add_configservice_configurations(self, parent_element):
        config_elem = ET.SubElement(parent_element, "configservice_configurations")

        for node_id, info in self.device_registry.items():
            device_type = info["type"].lower()
            
            # Map device types to their services (same as add_user_devices)
            if device_type == "router":
                services = ["OSPFv3", "OSPFv2", "IPForward", "zebra"]
            elif device_type == "mdr":
                services = ["zebra", "IPForward", "OSPFv3MDR"]
            elif device_type == "pc":
                services = ["DefaultRoute"]
            else:
                continue  # skip other types

            for svc in services:
                ET.SubElement(config_elem, "service", {
                    "name": svc,
                    "node": str(node_id)
                })


    def _get_bounded_position(self, idx):
        max_columns = (self.MAX_X - self.MIN_X) // self.X_STEP
        max_rows = (self.MAX_Y - self.MIN_Y) // self.Y_STEP
        total_slots = max_columns * max_rows

        idx = idx % total_slots  # wrap around

        row = idx // max_columns
        col = idx % max_columns

        if row % 2 == 1:
            col = max_columns - 1 - col  # snake pattern

        x = self.MIN_X + col * self.X_STEP
        y = self.MIN_Y + row * self.Y_STEP

        return float(x), float(y)
    
    def get_lat_lon(self, idx):
        max_columns = (self.MAX_X - self.MIN_X) // self.X_STEP
        max_rows = (self.MAX_Y - self.MIN_Y) // self.Y_STEP
        total_slots = max_columns * max_rows

        idx = idx % total_slots  # wrap around 

        row = idx // max_columns
        col = idx % max_columns

        if row % 2 == 1:
            col = max_columns - 1 - col

        LAT_START = 47.57889
        LAT_STEP = 0.00135

        LON_START = -122.13188
        LON_STEP = 0.00265

        latitude = LAT_START - (row * LAT_STEP)
        longitude = LON_START + (col * LON_STEP)

        return f"{latitude:.12f}", f"{longitude:.12f}"
    

    def generate_random_links(self):
        links = []
        seen_links = []

        # Group devices by type
      
        routers = []
        for device_id, device_info in self.device_registry.items():
            device_type = device_info["type"].lower()
            if device_type == "router":
                routers.append(device_id)

        
        switch_and_hubs = []
        for device_id, device_info in self.device_registry.items():
            device_type = device_info["type"].lower()
            if device_type in ("switch", "hub"):
                switch_and_hubs.append(device_id)


        pcs = []
        for device_id, device_info in self.device_registry.items():
            device_type = device_info["type"].lower()
            if device_type == "pc":
                pcs.append(device_id)


        # Link routers to each other 
        for i in range(len(routers)):
            for j in range(i + 1, len(routers)):
                r1, r2 = routers[i], routers[j]
                link = (min(r1, r2), max(r1, r2))
                if link not in seen_links:
                    links.append(link)
                    seen_links.append(link)

        # Attach each switch to a router 
        router_index = 0
        for device_id in switch_and_hubs:
            if routers:
                router_id = routers[router_index % len(routers)]
                link = (min(device_id, router_id), max(device_id, router_id))
                if link not in seen_links:
                    links.append(link)
                    seen_links.append(link)
                router_index += 1

        parent_devices = switch_and_hubs + routers  
    
        parent_index = 0
        for pc in pcs:
            for _ in range(len(parent_devices)):
                parent = parent_devices[parent_index % len(parent_devices)]
                link = (min(pc, parent), max(pc, parent))
                if link not in seen_links:
                    links.append(link)
                    seen_links.append(link)
                    parent_index += 1
                    break
                parent_index += 1


        return links










   