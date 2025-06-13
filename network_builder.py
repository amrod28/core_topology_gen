
import xml.etree.ElementTree as ET

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

        # Tracks all created devices with their properties
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
                x = 100 + self.current_id * 50
                y = 100 + self.current_id * 40
                lat = 47.576 + (self.current_id * 0.001)
                lon = -122.127 + (self.current_id * 0.001)


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
            "router": ["OSPFv3", "OSPFv2", "IPForward", "zebra"]
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

                # Add position info
                ET.SubElement(device, "position", {
                    "x": str(100 + self.current_id * 60),
                    "y": str(100 + self.current_id * 45),
                    "lat": str(47.575 + self.current_id * 0.001),
                    "lon": str(-122.127 + self.current_id * 0.001),
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
        # Generates link connections based on a list of (node1, node2) tuples
        
        subnet_counter = 1  # Used to generate unique subnets Might change

        # Build adjacency list
        adjacency = {}
        for node1, node2 in connections:
            adjacency.setdefault(node1, []).append(node2)
            adjacency.setdefault(node2, []).append(node1)
      
        self.adjacency = adjacency

        # Create direct links between PCs and routers
        for node1, node2 in connections:
            type1 = self.device_registry[node1]["type"].lower()
            type2 = self.device_registry[node2]["type"].lower()

            if self._is_direct_link(type1, type2):
                link = self._create_direct_link(node1, node2, subnet_counter)
                links_element.append(link)
                subnet_counter += 1

       
        # Create LAN links for switches/hubs
        for device_id in self.device_registry:
            device_type = self.device_registry[device_id]["type"].lower()
            if device_type in {"switch", "hub"} and device_id in adjacency:
                neighbors = adjacency[device_id]
                if neighbors:
                    link_group = self._create_lan_links(device_id, neighbors, subnet_counter)
                    links_element.extend(link_group)
                    subnet_counter += 1

    def _is_direct_link(self, type1, type2):
        # Checks PCs and routers for direct links
        valid = {"router", "pc"}
        return type1 in valid and type2 in valid
    
    def _create_direct_link(self, node1, node2, subnet_counter):
        # Create a link element between two devices, with IP interfaces
        ip4_prefix = f"10.0.{subnet_counter}." #TODO Change to be dynamic 
        ip6_prefix = f"2001::{subnet_counter}"

        iface1_id = self.device_registry[node1]["interfaces"]
        iface2_id = self.device_registry[node2]["interfaces"]

        # Build XML Component
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
        router_id = next((n for n in neighbors if self.device_registry[n]["type"].lower() == "router"), None)

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





   