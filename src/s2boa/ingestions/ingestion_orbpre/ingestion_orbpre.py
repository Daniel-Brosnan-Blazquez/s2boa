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

def get_date_from_angle(angle, orbital_period, ascending_node_time):
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
            start_orbpre_infos[start_orbit] = [event for event in orbpre_events for value in event["values"] if value["name"] == "orbit" and int(value["value"]) == int(start_orbit)]
        # end if
        if not start_orbit in next_start_orbpre_infos:
            next_start_orbpre_infos[start_orbit] = [event for event in orbpre_events for value in event["values"] if value["name"] == "orbit" and int(value["value"]) == int(start_orbit) + 1]
        # end if
        if not stop_orbit in stop_orbpre_infos:
            stop_orbpre_infos[stop_orbit] = [event for event in orbpre_events for value in event["values"] if value["name"] == "orbit" and int(value["value"]) == int(stop_orbit)]
        # end if
        if not stop_orbit in next_stop_orbpre_infos:
            next_stop_orbpre_infos[stop_orbit] = [event for event in orbpre_events for value in event["values"] if value["name"] == "orbit" and int(value["value"]) == int(stop_orbit) + 1]
        # end if

        if len(next_start_orbpre_infos[start_orbit]) == 0 or len(next_stop_orbpre_infos[stop_orbit]) == 0:
            status = "TIME_NOT_CORRECTED"
            corrected_start = planning_event.start
            corrected_stop = planning_event.stop
        else:
            status = "TIME_CORRECTED"
            start_orbital_period = (parser.parse(next_start_orbpre_infos[start_orbit][0]["start"]) - parser.parse(start_orbpre_infos[start_orbit][0]["start"])).total_seconds()
            stop_orbital_period = (parser.parse(next_stop_orbpre_infos[stop_orbit][0]["start"]) - parser.parse(stop_orbpre_infos[stop_orbit][0]["start"])).total_seconds()
            corrected_start = get_date_from_angle(start_angle, start_orbital_period, start_orbpre_infos[start_orbit][0]["start"])
            corrected_stop = get_date_from_angle(stop_angle, stop_orbital_period, stop_orbpre_infos[stop_orbit][0]["start"])

        # end if

        planning_event_values = planning_event.get_structured_values()

        planning_event_values = planning_event_values + [
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

        # Build completeness events
        # Alerts for station schedule are notified 5 days before the operation starts or now
        station_schedule_alert_notification_time = corrected_start - datetime.timedelta(days=5)
        if station_schedule_alert_notification_time < datetime.datetime.now() and corrected_start > datetime.datetime.now():
            station_schedule_alert_notification_time = datetime.datetime.now()
        # end if
        # Alerts for the planning operations are notified after 10 hours of their execution

        completeness_event_values = planning_event_values + [
            {"name": "status",
             "type": "text",
             "value": "MISSING"}]
        if planning_event.gauge.name == "PLANNED_PLAYBACK":
            downlink_mode = [value.value for value in planning_event.eventTexts if value.name == "playback_type"][0]
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
                    "insertion_type": "INSERT_and_ERASE_INTERSECTED_EVENTS_with_PRIORITY",
                    "name": "DFEP_SCHEDULE_COMPLETENESS",
                    "system": planning_event.gauge.system
                },
                "links": [{
                    "link": str(planning_event.event_uuid),
                    "link_mode": "by_uuid",
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
                    "insertion_type": "INSERT_and_ERASE_INTERSECTED_EVENTS_with_PRIORITY",
                    "name": "STATION_SCHEDULE_COMPLETENESS",
                    "system": planning_event.gauge.system
                },
                "links": [{
                    "link": str(planning_event.event_uuid),
                    "link_mode": "by_uuid",
                    "name": "STATION_SCHEDULE_COMPLETENESS",
                    "back_ref": "PLANNED_PLAYBACK"
                }],
                "start": start.isoformat(),
                "stop": stop.isoformat(),
                "values": completeness_event_values,
                "alerts": [{
                    "message": "The {} planned playback (with timings: {}_{}) over orbit {} is not covered by any station schedule".format(downlink_mode, corrected_start.isoformat(), corrected_stop.isoformat(), int(start_orbit)),
                    "generator": os.path.basename(__file__),
                    "notification_time": station_schedule_alert_notification_time.isoformat(),
                    "alert_cnf": {
                        "name": "ALERT-0001: MISSING STATION SCHEDULE",
                        "severity": "fatal",
                        "description": "Alert refers to the missing coverage of any station schedule for the corresponding planned playback",
                        "group": "S2_PLANNING"
                    }
                }]
            }
            list_of_completeness_events.append(completeness_event)
            
            if downlink_mode != "SAD":
                completeness_event = {
                    "gauge": {
                        "insertion_type": "INSERT_and_ERASE_INTERSECTED_EVENTS_with_PRIORITY",
                        "name": "PLANNED_PLAYBACK_COMPLETENESS_CHANNEL_1",
                        "system": planning_event.gauge.system
                    },
                    "links": [{
                        "link": str(planning_event.event_uuid),
                        "link_mode": "by_uuid",
                        "name": "PLAYBACK_COMPLETENESS",
                        "back_ref": "PLANNED_PLAYBACK"
                    }],
                    "start": start.isoformat(),
                    "stop": stop.isoformat(),
                    "values": completeness_event_values,
                    "alerts": [{
                        "message": "The {} planned playback (with timings: {}_{}) over orbit {}, expected to be received through channel 1, has not been received".format(downlink_mode, corrected_start.isoformat(), corrected_stop.isoformat(), int(start_orbit)),
                        "generator": os.path.basename(__file__),
                        "notification_time": (corrected_start + datetime.timedelta(hours=10)).isoformat(),
                        "alert_cnf": {
                            "name": "ALERT-0010: MISSING PLANNED PLAYBACK CH 1",
                            "severity": "fatal",
                            "description": "Alert refers to the missing execution of the corresponding planned playback through the channel 1",
                            "group": "S2_PLANNING"
                        }
                    }]
                }
                list_of_completeness_events.append(completeness_event)
            # end if
            if downlink_mode != "HKTM":
                completeness_event = {
                    "gauge": {
                        "insertion_type": "INSERT_and_ERASE_INTERSECTED_EVENTS_with_PRIORITY",
                        "name": "PLANNED_PLAYBACK_COMPLETENESS_CHANNEL_2",
                        "system": planning_event.gauge.system
                    },
                    "links": [{
                        "link": str(planning_event.event_uuid),
                        "link_mode": "by_uuid",
                        "name": "PLAYBACK_COMPLETENESS",
                        "back_ref": "PLANNED_PLAYBACK"
                    }],
                    "start": start.isoformat(),
                    "stop": stop.isoformat(),
                    "values": completeness_event_values,
                    "alerts": [{
                        "message": "The {} planned playback (with timings: {}_{}) over orbit {}, expected to be received through channel 2, has not been received".format(downlink_mode, corrected_start.isoformat(), corrected_stop.isoformat(), int(start_orbit)),
                        "generator": os.path.basename(__file__),
                        "notification_time": (corrected_start + datetime.timedelta(hours=10)).isoformat(),
                        "alert_cnf": {
                            "name": "ALERT-0011: MISSING PLANNED PLAYBACK CH 2",
                            "severity": "fatal",
                            "description": "Alert refers to the missing execution of the corresponding planned playback through the channel 2",
                            "group": "S2_PLANNING"
                        }
                    }]
                }
                list_of_completeness_events.append(completeness_event)
            # end if
        elif planning_event.gauge.name == "PLANNED_CUT_IMAGING":

            start = corrected_start + datetime.timedelta(seconds=10)
            stop = corrected_stop - datetime.timedelta(seconds=10)

            if start > stop:
                start = corrected_stop - datetime.timedelta(seconds=12)
                stop = corrected_stop - datetime.timedelta(seconds=6)
            # end if

            # Obtain imaging mode
            imaging_mode = [value.value for value in planning_event.eventTexts if value.name == "imaging_mode"][0]

            completeness_event = {
                "gauge": {
                    "insertion_type": "INSERT_and_ERASE_INTERSECTED_EVENTS_with_PRIORITY",
                    "name": "PLANNED_IMAGING_ISP_COMPLETENESS_CHANNEL_1",
                    "system": planning_event.gauge.system
                },
                "links": [{
                    "link": str(planning_event.event_uuid),
                    "link_mode": "by_uuid",
                    "name": "ISP_COMPLETENESS",
                    "back_ref": "PLANNED_IMAGING"
                }],
                "start": start.isoformat(),
                "stop": stop.isoformat(),
                "values": completeness_event_values,
                "alerts": [{
                    "message": "The part of the {} planned imaging (with timings: {}_{}) over orbit {} corresponding to channel 1 has not been received".format(imaging_mode, corrected_start.isoformat(), corrected_stop.isoformat(), int(start_orbit)),
                    "generator": os.path.basename(__file__),
                    "notification_time": (corrected_start + datetime.timedelta(hours=10)).isoformat(),
                    "alert_cnf": {
                        "name": "ALERT-0020: MISSING PLANNED IMAGING CH 1",
                        "severity": "fatal",
                        "description": "Alert refers to the missing reception of the corresponding planned imaging through channel 1",
                        "group": "S2_PLANNING"
                    }
                }]
            }
            list_of_completeness_events.append(completeness_event)
            completeness_event = {
                "gauge": {
                    "insertion_type": "INSERT_and_ERASE_INTERSECTED_EVENTS_with_PRIORITY",
                    "name": "PLANNED_IMAGING_ISP_COMPLETENESS_CHANNEL_2",
                    "system": planning_event.gauge.system
                },
                "links": [{
                    "link": str(planning_event.event_uuid),
                    "link_mode": "by_uuid",
                    "name": "ISP_COMPLETENESS",
                    "back_ref": "PLANNED_IMAGING"
                }],
                "start": start.isoformat(),
                "stop": stop.isoformat(),
                "values": completeness_event_values,
                "alerts": [{
                    "message": "The part of the {} planned imaging (with timings: {}_{}) over orbit {} corresponding to channel 2 has not been received".format(imaging_mode, corrected_start.isoformat(), corrected_stop.isoformat(), int(start_orbit)),
                    "generator": os.path.basename(__file__),
                    "notification_time": (corrected_start + datetime.timedelta(hours=10)).isoformat(),
                    "alert_cnf": {
                        "name": "ALERT-0021: MISSING PLANNED IMAGING CH 2",
                        "severity": "fatal",
                        "description": "Alert refers to the missing reception of the corresponding planned imaging through channel 2",
                        "group": "S2_PLANNING"
                    }
                }]
            }
            list_of_completeness_events.append(completeness_event)

            completeness_event = {
                "gauge": {
                    "insertion_type": "INSERT_and_ERASE_INTERSECTED_EVENTS_with_PRIORITY",
                    "name": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L0",
                    "system": planning_event.gauge.system
                },
                "links": [{
                    "link": str(planning_event.event_uuid),
                    "link_mode": "by_uuid",
                    "name": "PROCESSING_COMPLETENESS",
                    "back_ref": "PLANNED_IMAGING"
                }],
                "start": start.isoformat(),
                "stop": stop.isoformat(),
                "values": completeness_event_values,
                "alerts": [{
                    "message": "The L0 processing for the {} planned imaging (with timings: {}_{}) over orbit {} has not been performed".format(imaging_mode, corrected_start.isoformat(), corrected_stop.isoformat(), int(start_orbit)),
                    "generator": os.path.basename(__file__),
                    "notification_time": (corrected_start + datetime.timedelta(hours=10)).isoformat(),
                    "alert_cnf": {
                        "name": "ALERT-0030: MISSING L0 PROCESSING",
                        "severity": "fatal",
                        "description": "Alert refers to the missing L0 processing of the corresponding planned imaging",
                        "group": "S2_PLANNING"
                    }
                }]
            }
            list_of_completeness_events.append(completeness_event)
            completeness_event = {
                "gauge": {
                    "insertion_type": "INSERT_and_ERASE_INTERSECTED_EVENTS_with_PRIORITY",
                    "name": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L1B",
                    "system": planning_event.gauge.system
                },
                "links": [{
                    "link": str(planning_event.event_uuid),
                    "link_mode": "by_uuid",
                    "name": "PROCESSING_COMPLETENESS",
                    "back_ref": "PLANNED_IMAGING"
                }],
                "start": start.isoformat(),
                "stop": stop.isoformat(),
                "values": completeness_event_values,
                "alerts": [{
                    "message": "The L1B processing for the {} planned imaging (with timings: {}_{}) over orbit {} has not been performed".format(imaging_mode, corrected_start.isoformat(), corrected_stop.isoformat(), int(start_orbit)),
                    "generator": os.path.basename(__file__),
                    "notification_time": (corrected_start + datetime.timedelta(hours=10)).isoformat(),
                    "alert_cnf": {
                        "name": "ALERT-0032: MISSING L1B PROCESSING",
                        "severity": "fatal",
                        "description": "Alert refers to the missing L1B processing of the corresponding planned imaging",
                        "group": "S2_PLANNING"
                    }
                }]
            }
            list_of_completeness_events.append(completeness_event)
            if imaging_mode in ["SUN_CAL", "DARK_CAL_CSM_OPEN", "DARK_CAL_CSM_CLOSE", "VICARIOUS_CAL", "RAW", "TEST"]:
                completeness_event = {
                    "gauge": {
                        "insertion_type": "INSERT_and_ERASE_INTERSECTED_EVENTS_with_PRIORITY",
                        "name": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L1A",
                        "system": planning_event.gauge.system
                    },
                    "links": [{
                        "link": str(planning_event.event_uuid),
                        "link_mode": "by_uuid",
                        "name": "PROCESSING_COMPLETENESS",
                        "back_ref": "PLANNED_IMAGING"
                    }],
                    "start": start.isoformat(),
                    "stop": stop.isoformat(),
                    "values": completeness_event_values,
                    "alerts": [{
                        "message": "The L1A processing for the {} planned imaging (with timings: {}_{}) over orbit {} has not been performed".format(imaging_mode, corrected_start.isoformat(), corrected_stop.isoformat(), int(start_orbit)),
                        "generator": os.path.basename(__file__),
                        "notification_time": (corrected_start + datetime.timedelta(hours=10)).isoformat(),
                        "alert_cnf": {
                            "name": "ALERT-0031: MISSING L1A PROCESSING",
                            "severity": "fatal",
                            "description": "Alert refers to the missing L1A processing of the corresponding planned imaging",
                            "group": "S2_PLANNING"
                        }
                    }]
                }
                list_of_completeness_events.append(completeness_event)
            # end if
            if imaging_mode in ["NOMINAL", "VICARIOUS_CAL", "TEST"]:
                completeness_event = {
                    "gauge": {
                        "insertion_type": "INSERT_and_ERASE_INTERSECTED_EVENTS_with_PRIORITY",
                        "name": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L1C",
                        "system": planning_event.gauge.system
                    },
                    "links": [{
                        "link": str(planning_event.event_uuid),
                        "link_mode": "by_uuid",
                        "name": "PROCESSING_COMPLETENESS",
                        "back_ref": "PLANNED_IMAGING"
                    }],
                    "start": start.isoformat(),
                    "stop": stop.isoformat(),
                    "values": completeness_event_values,
                    "alerts": [{
                        "message": "The L1C processing for the {} planned imaging (with timings: {}_{}) over orbit {} has not been performed".format(imaging_mode, corrected_start.isoformat(), corrected_stop.isoformat(), int(start_orbit)),
                        "generator": os.path.basename(__file__),
                        "notification_time": (corrected_start + datetime.timedelta(hours=10)).isoformat(),
                        "alert_cnf": {
                            "name": "ALERT-0033: MISSING L1C PROCESSING",
                            "severity": "fatal",
                            "description": "Alert refers to the missing L1C processing of the corresponding planned imaging",
                            "group": "S2_PLANNING"
                        }
                    }]
                }
                list_of_completeness_events.append(completeness_event)
            # end if
            if imaging_mode in ["NOMINAL"]:
                completeness_event = {
                    "gauge": {
                        "insertion_type": "INSERT_and_ERASE_INTERSECTED_EVENTS_with_PRIORITY",
                        "name": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L2A",
                        "system": planning_event.gauge.system
                    },
                    "links": [{
                        "link": str(planning_event.event_uuid),
                        "link_mode": "by_uuid",
                        "name": "PROCESSING_COMPLETENESS",
                        "back_ref": "PLANNED_IMAGING"
                    }],
                    "start": start.isoformat(),
                    "stop": stop.isoformat(),
                    "values": completeness_event_values,
                    "alerts": [{
                        "message": "The L2A processing for the {} planned imaging (with timings: {}_{}) over orbit {} has not been performed".format(imaging_mode, corrected_start.isoformat(), corrected_stop.isoformat(), int(start_orbit)),
                        "generator": os.path.basename(__file__),
                        "notification_time": (corrected_start + datetime.timedelta(hours=10)).isoformat(),
                        "alert_cnf": {
                            "name": "ALERT-0034: MISSING L2A PROCESSING",
                            "severity": "fatal",
                            "description": "Alert refers to the missing L2A processing of the corresponding planned imaging",
                            "group": "S2_PLANNING"
                        }
                    }]
                }
                list_of_completeness_events.append(completeness_event)
            # end if
            
        # end if

    # end for

    return corrected_planning_events

