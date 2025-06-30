import xml.etree.ElementTree as ET
from network_builder import NetworkBuilder
import json 
from basic_core_structure import (
    add_session_origin,
    add_session_options,
    add_session_metadata,
    add_default_services,
    add_mobility_configurations
)




# Start scenario
scenario = ET.Element("scenario", {"name": "/tmp/tmpxwrcvn1n"}) #will need to be dynamic but ok for now 

# Load config
with open("scenario_config.json") as f:
    config = json.load(f)

device_config = config["devices"]


autogenerate = config.get("autogenerate_links", False)

# Handle static CORE XML sections 
networks = ET.SubElement(scenario, "networks")

builder = NetworkBuilder(start_id=1)

builder.add_user_networks(networks, device_config)


devices = ET.SubElement(scenario, "devices")

builder.add_user_devices(devices, device_config)

#connections

if autogenerate or "links" not in config:
    connections = builder.generate_random_links()
else:
    connections = config["links"]

links = ET.SubElement(scenario, "links")
builder.generate_links(links, connections)

builder.add_configservice_configurations(scenario)

add_mobility_configurations(scenario, builder.device_registry)



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
tree.write("scenario_with_static.xml", encoding="UTF-8", xml_declaration=True)


