"""
Ingestion module for the NPPF files of Sentinel-2

Written by DEIMOS Space S.L. (dibb)

module s2boa
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

# Import debugging
from eboa.debugging import debug

# Import logging
from eboa.logging import Log

# Import query
from eboa.engine.query import Query

logging_module = Log(name = __name__)
logger = logging_module.logger

version = "1.0"
imaging_modes={
    "MPMSSCAL": "SUN_CAL",
    "MPMSDASC": "DARK_CAL_CSM_OPEN",
    "MPMSDCLO": "DARK_CAL_CSM_CLOSE",
    "MPMSIVIC": "VICARIOUS_CAL",
    "MPMSNOBS": "NOMINAL",
    "MPMSIRAW": "RAW",
    "MPMSIDTS": "TEST"
}

record_types={
    "MPMMRNOM": "NOMINAL",
    "MPMMRNRT": "NRT"
}

playback_types={
    "MPMMPNOM": "NOMINAL",
    "MPMMPREG": "REGULAR",
    "MPMMPBRT": "RT",
    "MPMMPBHK": "HKTM",
    "MPMMPBSA": "SAD",
    "MPMMPBHS": "HKTM_SAD",
    "MPMMPNRT": "NRT"
}

playback_means={
    "MPXBSBOP": "XBAND",
    "MPG1STRT": "OCP",
    "MPG2STRT": "OCP",
    "MPG3STRT": "OCP"
}

playback_means_by_stop={
    "MPXBOPSB": "XBAND",
    "MPOCPRY2": "OCP"
}

@debug
def _generate_record_events(xpath_xml, source, list_of_events):
    """
    Method to generate the events for the MSI operations
    :param xpath_xml: source of information that was xpath evaluated
    :type xpath_xml: XPathEvaluator
    :param source: information of the source
    :type xpath_xml: dict
    :param list_of_events: list to store the events to be inserted into the eboa
    :type list_of_events: list
    
    Conceptual design of what is expected given the following inputs
    RECORD                  |--NRT--|
    RECORD          |--NOM--|       |--NOM--|
    IMAGING          |-------IMAGING-------|
    
    RESULT:
    RECORD EVENT 1  |--NOM--|
    RECORD EVENT 2          |--NRT--|
    RECORD EVENT 3                  |--NOM--|
    CUT_IMG EV 1     |------|
    CUT_IMG EV 2            |-------|
    CUT_IMG EV 3                    |------|
    IMAGING EVENT 1  |-------IMAGING-------|

    RECORD events and CUT_IMAGING events are linked by RECORD_OPERATION and IMAGING_OPERATION links
    IMAGING events and CUT_IMAGING events are linked by COMPLETE_IMAGING_OPERATION link (with back_ref)
    """

    satellite = source["name"][0:3]
    # Recording operations
    record_operations = xpath_xml("/Earth_Explorer_File/Data_Block/List_of_EVRQs/EVRQ[(RQ/RQ_Name='MPMMRNOM' or RQ/RQ_Name='MPMMRNRT') and boolean(following-sibling::EVRQ[RQ/RQ_Name='MPMMRSTP' or RQ/RQ_Name='MPMMRNRT' or RQ/RQ_Name='MPMMRNOM'])]")

    for record_operation in record_operations:
        # Record start information
        record_start = record_operation.xpath("RQ/RQ_Execution_Time")[0].text.split("=")[1]
        record_start_orbit = record_operation.xpath("RQ/RQ_Absolute_orbit")[0].text
        record_start_angle = record_operation.xpath("RQ/RQ_Deg_from_ANX")[0].text
        record_start_request = record_operation.xpath("RQ/RQ_Name")[0].text
        record_start_scn_dup = record_operation.xpath("RQ/List_of_RQ_Parameters/RQ_Parameter[RQ_Parameter_Name = 'SCN_DUP']/RQ_Parameter_Value")

        # Record stop information
        record_operation_stop = record_operation.xpath("following-sibling::EVRQ[RQ/RQ_Name='MPMMRSTP' or RQ/RQ_Name='MPMMRNRT' or RQ/RQ_Name='MPMMRNOM'][1]")[0]
        record_stop_orbit = record_operation_stop.xpath("RQ/RQ_Absolute_orbit")[0].text
        record_stop_angle = record_operation_stop.xpath("RQ/RQ_Deg_from_ANX")[0].text
        record_stop = record_operation_stop.xpath("RQ/RQ_Execution_Time")[0].text.split("=")[1]
        record_stop_request = record_operation_stop.xpath("RQ/RQ_Name")[0].text
        record_stop_scn_dup = record_operation_stop.xpath("RQ/List_of_RQ_Parameters/RQ_Parameter[RQ_Parameter_Name = 'SCN_DUP']/RQ_Parameter_Value")

        record_type = record_types[record_operation.xpath("RQ/RQ_Name")[0].text]

        following_imaging_operation = record_operation.xpath("following-sibling::EVRQ[RQ/RQ_Name='MPMSSCAL' or RQ/RQ_Name='MPMSDASC' or RQ/RQ_Name='MPMSDCLO' or RQ/RQ_Name='MPMSIVIC' or RQ/RQ_Name='MPMSNOBS' or RQ/RQ_Name='MPMSIRAW' or RQ/RQ_Name='MPMSIDTS' or RQ/RQ_Name='MPMSIMID' or RQ/RQ_Name='MPMSIDSB' or RQ/RQ_Name='MPMMRSTP' or RQ/RQ_Name='MPMMRNRT' or RQ/RQ_Name='MPMMRNOM'][1]")[0]
        if following_imaging_operation.xpath("RQ[RQ_Name='MPMSIMID' or RQ_Name='MPMSIDSB' or RQ_Name='MPMMRSTP' or RQ_Name='MPMMRNRT' or RQ_Name='MPMMRNOM']"):
            # The start of the cut imaging is the record operation because the imaging operation was going before this recording
            # The stop of the cut imaging is the start of the following imaging or the stop of this imaging or the stop of this recording
            cut_imaging_start_operation = record_operation
            cut_imaging_stop_operation = following_imaging_operation
            imaging_start_operation = record_operation.xpath("preceding-sibling::EVRQ[RQ/RQ_Name='MPMSSCAL' or RQ/RQ_Name='MPMSDASC' or RQ/RQ_Name='MPMSDCLO' or RQ/RQ_Name='MPMSIVIC' or RQ/RQ_Name='MPMSNOBS' or RQ/RQ_Name='MPMSIRAW' or RQ/RQ_Name='MPMSIDTS'][1]")[0]
            imaging_start = imaging_start_operation.xpath("RQ/RQ_Execution_Time")[0].text.split("=")[1]
            cut_imaging_start_request = imaging_start_operation.xpath("RQ/RQ_Name")[0].text
        else:
            # The start of the cut imaging is the start of the current imaging
            # The stop of the cut imaging is the stop of the current imaging or the stop of this recording
            cut_imaging_start_operation = following_imaging_operation
            cut_imaging_start_request = cut_imaging_start_operation.xpath("RQ/RQ_Name")[0].text
            cut_imaging_stop_operation = record_operation.xpath("following-sibling::EVRQ[(RQ/RQ_Name='MPMSIMID' or RQ/RQ_Name='MPMSIDSB' or RQ/RQ_Name='MPMMRSTP' or RQ/RQ_Name='MPMMRNRT' or RQ/RQ_Name='MPMMRNOM')][1]")[0]
            imaging_start = following_imaging_operation.xpath("RQ/RQ_Execution_Time")[0].text.split("=")[1]
        # end if

        # Imaging start information
        cut_imaging_start = cut_imaging_start_operation.xpath("RQ/RQ_Execution_Time")[0].text.split("=")[1]
        cut_imaging_start_orbit = cut_imaging_start_operation.xpath("RQ/RQ_Absolute_orbit")[0].text
        cut_imaging_start_angle = cut_imaging_start_operation.xpath("RQ/RQ_Deg_from_ANX")[0].text

        cut_imaging_mode = imaging_modes[cut_imaging_start_request]

        # Imaging stop information
        cut_imaging_stop = cut_imaging_stop_operation.xpath("RQ/RQ_Execution_Time")[0].text.split("=")[1]
        if cut_imaging_mode == "SUN_CAL":
            cut_imaging_stop = cut_imaging_start
        # end if
        cut_imaging_stop_orbit = cut_imaging_stop_operation.xpath("RQ/RQ_Absolute_orbit")[0].text
        cut_imaging_stop_angle = cut_imaging_stop_operation.xpath("RQ/RQ_Deg_from_ANX")[0].text
        cut_imaging_stop_request = cut_imaging_stop_operation.xpath("RQ/RQ_Name")[0].text

        record_link_id = "record_" + record_start

        # Record event
        record_event = {
            "link_ref": record_link_id,
            "gauge": {
                "insertion_type": "INSERT_and_ERASE",
                "name": "PLANNED_RECORD",
                "system": satellite
            },
            "start": record_start,
            "stop": record_stop,
            "values": [
                {"name": "record_type",
                 "type": "text",
                 "value": record_type},
                {"name": "start_request",
                 "type": "text",
                 "value": record_start_request},
                {"name": "stop_request",
                 "type": "text",
                 "value": record_stop_request},
                {"name": "start_orbit",
                 "type": "double",
                 "value": record_start_orbit},
                {"name": "start_angle",
                 "type": "double",
                 "value": record_start_angle},
                {"name": "stop_orbit",
                 "type": "double",
                 "value": record_stop_orbit},
                {"name": "stop_angle",
                 "type": "double",
                 "value": record_stop_angle},
                {"name": "satellite",
                 "type": "text",
                 "value": satellite}
            ]
        }

        if len(record_start_scn_dup) == 1 or len(record_stop_scn_dup) == 1:
            parameters = []
            record_event["values"].append(
                {"name": "parameters",
                 "type": "object",
                 "values": parameters},
            )
        # end if

        # Include parameters
        if len(record_start_scn_dup) == 1:
            parameters.append(
                    {"name": "start_scn_dup",
                     "type": "double",
                     "value": record_start_scn_dup[0].text},
            )
        # end if

        if len(record_stop_scn_dup) == 1:
            parameters.append(
                    {"name": "stop_scn_dup",
                     "type": "double",
                     "value": record_stop_scn_dup[0].text}
            )
        # end if

        # Insert record_event
        ingestion_functions.insert_event_for_ingestion(record_event, source, list_of_events)

        cut_imaging_link_id = "cut_imaging_" + cut_imaging_start
        imaging_link_id = "imaging_" + imaging_start

        # Imaging event
        cut_imaging_event = {
            "link_ref": cut_imaging_link_id,
            "gauge": {
                "insertion_type": "INSERT_and_ERASE",
                "name": "PLANNED_CUT_IMAGING",
                "system": satellite
            },
            "start": cut_imaging_start,
            "stop": cut_imaging_stop,
            "links": [
                {
                    "link": record_link_id,
                    "link_mode": "by_ref",
                    "name": "PLANNED_IMAGING",
                    "back_ref": "PLANNED_RECORD"
                },
                {
                    "link": imaging_link_id,
                    "link_mode": "by_ref",
                    "name": "PLANNED_IMAGING",
                    "back_ref": "PLANNED_COMPLETE_IMAGING"
                }
            ],
            "values": [
                {"name": "start_request",
                 "type": "text",
                 "value": cut_imaging_start_request},
                {"name": "stop_request",
                 "type": "text",
                 "value": cut_imaging_stop_request},
                {"name": "start_orbit",
                 "type": "double",
                 "value": cut_imaging_start_orbit},
                {"name": "start_angle",
                 "type": "double",
                 "value": cut_imaging_start_angle},
                {"name": "stop_orbit",
                 "type": "double",
                 "value": cut_imaging_stop_orbit},
                {"name": "stop_angle",
                 "type": "double",
                 "value": cut_imaging_stop_angle},
                {"name": "satellite",
                 "type": "text",
                 "value": satellite},
                {"name": "record_type",
                 "type": "text",
                 "value": record_type},
                {"name": "imaging_mode",
                 "type": "text",
                 "value": cut_imaging_mode}
            ]
        }

        if len(record_start_scn_dup) == 1 or len(record_stop_scn_dup) == 1:
            cut_imaging_event["values"].append(
                {"name": "parameters",
                 "type": "object",
                 "values": parameters},
            )
        # end if

        # Insert imaging_event
        ingestion_functions.insert_event_for_ingestion(cut_imaging_event, source, list_of_events)

    # end for

    # Imaging operations
    imaging_operations = xpath_xml("/Earth_Explorer_File/Data_Block/List_of_EVRQs/EVRQ[(RQ/RQ_Name='MPMSSCAL' or RQ/RQ_Name='MPMSDASC' or RQ/RQ_Name='MPMSDCLO' or RQ/RQ_Name='MPMSIVIC' or RQ/RQ_Name='MPMSNOBS' or RQ/RQ_Name='MPMSIRAW' or RQ/RQ_Name='MPMSIDTS') and boolean(following-sibling::EVRQ[(RQ/RQ_Name='MPMSIMID' or RQ/RQ_Name='MPMSIDSB' or RQ/RQ_Name='MPMMRSTP')])]")

    for imaging_operation in imaging_operations:
        # Imaging start information
        imaging_start = imaging_operation.xpath("RQ/RQ_Execution_Time")[0].text.split("=")[1]
        imaging_start_orbit = imaging_operation.xpath("RQ/RQ_Absolute_orbit")[0].text
        imaging_start_angle = imaging_operation.xpath("RQ/RQ_Deg_from_ANX")[0].text
        imaging_start_request = imaging_operation.xpath("RQ/RQ_Name")[0].text

        imaging_mode = imaging_modes[imaging_start_request]

        # Imaging stop information
        if imaging_mode in ["NOMINAL", "VICARIOUS_CAL"]:
            imaging_stop_operation = imaging_operation.xpath("following-sibling::EVRQ[(RQ/RQ_Name='MPMSIMID')][1]")[0]
        else:
            imaging_stop_operation = imaging_operation.xpath("following-sibling::EVRQ[(RQ/RQ_Name='MPMSIMID' or RQ/RQ_Name='MPMSIDSB' or RQ/RQ_Name='MPMMRSTP')][1]")[0]
        # end if
        
        imaging_stop = imaging_stop_operation.xpath("RQ/RQ_Execution_Time")[0].text.split("=")[1]
        if imaging_mode == "SUN_CAL":
            imaging_stop = imaging_start
        # end if
        imaging_stop_orbit = imaging_stop_operation.xpath("RQ/RQ_Absolute_orbit")[0].text
        imaging_stop_angle = imaging_stop_operation.xpath("RQ/RQ_Deg_from_ANX")[0].text
        imaging_stop_request = imaging_stop_operation.xpath("RQ/RQ_Name")[0].text

        imaging_link_id = "imaging_" + imaging_start

        # Imaging event
        imaging_event = {
            "link_ref": imaging_link_id,
            "gauge": {
                "insertion_type": "INSERT_and_ERASE",
                "name": "PLANNED_IMAGING",
                "system": satellite
            },
            "start": imaging_start,
            "stop": imaging_stop,
            "values": [
                {"name": "start_request",
                 "type": "text",
                 "value": imaging_start_request},
                {"name": "stop_request",
                 "type": "text",
                 "value": imaging_stop_request},
                {"name": "start_orbit",
                 "type": "double",
                 "value": imaging_start_orbit},
                {"name": "start_angle",
                 "type": "double",
                 "value": imaging_start_angle},
                {"name": "stop_orbit",
                 "type": "double",
                 "value": imaging_stop_orbit},
                {"name": "stop_angle",
                 "type": "double",
                 "value": imaging_stop_angle},
                {"name": "satellite",
                 "type": "text",
                 "value": satellite},
                {"name": "imaging_mode",
                 "type": "text",
                 "value": imaging_mode}
            ]
        }

        # Insert imaging_event
        ingestion_functions.insert_event_for_ingestion(imaging_event, source, list_of_events)

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
    parsed_xml = etree.parse(file_path)
    xpath_xml = etree.XPathEvaluator(parsed_xml)

    satellite = file_name[0:3]
    generation_time = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Source/Creation_Date")[0].text.split("=")[1]
    validity_start = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Validity_Period/Validity_Start")[0].text.split("=")[1]
    validity_stop = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Validity_Period/Validity_Stop")[0].text.split("=")[1]
    deletion_queue = xpath_xml("/Earth_Explorer_File/Data_Block/List_of_EVRQs/EVRQ[RQ/RQ_Name='MGSYQDEL']")
    if len(deletion_queue) == 1:
        validity_start = deletion_queue[0].xpath("RQ/RQ_Execution_Time")[0].text.split("=")[1]
    # end if

    source = {
        "name": file_name,
        "reception_time": reception_time,
        "generation_time": generation_time,
        "validity_start": validity_start,
        "validity_stop": validity_stop
    }

    # Generate record events
    _generate_record_events(xpath_xml, source, list_of_events)

    record_events = [event for event in list_of_events if event["gauge"]["name"] == "PLANNED_RECORD"]
    imaging_events = [event for event in list_of_events if event["gauge"]["name"] == "PLANNED_IMAGING"]

    list_of_events_record_stop_issue = []

    for imaging_event in imaging_events:

        recording_covering_imaging = [event for event in record_events if imaging_event["start"] >= event["start"] and imaging_event["stop"] <= event["stop"]]

        recording_intersecting_imaging = [event for event in record_events if imaging_event["start"] <= event["stop"] and imaging_event["stop"] >= event["start"]]

        imaging_mode = [value["value"] for value in imaging_event["values"] if value["name"] == "imaging_mode"][0]
        
        if len(recording_covering_imaging) == 1:
            imaging_coverage_status = "TOTALLY_COVERED_BY_RECORDING"
        elif len(recording_intersecting_imaging) >= 1:
            imaging_coverage_status = "NOT_TOTALLY_COVERED_BY_RECORDING"
        else:
            imaging_coverage_status = "NOT_COVERED_BY_RECORDING"
        # end if

        if len(recording_intersecting_imaging) >= 1:
            margin_start = (parser.parse(imaging_event["start"]) - parser.parse(recording_intersecting_imaging[0]["start"])).total_seconds()
            margin_stop = (parser.parse(recording_intersecting_imaging[0]["stop"]) - parser.parse(imaging_event["stop"])).total_seconds()
            recording_start = recording_intersecting_imaging[0]["start"]
            recording_stop = recording_intersecting_imaging[0]["stop"]
        else:
            margin_start = "N/A"
            margin_stop = "N/A"
            recording_start = "N/A"
            recording_stop = "N/A"
        # end if

        if margin_stop == -0.5 and imaging_event["start"] >= validity_start and imaging_event["stop"] <= validity_stop:
            event = {
                "gauge": {
                    "insertion_type": "INSERT_and_ERASE",
                    "name": "PLANNED_IMAGING_RECORD_STOP_ISSUE",
                    "system": satellite
                },
                "start": imaging_event["start"],
                "stop": imaging_event["stop"],
            }
            list_of_events_record_stop_issue.append(event)
        # end if

        print("{};{};{};{};{};{};{};{};{};{}".format(satellite, imaging_event["start"], imaging_event["stop"], imaging_mode, imaging_coverage_status, margin_start, margin_stop, recording_start, recording_stop, file_name))
    # end for

    list_of_events_with_footprint = functions.associate_footprints(list_of_events_record_stop_issue, satellite)

    # Build the xml
    data = {"operations": [{
        "mode": "insert_and_erase",
        "dim_signature": {
            "name": "RECORD_STOP_ISSUE_NPPF_" + satellite,
            "exec": os.path.basename(__file__),
            "version": version
        },
        "source": source,
        "events": list_of_events_with_footprint
    }]}
    
    return data