@debug
def _generate_corrected_planning_events(satellite, start_orbit, stop_orbit, list_of_events, list_of_completeness_events, query):
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

    events = _correct_planning_events(list_of_events, planning_events, list_of_completeness_events)

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

    # Generation time is changed to -1 days to avoid overriding data from EDRS and station scheduling
    generation_time = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Source/Creation_Date")[0].text.split("=")[1]
    validity_start = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Validity_Period/Validity_Start")[0].text.split("=")[1]
    reported_validity_stop = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Validity_Period/Validity_Stop")[0].text.split("=")[1]
    validity_stop = (parser.parse(reported_validity_stop) + datetime.timedelta(minutes=100)).isoformat()
    validity_start_corrected = xpath_xml("/Earth_Explorer_File/Data_Block/List_of_OSVs/OSV[1]/UTC")[0].text.split("=")[1]
    validity_stop_corrected = xpath_xml("/Earth_Explorer_File/Data_Block/List_of_OSVs/OSV[last()]/UTC")[0].text.split("=")[1]

    source = {
        "name": file_name,
        "reception_time": reception_time,
        "generation_time": generation_time,
        "validity_start": validity_start,
        "validity_stop": validity_stop,
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

    # Generate orbit predicted events
    _generate_orbpre_events(xpath_xml, source, list_of_events)

    functions.insert_ingestion_progress(session_progress, general_source_progress, 30)
    
    start_orbit = str(int(xpath_xml("/Earth_Explorer_File/Data_Block/List_of_OSVs/OSV[1]/Absolute_Orbit")[0].text))
    stop_orbit = str(int(xpath_xml("/Earth_Explorer_File/Data_Block/List_of_OSVs/OSV[last() - 1]/Absolute_Orbit")[0].text))

    # Generate corrected planning events
    list_of_completeness_events = []
    corrected_planning_events = _generate_corrected_planning_events(satellite, start_orbit, stop_orbit, list_of_events, list_of_completeness_events, query)

    functions.insert_ingestion_progress(session_progress, general_source_progress, 60)

    completeness = "true"
    completeness_message = ""
    if len(corrected_planning_events) == 0:
        completeness = "false"
        completeness_message = "MISSING_PLANNING"
    # end if

    source["ingestion_completeness"] = {
        "check": completeness,
        "message": completeness_message
    } 
    
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
    }]}

    functions.insert_ingestion_progress(session_progress, general_source_progress, 70)

    if len(corrected_planning_events) > 0:
        # Generate the footprint of the events
        corrected_planning_events_with_footprint = functions.associate_footprints(corrected_planning_events, satellite, list_of_events)

        data["operations"].append({
            "mode": "insert_and_erase",
            "dim_signature": {
                "name": "CORRECTED_NPPF_" + satellite,
                "exec": os.path.basename(__file__),
                "version": version
            },
            "source": {
                "name": file_name,
                "reception_time": reception_time,
                "generation_time": generation_time,
                "validity_start": validity_start_corrected,
                "validity_stop": validity_stop_corrected,
                "reported_validity_start": validity_start,
                "reported_validity_stop": reported_validity_stop
            },
            "events": corrected_planning_events_with_footprint
        })
    # end if
    
    functions.insert_ingestion_progress(session_progress, general_source_progress, 90)
    
    if len(list_of_completeness_events) > 0:
        # Generate the footprint of the events
        list_of_completeness_events_with_footprint = functions.associate_footprints(list_of_completeness_events, satellite, list_of_events)
        
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
                "validity_start": validity_start_corrected,
                "validity_stop": validity_stop_corrected,
                "reported_validity_start": validity_start,
                "reported_validity_stop": reported_validity_stop,
                "priority": 10
            },
            "events": list_of_completeness_events_with_footprint
        })
    # end if
    
    functions.insert_ingestion_progress(session_progress, general_source_progress, 100)

    query.close_session()

    new_file.close()
    
    return data
