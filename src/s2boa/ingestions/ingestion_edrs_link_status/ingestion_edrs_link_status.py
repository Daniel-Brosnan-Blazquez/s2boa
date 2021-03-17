"""
Ingestion module for the EDRS Report files

Written by DEIMOS Space S.L. (jubv)

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

# Import ingestion_functions.helpers
import eboa.ingestion.functions as ingestion_functions
import s2boa.ingestions.functions as functions
import s2boa.ingestions.xpath_functions as xpath_functions

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
    file_name = os.path.basename(file_path)

    # Remove namespaces
    new_file = tempfile.NamedTemporaryFile()
    new_file_path = new_file.name

    ingestion_functions.remove_namespaces(file_path, new_file_path)

    # Parse file
    parsed_xml = etree.parse(new_file_path)
    xpath_xml = etree.XPathEvaluator(parsed_xml)

    leo_satellite_id = xpath_xml("/Earth_Explorer_File/Data_Block/Session_Description/LEO_Satellite_ID")[0].text
    satellite = functions.get_satellite_name_by_alias(leo_satellite_id)

    edrs_unit = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Mission")[0].text
    session_id = xpath_xml("/Earth_Explorer_File/Data_Block/Session_ID")[0].text
    validity_start = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Validity_Period/Validity_Start")[0].text.split("=")[1]
    validity_stop = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Validity_Period/Validity_Stop")[0].text.split("=")[1]

    source = {
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
    
    planned_playback_uuids = []
    edrs_slots = query.get_events(explicit_refs = {"op": "==", "filter": session_id},
                                      gauge_names = {"op": "==", "filter": "SLOT_REQUEST_EDRS"},
                                      gauge_systems = {"op": "==", "filter": satellite})

    if len (edrs_slots) > 0:
        planned_playback_uuids = [link.event_uuid_link for edrs_slot in edrs_slots for link in edrs_slot.eventLinks if link.name == "PLANNED_PLAYBACK"]
    # end if

    links = []
    for planned_playback_uuid in planned_playback_uuids:
        links.append({
            "link": str(planned_playback_uuid),
            "link_mode": "by_uuid",
            "name": "LINK_EXECUTION_STATUS",
            "back_ref": "PLANNED_PLAYBACK"
        })
    # end for
    
    functions.insert_ingestion_progress(session_progress, general_source_progress, 40)

    events = []
    for dcsu in xpath_xml("/Earth_Explorer_File/Data_Block/List_of_DCSU_Info/DCSU_Info"):
        dcsu_id = dcsu.xpath("DCSU_ID")[0].text
        status = dcsu.xpath("Execution_Status")[0].text
        link_session_fer = dcsu.xpath("Link_session_FER")[0].text
        number_of_delivered_cadu = dcsu.xpath("Number_of_delivered_CADU")[0].text
        number_of_missing_cadu = dcsu.xpath("Number_of_missing_CADU")[0].text

        if (status == "SUCCESS" and int(link_session_fer) == 0 and number_of_missing_cadu == 0):
            characterized_status = "OK"
        else:
            characterized_status = "NOK"
        # end if

        events.append({
            "key": "LINK_EXECUTION_STATUS" + "-" + session_id + "-" + dcsu_id,
            "gauge": {
                "insertion_type": "EVENT_KEYS",
                "name": "LINK_EXECUTION_STATUS_DCSU_" + dcsu_id,
                "system": edrs_unit
            },
            "explicit_reference": session_id,
            "start": validity_start,
            "stop": validity_stop,
            "links": links,
            "values": [
                {
                    "name": "satellite",
                    "type": "text",
                    "value": satellite
                },
                {
                    "name": "edrs_unit",
                    "type": "text",
                    "value": edrs_unit
                },
                {
                    "name": "session_id",
                    "type": "text",
                    "value": session_id
                },
                {
                    "name": "status",
                    "type": "text",
                    "value": status
                },
                {
                    "name": "characterized_status",
                    "type": "text",
                    "value": characterized_status
                },
                {
                    "name": "dcsu_id",
                    "type": "text",
                    "value": dcsu_id
                },
                {
                    "name": "link_session_fer",
                    "type": "double",
                    "value": link_session_fer
                },
                {
                    "name": "number_of_delivered_cadu",
                    "type": "double",
                    "value": number_of_delivered_cadu
                },
                {
                    "name": "number_of_missing_cadu",
                    "type": "double",
                    "value": number_of_missing_cadu
                }]
        })
    
    functions.insert_ingestion_progress(session_progress, general_source_progress, 80)

    # Build the xml
    data = {"operations": [{
        "mode": "insert",
        "dim_signature": {
            "name": "LINK_EXECUTION_STATUS" + "_"+ satellite,
            "exec": os.path.basename(__file__),
            "version": version
        },
        "source": source,
        "events": events
    }]}
    
    functions.insert_ingestion_progress(session_progress, general_source_progress, 100)

    query.close_session()

    new_file.close()
    
    return data
