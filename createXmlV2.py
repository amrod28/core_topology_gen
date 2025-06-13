import xml.etree.ElementTree as ET
from network_builder import NetworkBuilder
import json 
from basic_core_structure import (
    add_session_origin,
    add_session_options,
    add_session_metadata,
    add_default_services
)






# Start scenario
scenario = ET.Element("scenario", {"name": "/tmp/tmpxwrcvn1n"}) #will need to be dynamic but ok for now 

# Load config
with open("scenario_config.json") as f:
    config = json.load(f)

device_config = config["devices"]
link_config = config["links"]


# Handle static CORE XML sections 
networks = ET.SubElement(scenario, "networks")

builder = NetworkBuilder(start_id=1)
# builder.add_user_networks(networks)
builder.add_user_networks(networks, device_config)


devices = ET.SubElement(scenario, "devices")
# builder.add_user_devices(devices)
builder.add_user_devices(devices, device_config)

# connections = [(4, 2), (4, 3),(4,1)]  
# connections = [(1, 2), (1, 3),(1,6),(6,4),(5,6) ]
# connections = [(1, 3), (1, 4),(8,5),(8,6),(8,9) ,(9,2) ,(2,7) ,(8,1)]

connections = link_config




links = ET.SubElement(scenario, "links")
builder.generate_links(links,  connections)

config_services = ET.SubElement(scenario, "configservice_configurations")


# Add static sections using helper methods
add_session_origin(scenario)
add_session_options(scenario)
add_session_metadata(scenario)
add_default_services(scenario)


tree = ET.ElementTree(scenario)

# Indent
ET.indent(tree, space="  ") 

# Save to file
tree.write("scenario_with_static1.xml", encoding="UTF-8", xml_declaration=True)


