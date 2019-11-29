"""
Ingestion module for the Station Acquisition Report files

Written by DEIMOS Space S.L. (femd)

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

    satellite = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/File_Name")[0].text[0:3]

    acq_id = xpath_xml("/Earth_Explorer_File/Data_Block/StationAcquisitionReport/StationDownlinkDetails/Acq_Id")[0].text
    start = xpath_xml("/Earth_Explorer_File/Data_Block/StationAcquisitionReport/StationDownlinkDetails/DownlinkStartTime")[0].text.split("=")[1]
    stop = xpath_xml("/Earth_Explorer_File/Data_Block/StationAcquisitionReport/StationDownlinkDetails/DownlinkEndTime")[0].text.split("=")[1]
    downlink_status = xpath_xml("/Earth_Explorer_File/Data_Block/StationAcquisitionReport/StationDownlinkDetails/DownlinkStatus")[0].text

    generation_time = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Source/Creation_Date")[0].text.split("=")[1]
    validity_start = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Validity_Period/Validity_Start")[0].text.split("=")[1]
    if start < validity_start:
        validity_start = start
    # end if
    validity_stop = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Validity_Period/Validity_Stop")[0].text.split("=")[1]
    if stop > validity_stop:
        validity_stop = stop
    # end if
    station = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Source/System")[0].text

    if downlink_status != "OK":
        characterized_downlink_status = "NOK"
    else:
        characterized_downlink_status = "OK"
    # end if

    comments = xpath_xml("/Earth_Explorer_File/Data_Block/StationAcquisitionReport/StationDownlinkDetails/Comments")[0].text
    if comments is None:
        comments=" "
    #end if

    antenna_id = xpath_xml("/Earth_Explorer_File/Data_Block/StationAcquisitionReport/StationDownlinkDetails/AntennaId")[0].text
    orbit,support_number = acq_id.split("_")


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
    
    playbacks = query.get_linked_events(gauge_names = {"filter":"PLANNED_PLAYBACK_CORRECTION","op":"=="},
                                         gauge_systems = {"filter":[satellite],"op":"in"},
                                         start_filters = [{"date":start,"op":">"}], stop_filters = [{"date":stop, "op":"<"}],
                                         link_names = {"filter":["TIME_CORRECTION"],"op":"in"},
                                         return_prime_events = False)

    links = []
    status = "MATCHED_PLAYBACK"
    if len(playbacks["linked_events"]) == 0:
        status = "NO_MATCHED_PLAYBACK"
    else:
        for playback in playbacks["linked_events"]:
            links.append({
                "link": str(playback.event_uuid),
                "link_mode": "by_uuid",
                "name": "STATION_ACQUISITION_REPORT",
                "back_ref": "PLANNED_PLAYBACK"
            })
        # end for
    # end if

    functions.insert_ingestion_progress(session_progress, general_source_progress, 40)
    
    # Build the xml
    data = {"operations": [{
        "mode": "insert",
        "dim_signature": {
            "name": "STATION_REPORT_" + station + "_"+ satellite,
            "exec": os.path.basename(__file__),
            "version": version
        },
        "source": source,
        "events": [{
            "key": "STATION_REPORT_" + station + "_" + satellite + "_" + acq_id,
            "gauge": {
                "insertion_type": "EVENT_KEYS",
                "name": "STATION_REPORT",
                "system": station
            },
            "start": start,
            "stop": stop,
            "links": links,
            "values": [
                {
                    "name": "downlink_status",
                    "type": "text",
                    "value": downlink_status
                },
                {
                    "name": "characterized_downlink_status",
                    "type": "text",
                    "value": characterized_downlink_status
                },
                {
                    "name": "comments",
                    "type": "text",
                    "value": comments
                },
                {
                    "name": "antenna_id",
                    "type": "text",
                    "value": antenna_id
                },{
                    "name": "satellite",
                    "type": "text",
                    "value": satellite
                },{
                    "name": "orbit",
                    "type": "double",
                    "value": orbit
                },{
                    "name": "support_number",
                    "type": "double",
                    "value": support_number
                },{
                    "name": "status",
                    "type": "text",
                    "value": status
                },{
                    "name": "station",
                    "type": "text",
                    "value": station
                }]
        }]
    }]}

    functions.insert_ingestion_progress(session_progress, general_source_progress, 80)
    
    functions.insert_ingestion_progress(session_progress, general_source_progress, 100)

    query.close_session()

    new_file.close()
    
    return data
