"""
Ingestion module for the NPPF files of Sentinel-2

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

# Import debugging
from eboa.debugging import debug

# Import logging
from eboa.logging import Log

# Import query
from eboa.engine.query import Query

# Import ORBPRE
from s2boa.ingestions.ingestion_orbpre.ingestion_orbpre import get_date_from_angle

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
        imaging_stop_operation = imaging_operation.xpath("following-sibling::EVRQ[(RQ/RQ_Name='MPMSIMID' or RQ/RQ_Name='MPMSIDSB' or RQ/RQ_Name='MPMMRSTP')][1]")[0]
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

@debug
def _generate_idle_events(xpath_xml, source, list_of_events):
    """
    Method to generate the events for the idle operation of the satellite
    :param xpath_xml: source of information that was xpath evaluated
    :type xpath_xml: XPathEvaluator
    :param source: information of the source
    :type xpath_xml: dict
    :param list_of_events: list to store the events to be inserted into the eboa
    :type list_of_events: list
    """

    satellite = source["name"][0:3]

    # Idle operations
    idle_operations = xpath_xml("/Earth_Explorer_File/Data_Block/List_of_EVRQs/EVRQ[RQ/RQ_Name='MPMSIMID' or RQ/RQ_Name='MPMSSBID']")

    for idle_operation in idle_operations:
        # Idle start information
        idle_start = idle_operation.xpath("RQ/RQ_Execution_Time")[0].text.split("=")[1]
        idle_start_orbit = idle_operation.xpath("RQ/RQ_Absolute_orbit")[0].text
        idle_start_angle = idle_operation.xpath("RQ/RQ_Deg_from_ANX")[0].text
        idle_start_request = idle_operation.xpath("RQ/RQ_Name")[0].text

        # Idle stop information
        idle_operation_stop = idle_operation.xpath("following-sibling::EVRQ[RQ/RQ_Name='MPMSSCAL' or RQ/RQ_Name='MPMSDASC' or RQ/RQ_Name='MPMSDCLO' or RQ/RQ_Name='MPMSIVIC' or RQ/RQ_Name='MPMSNOBS' or RQ/RQ_Name='MPMSIRAW' or RQ/RQ_Name='MPMSIDTS' or RQ/RQ_Name='MPMSIDSB'][1]")
        if len(idle_operation_stop) == 1:
            idle_stop_orbit = idle_operation_stop[0].xpath("RQ/RQ_Absolute_orbit")[0].text
            idle_stop_angle = idle_operation_stop[0].xpath("RQ/RQ_Deg_from_ANX")[0].text
            idle_stop = idle_operation_stop[0].xpath("RQ/RQ_Execution_Time")[0].text.split("=")[1]
            idle_stop_request = idle_operation_stop[0].xpath("RQ/RQ_Name")[0].text
            values = [
                {"name": "start_request",
                 "type": "text",
                 "value": idle_start_request},
                {"name": "stop_request",
                 "type": "text",
                 "value": idle_stop_request},
                {"name": "start_orbit",
                 "type": "double",
                 "value": idle_start_orbit},
                {"name": "start_angle",
                 "type": "double",
                 "value": idle_start_angle},
                {"name": "stop_orbit",
                 "type": "double",
                 "value": idle_stop_orbit},
                {"name": "stop_angle",
                 "type": "double",
                 "value": idle_stop_angle},
                {"name": "satellite",
                 "type": "text",
                 "value": satellite}
            ]
        else:
            idle_stop_orbit = None
            idle_stop_angle = None
            idle_stop = source["validity_stop"]
            idle_stop_request = None
            values = [
                {"name": "start_request",
                 "type": "text",
                 "value": idle_start_request},
                {"name": "start_orbit",
                 "type": "double",
                 "value": idle_start_orbit},
                {"name": "start_angle",
                 "type": "double",
                 "value": idle_start_angle},
                {"name": "satellite",
                 "type": "text",
                 "value": satellite}
            ]
        # end if

        # Idle event
        idle_event = {
            "link_ref": "idle_" + str(idle_start),
            "gauge": {
                "insertion_type": "INSERT_and_ERASE",
                "name": "PLANNED_IDLE",
                "system": satellite
            },
            "start": idle_start,
            "stop": idle_stop,
            "values": values
        }

        # Insert idle_event
        ingestion_functions.insert_event_for_ingestion(idle_event, source, list_of_events)

    # end for

    return

@debug
def _generate_playback_events(xpath_xml, source, list_of_events):
    """
    Method to generate the events for the idle operation of the satellite
    :param xpath_xml: source of information that was xpath evaluated
    :type xpath_xml: XPathEvaluator
    :param source: information of the source
    :type xpath_xml: dict
    :param list_of_events: list to store the events to be inserted into the eboa
    :type list_of_events: list

    Conceptual design of what is expected given the following inputs
    PLAYBACK MEAN      |------------XBAND------------|
    PLAYBACK MEAN                           |------------OCP-----------|
    PLAYBACK TYPES      |--NOM--||SAD|   |NOM||SAD|     |--NOM--||SAD|
    
    RESULT:
    PB MEAN EVENT 1    |------------XBAND------------|
    PB TY EVS LINKED    |--NOM--||SAD|   |NOM||SAD|
    PB MEAN EVENT 2                         |------------OCP----------
    PB TY EVS LINKED                                    |--NOM--||SAD|

    PB MEAN events and PB TY events are linked
    """

    satellite = source["name"][0:3]

    # Playback operations
    playback_operations = xpath_xml("/Earth_Explorer_File/Data_Block/List_of_EVRQs/EVRQ[(RQ/RQ_Name='MPXBSBOP' and boolean(following-sibling::EVRQ[RQ/RQ_Name='MPXBOPSB'])) or ((RQ/RQ_Name='MPG1STRT' or RQ/RQ_Name='MPG2STRT' or RQ/RQ_Name='MPG3STRT') and boolean(following-sibling::EVRQ[RQ/RQ_Name='MPOCPRY2']))]")

    for playback_operation in playback_operations:
        # Playback start information
        playback_start = playback_operation.xpath("RQ/RQ_Execution_Time")[0].text.split("=")[1]
        playback_start_orbit = playback_operation.xpath("RQ/RQ_Absolute_orbit")[0].text
        playback_start_angle = playback_operation.xpath("RQ/RQ_Deg_from_ANX")[0].text
        playback_start_request = playback_operation.xpath("RQ/RQ_Name")[0].text

        playback_mean = playback_means[playback_start_request]

        # Playback stop information
        if playback_mean == "XBAND":
            playback_operation_stop = playback_operation.xpath("following-sibling::EVRQ[RQ/RQ_Name='MPXBOPSB'][1]")[0]
        else:
            playback_operation_stop = playback_operation.xpath("following-sibling::EVRQ[RQ/RQ_Name='MPOCPRY2'][1]")[0]
        # end if
        playback_stop_orbit = playback_operation_stop.xpath("RQ/RQ_Absolute_orbit")[0].text
        playback_stop_angle = playback_operation_stop.xpath("RQ/RQ_Deg_from_ANX")[0].text
        playback_stop = playback_operation_stop.xpath("RQ/RQ_Execution_Time")[0].text.split("=")[1]
        playback_stop_request = playback_operation_stop.xpath("RQ/RQ_Name")[0].text

        playback_mean_link_id = "playback_mean_" + playback_stop

        # Playback event
        playback_event = {
            "link_ref": playback_mean_link_id,
            "gauge": {
                "insertion_type": "INSERT_and_ERASE",
                "name": "PLANNED_PLAYBACK_MEAN",
                "system": satellite
            },
            "start": playback_start,
            "stop": playback_stop,
            "values": [
                {"name": "start_request",
                 "type": "text",
                 "value": playback_start_request},
                {"name": "stop_request",
                 "type": "text",
                 "value": playback_stop_request},
                {"name": "start_orbit",
                 "type": "double",
                 "value": playback_start_orbit},
                {"name": "start_angle",
                 "type": "double",
                 "value": playback_start_angle},
                {"name": "stop_orbit",
                 "type": "double",
                 "value": playback_stop_orbit},
                {"name": "stop_angle",
                 "type": "double",
                 "value": playback_stop_angle},
                {"name": "satellite",
                 "type": "text",
                 "value": satellite},
                {"name": "playback_mean",
                 "type": "text",
                 "value": playback_mean}
            ]
        }

        # Insert playback_event
        ingestion_functions.insert_event_for_ingestion(playback_event, source, list_of_events)

    # end for


    # Associate the playback types to the playback means
    playback_type_start_operations = xpath_xml("/Earth_Explorer_File/Data_Block/List_of_EVRQs/EVRQ[(((RQ/RQ_Name='MPMMPNOM' or RQ/RQ_Name='MPMMPREG' or RQ/RQ_Name='MPMMPBRT' or RQ/RQ_Name='MPMMPNRT') and boolean(following-sibling::EVRQ[RQ/RQ_Name='MPMMPSTP'])) or RQ/RQ_Name='MPMMPBHK' or RQ/RQ_Name='MPMMPBSA' or RQ/RQ_Name='MPMMPBHS')  and (boolean(following-sibling::EVRQ[RQ/RQ_Name='MPXBOPSB']) or boolean(following-sibling::EVRQ[RQ/RQ_Name='MPOCPRY2']))]")

    for playback_type_start_operation in playback_type_start_operations:

        # Playback_Type start information
        playback_type_start = playback_type_start_operation.xpath("RQ/RQ_Execution_Time")[0].text.split("=")[1]
        playback_type_start_orbit = playback_type_start_operation.xpath("RQ/RQ_Absolute_orbit")[0].text
        playback_type_start_angle = playback_type_start_operation.xpath("RQ/RQ_Deg_from_ANX")[0].text
        playback_type_start_request = playback_type_start_operation.xpath("RQ/RQ_Name")[0].text

        playback_type = playback_types[playback_type_start_request]

        if playback_type in ["HKTM", "SAD", "HKTM_SAD"]:
            playback_type_stop_operation = playback_type_start_operation
        else:
            playback_type_stop_operation = playback_type_start_operation.xpath("following-sibling::EVRQ[RQ/RQ_Name='MPMMPSTP'][1]")[0]
        # end if

        # Playback_Type stop information
        playback_type_stop = playback_type_stop_operation.xpath("RQ/RQ_Execution_Time")[0].text.split("=")[1]
        playback_type_stop_orbit = playback_type_stop_operation.xpath("RQ/RQ_Absolute_orbit")[0].text
        playback_type_stop_angle = playback_type_stop_operation.xpath("RQ/RQ_Deg_from_ANX")[0].text
        playback_type_stop_request = playback_type_stop_operation.xpath("RQ/RQ_Name")[0].text

        playback_mean = playback_type_start_operation.xpath("following-sibling::EVRQ[RQ/RQ_Name='MPXBOPSB' or RQ/RQ_Name='MPOCPRY2'][1]")
        if len (playback_mean) > 0:
            playback_mean_start_request = playback_mean[0].xpath("RQ/RQ_Name")[0].text

            playback_mean = playback_means_by_stop[playback_mean_start_request]
        else:
            playback_mean = "N/A"
        # end if

        playback_mean_stop = playback_type_start_operation.xpath("following-sibling::EVRQ[RQ/RQ_Name='MPXBOPSB' or RQ/RQ_Name='MPOCPRY2'][1]")[0].xpath("RQ/RQ_Execution_Time")[0].text.split("=")[1]
        playback_mean_link_id = "playback_mean_" + playback_mean_stop

        # Playback_Type event
        playback_type_event = {
            "link_ref": "playback_" + playback_type_start,
            "gauge": {
                "insertion_type": "INSERT_and_ERASE",
                "name": "PLANNED_PLAYBACK",
                "system": satellite
            },
            "start": playback_type_start,
            "stop": playback_type_stop,
            "links": [
                {
                    "link": playback_mean_link_id,
                    "link_mode": "by_ref",
                    "name": "PLANNED_PLAYBACK",
                    "back_ref": "PLANNED_PLAYBACK_MEAN"
                }
            ],
            "values": [
                {"name": "start_request",
                 "type": "text",
                 "value": playback_type_start_request},
                {"name": "stop_request",
                 "type": "text",
                 "value": playback_type_stop_request},
                {"name": "start_orbit",
                 "type": "double",
                 "value": playback_type_start_orbit},
                {"name": "start_angle",
                 "type": "double",
                 "value": playback_type_start_angle},
                {"name": "stop_orbit",
                 "type": "double",
                 "value": playback_type_stop_orbit},
                {"name": "stop_angle",
                 "type": "double",
                 "value": playback_type_stop_angle},
                {"name": "satellite",
                 "type": "text",
                 "value": satellite},
                {"name": "playback_mean",
                 "type": "text",
                 "value": playback_mean},
                {"name": "playback_type",
                 "type": "text",
                 "value": playback_type}
            ]
        }

        parameters = []
        playback_type_event["values"].append(
            {"name": "parameters",
             "type": "object",
             "values": parameters},
        )
        if playback_type == "HKTM_SAD":
            parameters.append(
                {"name": "MEM_FRHK",
                 "type": "double",
                 "value": playback_type_start_operation.xpath("RQ/List_of_RQ_Parameters/RQ_Parameter[RQ_Parameter_Name = 'MEM_FRHK']/RQ_Parameter_Value")[0].text},
            )
            parameters.append(
                {"name": "MEM_FSAD",
                 "type": "double",
                 "value": playback_type_start_operation.xpath("RQ/List_of_RQ_Parameters/RQ_Parameter[RQ_Parameter_Name = 'MEM_FSAD']/RQ_Parameter_Value")[0].text},
            )
        # end if
        if playback_type in ["HKTM", "SAD", "NOMINAL", "REGULAR", "NRT", "RT"]:
            parameters.append(
                {"name": "MEM_FREE",
                 "type": "double",
                 "value": playback_type_start_operation.xpath("RQ/List_of_RQ_Parameters/RQ_Parameter[RQ_Parameter_Name = 'MEM_FREE']/RQ_Parameter_Value")[0].text},
            )
        # end if
        if playback_type in ["NOMINAL", "REGULAR", "NRT"]:
            parameters.append(
                {"name": "SCN_DUP",
                 "type": "double",
                 "value": playback_type_stop_operation.xpath("RQ/List_of_RQ_Parameters/RQ_Parameter[RQ_Parameter_Name = 'SCN_DUP']/RQ_Parameter_Value")[0].text},
            )
            parameters.append(
                {"name": "SCN_RWD",
                 "type": "double",
                 "value": playback_type_stop_operation.xpath("RQ/List_of_RQ_Parameters/RQ_Parameter[RQ_Parameter_Name = 'SCN_RWD']/RQ_Parameter_Value")[0].text},
            )
        # end if
        if playback_type == "RT":
            parameters.append(
                {"name": "SCN_DUP_START",
                 "type": "double",
                 "value": playback_type_start_operation.xpath("RQ/List_of_RQ_Parameters/RQ_Parameter[RQ_Parameter_Name = 'SCN_DUP']/RQ_Parameter_Value")[0].text},
            )
            parameters.append(
                {"name": "SCN_DUP_STOP",
                 "type": "double",
                 "value": playback_type_stop_operation.xpath("RQ/List_of_RQ_Parameters/RQ_Parameter[RQ_Parameter_Name = 'SCN_DUP']/RQ_Parameter_Value")[0].text},
            )
            parameters.append(
                {"name": "SCN_RWD",
                 "type": "double",
                 "value": playback_type_stop_operation.xpath("RQ/List_of_RQ_Parameters/RQ_Parameter[RQ_Parameter_Name = 'SCN_RWD']/RQ_Parameter_Value")[0].text},
            )
        # end if

        # Insert playback_type_event
        ingestion_functions.insert_event_for_ingestion(playback_type_event, source, list_of_events)

    # end for

    return

@debug
def _correct_planning_events(orbpre_events, planning_events, list_of_completeness_events):
    """
    Method to correct the planning events following Berthyl's algorithm
    """

    start_orbpre_infos = {}
    next_start_orbpre_infos = {}
    stop_orbpre_infos = {}
    next_stop_orbpre_infos = {}
    corrected_planning_events = []
    for planning_event in planning_events:
        satellite = planning_event["gauge"]["system"]
        start_orbit = int([obj["value"] for obj in planning_event["values"] if obj["name"] == "start_orbit"][0])
        stop_orbit = [obj["value"] for obj in planning_event["values"] if obj["name"] == "stop_orbit"]
        start_angle = float([obj["value"] for obj in planning_event["values"] if obj["name"] == "start_angle"][0])
        stop_angle = [obj["value"] for obj in planning_event["values"] if obj["name"] == "stop_angle"]

        if len(stop_orbit) == 0:
            stop_orbit = start_orbit
        else:
            stop_orbit = int(stop_orbit[0])
        # end if

        if len(stop_angle) == 0:
            stop_angle = start_angle
        else:
            stop_angle = float(stop_angle[0])
        # end if

        # Get predicted orbit information
        if not start_orbit in start_orbpre_infos:
            start_orbpre_infos[start_orbit] = [event for event in orbpre_events for value in event.eventDoubles if value.name == "orbit" and int(value.value) == int(start_orbit)]
        # end if
        if not start_orbit in next_start_orbpre_infos:
            next_start_orbpre_infos[start_orbit] = [event for event in orbpre_events for value in event.eventDoubles if value.name == "orbit" and int(value.value) == int(start_orbit) + 1]
        # end if
        if not stop_orbit in stop_orbpre_infos:
            stop_orbpre_infos[stop_orbit] = [event for event in orbpre_events for value in event.eventDoubles if value.name == "orbit" and int(value.value) == int(stop_orbit)]
        # end if
        if not stop_orbit in next_stop_orbpre_infos:
            next_stop_orbpre_infos[stop_orbit] = [event for event in orbpre_events for value in event.eventDoubles if value.name == "orbit" and int(value.value) == int(stop_orbit) + 1]
        # end if

        if len(next_start_orbpre_infos[start_orbit]) == 0 or len(next_stop_orbpre_infos[stop_orbit]) == 0:
            status = "TIME_NOT_CORRECTED"
            corrected_start = parser.parse(planning_event["start"])
            corrected_stop = parser.parse(planning_event["stop"])
        else:
            status = "TIME_CORRECTED"
            start_orbital_period = (next_start_orbpre_infos[start_orbit][0].start - start_orbpre_infos[start_orbit][0].start).total_seconds()
            stop_orbital_period = (next_stop_orbpre_infos[stop_orbit][0].start - stop_orbpre_infos[stop_orbit][0].start).total_seconds()
            corrected_start = get_date_from_angle(start_angle, start_orbital_period, start_orbpre_infos[start_orbit][0].start.isoformat())
            corrected_stop = get_date_from_angle(stop_angle, stop_orbital_period, stop_orbpre_infos[stop_orbit][0].start.isoformat())

        # end if

        planning_event_values = planning_event["values"] + [
            {"name": "status_correction",
             "type": "text",
             "value": status},
            {"name": "delta_start",
             "type": "double",
             "value": str((parser.parse(planning_event["start"]) - corrected_start).total_seconds())},
            {"name": "delta_stop",
             "type": "double",
             "value": str((parser.parse(planning_event["stop"]) - corrected_stop).total_seconds())}
        ]

        corrected_planning_event = {
            "gauge": {
                "insertion_type": "INSERT_and_ERASE",
                "name": planning_event["gauge"]["name"] + "_CORRECTION",
                "system": planning_event["gauge"]["system"]
            },
            "links": [{
                "link": planning_event["link_ref"],
                "link_mode": "by_ref",
                "name": "TIME_CORRECTION",
                "back_ref": "PLANNED_EVENT"
            }],
            "start": corrected_start.isoformat(),
            "stop": corrected_stop.isoformat(),
            "values": planning_event_values
        }

        corrected_planning_events.append(corrected_planning_event)

        # Build completeness events
        completeness_event_values = planning_event_values + [
            {"name": "status",
             "type": "text",
             "value": "MISSING"}]
        if planning_event["gauge"]["name"] == "PLANNED_PLAYBACK":
            downlink_mode = [value["value"] for value in planning_event["values"] if value["name"] == "playback_type"][0]
            if downlink_mode == "SAD" or downlink_mode == "HKTM_SAD":
                start = corrected_start + datetime.timedelta(seconds=2)
                stop = start
            elif downlink_mode == "HKTM":
                # HKTM
                start = corrected_start + datetime.timedelta(seconds=2)
                stop = start
            else:
                start = corrected_start + datetime.timedelta(seconds=9)
                stop = corrected_stop - datetime.timedelta(seconds=9)
            # end if

            if start > stop:
                start = corrected_stop - datetime.timedelta(seconds=4)
                stop = corrected_stop - datetime.timedelta(seconds=3)
            # end if

            # DFEP schedule completeness
            completeness_event = {
                "gauge": {
                    "insertion_type": "INSERT_and_ERASE_with_PRIORITY",
                    "name": "DFEP_SCHEDULE_COMPLETENESS",
                    "system": planning_event["gauge"]["system"]
                },
                "links": [{
                    "link": planning_event["link_ref"],
                    "link_mode": "by_ref",
                    "name": "DFEP_SCHEDULE_COMPLETENESS",
                    "back_ref": "PLANNED_PLAYBACK"
                }],
                "start": start.isoformat(),
                "stop": stop.isoformat(),
                "values": completeness_event_values
            }
            list_of_completeness_events.append(completeness_event)

            # Station schedule completeness
            completeness_event = {
                "gauge": {
                    "insertion_type": "INSERT_and_ERASE_with_PRIORITY",
                    "name": "STATION_SCHEDULE_COMPLETENESS",
                    "system": planning_event["gauge"]["system"]
                },
                "links": [{
                    "link": planning_event["link_ref"],
                    "link_mode": "by_ref",
                    "name": "STATION_SCHEDULE_COMPLETENESS",
                    "back_ref": "PLANNED_PLAYBACK"
                }],
                "start": start.isoformat(),
                "stop": stop.isoformat(),
                "values": completeness_event_values
            }
            list_of_completeness_events.append(completeness_event)

            if downlink_mode != "SAD":
                completeness_event = {
                    "gauge": {
                        "insertion_type": "INSERT_and_ERASE_with_PRIORITY",
                        "name": "PLANNED_PLAYBACK_COMPLETENESS_CHANNEL_1",
                        "system": planning_event["gauge"]["system"]
                    },
                    "links": [{
                        "link": planning_event["link_ref"],
                        "link_mode": "by_ref",
                        "name": "PLAYBACK_COMPLETENESS",
                        "back_ref": "PLANNED_PLAYBACK"
                    }],
                    "start": start.isoformat(),
                    "stop": stop.isoformat(),
                    "values": completeness_event_values
                }
                list_of_completeness_events.append(completeness_event)
            # end if
            if downlink_mode != "HKTM":
                completeness_event = {
                    "gauge": {
                        "insertion_type": "INSERT_and_ERASE_with_PRIORITY",
                        "name": "PLANNED_PLAYBACK_COMPLETENESS_CHANNEL_2",
                        "system": planning_event["gauge"]["system"]
                    },
                    "links": [{
                        "link": planning_event["link_ref"],
                        "link_mode": "by_ref",
                        "name": "PLAYBACK_COMPLETENESS",
                        "back_ref": "PLANNED_PLAYBACK"
                    }],
                    "start": start.isoformat(),
                    "stop": stop.isoformat(),
                    "values": completeness_event_values
                }
                list_of_completeness_events.append(completeness_event)
            # end if
        elif planning_event["gauge"]["name"] == "PLANNED_CUT_IMAGING":

            start = corrected_start + datetime.timedelta(seconds=10)
            stop = corrected_stop - datetime.timedelta(seconds=10)

            if start > stop:
                start = corrected_stop - datetime.timedelta(seconds=12)
                stop = corrected_stop - datetime.timedelta(seconds=6)
            # end if
            
            completeness_event = {
                "gauge": {
                    "insertion_type": "INSERT_and_ERASE_with_PRIORITY",
                    "name": "PLANNED_IMAGING_ISP_COMPLETENESS_CHANNEL_1",
                    "system": planning_event["gauge"]["system"]
                },
                "links": [{
                    "link": planning_event["link_ref"],
                    "link_mode": "by_ref",
                    "name": "ISP_COMPLETENESS",
                    "back_ref": "PLANNED_IMAGING"
                }],
                "start": start.isoformat(),
                "stop": stop.isoformat(),
                "values": completeness_event_values
            }
            list_of_completeness_events.append(completeness_event)
            completeness_event = {
                "gauge": {
                    "insertion_type": "INSERT_and_ERASE_with_PRIORITY",
                    "name": "PLANNED_IMAGING_ISP_COMPLETENESS_CHANNEL_2",
                    "system": planning_event["gauge"]["system"]
                },
                "links": [{
                    "link": planning_event["link_ref"],
                    "link_mode": "by_ref",
                    "name": "ISP_COMPLETENESS",
                    "back_ref": "PLANNED_IMAGING"
                }],
                "start": start.isoformat(),
                "stop": stop.isoformat(),
                "values": completeness_event_values
            }
            list_of_completeness_events.append(completeness_event)

            imaging_mode = [value["value"] for value in planning_event["values"] if value["name"] == "imaging_mode"][0]
            completeness_event = {
                "gauge": {
                    "insertion_type": "INSERT_and_ERASE_with_PRIORITY",
                    "name": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L0",
                    "system": planning_event["gauge"]["system"]
                },
                "links": [{
                    "link": planning_event["link_ref"],
                    "link_mode": "by_ref",
                    "name": "PROCESSING_COMPLETENESS",
                    "back_ref": "PLANNED_IMAGING"
                }],
                "start": start.isoformat(),
                "stop": stop.isoformat(),
                "values": completeness_event_values
            }
            list_of_completeness_events.append(completeness_event)
            completeness_event = {
                "gauge": {
                    "insertion_type": "INSERT_and_ERASE_with_PRIORITY",
                    "name": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L1B",
                    "system": planning_event["gauge"]["system"]
                },
                "links": [{
                    "link": planning_event["link_ref"],
                    "link_mode": "by_ref",
                    "name": "PROCESSING_COMPLETENESS",
                    "back_ref": "PLANNED_IMAGING"
                }],
                "start": start.isoformat(),
                "stop": stop.isoformat(),
                "values": completeness_event_values
            }
            list_of_completeness_events.append(completeness_event)
            if imaging_mode in ["SUN_CAL", "DARK_CAL_CSM_OPEN", "DARK_CAL_CSM_CLOSE", "VICARIOUS_CAL", "RAW", "TEST"]:
                completeness_event = {
                    "gauge": {
                        "insertion_type": "INSERT_and_ERASE_with_PRIORITY",
                        "name": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L1A",
                        "system": planning_event["gauge"]["system"]
                    },
                    "links": [{
                        "link": planning_event["link_ref"],
                        "link_mode": "by_ref",
                        "name": "PROCESSING_COMPLETENESS",
                        "back_ref": "PLANNED_IMAGING"
                    }],
                    "start": start.isoformat(),
                    "stop": stop.isoformat(),
                    "values": completeness_event_values
                }
                list_of_completeness_events.append(completeness_event)
            # end if
            if imaging_mode in ["NOMINAL", "VICARIOUS_CAL", "TEST"]:
                completeness_event = {
                    "gauge": {
                        "insertion_type": "INSERT_and_ERASE_with_PRIORITY",
                        "name": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L1C",
                        "system": planning_event["gauge"]["system"]
                    },
                    "links": [{
                        "link": planning_event["link_ref"],
                        "link_mode": "by_ref",
                        "name": "PROCESSING_COMPLETENESS",
                        "back_ref": "PLANNED_IMAGING"
                    }],
                    "start": start.isoformat(),
                    "stop": stop.isoformat(),
                    "values": completeness_event_values
                }
                list_of_completeness_events.append(completeness_event)
            # end if
            if imaging_mode in ["NOMINAL"]:
                completeness_event = {
                    "gauge": {
                        "insertion_type": "INSERT_and_ERASE_with_PRIORITY",
                        "name": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L2A",
                        "system": planning_event["gauge"]["system"]
                    },
                    "links": [{
                        "link": planning_event["link_ref"],
                        "link_mode": "by_ref",
                        "name": "PROCESSING_COMPLETENESS",
                        "back_ref": "PLANNED_IMAGING"
                    }],
                    "start": start.isoformat(),
                    "stop": stop.isoformat(),
                    "values": completeness_event_values
                }
                list_of_completeness_events.append(completeness_event)
            # end if
            
        # end if
        
    # end for

    return corrected_planning_events

@debug
def _associate_acquisition_schedules(acquisition_schedule_events, planned_playbacks, planned_playback_means):
    """
    Method to associate the acquisition schedule events to the plan
    """
    station_schedule_events = [event for event in acquisition_schedule_events if event.gauge.name == "STATION_SCHEDULE"]
    dfep_schedule_events = [event for event in acquisition_schedule_events if event.gauge.name == "DFEP_SCHEDULE"]
    station_schedule_completeness_events = [event for event in acquisition_schedule_events if event.gauge.name == "STATION_SCHEDULE_COMPLETENESS"]
    dfep_schedule_completeness_events = [event for event in acquisition_schedule_events if event.gauge.name == "DFEP_SCHEDULE_COMPLETENESS"]
    sra_events = [event for event in acquisition_schedule_events if event.gauge.name == "SLOT_REQUEST_EDRS"]
    for planned_playback in planned_playbacks:
        planned_playback_mean_ref = [link["link"] for link in planned_playback["links"] if link["back_ref"] == "PLANNED_PLAYBACK_MEAN"][0]
        planned_playback_mean = [planned_playback_mean for planned_playback_mean in planned_playback_means if planned_playback_mean["link_ref"] == planned_playback_mean_ref][0]

        mean = [value["value"] for value in planned_playback_mean["values"] if value["name"] == "playback_mean"][0]

        station_schedule_completeness_event = [event for event in station_schedule_completeness_events for value in event.eventTexts if value.name == "playback_mean" and value.value == mean and parser.parse(planned_playback["start"]) < event.stop and parser.parse(planned_playback["stop"]) > event.start]
        if len(station_schedule_completeness_event) > 0:
            planned_playback["links"].append({
                "link": str(station_schedule_completeness_event[0].event_uuid),
                "link_mode": "by_uuid",
                "name": "PLANNED_PLAYBACK",
                "back_ref": "STATION_SCHEDULE_COMPLETENESS"
            })
        # end if

        dfep_schedule_completeness_event = [event for event in dfep_schedule_completeness_events for value in event.eventTexts if value.name == "playback_mean" and value.value == mean and parser.parse(planned_playback["start"]) < event.stop and parser.parse(planned_playback["stop"]) > event.start]
        if len(dfep_schedule_completeness_event) > 0:
            planned_playback["links"].append({
                "link": str(dfep_schedule_completeness_event[0].event_uuid),
                "link_mode": "by_uuid",
                "name": "PLANNED_PLAYBACK",
                "back_ref": "DFEP_SCHEDULE_COMPLETENESS"
            })
        # end if

        station = None
        if mean == "OCP":
            sra_event = [event for event in sra_events if parser.parse(planned_playback["start"]) < event.stop and parser.parse(planned_playback["stop"]) > event.start]
            if len(sra_event) > 0:
                planned_playback["links"].append({
                    "link": str(sra_event[0].event_uuid),
                    "link_mode": "by_uuid",
                    "name": "PLANNED_PLAYBACK",
                    "back_ref": "SLOT_REQUEST_EDRS"
                })
                station = "EDRS"
            # end if
        else:
            station_schedule_event = [event for event in station_schedule_events if parser.parse(planned_playback["start"]) < event.stop and parser.parse(planned_playback["stop"]) > event.start]
            if len(station_schedule_event) > 0:
                planned_playback["links"].append({
                    "link": str(station_schedule_event[0].event_uuid),
                    "link_mode": "by_uuid",
                    "name": "PLANNED_PLAYBACK",
                    "back_ref": "STATION_SCHEDULE"
                })
                station = [value.value for value in station_schedule_event[0].eventTexts if value.name == "station"][0]
            # end if

            dfep_schedule_event = [event for event in dfep_schedule_events if parser.parse(planned_playback["start"]) < event.stop and parser.parse(planned_playback["stop"]) > event.start]
            if len(dfep_schedule_event) > 0:
                planned_playback["links"].append({
                    "link": str(dfep_schedule_event[0].event_uuid),
                    "link_mode": "by_uuid",
                    "name": "PLANNED_PLAYBACK",
                    "back_ref": "DFEP_SCHEDULE"
                })
                station = [value.value for value in dfep_schedule_event[0].eventTexts if value.name == "station"][0]
            # end if
        # end if

        # Associate station to the values of the planned playback
        if station:
            planned_playback["values"].append({
                "name": "station_schedule",
                "type": "object",
                "values": [{"name": "station",
                            "type": "text",
                            "value": station}]
            })
            planned_playback["values"].append({
                "name": "dfep_schedule",
                "type": "object",
                "values": [{"name": "station",
                            "type": "text",
                            "value": station}]
            })
        # end if
        
    # end for

def process_file(file_path, engine, query, reception_time, tgz_filename = None):
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
    if tgz_filename != None:
        file_name = tgz_filename
    else:
        file_name = os.path.basename(file_path)
    # end if
    parsed_xml = etree.parse(file_path)
    xpath_xml = etree.XPathEvaluator(parsed_xml)

    satellite = file_name[0:3]
    reported_generation_time = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Source/Creation_Date")[0].text.split("=")[1]    
    reported_validity_start = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Validity_Period/Validity_Start")[0].text.split("=")[1]
    validity_stop = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Validity_Period/Validity_Stop")[0].text.split("=")[1]
    deletion_queue = xpath_xml("/Earth_Explorer_File/Data_Block/List_of_EVRQs/EVRQ[RQ/RQ_Name='MGSYQDEL']")

    # Generation time is changed to be the validity start in case the generation time is greater than the validity start to avoid problems on completeness analysis
    generation_time = reported_generation_time
    if reported_generation_time > reported_validity_start:
        generation_time = reported_validity_start
    # end if

    validity_start = reported_validity_start
    if len(deletion_queue) == 1:
        validity_start = deletion_queue[0].xpath("RQ/RQ_Execution_Time")[0].text.split("=")[1]
    # end if

    source = {
        "name": file_name,
        "reception_time": reception_time,
        "generation_time": generation_time,
        "reported_generation_time": reported_generation_time,
        "validity_start": validity_start,
        "reported_validity_start": reported_validity_start,
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
    
    # Generate record events
    _generate_record_events(xpath_xml, source, list_of_events)

    functions.insert_ingestion_progress(session_progress, general_source_progress, 40)

    # Generate playback events
    _generate_playback_events(xpath_xml, source, list_of_events)

    functions.insert_ingestion_progress(session_progress, general_source_progress, 70)

    # Generate idle events
    _generate_idle_events(xpath_xml, source, list_of_events)

    functions.insert_ingestion_progress(session_progress, general_source_progress, 95)

    ###
    # Generate corrected events
    ###
    # Get orbit period covered by the NPPF
    start_orbits = [value["value"] for event in list_of_events for value in event["values"] if value["name"] == "start_orbit"]
    start_orbits.sort(key=lambda x: x)
    stop_orbits = [value["value"] for event in list_of_events for value in event["values"] if value["name"] == "stop_orbit"]
    stop_orbits.sort(key=lambda x: x)

    # Get orbpre events
    orbpre_events = []
    if len(start_orbits) > 0:
        orbpre_events = query.get_events(gauge_names = {"filter": "ORBIT_PREDICTION", "op": "=="},
                                         gauge_systems = {"filter": satellite, "op": "=="},
                                         value_filters = [{"name": {"filter": "orbit", "op": "=="},
                                                           "type": "double",
                                                           "value": {"filter": str(int(start_orbits[0]) - 1), "op": ">="}},
                                                          {"name": {"filter": "orbit", "op": "=="},
                                                           "type": "double",
                                                           "value": {"filter": str(int(stop_orbits[-1]) + 1), "op": "<="}}],
                                         order_by = {"field": "start", "descending": False})
    # end if

    list_of_corrected_events = []
    list_of_completeness_events = []
    if len(orbpre_events) > 0:
        first_orbit_orbpre_events = [value.value for value in orbpre_events[0].eventDoubles if value.name == "orbit"]
        last_orbit_orbpre_events = [value.value for value in orbpre_events[-1].eventDoubles if value.name == "orbit"]

        planning_events_covered_by_orbpre = []
        for event in list_of_events:
            start_orbit = [value["value"] for value in event["values"] if value["name"] == "start_orbit"]
            stop_orbit = [value["value"] for value in event["values"] if value["name"] == "stop_orbit"]
            if int(start_orbit[0]) >= int(first_orbit_orbpre_events[0]) and int(stop_orbit[0]) <= int(last_orbit_orbpre_events[0]):
                planning_events_covered_by_orbpre.append(event)
            # end if
        # end for

        list_of_corrected_events = _correct_planning_events(orbpre_events, planning_events_covered_by_orbpre, list_of_completeness_events)
    # end if

    ###
    # Generate acquisition schedule events
    ###
    # Get acquisition schedule events
    acquisition_schedule_events =  query.get_events(gauge_names = {"filter": ["STATION_SCHEDULE", "DFEP_SCHEDULE", "STATION_SCHEDULE_COMPLETENESS", "DFEP_SCHEDULE_COMPLETENESS", "SLOT_REQUEST_EDRS"], "op": "in"},
                                                    gauge_systems = {"filter": satellite, "op": "=="},
                                                    start_filters = [{"date": validity_start, "op": ">"}],
                                                    stop_filters = [{"date": validity_stop, "op": "<"}],
                                                    order_by = {"field": "start", "descending": False})
    if len(acquisition_schedule_events) > 0:

        planned_playbacks_covered_by_schedule = [event for event in list_of_events if event["gauge"]["name"] == "PLANNED_PLAYBACK" and parser.parse(event["start"]) < acquisition_schedule_events[0].stop and parser.parse(event["stop"]) > acquisition_schedule_events[-1].start]
        planned_playback_means_covered_by_schedule = [event for event in list_of_events if event["gauge"]["name"] == "PLANNED_PLAYBACK_MEAN" and parser.parse(event["start"]) < acquisition_schedule_events[0].stop and parser.parse(event["stop"]) > acquisition_schedule_events[-1].start]

        _associate_acquisition_schedules(acquisition_schedule_events, planned_playbacks_covered_by_schedule, planned_playback_means_covered_by_schedule)
    # end if
    
    # Build the xml
    data = {"operations": [{
        "mode": "insert_and_erase",
        "dim_signature": {
            "name": "NPPF_" + satellite,
            "exec": os.path.basename(__file__),
            "version": version
        },
        "source": source,
        "events": list_of_events
    }]}

    if len(list_of_corrected_events) > 0:
        # Generate the footprint of the events
        list_of_corrected_events_with_footprint = functions.associate_footprints(list_of_corrected_events, satellite)

        data["operations"].append({
            "mode": "insert_and_erase",
            "dim_signature": {
                "name": "CORRECTED_NPPF_" + satellite,
                "exec": os.path.basename(__file__),
                "version": version
            },
            "source": source,
            "events": list_of_corrected_events_with_footprint
        })
    # end if

    if len(list_of_completeness_events) > 0:
        # Generate the footprint of the events
        list_of_completeness_events_with_footprint = functions.associate_footprints(list_of_completeness_events, satellite)

        source_with_priority = source.copy()
        source_with_priority["priority"] = 10

        data["operations"].append({
            "mode": "insert",
            "dim_signature": {
                "name": "COMPLETENESS_NPPF_" + satellite,
                "exec": os.path.basename(__file__),
                "version": version
            },
            "source": source_with_priority,
            "events": list_of_completeness_events_with_footprint
        })
    # end if

    functions.insert_ingestion_progress(session_progress, general_source_progress, 100)

    query.close_session()
    
    return data
