"""
Ingestion module for the ORBPRE files of Sentinel-2

Written by DEIMOS Space S.L. (dibb)

module eboa
"""
# Import python utilities
import os
import argparse
from dateutil import parser
import datetime
import tempfile
import json
import math

# Import xml parser
from lxml import etree, objectify

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

def _get_date_from_angle(angle, orbital_period, ascending_node_time):
    """
    """
    sin1 = math.sin(math.radians(angle))
    sin2 = math.sin(math.radians(2*angle))
    cos1 = math.cos(math.radians(angle))
    cos2 = math.cos(math.radians(2*angle))
    cos3 = math.cos(math.radians(3*angle))
    mean_ops = angle - 0.13175612 - 2*(-0.0001529)*sin1 - 2*(-0.0660818)*cos1 - 2*0.16855853*sin2 - 2*(-0.0007759)*cos2 - 2*0.0009872*cos3 - 2*0.00687159*sin2
    seconds_angle = (mean_ops * orbital_period) / 360.0

    return parser.parse(ascending_node_time) + datetime.timedelta(seconds=seconds_angle)

@debug
def _correct_planning_events(orbpre_events, planning_events):
    """
    Method to correct the planning events following Berthyl's algorithm
    """
    start_orbpre_infos = {}
    next_start_orbpre_infos = {}
    stop_orbpre_infos = {}
    next_stop_orbpre_infos = {}
    corrected_planning_events = []
    for planning_event in planning_events:
        satellite = planning_event.gauge.system
        start_orbit = [obj.value for obj in planning_event.eventDoubles if obj.name == "start_orbit"][0]
        stop_orbit = [obj.value for obj in planning_event.eventDoubles if obj.name == "stop_orbit"]
        start_angle = [obj.value for obj in planning_event.eventDoubles if obj.name == "start_angle"][0]
        stop_angle = [obj.value for obj in planning_event.eventDoubles if obj.name == "stop_angle"]

        if len(stop_orbit) == 0:
            stop_orbit = start_orbit
        else:
            stop_orbit = stop_orbit[0]
        # end if

        if len(stop_angle) == 0:
            stop_angle = start_angle
        else:
            stop_angle = stop_angle[0]
        # end if

        # Get predicted orbit information
        if not start_orbit in start_orbpre_infos:
            start_orbpre_infos[start_orbit] = [event for event in orbpre_events for value in event["values"][0]["values"] if value["name"] == "orbit" and int(value["value"]) == int(start_orbit)]
        # end if
        if not start_orbit in next_start_orbpre_infos:
            next_start_orbpre_infos[start_orbit] = [event for event in orbpre_events for value in event["values"][0]["values"] if value["name"] == "orbit" and int(value["value"]) == int(start_orbit) + 1]
        # end if
        if not stop_orbit in stop_orbpre_infos:
            stop_orbpre_infos[stop_orbit] = [event for event in orbpre_events for value in event["values"][0]["values"] if value["name"] == "orbit" and int(value["value"]) == int(stop_orbit)]
        # end if
        if not stop_orbit in next_stop_orbpre_infos:
            next_stop_orbpre_infos[stop_orbit] = [event for event in orbpre_events for value in event["values"][0]["values"] if value["name"] == "orbit" and int(value["value"]) == int(stop_orbit) + 1]
        # end if

        if len(next_start_orbpre_infos[start_orbit]) == 0 or len(next_stop_orbpre_infos[stop_orbit]) == 0:
            status = "TIME_NOT_CORRECTED"
            corrected_start = planning_event.start
            corrected_stop = planning_event.stop
        else:
            status = "TIME_CORRECTED"
            start_orbital_period = (parser.parse(next_start_orbpre_infos[start_orbit][0]["start"]) - parser.parse(start_orbpre_infos[start_orbit][0]["start"])).total_seconds()
            stop_orbital_period = (parser.parse(next_stop_orbpre_infos[stop_orbit][0]["start"]) - parser.parse(stop_orbpre_infos[stop_orbit][0]["start"])).total_seconds()
            corrected_start = _get_date_from_angle(start_angle, start_orbital_period, start_orbpre_infos[start_orbit][0]["start"])
            corrected_stop = _get_date_from_angle(stop_angle, stop_orbital_period, stop_orbpre_infos[stop_orbit][0]["start"])

        # end if

        planning_event_values = planning_event.get_structured_values()

        planning_event_values[0]["values"] = planning_event_values[0]["values"] + [
            {"name": "status_correction",
             "type": "text",
             "value": status},
            {"name": "delta_start",
             "type": "double",
             "value": str((planning_event.start - corrected_start).total_seconds())},
            {"name": "delta_stop",
             "type": "double",
             "value": str((planning_event.stop - corrected_stop).total_seconds())}
        ]

        corrected_planning_event = {
            "gauge": {
                "insertion_type": "INSERT_and_ERASE",
                "name": planning_event.gauge.name + "_CORRECTION",
                "system": planning_event.gauge.system
            },
            "links": [{
                "link": str(planning_event.event_uuid),
                "link_mode": "by_uuid",
                "name": "TIME_CORRECTION",
                "back_ref": "PLANNED_EVENT"
            }],
            "start": corrected_start.isoformat(),
            "stop": corrected_stop.isoformat(),
            "values": planning_event_values
        }

        corrected_planning_events.append(corrected_planning_event)

    # end for

    return corrected_planning_events

