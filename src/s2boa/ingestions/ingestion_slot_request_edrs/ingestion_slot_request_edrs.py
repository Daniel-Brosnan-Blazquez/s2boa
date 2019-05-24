"""
Ingestion module for the SRA (Slot request for unit A) files of Sentinel-2

Written by DEIMOS Space S.L. (dibb)

module eboa
"""
# Import python utilities
import os
import argparse
from dateutil import parser
import datetime
import json
from tempfile import mkstemp

# Import xml parser
from lxml import etree

# Import query
from eboa.engine.query import Query

# Import ingestion_functions.helpers
import eboa.ingestion.functions as ingestion_functions

# Import query
from eboa.engine.query import Query

# Import debugging
from eboa.debugging import debug

# Import logging
from eboa.logging import Log

logging_module = Log()
logger = logging_module.logger

version = "1.0"

def process_file(file_path, engine, query):
    """
    Function to process the file and insert its relevant information
    into the DDBB of the eboa
    
    :param file_path: path to the file to be processed
    :type file_path: str
    """
    list_of_events = []
    list_of_explicit_references = []
    file_name = os.path.basename(file_path)

    # Remove namespaces
    (_, new_file_path) = new_file = mkstemp()
    ingestion_functions.remove_namespaces(file_path, new_file_path)

    # Parse file
    parsed_xml = etree.parse(new_file_path)
    xpath_xml = etree.XPathEvaluator(parsed_xml)

    satellite = file_name[0:3]
    generation_time = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Source/Creation_Date")[0].text.split("=")[1]
    validity_start = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Validity_Period/Validity_Start")[0].text.split("=")[1]
    validity_stop = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Validity_Period/Validity_Stop")[0].text.split("=")[1]
    edrs = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Mission")[0].text

    source = {
        "name": file_name,
        "generation_time": generation_time,
        "validity_start": validity_start,
        "validity_stop": validity_stop
    }

    # Extract the slots
    slots = xpath_xml("/Earth_Explorer_File/Data_Block/List_of_Sessions/Session")
    for slot in slots:
        start = slot.xpath("Start_Time")[0].text.split("=")[1]
        stop = slot.xpath("Stop_Time")[0].text.split("=")[1]
        session_id = slot.xpath("Session_ID")[0].text
        sentinel = slot.xpath("LEO_Satellite_ID")[0].text
        orbit_node = slot.xpath("LEO_Absolute_Orbit")
        orbit = -1
        if orbit_node:
            orbit = orbit_node[0].text
        # end if

        # Get the associated planned playback in the NPPF
        playbacks = query.get_linked_events(gauge_names = {"filter": "PLANNED_PLAYBACK_CORRECTION", "op": "like"},
                                                 gauge_systems = {"filter": sentinel, "op": "like"},
                                                 start_filters = [{"date": start, "op": ">"}],
                                                 stop_filters = [{"date": stop, "op": "<"}],
                                                 link_names = {"filter": ["TIME_CORRECTION"], "op": "in"},
                                                 return_prime_events = False)

        status = "NO_MATCHED_PLAYBACK"
        links = []
        if len(playbacks["linked_events"]) > 0:
            for playback in playbacks["linked_events"]:
                # Get the planned playback mean
                planned_playback_mean_uuids = [link.event_uuid_link for link in playback.eventLinks if link.name == "PLANNED_PLAYBACK_MEAN"]
                if len(planned_playback_mean_uuids) > 0:

                    mean = [value.value for value in playback.eventTexts if value.name == "playback_mean"][0]

                    if mean == "OCP":
                        status = "MATCHED_PLAYBACK"
                        links.append({
                            "link": str(playback.event_uuid),
                            "link_mode": "by_uuid",
                            "name": "SLOT_REQUEST_EDRS",
                            "back_ref": "PLANNED_PLAYBACK"
                        })
                        value = {
                            "name": "station_schedule",
                            "type": "object",
                            "values": [{"name": "station",
                                        "type": "text",
                                        "value": "EDRS"}]
                        }
                        engine.insert_event_values(playback.event_uuid, value)
                        planned_playback_correction_uuid = [event_link.event_uuid_link for event_link in playback.eventLinks if event_link.name == "TIME_CORRECTION"][0]
                        engine.insert_event_values(planned_playback_correction_uuid, value)

                        value = {
                            "name": "dfep_schedule",
                            "type": "object",
                            "values": [{"name": "station",
                                        "type": "text",
                                        "value": "EDRS"}]
                        }
                        engine.insert_event_values(playback.event_uuid, value)
                        planned_playback_correction_uuid = [event_link.event_uuid_link for event_link in playback.eventLinks if event_link.name == "TIME_CORRECTION"][0]
                        engine.insert_event_values(planned_playback_correction_uuid, value)

                    # end if
                # end if
            # end for
        # end if

        # Associate the explicit reference to the group EDRS_SESSION_IDs
        explicit_reference = {
            "name": session_id,
            "group": "EDRS_SESSION_IDs"
        }
        list_of_explicit_references.append(explicit_reference)
        slot_event = {
            "explicit_reference": session_id,
            "gauge": {
                "insertion_type": "INSERT_and_ERASE",
                "name": "SLOT_REQUEST_EDRS",
                "system": sentinel
            },
            "links": links,
            "start": start,
            "stop": stop,
            "values": [{
                "name": "slot_request_information",
                "type": "object",
                "values": [
                    {"name": "session_id",
                     "type": "text",
                     "value": session_id},
                    {"name": "edrs_unit",
                     "type": "text",
                     "value": edrs},
                    {"name": "orbit",
                     "type": "double",
                     "value": str(orbit)},
                    {"name": "satellite",
                     "type": "text",
                     "value": sentinel},
                    {"name": "status",
                     "type": "text",
                     "value": status}
                ]
            }]
        }

        # Insert slot_event
        ingestion_functions.insert_event_for_ingestion(slot_event, source, list_of_events)
    # end for

    # Build the xml
    data = {"operations": [{
        "mode": "insert_and_erase",
        "dim_signature": {
            "name": "SLOT_REQUEST_EDRS",
            "exec": os.path.basename(__file__),
            "version": version
        },
        "source": source,
        "explicit_references": list_of_explicit_references,
        "events": list_of_events
    }]}

    os.remove(new_file_path)

    return data
