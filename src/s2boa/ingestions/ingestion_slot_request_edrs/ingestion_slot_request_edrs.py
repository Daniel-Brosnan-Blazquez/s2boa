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
import tempfile

# Import xml parser
from lxml import etree

# Import query
from eboa.engine.query import Query

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

def process_file(file_path, engine, query, reception_time):
    """
    Function to process the file and insert its relevant information
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
    list_of_explicit_references = []
    file_name = os.path.basename(file_path)

    # Remove namespaces
    new_file = tempfile.NamedTemporaryFile()
    new_file_path = new_file.name

    ingestion_functions.remove_namespaces(file_path, new_file_path)

    # Parse file
    parsed_xml = etree.parse(new_file_path)
    xpath_xml = etree.XPathEvaluator(parsed_xml)

    satellite = file_name[0:3]
    generation_time = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Source/Creation_Date")[0].text.split("=")[1]
    validity_start = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Validity_Period/Validity_Start")[0].text.split("=")[1]
    validity_stop = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Validity_Period/Validity_Stop")[0].text.split("=")[1]
    edrs = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Mission")[0].text

    # Generation time is changed to be the validity start to avoid overriding data by the ingestion_orbpre.py module
    source = {
        "name": file_name,
        "reception_time": reception_time,
        "generation_time": generation_time,
        "validity_start": validity_start,
        "validity_stop": validity_stop
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
    
    # Extract the slots
    list_of_completeness_events = {}
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
        playbacks = query.get_linked_events(gauge_names = {"filter": "PLANNED_PLAYBACK_CORRECTION", "op": "=="},
                                                 gauge_systems = {"filter": sentinel, "op": "=="},
                                                 start_filters = [{"date": start, "op": ">"}],
                                                 stop_filters = [{"date": stop, "op": "<"}],
                                                 link_names = {"filter": ["TIME_CORRECTION"], "op": "in"},
                                                 return_prime_events = False)

        links_slot_request = []
        links_dfep_schedule = []
        links_station_schedule = []
        if len(playbacks["linked_events"]) > 0:
            for playback in playbacks["linked_events"]:
                # Get the planned playback mean
                planned_playback_mean_uuids = [link.event_uuid_link for link in playback.eventLinks if link.name == "PLANNED_PLAYBACK_MEAN"]
                if len(planned_playback_mean_uuids) > 0:

                    mean = [value.value for value in playback.eventTexts if value.name == "playback_mean"][0]

                    if mean == "OCP":
                        links_slot_request.append({
                            "link": str(playback.event_uuid),
                            "link_mode": "by_uuid",
                            "name": "SLOT_REQUEST_EDRS",
                            "back_ref": "PLANNED_PLAYBACK"
                        })
                        links_dfep_schedule.append({
                            "link": str(playback.event_uuid),
                            "link_mode": "by_uuid",
                            "name": "DFEP_SCHEDULE_COMPLETENESS",
                            "back_ref": "PLANNED_PLAYBACK"
                        })
                        links_station_schedule.append({
                            "link": str(playback.event_uuid),
                            "link_mode": "by_uuid",
                            "name": "STATION_SCHEDULE_COMPLETENESS",
                            "back_ref": "PLANNED_PLAYBACK"
                        })
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
            "links": links_slot_request,
            "start": start,
            "stop": stop,
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
                {"name": "station",
                 "type": "text",
                 "value": "EDRS"}
            ]
        }

        # Insert slot_event
        ingestion_functions.insert_event_for_ingestion(slot_event, source, list_of_events)

        if not sentinel in list_of_completeness_events:
            list_of_completeness_events[sentinel] = []
        # end if
        
        # DFEP schedule completeness event
        slot_dfep_schedule_completeness_event = {
            "explicit_reference": session_id,
            "gauge": {
                "insertion_type": "INSERT_and_ERASE_per_EVENT_with_PRIORITY",
                "name": "DFEP_SCHEDULE_COMPLETENESS",
                "system": sentinel
            },
            "links": links_dfep_schedule,
            "start": start,
            "stop": stop,
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
                {"name": "station",
                 "type": "text",
                 "value": "EDRS"},
                {"name": "playback_mean",
                 "type": "text",
                 "value": "OCP"}
            ]
        }

        # Insert completeness event
        ingestion_functions.insert_event_for_ingestion(slot_dfep_schedule_completeness_event, source, list_of_completeness_events[sentinel])
        
        # Station schedule completeness event
        slot_station_schedule_completeness_event = {
            "explicit_reference": session_id,
            "gauge": {
                "insertion_type": "INSERT_and_ERASE_per_EVENT_with_PRIORITY",
                "name": "STATION_SCHEDULE_COMPLETENESS",
                "system": sentinel
            },
            "links": links_station_schedule,
            "start": start,
            "stop": stop,
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
                {"name": "station",
                 "type": "text",
                 "value": "EDRS"},
                {"name": "playback_mean",
                 "type": "text",
                 "value": "OCP"}
            ]
        }

        # Insert completeness event
        ingestion_functions.insert_event_for_ingestion(slot_station_schedule_completeness_event, source, list_of_completeness_events[sentinel])

    # end for

    functions.insert_ingestion_progress(session_progress, general_source_progress, 90)
    
    # Build the xml
    data = {"operations": [{
        "mode": "insert_and_erase",
        "dim_signature": {
            "name": "SLOT_REQUEST_EDRS_" + edrs,
            "exec": os.path.basename(__file__),
            "version": version
        },
        "source": source,
        "explicit_references": list_of_explicit_references,
        "events": list_of_events
    }]}

    functions.insert_ingestion_progress(session_progress, general_source_progress, 95)

    for satellite in list_of_completeness_events:
        if len(list_of_completeness_events[satellite]) > 0:
            data["operations"].append({
                "mode": "insert",
                "dim_signature": {
                    "name": "COMPLETENESS_NPPF_" + satellite,
                    "exec": os.path.basename(__file__),
                    "version": version
                },
                "source": {
                    "name": file_name,
                    "reception_time": reception_time,
                    "generation_time": generation_time,
                    "reported_validity_start": validity_start,
                    "reported_validity_stop": validity_stop,
                    "validity_start": validity_start,
                    "validity_stop": validity_stop,
                    "priority": 30
                },
                "events": list_of_completeness_events[satellite]
            })
        # end if
    # end for
    
    functions.insert_ingestion_progress(session_progress, general_source_progress, 100)

    query.close_session()    

    new_file.close()
    
    return data
