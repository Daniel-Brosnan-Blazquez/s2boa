"""
Ingestion module for the TLM_REQ_B files of Sentinel-2

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

# Event values
def define_telemetry_values(satellite, value):
    telemetry_values = [
    {
        "name": "satellite",
        "type": "text",
        "value": satellite
    },
    {
        "name": "number_of_scenes",
        "type": "double",
        "value": value
    }]
    return telemetry_values

# Memory occupation events
def memory_occupation_events(xpath_xml, list_of_events, satellite, parameter_name): 
    telemetry_values_list = xpath_xml("/Earth_Explorer_File/ResponsePart/Response/ParamResponse/ParamSampleList/ParamSampleListElement")
    if parameter_name == 'MST00058':
        gauge_name = "NOMINAL_MEMORY_OCCUPATION"
    # end if
    if parameter_name == 'MST00059':
        gauge_name = "NRT_MEMORY_OCCUPATION"
    # end if
    if parameter_name == 'MST00192':
        gauge_name = "LAST_REPLAYED_SCENE"
    # end if
         
    first_time = True
    for telemetry_value in telemetry_values_list:
        if telemetry_value.xpath("Name")[0].text == parameter_name:
            if first_time:
                engineering_value = telemetry_value.xpath("EngineeringValue")[0].text
                event_start = telemetry_value.xpath("TimeStampAsciiA")[0].text
                telemetry_values = define_telemetry_values(satellite, engineering_value)
                first_time = False
            # end if
            if int(telemetry_value.xpath("EngineeringValue")[0].text) != int(engineering_value):
                event_stop = telemetry_value.xpath("TimeStampAsciiA")[0].text
                memory_occupation_event = {
                "gauge": {
                    "name": gauge_name,
                    "system": satellite,
                    "insertion_type": "INSERT_and_ERASE"
                },
                "values": telemetry_values,
                "start": event_start,
                "stop": event_stop
                }
                list_of_events.append(memory_occupation_event)
                engineering_value = telemetry_value.xpath("EngineeringValue")[0].text
                event_start = telemetry_value.xpath("TimeStampAsciiA")[0].text
                telemetry_values = define_telemetry_values(satellite, engineering_value)
            # end if
        # end if
    # end loop
    event_stop = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Validity_Period/Validity_Stop")[0].text.split("=")[1]
    memory_occupation_event = {
        "gauge": {
            "name": gauge_name,
            "system": satellite,
            "insertion_type": "INSERT_and_ERASE"
        },
        "values": telemetry_values,
        "start": event_start,
        "stop": event_stop
        }
    list_of_events.append(memory_occupation_event)

# Discrepancy events
def discrepancy_events(xpath_xml, list_of_events, satellite, parameter_name_1, parameter_name_2):
    list_of_engineering_values = []
    telemetry_values_list = xpath_xml("/Earth_Explorer_File/ResponsePart/Response/ParamResponse/ParamSampleList/ParamSampleListElement")
    if parameter_name_2 == 'MST00202':
        gauge_name = "DISCREPANCY_CHANNEL_2_NOMINAL_MEMORY_OCCUPATION"
    # end if
    if parameter_name_2 == 'MST00203':
        gauge_name = "DISCREPANCY_CHANNEL_2_NRT_MEMORY_OCCUPATION"
    # end if
    if parameter_name_2 == 'MST00205':
        gauge_name = "DISCREPANCY_CHANNEL_2_LAST_REPLAYED_SCENE"
    # end if
    for telemetry_value in telemetry_values_list:
        if telemetry_value.xpath("Name")[0].text == parameter_name_1:
            list_of_engineering_values.append(telemetry_value.xpath("EngineeringValue")[0].text)
        # end if
    # end for
    
    i = 0
    for telemetry_value in telemetry_values_list: 
        if telemetry_value.xpath("Name")[0].text == parameter_name_2:
            if int(telemetry_value.xpath("EngineeringValue")[0].text) != int(list_of_engineering_values[i]):
                event_start = telemetry_value.xpath("TimeStampAsciiA")[0].text
                event_stop = telemetry_value.xpath("TimeStampAsciiA")[0].text
                discrepancy_value = int(list_of_engineering_values[i]) - int(telemetry_value.xpath("EngineeringValue")[0].text)
                telemetry_values = define_telemetry_values(satellite, discrepancy_value)
                discrepancy_event = {
                    "gauge": {
                        "name": gauge_name,
                        "system": satellite,
                        "insertion_type": "INSERT_and_ERASE"
                    },
                    "values": telemetry_values,
                    "start": event_start,
                    "stop": event_stop
                }
                list_of_events.append(discrepancy_event)
            # end if
            i += 1
        # end if
    # end for

# Memory gap events
def gap_events(xpath_xml, list_of_events, satellite, parameter_name): 
    telemetry_values_list = xpath_xml("/Earth_Explorer_File/ResponsePart/Response/ParamResponse/ParamSampleList/ParamSampleListElement")
    if parameter_name == 'MST00058':
        gauge_name = "NOMINAL_MEMORY_OCCUPATION_CHANNEL_1_GAP"
    # end if
    if parameter_name == 'MST00202':
        gauge_name = "NOMINAL_MEMORY_OCCUPATION_CHANNEL_2_GAP"
    # end if
    if parameter_name == 'MST00059':
        gauge_name = "NRT_MEMORY_OCCUPATION_CHANNEL_1_GAP"
    # end if
    if parameter_name == 'MST00203':
        gauge_name = "NRT_MEMORY_OCCUPATION_CHANNEL_2_GAP"
    # end if
    if parameter_name == 'MST00192':
        gauge_name = "LAST_REPLAYED_SCENE_CHANNEL_1_GAP"
    # end if
    if parameter_name == 'MST00205':
        gauge_name = "LAST_REPLAYED_SCENE_CHANNEL_2_GAP"
    # end if
    first_time = True
    for telemetry_value in telemetry_values_list:
        if telemetry_value.xpath("Name")[0].text == parameter_name:
            if first_time:
                previous_time = telemetry_value.xpath("TimeStampAsciiA")[0].text
                first_time = False
            # end if
            current_time = telemetry_value.xpath("TimeStampAsciiA")[0].text
            time_start = datetime.datetime.strptime(previous_time, '%Y-%m-%dT%H:%M:%S.%f')
            time_stop = datetime.datetime.strptime(current_time, '%Y-%m-%dT%H:%M:%S.%f')
            diff_time = time_stop - time_start
            if diff_time.total_seconds() > 6.0:
                telemetry_values = [
                    {
                        "name": "satellite",
                        "type": "text",
                        "value": satellite
                    }
                ]
                gap_event = {
                    "gauge": {
                        "name": gauge_name,
                        "system": satellite,
                        "insertion_type": "INSERT_and_ERASE"
                    },
                    "values": telemetry_values,
                    "start": previous_time,
                    "stop": current_time
                }
                list_of_events.append(gap_event)
            # end if
            previous_time = current_time
    # end loop


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
    file_name = os.path.basename(file_path)

    # Remove namespaces
    new_file = tempfile.NamedTemporaryFile()
    new_file_path = new_file.name

    ingestion_functions.remove_namespaces(file_path, new_file_path)

    # Parse file
    parsed_xml = etree.parse(new_file_path)
    xpath_xml = etree.XPathEvaluator(parsed_xml)

    list_of_annotations = []
    list_of_events = []

    # Obtain the satellite
    satellite = file_name[0:3]
    
    # Obtain validity period
    validity_start = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Validity_Period/Validity_Start")[0].text.split("=")[1]
    validity_stop = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Validity_Period/Validity_Stop")[0].text.split("=")[1]
    # Obtain the generation_date
    generation_date = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Source/Creation_Date")[0].text.split("=")[1]

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

    # add events
    # add nominal memory occupation events
    memory_occupation_events(xpath_xml, list_of_events, satellite, 'MST00058')

    functions.insert_ingestion_progress(session_progress, general_source_progress, 20)

    # add nominal memory occupation discrepancy events
    discrepancy_events(xpath_xml, list_of_events, satellite, 'MST00058', 'MST00202')
    
    functions.insert_ingestion_progress(session_progress, general_source_progress, 40)

    # add ntr memory occupation events
    memory_occupation_events(xpath_xml, list_of_events, satellite, 'MST00059')

    functions.insert_ingestion_progress(session_progress, general_source_progress, 50)

    # add nrt memory occupation discrepancy events
    discrepancy_events(xpath_xml, list_of_events, satellite, 'MST00059', 'MST00203')

    functions.insert_ingestion_progress(session_progress, general_source_progress, 60)

    # add last replayed scene events
    memory_occupation_events(xpath_xml, list_of_events, satellite, 'MST00192')

    functions.insert_ingestion_progress(session_progress, general_source_progress, 70)

    # add last replayed scene discrepancy events
    discrepancy_events(xpath_xml, list_of_events, satellite, 'MST00192', 'MST00205')


    functions.insert_ingestion_progress(session_progress, general_source_progress, 80)

    # add nominal memory occupation for channel 1 gap events
    gap_events(xpath_xml, list_of_events, satellite, 'MST00058')
    # add nominal memory occupation for channel 2 gap events
    gap_events(xpath_xml, list_of_events, satellite, 'MST00059')
    # add nrt memory occupation for channel 1 gap events
    gap_events(xpath_xml, list_of_events, satellite, 'MST00202')
    # add nrt memory occupation for channel 1 gap events
    gap_events(xpath_xml, list_of_events, satellite, 'MST00203')
    # add last replayed scene for channel 1 gap events
    gap_events(xpath_xml, list_of_events, satellite, 'MST00192')
    # add last replayed scene for channel 2 gap events
    gap_events(xpath_xml, list_of_events, satellite, 'MST00205')


    data = {"operations": [{
                "mode": "insert_and_erase",
                "dim_signature": {
                    "name": "MEMORY_EVOLUTION_" + satellite,
                    "exec": os.path.basename(__file__),
                    "version": "1.0"
                },
            "source": {
                 "name": file_name,
                 "reception_time": reception_time,
                 "generation_time": generation_date,
                 "validity_start": validity_start,
                 "validity_stop": validity_stop,
            },
            "annotations": list_of_annotations,
            "events": list_of_events
            }]}
    
    functions.insert_ingestion_progress(session_progress, general_source_progress, 100)
    query.close_session()
    return data