@debug
def _generate_corrected_planning_events(satellite, start_orbit, stop_orbit, list_of_events, query):
    """
    """
    # Get planning events to correct their timings
    planning_gauges = query.get_gauges(dim_signatures = {"filter": ["NPPF_" + satellite], "op": "in"})

    planning_events = query.get_events(gauge_uuids = {"filter": [gauge.gauge_uuid for gauge in planning_gauges], "op": "in"},
                                       value_filters = [{"name": {"filter": "start_orbit", "op": "=="},
                                                         "type": "double",
                                                         "value": {"filter": start_orbit, "op": ">="}},
                                                        {"name": {"filter": "start_orbit", "op": "=="},
                                                         "type": "double",
                                                         "value": {"filter": stop_orbit, "op": "<="}}])

    planning_events = query.get_events(event_uuids = {"filter": [event.event_uuid for event in planning_events], "op": "in"},
                                       value_filters = [{"name": {"filter": "stop_orbit", "op": "=="},
                                                         "type": "double",
                                                         "value": {"filter": stop_orbit, "op": "<="}}])

    events = _correct_planning_events(list_of_events, planning_events)

    return events

@debug
def _generate_orbpre_events(xpath_xml, source, list_of_events):
    """
    Method to generate the events of the orbit predicted files

    :param xpath_xml: source of information that was xpath evaluated
    :type xpath_xml: XPathEvaluator
    :param source: information of the source
    :type xpath_xml: dict
    :param list_of_events: list to store the events to be inserted into the eboa
    :type list_of_events: list
    """

    satellite = source["name"][0:3]

    # Orbit predicted records
    orbpre_records = xpath_xml("/Earth_Explorer_File/Data_Block/List_of_OSVs/OSV")

    i = 0
    for orbpre_record in orbpre_records:
        # Orbit predicted information
        start = orbpre_record.xpath("UTC")[0].text.split("=")[1]
        if i+1 < len(orbpre_records):
            stop = orbpre_records[i+1].xpath("UTC")[0].text.split("=")[1]
        else:
            stop = start
        # end if
        i += 1

        tai = orbpre_record.xpath("TAI")[0].text.split("=")[1]
        ut1 = orbpre_record.xpath("UT1")[0].text.split("=")[1]
        orbit = int(orbpre_record.xpath("Absolute_Orbit")[0].text)
        x = orbpre_record.xpath("X")[0].text
        y = orbpre_record.xpath("Y")[0].text
        z = orbpre_record.xpath("Z")[0].text
        vx = orbpre_record.xpath("VX")[0].text
        vy = orbpre_record.xpath("VY")[0].text
        vz = orbpre_record.xpath("VZ")[0].text
        quality = orbpre_record.xpath("Quality")[0].text

        # Orbit predicted event
        orbpre_event = {
            "key": "ORBIT_PREDICTION-" + satellite + "-" + str(orbit),
            "gauge": {
                "insertion_type": "EVENT_KEYS",
                "name": "ORBIT_PREDICTION",
                "system": satellite
            },
            "start": start,
            "stop": stop,
            "values": [{
                "name": "orbit_information",
                "type": "object",
                "values": [
                    {"name": "tai",
                     "type": "timestamp",
                     "value": tai},
                    {"name": "ut1",
                     "type": "timestamp",
                     "value": ut1},
                    {"name": "orbit",
                     "type": "double",
                     "value": str(orbit)},
                    {"name": "x",
                     "type": "double",
                     "value": x},
                    {"name": "y",
                     "type": "double",
                     "value": y},
                    {"name": "z",
                     "type": "double",
                     "value": z},
                    {"name": "vx",
                     "type": "double",
                     "value": vx},
                    {"name": "vy",
                     "type": "double",
                     "value": vy},
                    {"name": "vz",
                     "type": "double",
                     "value": vz},
                    {"name": "satellite",
                     "type": "text",
                     "value": satellite},
                    {"name": "quality",
                     "type": "double",
                     "value": quality}
                ]
            }]
        }

        # Insert orbpre_event
        ingestion_functions.insert_event_for_ingestion(orbpre_event, source, list_of_events)

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
    validity_stop = (parser.parse(xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Validity_Period/Validity_Stop")[0].text.split("=")[1]) + datetime.timedelta(minutes=100)).isoformat()

    source = {
        "name": file_name,
        "reception_time": reception_time,
        "generation_time": generation_time,
        "validity_start": validity_start,
        "validity_stop": validity_stop
    }

    validity_start_corrected = xpath_xml("/Earth_Explorer_File/Data_Block/List_of_OSVs/OSV[1]/UTC")[0].text.split("=")[1]
    validity_stop_corrected = xpath_xml("/Earth_Explorer_File/Data_Block/List_of_OSVs/OSV[last()]/UTC")[0].text.split("=")[1]
    source_corrected = {
        "name": file_name,
        "reception_time": reception_time,
        "generation_time": generation_time,
        "validity_start": validity_start_corrected,
        "validity_stop": validity_stop_corrected
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

    # Generate orbit predicted events
    _generate_orbpre_events(xpath_xml, source, list_of_events)

    functions.insert_ingestion_progress(session_progress, general_source_progress, 30)
    
    start_orbit = str(int(xpath_xml("/Earth_Explorer_File/Data_Block/List_of_OSVs/OSV[1]/Absolute_Orbit")[0].text))
    stop_orbit = str(int(xpath_xml("/Earth_Explorer_File/Data_Block/List_of_OSVs/OSV[last() - 1]/Absolute_Orbit")[0].text))

    # Generate corrected planning events
    corrected_planning_events = _generate_corrected_planning_events(satellite, start_orbit, stop_orbit, list_of_events, query)

    functions.insert_ingestion_progress(session_progress, general_source_progress, 60)
    
    # Generate the footprint of the events
    corrected_planning_events_with_footprint = functions.associate_footprints(corrected_planning_events, satellite, list_of_events)

    functions.insert_ingestion_progress(session_progress, general_source_progress, 90)
    
    # Build the xml
    data = {"operations": [{
        "mode": "insert",
        "dim_signature": {
            "name": "ORBPRE",
            "exec": os.path.basename(__file__),
            "version": version
        },
        "source": source,
        "events": list_of_events
    },
    {
        "mode": "insert_and_erase",
        "dim_signature": {
            "name": "CORRECTED_NPPF_" + satellite,
            "exec": os.path.basename(__file__),
            "version": version
        },
        "source": source_corrected,
        "events": corrected_planning_events_with_footprint
    }]}

    functions.insert_ingestion_progress(session_progress, general_source_progress, 100)

    query.close_session()

    new_file.close()
    
    return data
