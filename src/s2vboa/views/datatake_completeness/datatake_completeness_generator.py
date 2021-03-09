"""
Generator module for the datatake completeness view for the monitoring of the Sentinel-2 constellation

Written by DEIMOS Space S.L. (jubv)

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

    app = create_app()
    client = app.test_client()
    response = client.post("/views/datatake-completeness", data={
        "start": begin,
        "stop": end,
        "mission": "S2_",
        "show_datatake_completeness_map": True,
        "show_datatake_completeness_timeline": True
    })

    html_file_path = export_html(response)

    metadata["operations"][0]["report"]["generator_version"] = version
    metadata["operations"][0]["report"]["group"] = "DATATAKE_COMPLETENESS"
    metadata["operations"][0]["report"]["group_description"] = "Group of reports dedicated for the monitoring of the datatake completeness of the Sentinel-2 constellation"

    return html_file_path
