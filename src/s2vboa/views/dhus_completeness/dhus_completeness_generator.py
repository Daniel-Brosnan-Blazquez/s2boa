"""
Generator module for the acquisition view for the monitoring of the Sentinel-2 constellation

Written by DEIMOS Space S.L. (dibb)

module s2vboa
"""
# Import python utilities
import os

# Import helpers
from vboa.functions import export_html

# Import vboa app creator
from s2vboa import create_app

version = "1.0"

def generate_report(begin, end, metadata, parameters = None):

    levels = "ALL"
    if "levels" in parameters:
        if parameters["levels"] in ["L1C", "L2A", "ALL"]:
            levels = parameters["levels"]
        # end if
    # end if
    
    app = create_app()
    client = app.test_client()
    response = client.post("/views/dhus-completeness", data={
        "start": begin,
        "stop": end,
        "mission": "S2_",
        "levels": levels,
    })

    html_file_path = export_html(response)

    metadata["operations"][0]["report"]["generator_version"] = version
    metadata["operations"][0]["report"]["group"] = "DHUS_COMPLETENESS"
    metadata["operations"][0]["report"]["group_description"] = "Group of reports dedicated for the monitoring of the dissemination of Sentinel-2 production to DHUS"

    return html_file_path
