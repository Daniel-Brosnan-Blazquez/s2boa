"""
Ingestion module for the DFEP schedule files of Sentinel-2

Written by DEIMOS Space S.L. (dibb)

module eboa
"""
# Import python utilities
import os
import argparse
from dateutil import parser
import datetime
import json

# Import xml parser
from lxml import etree

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

@debug
def _generate_dfep_schedule_events(xpath_xml, source, engine, query, list_of_events):
    """
    Method to generate the events of the dfep schedule files

    :param xpath_xml: source of information that was xpath evaluated
    :type xpath_xml: XPathEvaluator
    :param source: information of the source
    :type xpath_xml: dict
    :param list_of_events: list to store the events to be inserted into the eboa
    :type list_of_events: list
    """

    satellite = source["name"][0:3]
    station = xpath_xml("/Earth_Explorer_File/Data_Block/sched/station")[0].get("name")

    # schedulings
    schedulings = xpath_xml("/Earth_Explorer_File/Data_Block/sched/station/acq[action = 'ADD']")
    for schedule in schedulings:

        start = schedule.xpath("start")[0].text
        stop = schedule.xpath("stop")[0].text

        playbacks = query.get_linked_events(gauge_names = {"filter": "PLANNED_PLAYBACK_CORRECTION", "op": "like"},
                                            gauge_systems = {"filter": [satellite], "op": "in"},
                                            start_filters = [{"date": start, "op": ">"}],
                                            stop_filters = [{"date": stop, "op": "<"}],
                                            link_names = {"filter": "TIME_CORRECTION", "op": "like"},
                                            return_prime_events = False)

        status = "MATCHED_PLAYBACK"
        links = []
        if len(playbacks["linked_events"]) == 0:
            status = "NO_MATCHED_PLAYBACK"
        else:
            for playback in playbacks["linked_events"]:
                links.append({
                    "link": str(playback.event_uuid),
                    "link_mode": "by_uuid",
                    "name": "DFEP_SCHEDULE",
                    "back_ref": "PLANNED_PLAYBACK"
                })
                value = {
                    "name": "dfep_schedule",
                    "type": "object",
                    "values": [{"name": "station",
                                "type": "text",
                                "value": station}]
                }
                engine.insert_event_values(playback.event_uuid, value)
                planned_playback_correction_uuid = [event_link.event_uuid_link for event_link in playback.eventLinks if event_link.name == "TIME_CORRECTION"][0]
                engine.insert_event_values(planned_playback_correction_uuid, value)
            # end for
        # end if

        # TODO: This could be a place to create an alert as the DFEP schedule would not cover correctly the planned playbacks

        orbit = schedule.xpath("@id")[0].split("_")[1]
        # DFEP schedule event
        dfep_schedule_event = {
            "gauge": {
                "insertion_type": "INSERT_and_ERASE",
                "name": "DFEP_SCHEDULE",
                "system": station
            },
            "links": links,
            "start": start,
            "stop": stop,
            "values": [{
                "name": "schedule_information",
                "type": "object",
                "values": [
                    {"name": "orbit",
                     "type": "double",
                     "value": str(orbit)},
                    {"name": "satellite",
                     "type": "text",
                     "value": satellite},
                    {"name": "station",
                     "type": "text",
                     "value": station},
                    {"name": "status",
                     "type": "text",
                     "value": status}
                ]
            }]
        }

        # Insert dfep_schedule_event
        ingestion_functions.insert_event_for_ingestion(dfep_schedule_event, source, list_of_events)

    # end for

    return

def process_file(file_path, engine, query):
    """Function to process the file and insert its relevant information
    into the DDBB of the eboa

    :param file_path: path to the file to be processed
    :type file_path: str
    """
    list_of_events = []
    file_name = os.path.basename(file_path)

    # Parse file
    parsed_xml = etree.parse(file_path)
    xpath_xml = etree.XPathEvaluator(parsed_xml)

    satellite = file_name[0:3]
    generation_time = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Source/Creation_Date")[0].text.split("=")[1]
    validity_start = xpath_xml("/Earth_Explorer_File/Data_Block/sched/station/acq[action = 'DELETE_RANGE']/start")[0].text
    validity_stop = xpath_xml("/Earth_Explorer_File/Data_Block/sched/station/acq[action = 'DELETE_RANGE']/stop")[0].text
    station = xpath_xml("/Earth_Explorer_File/Data_Block/sched/station")[0].get("name")

    source = {
        "name": file_name,
        "generation_time": generation_time,
        "validity_start": validity_start,
        "validity_stop": validity_stop
    }

    # Generate dfep schedule events
    _generate_dfep_schedule_events(xpath_xml, source, engine, query, list_of_events)

    # Build the xml
    data = {"operations": [{
        "mode": "insert_and_erase",
        "dim_signature": {
            "name": "DFEP_SCHEDULE_" + station + "_" + satellite,
            "exec": os.path.basename(__file__),
            "version": version
        },
        "source": source,
        "events": list_of_events
    }]}

    return data
