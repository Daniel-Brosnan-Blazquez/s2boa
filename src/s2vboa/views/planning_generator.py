"""
Generator module for the planning view for the monitoring of the Sentinel-2 constellation

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

def generate_report(begin, end, metadata):

    app = create_app()
    client = app.test_client()
    response = client.post("/views/planning", data={
        "start": begin,
        "stop": end,
        "mission": "S2_",
        "show_planning_timeline": True,
        "show_planning_x_time_evolution": True,
        "show_planning_table_details": True,
        "show_planning_map": True
    })

    html_file_path = export_html(response)

    metadata["operations"][0]["report"]["generator"] = os.path.basename(__file__)
    metadata["operations"][0]["report"]["generator_version"] = version
    metadata["operations"][0]["report"]["group"] = "PLANNING"
    metadata["operations"][0]["report"]["group_description"] = "Group of reports dedicated for the monitoring of the planning of the Sentinel-2 constellation"

    return html_file_path
