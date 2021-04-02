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
import s2boa.ingestions.functions as functions

# Import query
from eboa.engine.query import Query

# Import debugging
from eboa.debugging import debug

# Import logging
from eboa.logging import Log

# Import query
from eboa.engine.query import Query

logging_module = Log(name = __name__)
logger = logging_module.logger

version = "1.0"

@debug
def _generate_dfep_schedule_events(xpath_xml, source, engine, query, list_of_events, list_of_completeness_events):
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

        playbacks = query.get_linked_events(gauge_names = {"filter": "PLANNED_PLAYBACK_CORRECTION", "op": "=="},
                                            gauge_systems = {"filter": [satellite], "op": "in"},
                                            start_filters = [{"date": start, "op": ">"}],
                                            stop_filters = [{"date": stop, "op": "<"}],
                                            link_names = {"filter": "TIME_CORRECTION", "op": "=="},
                                            return_prime_events = False)

        links = []
        if len(playbacks["linked_events"]) > 0:
            for playback in playbacks["linked_events"]:
                links.append({
                    "link": str(playback.event_uuid),
                    "link_mode": "by_uuid",
                    "name": "DFEP_SCHEDULE",
                    "back_ref": "PLANNED_PLAYBACK"
                })
            # end for
        # end if

        links_completeness = []
        if len(playbacks["linked_events"]) > 0:
            for playback in playbacks["linked_events"]:
                links_completeness.append({
                    "link": str(playback.event_uuid),
                    "link_mode": "by_uuid",
                    "name": "DFEP_SCHEDULE_COMPLETENESS",
                    "back_ref": "PLANNED_PLAYBACK"
                })
            # end for
        # end if

        # TODO: This could be a place to create an alert as the DFEP schedule would not cover correctly the planned playbacks

        orbit = schedule.xpath("@id")[0].split("_")[1]
        # DFEP schedule event
        dfep_schedule_event = {
            "gauge": {
                "insertion_type": "INSERT_and_ERASE",
                "name": "DFEP_SCHEDULE",
                "system": satellite
            },
            "links": links,
            "start": start,
            "stop": stop,
            "values": [
                {"name": "orbit",
                 "type": "double",
                 "value": str(orbit)},
                {"name": "satellite",
                 "type": "text",
                 "value": satellite},
                {"name": "station",
                 "type": "text",
                 "value": station}
            ]
        }

        # Insert dfep_schedule_event
        ingestion_functions.insert_event_for_ingestion(dfep_schedule_event, source, list_of_events)

        # DFEP schedule completeness event
        dfep_schedule_completeness_event = {
            "gauge": {
                "insertion_type": "INSERT_and_ERASE_per_EVENT_with_PRIORITY",
                "name": "DFEP_SCHEDULE_COMPLETENESS",
                "system": satellite
            },
            "links": links_completeness,
            "start": start,
            "stop": stop,
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
                {"name": "playback_mean",
                 "type": "text",
                 "value": "XBAND"}
            ]
        }

        # Insert dfep_schedule_event
        ingestion_functions.insert_event_for_ingestion(dfep_schedule_completeness_event, source, list_of_completeness_events)

    # end for

    return

def process_file(file_path, engine, query, reception_time):
    """Function to process the file and insert its relevant information
    into the DDBB of the eboa

    :param file_path: path to the file to be processed
    :type file_path: str
    :param engine: Engine instance
    :type engine: Engine
    :param query: Query instance
    :type query: Query
    :param reception_time: time of the reception of the file by the triggering
    :type reception_time: str
    """
    list_of_events = []
    file_name = os.path.basename(file_path)

    # Parse file
    parsed_xml = etree.parse(file_path)
    xpath_xml = etree.XPathEvaluator(parsed_xml)

    satellite = file_name[0:3]
    generation_time = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Source/Creation_Date")[0].text.split("=")[1]
    reported_validity_start = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Validity_Period/Validity_Start")[0].text.split("=")[1]
    reported_validity_stop = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Validity_Period/Validity_Stop")[0].text.split("=")[1]
    validity_start = xpath_xml("/Earth_Explorer_File/Data_Block/sched/station/acq[action = 'DELETE_RANGE']/start")[0].text
    validity_stop = xpath_xml("/Earth_Explorer_File/Data_Block/sched/station/acq[action = 'DELETE_RANGE']/stop")[0].text
    station = xpath_xml("/Earth_Explorer_File/Data_Block/sched/station")[0].get("name")

    # Generation time is changed to be the validity start to avoid overriding data by the ingestion_orbpre.py module
    source = {
        "name": file_name,
        "reception_time": reception_time,
        "generation_time": generation_time,
        "validity_start": validity_start,
        "validity_stop": validity_stop,
        "reported_validity_start": reported_validity_start,
        "reported_validity_stop": reported_validity_stop
    }

    # Get the general source entry (processor = None, version = None, DIM signature = PENDING_SOURCES)
    # This is for registrering the ingestion progress
    query_general_source = Query()
    session_progress = query_general_source.session
    general_source_progress = query_general_source.get_sources(names = {"filter": file_name, "op": "=="},
                                                               dim_signatures = {"filter": "PENDING_SOURCES", "op": "=="},
                                                               processors = {"filter": "", "op": "=="},
                                                               processor_version_filters = [{"filter": "", "op": "=="}])

    if len(general_source_progress) > 0:
        general_source_progress = general_source_progress[0]
    # end if

    functions.insert_ingestion_progress(session_progress, general_source_progress, 10)
    
    # Generate dfep schedule events
    list_of_completeness_events = []
    _generate_dfep_schedule_events(xpath_xml, source, engine, query, list_of_events, list_of_completeness_events)

    functions.insert_ingestion_progress(session_progress, general_source_progress, 90)
    
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

    functions.insert_ingestion_progress(session_progress, general_source_progress, 95)

    if len(list_of_completeness_events) > 0:
        iterator = 1
        for event in list_of_completeness_events:
            data["operations"].append({
                "mode": "insert",
                "dim_signature": {
                    "name": "COMPLETENESS_NPPF_" + satellite,
                    "exec": "event_" + str(iterator) + "_" + os.path.basename(__file__),
                    "version": version
                },
                "source": {
                    "name": file_name,
                    "reception_time": reception_time,
                    "generation_time": generation_time,
                    "reported_validity_start": reported_validity_start,
                    "reported_validity_stop": reported_validity_stop,
                    "validity_start": event["start"],
                    "validity_stop": event["stop"],
                    "priority": 30
                },
                "events": [event]
            })
            iterator += 1
        # end for
    # end if
    
    functions.insert_ingestion_progress(session_progress, general_source_progress, 100)

    query.close_session()
    
    return data
