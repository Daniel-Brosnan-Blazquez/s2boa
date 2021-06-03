"""
Ingestion module for the REP_PASS_E_VGS files of Sentinel-2

Written by DEIMOS Space S.L. (dibb)

module s2boa
"""
# Import python utilities
import os
import argparse
import datetime
import json
import tempfile
from dateutil import parser
import math

# Import xml parser
from lxml import etree

# Import ingestion_functions.helpers
import eboa.ingestion.functions as ingestion_functions
import s2boa.ingestions.functions as functions
import s2boa.ingestions.xpath_functions as xpath_functions

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

def _get_station(xpath_xml):
    """
    Method to obtain the station identifier
    :param xpath_xml: source of information that was xpath evaluated
    :type xpath_xml: XPathEvaluator
    """
    
    # Obtain the station using the DCS unit 
    dcs = xpath_xml("/Earth_Explorer_File/Data_Block/input_files/input_file")[0].text[0:6]
    station = functions.get_centre_name_by_alias(dcs)

    # Obtain the station using the centre name in case the DCS unit does not match
    if station == "UNKN":
        station_alias = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Source/System")[0].text
        station = functions.get_centre_name_by_alias(station_alias)
    # end if

    return station

@debug
def _generate_acquisition_data_information(xpath_xml, source, engine, query, list_of_events, list_of_planning_operations):
    """
    Method to generate the events for the idle operation of the satellite
    :param xpath_xml: source of information that was xpath evaluated
    :type xpath_xml: XPathEvaluator
    :param source: information of the source
    :type source: dict
    :param engine: object to access the engine of the EBOA
    :type engine: Engine
    :param query: object to access the query interface of the EBOA
    :type query: Query
    :param list_of_events: list to store the events to be inserted into the eboa
    :type list_of_events: list

    :return: status -> COMPLETE: there were no gaps during the acquisition; INCOMPLETE: there were gaps during the acquisition
    :rtype: str

    """

    general_status = "COMPLETE"

    # Obtain the satellite
    satellite = source["name"][0:3]

    # Obtain the station
    station = _get_station(xpath_xml)

    # Obtain link session ID
    session_id = xpath_xml("/Earth_Explorer_File/Data_Block/input_files/input_file[1]")[0].text[7:31]

    # Obtain channel
    channel = xpath_xml("/Earth_Explorer_File/Data_Block/child::*[contains(name(),'data_')]")[0].tag[6:7]

    # Obtain downlink orbit
    downlink_orbit = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Variable_Header/Downlink_Orbit")[0].text

    # Obtain number of received packets and transfer frames
    number_of_received_isps = sum([int(num.text) for num in xpath_xml("/Earth_Explorer_File/Data_Block/*[contains(name(),'data_C')]/Status[NumFrames > 0 and (@VCID = 2 or @VCID = 4 or @VCID = 5 or @VCID = 6 or @VCID = 20 or @VCID = 21 or @VCID = 22)]/ISP_Status/Summary/NumPackets")])
    number_of_received_transfer_frames = sum([int(num.text) for num in xpath_xml("/Earth_Explorer_File/Data_Block/*[contains(name(),'data_C')]/Status[NumFrames > 0 and @VCID = 3]/NumFrames")])

    # Obtain number of distributed packets and transfer frames    
    number_of_distributed_isps = sum([int(num.text) for num in xpath_xml("/Earth_Explorer_File/Data_Block/*[contains(name(),'distribution_C') and contains(name(),'ISP')]/NumberofPackets")])
    number_of_distributed_transfer_frames = sum([int(num.text) for num in xpath_xml("/Earth_Explorer_File/Data_Block/*[contains(name(),'distribution_C') and contains(name(),'TF')]/NumberofPackets")])

    # Obtain the nodes of distribution
    status_distribution_isps = xpath_xml("/Earth_Explorer_File/Data_Block/*[contains(name(),'distribution_C') and contains(name(),'ISP')][NumberofPackets > 0 or (NumberofPackets = 0 and not(Status = 'DELIVERED'))]/Status")
    status_distribution_transfer_frames = xpath_xml("/Earth_Explorer_File/Data_Block/*[contains(name(),'distribution_C') and contains(name(),'TF')]/Status")

    links_distribution_isps = []
    links_distribution_tfs = []

    # Get the acquisition timings for getting the covered planned playbacks
    acquisition_starts = xpath_xml("/Earth_Explorer_File/Data_Block/*[contains(name(),'data_C')]/Status/AcqStartTime")
    acquisition_starts_in_iso_8601 = [functions.three_letter_to_iso_8601(acquisition_start.text) for acquisition_start in acquisition_starts]
    acquisition_starts_in_iso_8601.sort()

    acquisition_stops = xpath_xml("/Earth_Explorer_File/Data_Block/*[contains(name(),'data_C')]/Status/AcqStopTime")
    acquisition_stops_in_iso_8601 = [functions.three_letter_to_iso_8601(acquisition_stop.text) for acquisition_stop in acquisition_stops]
    acquisition_stops_in_iso_8601.sort()
    
    planned_playback_uuids = []
    if station == "EDRS":
        edrs_slots = query.get_events(explicit_refs = {"op": "==", "filter": session_id},
                                      gauge_names = {"op": "==", "filter": "SLOT_REQUEST_EDRS"},
                                      gauge_systems = {"op": "==", "filter": satellite})

        if len (edrs_slots) > 0:
            planned_playback_uuids = [link.event_uuid_link for edrs_slot in edrs_slots for link in edrs_slot.eventLinks if link.name == "PLANNED_PLAYBACK"]
        # end if
    else:
        station_schedule_events = query.get_events(gauge_names = {"op": "==", "filter": "STATION_SCHEDULE"},
                                                gauge_systems = {"op": "==", "filter": satellite},
                                                value_filters = [{"name": {"op": "==", "filter": "station"}, "type": "text", "value": {"op": "==", "filter": station}},
                                                                 {"name": {"op": "==", "filter": "orbit"}, "type": "double", "value": {"op": "==", "filter": downlink_orbit}}])

        if len (station_schedule_events) > 0:
            planned_playback_uuids = [link.event_uuid_link for station_schedule_event in station_schedule_events for link in station_schedule_event.eventLinks if link.name == "PLANNED_PLAYBACK"]
        # end if
    # end if

    planned_playbacks = []
    if len (planned_playback_uuids) > 0:
        planned_playbacks_and_playback_completeness = query.get_linking_events(event_uuids = {"op": "in", "filter": planned_playback_uuids}, link_names = {"filter": "PLAYBACK_COMPLETENESS", "op": "=="})
        planned_playbacks = planned_playbacks_and_playback_completeness["prime_events"]
        planned_playback_completeness = planned_playbacks_and_playback_completeness["linking_events"]
    # end if

    links_dfep_acquisition_validity = []
    for planned_playback_uuid in planned_playback_uuids:
        links_dfep_acquisition_validity.append({
            "link": str(planned_playback_uuid),
            "link_mode": "by_uuid",
            "name": "DFEP_ACQUISITION_VALIDITY",
            "back_ref": "PLANNED_PLAYBACK"
        })
    # end for
    dfep_acquisition_validity_event = {
        "explicit_reference": session_id,
        "key": session_id + "_CHANNEL_" + channel,
        "gauge": {
            "insertion_type": "SIMPLE_UPDATE",
            "name": "DFEP_ACQUISITION_VALIDITY",
            "system": station
        },
        "links": links_dfep_acquisition_validity,
        "start": source["reported_validity_start"],
        "stop": source["reported_validity_stop"],
        "values": [
            {"name": "downlink_orbit",
             "type": "double",
             "value": downlink_orbit},
            {"name": "satellite",
             "type": "text",
             "value": satellite},
            {"name": "reception_station",
             "type": "text",
             "value": station},
            {"name": "channel",
             "type": "double",
             "value": channel}
        ]
    }
    # Insert playback_validity_event
    list_of_events.append(dfep_acquisition_validity_event)
    
    # List for the playback completeness analysis of the plan
    list_of_playback_completeness_events = []
    
    vcids = xpath_xml("/Earth_Explorer_File/Data_Block/*[contains(name(),'data_C')]/Status[NumFrames > 0 and (@VCID = 2 or @VCID = 3 or @VCID = 4 or @VCID = 5 or @VCID = 6 or @VCID = 20 or @VCID = 21 or @VCID = 22)]")
    for vcid in vcids:
        vcid_number = vcid.get("VCID")
        downlink_mode = functions.get_vcid_mode(vcid_number)
        # Acquisition segment
        acquisition_start = functions.three_letter_to_iso_8601(vcid.xpath("AcqStartTime")[0].text)
        acquisition_stop = functions.three_letter_to_iso_8601(vcid.xpath("AcqStopTime")[0].text)

        # Reference to the playback validity event
        playback_validity_event_link_ref = "PLAYBACK_VALIDITY_" + vcid_number

        status = "COMPLETE"

        # Process playback gaps
        gaps = vcid.xpath("Gaps/Gap")
        if len(gaps) > 0:
            i = 0
            start_datetime = parser.parse(functions.three_letter_to_iso_8601(gaps[0].xpath("PreAcqTime")[0].text))
            while i < len(gaps):
                i += 1
                general_status = "INCOMPLETE"
                status = "INCOMPLETE"
                stop_datetime = parser.parse(functions.three_letter_to_iso_8601(gaps[i-1].xpath("PostAcqTime")[0].text))

                # Check that the difference between its stop and the start of the following (if exists) is lower than 1 second
                if i < len(gaps):
                    start_next_datetime = parser.parse(functions.three_letter_to_iso_8601(gaps[i].xpath("PreAcqTime")[0].text))
                    if (start_next_datetime - stop_datetime).total_seconds() < 1:
                        continue
                    # end if
                # end if
                
                gap_event = {
                    "explicit_reference": session_id,
                    "key": session_id + "_CHANNEL_" + channel,
                    "gauge": {
                        "insertion_type": "SIMPLE_UPDATE",
                        "name": "PLAYBACK_GAP",
                        "system": station
                    },
                    "start": start_datetime.isoformat(),
                    "stop": stop_datetime.isoformat(),
                    "links": [
                        {
                            "link": playback_validity_event_link_ref,
                            "link_mode": "by_ref",
                            "name": "PLAYBACK_GAP",
                            "back_ref": "PLAYBACK_VALIDITY"
                        }],
                    "values": [
                        {"name": "downlink_orbit",
                         "type": "double",
                         "value": downlink_orbit},
                        {"name": "satellite",
                         "type": "text",
                         "value": satellite},
                        {"name": "reception_station",
                         "type": "text",
                         "value": station},
                        {"name": "channel",
                         "type": "double",
                         "value": channel},
                        {"name": "vcid",
                         "type": "double",
                         "value": vcid_number},
                        {"name": "playback_type",
                         "type": "text",
                         "value": downlink_mode}
                    ]
                }

                # Insert gap_event
                list_of_events.append(gap_event)

                # Move start to the next start if exists
                if i < len(gaps):
                    start_datetime = parser.parse(functions.three_letter_to_iso_8601(gaps[i].xpath("PreAcqTime")[0].text))
                # end if

            # end while
        # end if

        links = []
        if len(planned_playbacks) > 0:
            if downlink_mode in ["NOMINAL", "NRT"]:
                planned_playback_type = [downlink_mode, "REGULAR"]
            elif downlink_mode in ["SAD", "HKTM"]:
                planned_playback_type = [downlink_mode, "HKTM_SAD"]
            else:
                planned_playback_type = [downlink_mode]
            # end if

            associated_planned_playbacks = []
            for planned_playback in planned_playbacks:
                matched_values = [value for value in planned_playback.eventTexts if value.name == "playback_type" and value.value in planned_playback_type]
                if len(matched_values) > 0:
                    associated_planned_playbacks.append(planned_playback)
                # end if
            # end for

            for planned_playback in associated_planned_playbacks:

                planned_playback_completeness_uuids = [event_link.event_uuid_link for event_link in planned_playback.eventLinks if event_link.name == "PLAYBACK_COMPLETENESS"]

                planned_playback_completeness_starts = [event.start for event in planned_playback_completeness if event.event_uuid in planned_playback_completeness_uuids]
                planned_playback_completeness_starts.sort()
                planned_playback_completeness_stops = [event.stop for event in planned_playback_completeness if event.event_uuid in planned_playback_completeness_uuids]
                planned_playback_completeness_stops.sort()
                
                links.append({
                    "link": str(planned_playback.event_uuid),
                    "link_mode": "by_uuid",
                    "name": "PLAYBACK_VALIDITY",
                    "back_ref": "PLANNED_PLAYBACK"
                })

                if vcid_number == "3":
                    links_distribution_tfs.append({
                        "link": str(planned_playback.event_uuid),
                        "link_mode": "by_uuid",
                        "name": "DISTRIBUTION_STATUS",
                        "back_ref": "PLANNED_PLAYBACK"
                    })
                else:
                    links_distribution_isps.append({
                        "link": str(planned_playback.event_uuid),
                        "link_mode": "by_uuid",
                        "name": "DISTRIBUTION_STATUS",
                        "back_ref": "PLANNED_PLAYBACK"
                    })
                # end if
                
                completeness_status = "RECEIVED"
                if status != "COMPLETE":
                    completeness_status = status
                # end if

                start = planned_playback_completeness_starts[0] - datetime.timedelta(seconds=1)
                stop = planned_playback_completeness_stops[-1] + datetime.timedelta(seconds=1)
                
                list_of_playback_completeness_events.append({
                    "explicit_reference": session_id,
                    "gauge": {
                        "insertion_type": "INSERT_and_ERASE_per_EVENT_with_PRIORITY",
                        "name": "PLANNED_PLAYBACK_COMPLETENESS_CHANNEL_" + channel,
                        "system": satellite
                    },
                    "links": [
                        {
                            "link": str(planned_playback.event_uuid),
                            "link_mode": "by_uuid",
                            "name": "PLAYBACK_COMPLETENESS",
                            "back_ref": "PLANNED_PLAYBACK"
                        },
                        {
                            "link": playback_validity_event_link_ref,
                            "link_mode": "by_ref",
                            "name": "PLAYBACK_COMPLETENESS",
                            "back_ref": "PLAYBACK_VALIDITY"
                        }],
                    "start": start.isoformat(),
                    "stop": stop.isoformat(),
                    "values": [
                        {"name": "status",
                         "type": "text",
                         "value": completeness_status},
                        {"name": "downlink_orbit",
                         "type": "double",
                         "value": downlink_orbit},
                        {"name": "satellite",
                         "type": "text",
                         "value": satellite},
                        {"name": "reception_station",
                         "type": "text",
                         "value": station},
                        {"name": "channel",
                         "type": "double",
                         "value": channel},
                        {"name": "vcid",
                         "type": "double",
                         "value": vcid_number},
                        {"name": "playback_type",
                         "type": "text",
                         "value": downlink_mode},
                    ]
                }
                )

            # end for
        # end if

        playback_event = {
            "link_ref": playback_validity_event_link_ref,
            "explicit_reference": session_id,
            "key": session_id + "_CHANNEL_" + channel,
            "gauge": {
                "insertion_type": "SIMPLE_UPDATE",
                "name": "PLAYBACK_VALIDITY_" + vcid_number,
                "system": station
            },
            "start": acquisition_start,
            "stop": acquisition_stop,
            "links": links,
            "values": [
                {"name": "downlink_orbit",
                 "type": "double",
                 "value": downlink_orbit},
                {"name": "satellite",
                 "type": "text",
                 "value": satellite},
                {"name": "reception_station",
                 "type": "text",
                 "value": station},
                {"name": "channel",
                 "type": "double",
                 "value": channel},
                {"name": "vcid",
                 "type": "double",
                 "value": vcid_number},
                {"name": "playback_type",
                 "type": "text",
                 "value": downlink_mode},
                {"name": "status",
                 "type": "text",
                 "value": status}
            ]
        }

        # Insert playback_event
        list_of_events.append(playback_event)

    # end for

    # Register distribution status
    if len(status_distribution_transfer_frames) > 0:
        completeness_status = "OK"
        if number_of_distributed_transfer_frames != number_of_received_transfer_frames:
            completeness_status = "NOK"
        # end if
        distribution_status_event = {
            "explicit_reference": session_id,
            "key": session_id + "_CHANNEL_" + channel,
            "gauge": {
                "insertion_type": "SIMPLE_UPDATE",
                "name": "PLAYBACK_HKTM_DISTRIBUTION_STATUS_CHANNEL_" + channel,
                "system": station
            },
            "links": links_distribution_tfs,
            "start": acquisition_starts_in_iso_8601[0],
            "stop": acquisition_stops_in_iso_8601[-1],
            "values": [
                {"name": "status",
                 "type": "text",
                 "value": status_distribution_transfer_frames[0].text},
                {"name": "downlink_orbit",
                 "type": "double",
                 "value": downlink_orbit},
                {"name": "satellite",
                 "type": "text",
                 "value": satellite},
                {"name": "reception_station",
                 "type": "text",
                 "value": station},
                {"name": "channel",
                 "type": "double",
                 "value": channel},
                {"name": "completeness_status",
                 "type": "text",
                 "value": completeness_status},
                {"name": "number_of_received_transfer_frames",
                 "type": "double",
                 "value": number_of_received_transfer_frames},
                {"name": "number_of_distributed_transfer_frames",
                 "type": "double",
                 "value": number_of_distributed_transfer_frames},
                {"name": "completeness_difference",
                 "type": "double",
                 "value": number_of_received_transfer_frames - number_of_distributed_transfer_frames}
            ]
        }
        # Insert playback_validity_event
        list_of_events.append(distribution_status_event)
    # end if

    if len(status_distribution_isps) > 0:
        completeness_status = "OK"
        if number_of_distributed_isps != number_of_received_isps:
            completeness_status = "NOK"
        # end if
        distribution_status_event = {
            "explicit_reference": session_id,
            "key": session_id + "_CHANNEL_" + channel,
            "gauge": {
                "insertion_type": "SIMPLE_UPDATE",
                "name": "PLAYBACK_ISP_DISTRIBUTION_STATUS_CHANNEL_" + channel,
                "system": station
            },
            "links": links_distribution_isps,
            "start": acquisition_starts_in_iso_8601[0],
            "stop": acquisition_stops_in_iso_8601[-1],
            "values": [
                {"name": "status",
                 "type": "text",
                 "value": status_distribution_isps[0].text},
                {"name": "downlink_orbit",
                 "type": "double",
                 "value": downlink_orbit},
                {"name": "satellite",
                 "type": "text",
                 "value": satellite},
                {"name": "reception_station",
                 "type": "text",
                 "value": station},
                {"name": "channel",
                 "type": "double",
                 "value": channel},
                {"name": "completeness_status",
                 "type": "text",
                 "value": completeness_status},
                {"name": "number_of_received_isps",
                 "type": "double",
                 "value": number_of_received_isps},
                {"name": "number_of_distributed_isps",
                 "type": "double",
                 "value": number_of_distributed_isps},
                {"name": "completeness_difference",
                 "type": "double",
                 "value": number_of_received_isps - number_of_distributed_isps}
            ]
        }
        # Insert playback_validity_event
        list_of_events.append(distribution_status_event)
    # end if
    
    # Insert completeness operation for the completeness analysis of the plan
    if len(list_of_playback_completeness_events) > 0:
        playback_planning_completeness_event_starts = [event["start"] for event in list_of_playback_completeness_events]
        playback_planning_completeness_event_starts.sort()
        playback_planning_completeness_event_stops = [event["stop"] for event in list_of_playback_completeness_events]
        playback_planning_completeness_event_stops.sort()

        # Generate the footprint of the events
        list_of_playback_completeness_events_with_footprints = functions.associate_footprints(list_of_playback_completeness_events, satellite)

        playback_planning_completeness_operation = {
            "mode": "insert",
            "dim_signature": {
                "name": "COMPLETENESS_NPPF_" + satellite,
                "exec": "playback_planning_completeness_" + os.path.basename(__file__),
                "version": version
            },
            "source": {
                "name": source["name"],
                "reception_time": source["reception_time"],
                "generation_time": source["generation_time"],
                "validity_start": str(playback_planning_completeness_event_starts[0]),
                "validity_stop": str(playback_planning_completeness_event_stops[-1]),
                "reported_validity_start": source["reported_validity_start"],
                "reported_validity_stop": source["reported_validity_stop"],
                "priority": 30
            },
            "events": list_of_playback_completeness_events_with_footprints
        }

        list_of_planning_operations.append(playback_planning_completeness_operation)
    # end if


    return general_status

@debug
def _generate_received_data_information(xpath_xml, source, engine, query, list_of_events, list_of_isp_validity_processing_completeness_events, list_of_planning_operations):
    """
    Method to generate the events for the idle operation of the satellite
    :param xpath_xml: source of information that was xpath evaluated
    :type xpath_xml: XPathEvaluator
    :param source: information of the source
    :type source: dict
    :param engine: object to access the engine of the EBOA
    :type engine: Engine
    :param query: object to access the query interface of the EBOA
    :type query: Query
    :param list_of_events: list to store the events to be inserted into the eboa
    :type list_of_events: list

    :return: status -> COMPLETE: there are no ISP gaps; INCOMPLETE: there are ISP gaps
    :rtype: str

    """

    status = "COMPLETE"

    # Obtain the satellite
    satellite = source["name"][0:3]

    # Obtain the station
    station = _get_station(xpath_xml)
    
    # Obtain link session ID
    session_id = xpath_xml("/Earth_Explorer_File/Data_Block/input_files/input_file[1]")[0].text[7:31]

    # Obtain channel
    channel = xpath_xml("/Earth_Explorer_File/Data_Block/child::*[contains(name(),'data_')]")[0].tag[6:7]

    # Obtain downlink orbit
    downlink_orbit = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Variable_Header/Downlink_Orbit")[0].text

    # SAD data analysis
    sad_data = xpath_xml("/Earth_Explorer_File/Data_Block/*[contains(name(),'data_C')]/Status[NumFrames > 0 and (@VCID = 2)]/ISP_Status/Status[@APID = 150]")
    sad_start = None
    sad_stop = None
    if len(sad_data) > 0:
        sad_start = functions.convert_from_gps_to_utc(sad_data[0].xpath("three_letter_to_iso_8601(string(SensStartTime))"))
        sad_stop = functions.convert_from_gps_to_utc(sad_data[0].xpath("three_letter_to_iso_8601(string(SensStopTime))"))

        if sad_start > sad_stop:
            sad_start_aux = sad_start
            sad_start = sad_stop
            sad_stop = sad_start_aux
        # end if
        
        sad_data_event = {
            "link_ref": "SAD_DATA",
            "explicit_reference": session_id,
            "key": session_id + "_CHANNEL_" + channel,
            "gauge": {
                "insertion_type": "SIMPLE_UPDATE",
                "name": "SAD_DATA",
                "system": station
            },
            "start": sad_start,
            "stop": sad_stop,
            "values": [
                {"name": "downlink_orbit",
                 "type": "double",
                 "value": downlink_orbit},
                {"name": "satellite",
                 "type": "text",
                 "value": satellite},
                {"name": "reception_station",
                 "type": "text",
                 "value": station}
            ]
        }

        # Insert sad_data event
        list_of_events.append(sad_data_event)

    # end if
    
    # List for the isp completeness analysis of the plan
    list_of_isp_completeness_events = []

    vcids = xpath_xml("/Earth_Explorer_File/Data_Block/*[contains(name(),'data_C')]/Status[NumFrames > 0 and (@VCID = 4 or @VCID = 5 or @VCID = 6 or @VCID = 20 or @VCID = 21 or @VCID = 22)]")
    for vcid in vcids:
        # Iterator and timeline for the ISP gaps
        isp_gap_iterator = 0
        timeline_isp_gaps = []

        vcid_number = vcid.get("VCID")
        downlink_mode = functions.get_vcid_mode(vcid_number)
        # Obtain the sensing segment received (EFEP reports only give information about the start date of the first and last scenes)
        sensing_starts = vcid.xpath("ISP_Status/Status/SensStartTime")
        sensing_starts_in_iso_8601 = [functions.three_letter_to_iso_8601(sensing_start.text) for sensing_start in sensing_starts]

        # Sort list
        sensing_starts_in_iso_8601.sort()
        sensing_start = sensing_starts_in_iso_8601[0]
        corrected_sensing_start = functions.convert_from_gps_to_utc(sensing_start)

        sensing_stops = vcid.xpath("ISP_Status/Status/SensStopTime")
        sensing_stops_in_iso_8601 = [functions.three_letter_to_iso_8601(sensing_stop.text) for sensing_stop in sensing_stops]

        # Sort list
        sensing_stops_in_iso_8601.sort()
        sensing_stop = sensing_stops_in_iso_8601[-1]
        # Add 1 scene at the end
        corrected_sensing_stop = (parser.parse(functions.convert_from_gps_to_utc(sensing_stop)) + datetime.timedelta(seconds=3.608)).isoformat()

        # APID configuration
        apid_conf = functions.get_vcid_apid_configuration(vcid_number)

        # Get all the APIDs which contain data
        apids = xpath_xml("/Earth_Explorer_File/Data_Block/*[contains(name(),'data_C')]/Status[number(@VCID) = $vcid_number]/ISP_Status/Status[NumPackets > 0 and number(@APID) >= number($min_apid) and number(@APID) <= number($max_apid)]", vcid_number = int(vcid_number), min_apid = apid_conf["min_apid"], max_apid = apid_conf["max_apid"])

        # Reference to the raw ISP validity event
        raw_isp_validity_event_link_ref = "RAW_ISP_VALIDITY_" + vcid_number

        # Obtain sensing segments per apid
        # Obtain sensing gaps per apid (the gap is clean, PreCounter = threshold and PostCounter = 0)
        sensing_gaps_per_apid = {}
        received_datablocks_per_apid = {}

        timelines_of_sensing_gaps = []
        for apid in apids:
            apid_number = apid.get("APID")
            sensing_gaps_per_apid[apid_number] = []
            received_datablocks_per_apid[apid_number] = []
            band_detector = functions.get_band_detector(apid_number)
            counter_threshold = functions.get_counter_threshold(band_detector["band"])
            sensing_gaps = apid.xpath("Gaps/Gap[dates_difference(three_letter_to_iso_8601(string(PostSensTime)),three_letter_to_iso_8601(string(PreSensTime))) > 4]")

            for sensing_gap in sensing_gaps:
                sensing_gaps_per_apid[apid_number].append({
                    "id": apid_number,
                    "start": parser.parse(functions.convert_from_gps_to_utc(functions.three_letter_to_iso_8601(sensing_gap.xpath("string(PreSensTime)")))),
                    "stop": parser.parse(functions.convert_from_gps_to_utc(functions.three_letter_to_iso_8601(sensing_gap.xpath("string(PostSensTime)")))) - datetime.timedelta(seconds=0.001),
                })
            # end for

            sensing_gaps = apid.xpath("Gaps/Gap[boolean(following-sibling::Gap) and dates_difference(three_letter_to_iso_8601(string(following-sibling::Gap/PreSensTime)), three_letter_to_iso_8601(string(PostSensTime))) > 4]")

            for sensing_gap in sensing_gaps:
                sensing_gaps_per_apid[apid_number].append({
                    "id": apid_number,
                    "start": parser.parse(functions.convert_from_gps_to_utc(functions.three_letter_to_iso_8601(sensing_gap.xpath("string(PostSensTime)")))),
                    "stop": parser.parse(functions.convert_from_gps_to_utc(functions.three_letter_to_iso_8601(sensing_gap.xpath("string(following-sibling::Gap/PreSensTime)")))),
                })
            # end for

            # Introduce gaps for the last scenes if they are not available
            last_gap_post_sens_time = apid.xpath("Gaps/Gap[last()]/PostSensTime")
            if len(last_gap_post_sens_time) > 0 and functions.three_letter_to_iso_8601(last_gap_post_sens_time[0].text) < sensing_stop:
                sensing_gaps_per_apid[apid_number].append({
                    "id": apid_number,
                    "start": parser.parse(functions.convert_from_gps_to_utc(functions.three_letter_to_iso_8601(last_gap_post_sens_time[0].text))),
                    "stop": parser.parse(functions.convert_from_gps_to_utc(sensing_stop)) - datetime.timedelta(seconds=0.001),
                })                
            # end if

            sensing_gaps_per_apid[apid_number].sort(key=lambda segment: segment["start"])
            timelines_of_sensing_gaps.append(sensing_gaps_per_apid[apid_number])
            covered_sensing_start_three_letter = apid.xpath("Gaps/Gap[1]/PreSensTime")
            covered_sensing_stop_three_letter = apid.xpath("Gaps/Gap[last()]/PostSensTime")
            if len(covered_sensing_start_three_letter) > 0 and len(covered_sensing_stop_three_letter) > 0:
                covered_sensing_start = functions.three_letter_to_iso_8601(covered_sensing_start_three_letter[0].text)
                covered_sensing_stop = functions.three_letter_to_iso_8601(covered_sensing_stop_three_letter[0].text)
                covered_sensing = {
                    "id": "covered_sensing",
                    "start": parser.parse(functions.convert_from_gps_to_utc(covered_sensing_start)),
                    "stop": parser.parse(functions.convert_from_gps_to_utc(covered_sensing_stop))
                }
                received_datablocks_per_apid[apid_number] = [segment for segment in ingestion_functions.difference_timelines([covered_sensing], sensing_gaps_per_apid[apid_number]) if segment["id"] == "covered_sensing"]
            # end if
        # end for

        # Obtain the sensing gaps common to all apids
        sensing_gaps = ingestion_functions.intersect_many_timelines(timelines_of_sensing_gaps)

        # Received datablocks (removed the scene added which will be added to every datastrip)
        covered_sensing = {
            "id": "covered_sensing",
            "start": parser.parse(corrected_sensing_start),
            "stop": parser.parse(corrected_sensing_stop) - datetime.timedelta(seconds=3.608)
        }
        received_datablocks = [segment for segment in ingestion_functions.difference_timelines([covered_sensing], sensing_gaps) if segment["id"] == "covered_sensing"]

        # Create ISP gaps for complete missing scenes
        for apid_number in functions.get_apid_numbers(channel):
            gaps = []
            if str(apid_number) in received_datablocks_per_apid:
                gaps = ingestion_functions.difference_timelines(received_datablocks, received_datablocks_per_apid[str(apid_number)])
            else:
                gaps = received_datablocks
            # end if

            for gap in gaps:
                start = gap["start"]
                stop = gap["stop"] + datetime.timedelta(seconds=3.608)
                status = "INCOMPLETE"
                band_detector = functions.get_band_detector(apid_number)

                isp_gap_event = {
                    "link_ref": "ISP_GAP_" + str(isp_gap_iterator),
                    "explicit_reference": session_id,
                    "key": session_id + "_CHANNEL_" + channel,
                    "gauge": {
                        "insertion_type": "SIMPLE_UPDATE",
                        "name": "ISP_GAP",
                        "system": station
                    },
                    "links": [
                        {
                            "link": raw_isp_validity_event_link_ref,
                            "link_mode": "by_ref",
                            "name": "ISP_GAP",
                            "back_ref": "RAW_ISP_VALIDITY"
                        }],
                    "start": start.isoformat(),
                    "stop": stop.isoformat(),
                    "values": [
                        {"name": "impact",
                         "type": "text",
                         "value": "COMPLETE_SCENES_BAND"},
                        {"name": "band",
                         "type": "text",
                         "value": band_detector["band"]},
                        {"name": "detector",
                         "type": "double",
                         "value": band_detector["detector"]},
                        {"name": "downlink_orbit",
                         "type": "double",
                         "value": downlink_orbit},
                        {"name": "satellite",
                         "type": "text",
                         "value": satellite},
                        {"name": "reception_station",
                         "type": "text",
                         "value": station},
                        {"name": "vcid",
                         "type": "double",
                         "value": vcid_number},
                        {"name": "playback_type",
                         "type": "text",
                         "value": downlink_mode},
                        {"name": "apid",
                         "type": "double",
                         "value": apid_number}
                    ]
                }

                # Insert isp_gap_event
                list_of_events.append(isp_gap_event)

                # Insert segment for associating the ISP gap
                timeline_isp_gaps.append({
                    "id": "ISP_GAP_" + str(isp_gap_iterator),
                    "start": start,
                    "stop": stop
                })

                isp_gap_iterator += 1
            # end for
        # end for

        # Create ISP gaps for gaps at the beginning of the APIDs (StartCounter != 0)
        apids_with_gaps_at_the_beginning = xpath_xml("/Earth_Explorer_File/Data_Block/*[contains(name(),'data_C')]/Status[number(@VCID) = $vcid_number or number(@VCID) = $corresponding_vcid_number]/ISP_Status/Status[NumPackets > 0 and not(StartCounter = 0)]", vcid_number = int(vcid_number), corresponding_vcid_number = int(vcid_number) + 16)
        for apid in apids_with_gaps_at_the_beginning:
            apid_number = apid.get("APID")
            status = "INCOMPLETE"
            band_detector = functions.get_band_detector(apid_number)

            counter_threshold = functions.get_counter_threshold(band_detector["band"])
            start = parser.parse(functions.convert_from_gps_to_utc(functions.three_letter_to_iso_8601(apid.xpath("string(SensStartTime)"))))

            missing_packets = int(apid.xpath("string(StartCounter)"))

            seconds_gap = (missing_packets / counter_threshold) * 3.608

            stop = start + datetime.timedelta(seconds=seconds_gap)

            isp_gap_event = {
                "link_ref": "ISP_GAP_" + str(isp_gap_iterator),
                "explicit_reference": session_id,
                "key": session_id + "_CHANNEL_" + channel,
                "gauge": {
                    "insertion_type": "SIMPLE_UPDATE",
                    "name": "ISP_GAP",
                    "system": station
                },
                "links": [
                    {
                        "link": raw_isp_validity_event_link_ref,
                        "link_mode": "by_ref",
                        "name": "ISP_GAP",
                        "back_ref": "RAW_ISP_VALIDITY"
                    }],
                "start": start.isoformat(),
                "stop": stop.isoformat(),
                "values": [
                    {"name": "impact",
                     "type": "text",
                     "value": "AT_BEGINNING"},
                    {"name": "band",
                     "type": "text",
                     "value": band_detector["band"]},
                    {"name": "detector",
                     "type": "double",
                     "value": band_detector["detector"]},
                    {"name": "downlink_orbit",
                     "type": "double",
                     "value": downlink_orbit},
                    {"name": "satellite",
                     "type": "text",
                     "value": satellite},
                    {"name": "reception_station",
                     "type": "text",
                     "value": station},
                    {"name": "vcid",
                     "type": "double",
                     "value": vcid_number},
                    {"name": "playback_type",
                     "type": "text",
                     "value": downlink_mode},
                    {"name": "apid",
                     "type": "double",
                     "value": apid_number},
                    {"name": "missing_packets",
                     "type": "double",
                     "value": missing_packets}
                ]
            }

            # Insert isp_gap_event
            list_of_events.append(isp_gap_event)

            # Insert segment for associating the ISP gap
            timeline_isp_gaps.append({
                "id": "ISP_GAP_" + str(isp_gap_iterator),
                "start": start,
                "stop": stop
            })

            isp_gap_iterator += 1
        # end for

        # Create ISP gaps for gaps between MSI
        gaps_smaller_than_scene = xpath_xml("/Earth_Explorer_File/Data_Block/*[contains(name(),'data_C')]/Status[number(@VCID) = $vcid_number]/ISP_Status/Status[NumPackets > 0]/Gaps/Gap[(not (PreCounter = get_counter_threshold_from_apid(string(../../@APID))) or not (PostCounter = 0)) and not(dates_difference(three_letter_to_iso_8601(string(PostSensTime)),three_letter_to_iso_8601(string(PreSensTime))) > 4)]", vcid_number = int(vcid_number))

        for gap in gaps_smaller_than_scene:
            status = "INCOMPLETE"
            apid_number = gap.xpath("../../@APID")[0]
            band_detector = functions.get_band_detector(apid_number)

            counter_threshold = functions.get_counter_threshold(band_detector["band"])

            # Get sensing timings
            pre_scene_start = parser.parse(functions.convert_from_gps_to_utc(functions.three_letter_to_iso_8601(gap.xpath("string(PreSensTime)"))))
            post_scene_start = parser.parse(functions.convert_from_gps_to_utc(functions.three_letter_to_iso_8601(gap.xpath("string(PostSensTime)"))))

            # Get counters
            counter_start = int(gap.xpath("string(PreCounter)"))
            counter_stop = int(gap.xpath("string(PostCounter)"))

            if counter_start == counter_threshold:
                missing_packets = counter_stop
            elif counter_stop == 0:
                missing_packets = counter_threshold - counter_start
            elif pre_scene_start < post_scene_start:
                missing_packets = counter_threshold - counter_start + counter_stop
            else:
                missing_packets = counter_stop - counter_start
            # end if

            if counter_start == counter_threshold:
                seconds_from_pre_scene_start_to_gap_start = 3.608
            else:
                seconds_from_pre_scene_start_to_gap_start = (counter_start / counter_threshold) * 3.608
            # end if
            if counter_stop == 0:
                seconds_from_post_scene_start_to_gap_stop = 0
            else:
                seconds_from_post_scene_start_to_gap_stop = (counter_stop / counter_threshold) * 3.608
            # end if

            # Set timings of the ISP_GAP
            start = pre_scene_start + datetime.timedelta(seconds=seconds_from_pre_scene_start_to_gap_start)
            stop = post_scene_start + datetime.timedelta(seconds=seconds_from_post_scene_start_to_gap_stop)
            
            isp_gap_event = {
                "link_ref": "ISP_GAP_" + str(isp_gap_iterator),
                "explicit_reference": session_id,
                "key": session_id + "_CHANNEL_" + channel,
                "gauge": {
                    "insertion_type": "SIMPLE_UPDATE",
                    "name": "ISP_GAP",
                    "system": station
                },
                "links": [
                    {
                        "link": raw_isp_validity_event_link_ref,
                        "link_mode": "by_ref",
                        "name": "ISP_GAP",
                        "back_ref": "RAW_ISP_VALIDITY"
                    }],
                "start": start.isoformat(),
                "stop": stop.isoformat(),
                "values": [
                    {"name": "impact",
                     "type": "text",
                     "value": "BETWEEN_MSI"},
                    {"name": "band",
                     "type": "text",
                     "value": band_detector["band"]},
                    {"name": "detector",
                     "type": "double",
                     "value": band_detector["detector"]},
                    {"name": "downlink_orbit",
                     "type": "double",
                     "value": downlink_orbit},
                    {"name": "satellite",
                     "type": "text",
                     "value": satellite},
                    {"name": "reception_station",
                     "type": "text",
                     "value": station},
                    {"name": "vcid",
                     "type": "double",
                     "value": vcid_number},
                    {"name": "playback_type",
                     "type": "text",
                     "value": downlink_mode},
                    {"name": "apid",
                     "type": "double",
                     "value": apid_number},
                    {"name": "counter_start",
                     "type": "double",
                     "value": counter_start},
                    {"name": "counter_stop",
                     "type": "double",
                     "value": counter_stop},
                    {"name": "missing_packets",
                     "type": "double",
                     "value": missing_packets}
                ]
            }

            # Insert isp_gap_event
            list_of_events.append(isp_gap_event)

            # Insert segment for associating the ISP gap
            timeline_isp_gaps.append({
                "id": "ISP_GAP_" + str(isp_gap_iterator),
                "start": start,
                "stop": stop
            })

            isp_gap_iterator += 1
        # end for

        # Merge timeline of isp gaps
        merged_timeline_isp_gaps = ingestion_functions.merge_timeline(ingestion_functions.sort_timeline_by_start(timeline_isp_gaps))
        
        # Received number of packets
        # The packets registered in the APID 2047 have to be discarded
        received_number_packets_apid_2047 = 0
        received_number_packets_apid_2047_node = vcid.xpath("ISP_Status/Status[@APID = 2047]/NumPackets") 
        if len(received_number_packets_apid_2047_node) > 0:
            received_number_packets_apid_2047 = int(received_number_packets_apid_2047_node[0].text)
        # end if
        received_number_packets = int(vcid.xpath("ISP_Status/Summary/NumPackets")[0].text) - int(received_number_packets_apid_2047)

        sad_status = "MISSING"
        if len(sad_data) > 0 and (sad_start > corrected_sensing_start or sad_stop < corrected_sensing_stop):
            sad_status = "PARTIAL"
        elif len(sad_data) > 0:
            sad_status = "COMPLETE"
        # end if

        raw_isp_validity_event = {
            "link_ref": raw_isp_validity_event_link_ref,
            "explicit_reference": session_id,
            "key": session_id + "_CHANNEL_" + channel,
            "gauge": {
                "insertion_type": "SIMPLE_UPDATE",
                "name": "RAW_ISP_VALIDITY",
                "system": station
            },
            "start": corrected_sensing_start,
            "stop": corrected_sensing_stop,
            "values": [
                {"name": "status",
                 "type": "text",
                 "value": status},
                {"name": "downlink_orbit",
                 "type": "double",
                 "value": downlink_orbit},
                {"name": "satellite",
                 "type": "text",
                 "value": satellite},
                {"name": "reception_station",
                 "type": "text",
                 "value": station},
                {"name": "channel",
                 "type": "double",
                 "value": channel},
                {"name": "vcid",
                 "type": "double",
                 "value": vcid_number},
                {"name": "playback_type",
                 "type": "text",
                 "value": downlink_mode},
                {"name": "num_packets",
                 "type": "double",
                 "value": str(received_number_packets)},
                {"name": "num_frames",
                 "type": "double",
                 "value": vcid.xpath("NumFrames")[0].text}
            ]
        }

        raw_isp_validity_event["values"].append(
            {"name": "sad_status",
             "type": "text",
             "value": sad_status})
        if len(sad_data) > 0:
            raw_isp_validity_event["links"] = [
                {
                    "link": "SAD_DATA",
                    "link_mode": "by_ref",
                    "name": "RAW_ISP_VALIDITY",
                    "back_ref": "SAD_DATA"
                }]
        # end if
        
        # Insert raw_isp_validity_event
        list_of_events.append(raw_isp_validity_event)

        # Merge timeline of isp gaps
        merged_timeline_isp_gaps = ingestion_functions.merge_timeline(ingestion_functions.sort_timeline_by_start(timeline_isp_gaps))

        # Obtain the planned imaging events from the corrected events which record type corresponds to the downlink mode and are intersecting the segment of the RAW_ISP_VALIDTY
        if downlink_mode != "RT":
            corrected_planned_imagings = query.get_events(gauge_names = {"filter": "PLANNED_CUT_IMAGING_CORRECTION", "op": "=="},
                                                          gauge_systems = {"filter": [satellite], "op": "in"},
                                                          value_filters = [{"name": {"op": "==", "filter": "record_type"}, "type": "text", "value": {"op": "==", "filter": downlink_mode}}],
                                                          start_filters = [{"date": corrected_sensing_stop, "op": "<"}],
                                                          stop_filters = [{"date": corrected_sensing_start, "op": ">"}])
        else:
            corrected_planned_imagings = query.get_events(gauge_names = {"filter": "PLANNED_CUT_IMAGING_CORRECTION", "op": "=="},
                                                          gauge_systems = {"filter": [satellite], "op": "in"},
                                                          start_filters = [{"date": corrected_sensing_stop, "op": "<"}],
                                                          stop_filters = [{"date": corrected_sensing_start, "op": ">"}])
        # end if

        corrected_planned_imagings_segments = ingestion_functions.convert_eboa_events_to_date_segments(corrected_planned_imagings)

        # Obtain the duration of the MSI received (Add the duration of the last scene)
        isp_validity_timeline_duration = sum([(received_datablock["stop"] - received_datablock["start"]).total_seconds() + 3.608 for received_datablock in received_datablocks])
        expected_number_scenes = round(isp_validity_timeline_duration / 3.608)
        expected_number_packets = expected_number_scenes * 6480

        if (expected_number_packets - received_number_packets) == 0:
            packet_status = "OK"
        else:
            packet_status = "MISSING"
        # end if

        raw_isp_validity_event["values"].append({"name": "expected_num_packets",
                                                 "type": "double",
                                                 "value": str(expected_number_packets)})
        raw_isp_validity_event["values"].append({"name": "diff_expected_received",
                                                 "type": "double",
                                                 "value": str(expected_number_packets - received_number_packets)})
        raw_isp_validity_event["values"].append({"name": "packet_status",
                                                 "type": "text",
                                                 "value": packet_status})

        # Build the ISP_VALIDITY events
        for received_datablock in received_datablocks:
            start = received_datablock["start"]
            # Add the last scene
            stop = received_datablock["stop"] + datetime.timedelta(seconds=3.608)
            links_isp_validity = []
            links_isp_completeness = []
            imaging_mode = None
            
            intersected_planned_imagings_segments = ingestion_functions.intersect_timelines([received_datablock], corrected_planned_imagings_segments)

            if len(intersected_planned_imagings_segments) > 0:
                intersected_planned_imagings_segment = intersected_planned_imagings_segments[0]
                corrected_planned_imaging = [event for event in corrected_planned_imagings if event.event_uuid == intersected_planned_imagings_segment["id2"]][0]
                planned_imaging_uuid = [event_link.event_uuid_link for event_link in corrected_planned_imaging.eventLinks if event_link.name == "PLANNED_EVENT"][0]

                # Obtain sensing orbit
                sensing_orbit_values = query.get_event_values_interface(value_type="double",
                                                                        value_filters=[{"name": {"op": "==", "filter": "start_orbit"}, "type": "double"}],
                                                                        event_uuids = {"op": "in", "filter": [planned_imaging_uuid]})
                sensing_orbit = sensing_orbit_values[0].value

                # Obtain imaging mode
                imaging_mode_values = query.get_event_values_interface(value_type="text",
                                                                        value_filters=[{"name": {"op": "==", "filter": "imaging_mode"}, "type": "text"}],
                                                                        event_uuids = {"op": "in", "filter": [planned_imaging_uuid]})
                imaging_mode = imaging_mode_values[0].value

                # Set links to the plan
                links_isp_validity.append({
                    "link": str(planned_imaging_uuid),
                    "link_mode": "by_uuid",
                    "name": "ISP_VALIDITY",
                    "back_ref": "PLANNED_IMAGING"
                })
                links_isp_completeness.append({
                    "link": str(planned_imaging_uuid),
                    "link_mode": "by_uuid",
                    "name": "ISP_COMPLETENESS",
                    "back_ref": "PLANNED_IMAGING"
                })

            # end if

            # ISP validity event
            isp_validity_event_link_ref = "ISP_VALIDITY_" + vcid_number + "_" + str(start)

            sad_status = "MISSING"
            if len(sad_data) > 0 and (sad_start > start.isoformat() or sad_stop < stop.isoformat()):
                sad_status = "PARTIAL"
            elif len(sad_data) > 0:
                sad_status = "COMPLETE"
            # end if

            start_l0 = start + datetime.timedelta(seconds=6)
            stop_l0 = stop - datetime.timedelta(seconds=6)
            if start_l0 > stop_l0:
                start_l0 = start
                stop_l0 = stop
            # end if

            isp_validity_processing_completeness_event = {
                "explicit_reference": session_id,
                "gauge": {
                    "insertion_type": "INSERT_and_ERASE_per_EVENT_with_PRIORITY",
                    "name": "ISP_VALIDITY_PROCESSING_COMPLETENESS_L0_CHANNEL_" + channel,
                    "system": satellite
                },
                "start": start_l0.isoformat(),
                "stop": stop_l0.isoformat(),
                "links": [{
                    "link": isp_validity_event_link_ref,
                    "link_mode": "by_ref",
                    "name": "PROCESSING_COMPLETENESS",
                    "back_ref": "ISP_VALIDITY"
                }],
                "values": [
                    {"name": "status",
                     "type": "text",
                     "value": "MISSING"},
                    {"name": "level",
                     "type": "text",
                     "value": "L0"},
                    {"name": "downlink_orbit",
                     "type": "double",
                     "value": downlink_orbit},
                    {"name": "satellite",
                     "type": "text",
                     "value": satellite},
                    {"name": "reception_station",
                     "type": "text",
                     "value": station},
                    {"name": "channel",
                     "type": "double",
                     "value": channel},
                    {"name": "vcid",
                     "type": "double",
                     "value": vcid_number},
                    {"name": "playback_type",
                     "type": "text",
                     "value": downlink_mode}
                ]
            }

            if len(intersected_planned_imagings_segments) > 0:
                isp_validity_processing_completeness_event["values"].append(
                    {"name": "sensing_orbit",
                     "type": "double",
                     "value": sensing_orbit})
                isp_validity_processing_completeness_event["values"].append(
                    {"name": "imaging_mode",
                     "type": "text",
                     "value": imaging_mode})
            # end if

            isp_validity_processing_completeness_event["values"].append(
                {"name": "sad_status",
                 "type": "text",
                 "value": sad_status})
            if len(sad_data) > 0:
                isp_validity_processing_completeness_event["links"].append(
                    {
                        "link": "SAD_DATA",
                        "link_mode": "by_ref",
                        "name": "PROCESSING_COMPLETENESS",
                        "back_ref": "SAD_DATA"
                    })
            # end if

            list_of_isp_validity_processing_completeness_events.append(isp_validity_processing_completeness_event)

            start_after_l0 = start + datetime.timedelta(seconds=6)
            stop_after_l0 = stop - datetime.timedelta(seconds=6)

            sad_status = "MISSING"
            if len(sad_data) > 0 and (sad_start > start_after_l0.isoformat() or sad_stop < stop_after_l0.isoformat()):
                sad_status = "PARTIAL"
            elif len(sad_data) > 0:
                sad_status = "COMPLETE"
            # end if

            if stop_after_l0 > start_after_l0:
                isp_validity_processing_completeness_event = {
                    "explicit_reference": session_id,
                    "gauge": {
                        "insertion_type": "INSERT_and_ERASE_per_EVENT_with_PRIORITY",
                        "name": "ISP_VALIDITY_PROCESSING_COMPLETENESS_L1B_CHANNEL_" + channel,
                        "system": satellite
                    },
                    "start": start_after_l0.isoformat(),
                    "stop": stop_after_l0.isoformat(),
                    "links": [{
                        "link": isp_validity_event_link_ref,
                        "link_mode": "by_ref",
                        "name": "PROCESSING_COMPLETENESS",
                        "back_ref": "ISP_VALIDITY"
                    }],
                    "values": [
                        {"name": "status",
                         "type": "text",
                         "value": "MISSING"},
                        {"name": "level",
                         "type": "text",
                         "value": "L1B"},
                        {"name": "downlink_orbit",
                         "type": "double",
                         "value": downlink_orbit},
                        {"name": "satellite",
                         "type": "text",
                         "value": satellite},
                        {"name": "reception_station",
                         "type": "text",
                         "value": station},
                        {"name": "channel",
                         "type": "double",
                         "value": channel},
                        {"name": "vcid",
                         "type": "double",
                         "value": vcid_number},
                        {"name": "playback_type",
                         "type": "text",
                         "value": downlink_mode}
                    ]
                }

                if len(intersected_planned_imagings_segments) > 0:
                    isp_validity_processing_completeness_event["values"].append(
                        {"name": "sensing_orbit",
                         "type": "double",
                         "value": sensing_orbit})
                    isp_validity_processing_completeness_event["values"].append(
                        {"name": "imaging_mode",
                         "type": "text",
                         "value": imaging_mode})
                # end if

                isp_validity_processing_completeness_event["values"].append(
                    {"name": "sad_status",
                     "type": "text",
                     "value": sad_status})
                if len(sad_data) > 0:
                    isp_validity_processing_completeness_event["links"].append(
                        {
                            "link": "SAD_DATA",
                            "link_mode": "by_ref",
                            "name": "PROCESSING_COMPLETENESS",
                            "back_ref": "SAD_DATA"
                        })
                # end if

                list_of_isp_validity_processing_completeness_events.append(isp_validity_processing_completeness_event)

                if imaging_mode in ["SUN_CAL", "DARK_CAL_CSM_OPEN", "DARK_CAL_CSM_CLOSE", "VICARIOUS_CAL", "RAW", "TEST"]:

                    sad_status = "MISSING"
                    if len(sad_data) > 0 and (sad_start > start_after_l0.isoformat() or sad_stop < stop_after_l0.isoformat()):
                        sad_status = "PARTIAL"
                    elif len(sad_data) > 0:
                        sad_status = "COMPLETE"
                    # end if

                    isp_validity_processing_completeness_event = {
                        "explicit_reference": session_id,
                        "gauge": {
                            "insertion_type": "INSERT_and_ERASE_per_EVENT_with_PRIORITY",
                            "name": "ISP_VALIDITY_PROCESSING_COMPLETENESS_L1A_CHANNEL_" + channel,
                            "system": satellite
                        },
                        "start": start_after_l0.isoformat(),
                        "stop": stop_after_l0.isoformat(),
                        "links": [{
                            "link": isp_validity_event_link_ref,
                            "link_mode": "by_ref",
                            "name": "PROCESSING_COMPLETENESS",
                            "back_ref": "ISP_VALIDITY"
                        }],
                        "values": [
                            {"name": "status",
                             "type": "text",
                             "value": "MISSING"},
                            {"name": "level",
                             "type": "text",
                             "value": "L1A"},
                            {"name": "downlink_orbit",
                             "type": "double",
                             "value": downlink_orbit},
                            {"name": "satellite",
                             "type": "text",
                             "value": satellite},
                            {"name": "reception_station",
                             "type": "text",
                             "value": station},
                            {"name": "channel",
                             "type": "double",
                             "value": channel},
                            {"name": "vcid",
                             "type": "double",
                             "value": vcid_number},
                            {"name": "playback_type",
                             "type": "text",
                             "value": downlink_mode}
                        ]
                    }

                    if len(intersected_planned_imagings_segments) > 0:
                        isp_validity_processing_completeness_event["values"].append(
                            {"name": "sensing_orbit",
                             "type": "double",
                             "value": sensing_orbit})
                        isp_validity_processing_completeness_event["values"].append(
                            {"name": "imaging_mode",
                             "type": "text",
                             "value": imaging_mode})
                    # end if

                    isp_validity_processing_completeness_event["values"].append(
                        {"name": "sad_status",
                         "type": "text",
                         "value": sad_status})
                    if len(sad_data) > 0:
                        isp_validity_processing_completeness_event["links"].append(
                            {
                                "link": "SAD_DATA",
                                "link_mode": "by_ref",
                                "name": "PROCESSING_COMPLETENESS",
                                "back_ref": "SAD_DATA"
                            })
                    # end if

                    list_of_isp_validity_processing_completeness_events.append(isp_validity_processing_completeness_event)
                # end if

                if imaging_mode in ["NOMINAL", "VICARIOUS_CAL", "TEST"]:

                    sad_status = "MISSING"
                    if len(sad_data) > 0 and (sad_start > start_after_l0.isoformat() or sad_stop < stop_after_l0.isoformat()):
                        sad_status = "PARTIAL"
                    elif len(sad_data) > 0:
                        sad_status = "COMPLETE"
                    # end if

                    isp_validity_processing_completeness_event = {
                        "explicit_reference": session_id,
                        "gauge": {
                            "insertion_type": "INSERT_and_ERASE_per_EVENT_with_PRIORITY",
                            "name": "ISP_VALIDITY_PROCESSING_COMPLETENESS_L1C_CHANNEL_" + channel,
                            "system": satellite
                        },
                        "start": start_after_l0.isoformat(),
                        "stop": stop_after_l0.isoformat(),
                        "links": [{
                            "link": isp_validity_event_link_ref,
                            "link_mode": "by_ref",
                            "name": "PROCESSING_COMPLETENESS",
                            "back_ref": "ISP_VALIDITY"
                        }],
                        "values": [
                            {"name": "status",
                             "type": "text",
                             "value": "MISSING"},
                            {"name": "level",
                             "type": "text",
                             "value": "L1C"},
                            {"name": "downlink_orbit",
                             "type": "double",
                             "value": downlink_orbit},
                            {"name": "satellite",
                             "type": "text",
                             "value": satellite},
                            {"name": "reception_station",
                             "type": "text",
                             "value": station},
                            {"name": "channel",
                             "type": "double",
                             "value": channel},
                            {"name": "vcid",
                             "type": "double",
                             "value": vcid_number},
                            {"name": "playback_type",
                             "type": "text",
                             "value": downlink_mode}
                        ]
                    }

                    if len(intersected_planned_imagings_segments) > 0:
                        isp_validity_processing_completeness_event["values"].append(
                            {"name": "sensing_orbit",
                             "type": "double",
                             "value": sensing_orbit})
                        isp_validity_processing_completeness_event["values"].append(
                            {"name": "imaging_mode",
                             "type": "text",
                             "value": imaging_mode})
                    # end if

                    isp_validity_processing_completeness_event["values"].append(
                        {"name": "sad_status",
                         "type": "text",
                         "value": sad_status})
                    if len(sad_data) > 0:
                        isp_validity_processing_completeness_event["links"].append(
                            {
                                "link": "SAD_DATA",
                                "link_mode": "by_ref",
                                "name": "PROCESSING_COMPLETENESS",
                                "back_ref": "SAD_DATA"
                            })
                    # end if

                    list_of_isp_validity_processing_completeness_events.append(isp_validity_processing_completeness_event)
                # end if

                if imaging_mode in ["NOMINAL"]:

                    sad_status = "MISSING"
                    if len(sad_data) > 0 and (sad_start > start_after_l0.isoformat() or sad_stop < stop_after_l0.isoformat()):
                        sad_status = "PARTIAL"
                    elif len(sad_data) > 0:
                        sad_status = "COMPLETE"
                    # end if

                    isp_validity_processing_completeness_event = {
                        "explicit_reference": session_id,
                        "gauge": {
                            "insertion_type": "INSERT_and_ERASE_per_EVENT_with_PRIORITY",
                            "name": "ISP_VALIDITY_PROCESSING_COMPLETENESS_L2A_CHANNEL_" + channel,
                            "system": satellite
                        },
                        "start": start_after_l0.isoformat(),
                        "stop": stop_after_l0.isoformat(),
                        "links": [{
                            "link": isp_validity_event_link_ref,
                            "link_mode": "by_ref",
                            "name": "PROCESSING_COMPLETENESS",
                            "back_ref": "ISP_VALIDITY"
                        }],
                        "values": [
                            {"name": "status",
                             "type": "text",
                             "value": "MISSING"},
                            {"name": "level",
                             "type": "text",
                             "value": "L2A"},
                            {"name": "downlink_orbit",
                             "type": "double",
                             "value": downlink_orbit},
                            {"name": "satellite",
                             "type": "text",
                             "value": satellite},
                            {"name": "reception_station",
                             "type": "text",
                             "value": station},
                            {"name": "channel",
                             "type": "double",
                             "value": channel},
                            {"name": "vcid",
                             "type": "double",
                             "value": vcid_number},
                            {"name": "playback_type",
                             "type": "text",
                             "value": downlink_mode}
                        ]
                    }

                    if len(intersected_planned_imagings_segments) > 0:
                        isp_validity_processing_completeness_event["values"].append(
                            {"name": "sensing_orbit",
                             "type": "double",
                             "value": sensing_orbit})
                        isp_validity_processing_completeness_event["values"].append(
                            {"name": "imaging_mode",
                             "type": "text",
                             "value": imaging_mode})
                    # end if

                    isp_validity_processing_completeness_event["values"].append(
                        {"name": "sad_status",
                         "type": "text",
                         "value": sad_status})
                    if len(sad_data) > 0:
                        isp_validity_processing_completeness_event["links"].append(
                            {
                                "link": "SAD_DATA",
                                "link_mode": "by_ref",
                                "name": "PROCESSING_COMPLETENESS",
                                "back_ref": "SAD_DATA"
                            })
                    # end if

                    list_of_isp_validity_processing_completeness_events.append(isp_validity_processing_completeness_event)
                # end if
            # end if

            isp_gaps_intersected = ingestion_functions.intersect_timelines([received_datablock], merged_timeline_isp_gaps)

            isp_validity_status = "COMPLETE"
            if len(isp_gaps_intersected) > 0:
                isp_validity_status = "INCOMPLETE"
            # end if

            links = links_isp_validity + [
                {
                    "link": raw_isp_validity_event_link_ref,
                    "link_mode": "by_ref",
                    "name": "ISP_VALIDITY",
                    "back_ref": "RAW_ISP_VALIDITY"
                },{
                    "link": "PLAYBACK_VALIDITY_" + vcid_number,
                    "link_mode": "by_ref",
                    "name": "ISP_VALIDITY",
                    "back_ref": "PLAYBACK_VALIDITY"
                }]

            for isp_gap_intersected in isp_gaps_intersected:
                for id in isp_gap_intersected["id2"]:
                    links.append({
                        "link": id,
                        "link_mode": "by_ref",
                        "name": "ISP_VALIDITY",
                        "back_ref": "ISP_GAP"
                    })
                # end for
            # end for

            sad_status = "MISSING"
            if len(sad_data) > 0 and (sad_start > start.isoformat() or sad_stop < stop.isoformat()):
                sad_status = "PARTIAL"
            elif len(sad_data) > 0:
                sad_status = "COMPLETE"
            # end if

            isp_validity_event = {
                "link_ref": isp_validity_event_link_ref,
                "explicit_reference": session_id,
                "key": session_id + "_CHANNEL_" + channel,
                "gauge": {
                    "insertion_type": "SIMPLE_UPDATE",
                    "name": "ISP_VALIDITY",
                    "system": station
                },
                "links": links,
                "start": start.isoformat(),
                "stop": stop.isoformat(),
                "values": [
                    {"name": "status",
                     "type": "text",
                     "value": isp_validity_status},
                    {"name": "downlink_orbit",
                     "type": "double",
                     "value": downlink_orbit},
                    {"name": "satellite",
                     "type": "text",
                     "value": satellite},
                    {"name": "reception_station",
                     "type": "text",
                     "value": station},
                    {"name": "channel",
                     "type": "double",
                     "value": channel},
                    {"name": "vcid",
                     "type": "double",
                     "value": vcid_number},
                    {"name": "playback_type",
                     "type": "text",
                     "value": downlink_mode}
                ]
            }

            if len(intersected_planned_imagings_segments) > 0:
                isp_validity_event["values"].append(
                    {"name": "sensing_orbit",
                     "type": "double",
                     "value": sensing_orbit})
                isp_validity_event["values"].append(
                    {"name": "imaging_mode",
                     "type": "text",
                     "value": imaging_mode})
            # end if

            isp_validity_event["values"].append(
                {"name": "sad_status",
                 "type": "text",
                 "value": sad_status})
            if len(sad_data) > 0:
                isp_validity_event["links"].append(
                    {
                        "link": "SAD_DATA",
                        "link_mode": "by_ref",
                        "name": "ISP_VALIDITY",
                        "back_ref": "SAD_DATA"
                    })
            # end if

            # Insert isp_validity_event
            list_of_events.append(isp_validity_event)

            completeness_status = "RECEIVED"
            if isp_validity_status != "COMPLETE":
                completeness_status = isp_validity_status
            # end if

            sad_status = "MISSING"
            if len(sad_data) > 0 and (sad_start > start.isoformat() or sad_stop < stop.isoformat()):
                sad_status = "PARTIAL"
            elif len(sad_data) > 0:
                sad_status = "COMPLETE"
            # end if

            isp_validity_completeness_event = {
                "explicit_reference": session_id,
                "key": session_id + "_CHANNEL_" + channel,
                "gauge": {
                    "insertion_type": "INSERT_and_ERASE_per_EVENT_with_PRIORITY",
                    "name": "PLANNED_IMAGING_ISP_COMPLETENESS_CHANNEL_" + channel,
                    "system": satellite
                },
                "links": links_isp_completeness + [
                    {
                        "link": isp_validity_event_link_ref,
                        "link_mode": "by_ref",
                        "name": "PLANNED_COMPLETENESS",
                        "back_ref": "ISP_VALIDITY"
                    }],
                "start": start.isoformat(),
                "stop": stop.isoformat(),
                "values": [
                    {"name": "status",
                     "type": "text",
                     "value": completeness_status},
                    {"name": "downlink_orbit",
                     "type": "double",
                     "value": downlink_orbit},
                    {"name": "satellite",
                     "type": "text",
                     "value": satellite},
                    {"name": "reception_station",
                     "type": "text",
                     "value": station},
                    {"name": "channel",
                     "type": "double",
                     "value": channel},
                    {"name": "vcid",
                     "type": "double",
                     "value": vcid_number},
                    {"name": "playback_type",
                     "type": "text",
                     "value": downlink_mode}
                ]
            }

            if len(intersected_planned_imagings_segments) > 0:
                isp_validity_completeness_event["values"].append(
                    {"name": "sensing_orbit",
                     "type": "double",
                     "value": sensing_orbit})
                isp_validity_completeness_event["values"].append(
                    {"name": "imaging_mode",
                     "type": "text",
                     "value": imaging_mode})
            # end if

            isp_validity_completeness_event["values"].append(
                {"name": "sad_status",
                 "type": "text",
                 "value": sad_status})
            if len(sad_data) > 0:
                isp_validity_completeness_event["links"].append(
                    {
                        "link": "SAD_DATA",
                        "link_mode": "by_ref",
                        "name": "PLANNED_PROCESSING_COMPLETENESS",
                        "back_ref": "SAD_DATA"
                    })
            # end if

            # Insert isp_validity_event
            list_of_isp_completeness_events.append(isp_validity_completeness_event)
        # end for

    # end for

    # Insert completeness operation for the completeness analysis of the plan
    if len(list_of_isp_completeness_events) > 0:
        isp_planning_completeness_event_starts = [event["start"] for event in list_of_isp_completeness_events]
        isp_planning_completeness_event_starts.sort()
        isp_planning_completeness_event_stops = [event["stop"] for event in list_of_isp_completeness_events]
        isp_planning_completeness_event_stops.sort()

        # Generate the footprint of the events
        list_of_isp_completeness_events_with_footprints = functions.associate_footprints(list_of_isp_completeness_events, satellite)
        
        # Completeness operation for the isp completeness analysis of the plan
        isp_planning_completeness_operation = {
            "mode": "insert",
            "dim_signature": {
                "name": "COMPLETENESS_NPPF_" + satellite,
                "exec": "isp_planning_completeness_" + os.path.basename(__file__),
                "version": version
            },
            "source": {
                "name": source["name"],
                "reception_time": source["reception_time"],
                "generation_time": source["generation_time"],
                "validity_start": str(isp_planning_completeness_event_starts[0]),
                "validity_stop": str(isp_planning_completeness_event_stops[-1]),
                "reported_validity_start": source["reported_validity_start"],
                "reported_validity_stop": source["reported_validity_stop"],
                "priority": 30
            },
            "events": list_of_isp_completeness_events_with_footprints
        }

        list_of_planning_operations.append(isp_planning_completeness_operation)
    # end if

    return status

@debug
def _generate_pass_information(xpath_xml, source, engine, query, list_of_annotations, list_of_explicit_references, isp_status, acquisition_status):
    """
    Method to generate the events for the idle operation of the satellite
    :param xpath_xml: source of information that was xpath evaluated
    :type xpath_xml: XPathEvaluator
    :param source: information of the source
    :type source: dict
    :param engine: object to access the engine of the EBOA
    :type engine: Engine
    :param query: object to access the query interface of the EBOA
    :type query: Query
    :param list_of_annotations: list to store the annotations to be inserted into the eboa
    :type list_of_annotations: list
    :param list_of_explicit_references: list to store the annotations to be inserted into the eboa
    :type list_of_explicit_references: list
    """

    # Obtain the satellite
    satellite = source["name"][0:3]

    # Obtain the station
    station = _get_station(xpath_xml)
    
    # Obtain link session ID
    session_id = xpath_xml("/Earth_Explorer_File/Data_Block/input_files/input_file[1]")[0].text[7:31]

    # Obtain channel
    channel = xpath_xml("/Earth_Explorer_File/Data_Block/child::*[contains(name(),'data_')]")[0].tag[6:7]

    # Obtain downlink orbit
    downlink_orbit = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Variable_Header/Downlink_Orbit")[0].text

    # Associate the explicit reference to the group
    explicit_reference = {
        "name": session_id,
        "group": "STATION_LINK_SESSION_IDs"
    }

    list_of_explicit_references.append(explicit_reference)

    # Link session
    link_details_annotation = {
        "explicit_reference": session_id,
        "annotation_cnf": {
            "name": "LINK_DETAILS_CH" + channel,
            "system": station
        },
        "values": [
            {"name": "session_id",
             "type": "text",
             "value": session_id},
            {"name": "downlink_orbit",
             "type": "double",
             "value": downlink_orbit},
            {"name": "satellite",
             "type": "text",
             "value": satellite},
            {"name": "reception_station",
             "type": "text",
             "value": station},
            {"name": "isp_status",
             "type": "text",
             "value": isp_status},
            {"name": "acquisition_status",
             "type": "text",
             "value": acquisition_status}
        ]
    }

    list_of_annotations.append(link_details_annotation)

    return

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
    list_of_planning_operations = []
    list_of_annotations = []
    list_of_explicit_references = []
    file_name = os.path.basename(file_path)

    # Remove namespaces
    new_file = tempfile.NamedTemporaryFile()
    new_file_path = new_file.name

    ingestion_functions.remove_namespaces(file_path, new_file_path)

    # Parse file
    parsed_xml = etree.parse(new_file_path)

    # Register functions for using in XPATH
    ns = etree.FunctionNamespace(None)
    ns["three_letter_to_iso_8601"] = xpath_functions.three_letter_to_iso_8601
    ns["dates_difference"] = xpath_functions.dates_difference
    ns["get_counter_threshold_from_apid"] = xpath_functions.get_counter_threshold_from_apid
    xpath_xml = etree.XPathEvaluator(parsed_xml)

    satellite = file_name[0:3]
    generation_time = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Source/Creation_Date")[0].text.split("=")[1]
    reported_validity_start = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Validity_Period/Validity_Start")[0].text.split("=")[1]
    reported_validity_stop = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Validity_Period/Validity_Stop")[0].text.split("=")[1]
    # Set the validity start to be the first sensing received to avoid error ingesting
    sensing_starts = xpath_xml("/Earth_Explorer_File/Data_Block/*[contains(name(),'data_C')]/Status[@VCID = 2 or @VCID = 4 or @VCID = 5 or @VCID = 6 or @VCID = 20 or @VCID = 21 or @VCID = 22]/ISP_Status/Status/SensStartTime")
    sensing_stops = xpath_xml("/Earth_Explorer_File/Data_Block/*[contains(name(),'data_C')]/Status[@VCID = 2 or @VCID = 4 or @VCID = 5 or @VCID = 6 or @VCID = 20 or @VCID = 21 or @VCID = 22]/ISP_Status/Status/SensStopTime")

    acquisition_starts = xpath_xml("/Earth_Explorer_File/Data_Block/*[contains(name(),'data_C')]/Status/ISP_Status/Status/AcqStartTime")

    if len(sensing_starts) > 0:
        # Set the validity start to be the first sensing timing acquired to avoid error ingesting
        sensing_starts_in_iso_8601 = [functions.three_letter_to_iso_8601(sensing_start.text) for sensing_start in sensing_starts]

        # Sort list
        sensing_starts_in_iso_8601.sort()
        corrected_sensing_start = functions.convert_from_gps_to_utc(sensing_starts_in_iso_8601[0])
        validity_start = corrected_sensing_start
    elif len(acquisition_starts) > 0:
        # Set the validity start to be the first acquisition timing registered to avoid error ingesting
        acquisition_starts_in_iso_8601 = [functions.three_letter_to_iso_8601(acquisition_start.text) for acquisition_start in acquisition_starts]

        # Sort list
        acquisition_starts_in_iso_8601.sort()
        validity_start = acquisition_starts_in_iso_8601[0]
    else:
        validity_start = reported_validity_start
    # end if

    if len(sensing_stops) > 0:
        # Set the validity stop to be the first sensing timing acquired to avoid error ingesting
        sensing_stops_in_iso_8601 = [functions.three_letter_to_iso_8601(sensing_stop.text) for sensing_stop in sensing_stops]

        # Sort list
        sensing_stops_in_iso_8601.sort()
    # end if
    
    acquisition_stops = xpath_xml("/Earth_Explorer_File/Data_Block/*[contains(name(),'data_C')]/Status/AcqStopTime")
    if len(acquisition_stops) > 0:
        # Set the validity stop to be the last acquisition timing registered to avoid error ingesting
        acquisition_stops_in_iso_8601 = [functions.three_letter_to_iso_8601(acquisition_stop.text) for acquisition_stop in acquisition_stops]

        # Sort list
        acquisition_stops_in_iso_8601.sort()
        if len(sensing_stops) > 0 and sensing_stops_in_iso_8601[-1] > acquisition_stops_in_iso_8601[-1]:
            validity_stop = sensing_stops_in_iso_8601[-1]
        else:
            validity_stop = acquisition_stops_in_iso_8601[-1]
        # end if
    else:
        validity_stop = reported_validity_stop
    # end if

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
    
    # Obtain link session ID
    session_id_xpath = xpath_xml("/Earth_Explorer_File/Data_Block/input_files/input_file[1]")

    if len(session_id_xpath) > 0:
        # Extract the information of the received data
        list_of_isp_validity_processing_completeness_events = []
        isp_status = _generate_received_data_information(xpath_xml, source, engine, query, list_of_events, list_of_isp_validity_processing_completeness_events, list_of_planning_operations)

        functions.insert_ingestion_progress(session_progress, general_source_progress, 30)
        
        # Extract the information of the received data
        acquisition_status = _generate_acquisition_data_information(xpath_xml, source, engine, query, list_of_events, list_of_planning_operations)

        functions.insert_ingestion_progress(session_progress, general_source_progress, 50)

        # Extract the information of the pass
        _generate_pass_information(xpath_xml, source, engine, query, list_of_annotations, list_of_explicit_references, isp_status, acquisition_status)

        functions.insert_ingestion_progress(session_progress, general_source_progress, 60)
    # end if

    functions.insert_ingestion_progress(session_progress, general_source_progress, 70)

    # Correct validity start for the case of memory empty before the start of the downlink
    if len(list_of_events) > 0:
        events_starts = [event["start"] for event in list_of_events]
        events_starts.sort()
        if source["validity_start"] > events_starts[0]:
            source["validity_start"] = events_starts[0]
        # end if
    # end if
    
    # Build the xml
    data = {}

    # Generate the footprint of the events
    list_of_events_with_footprint = functions.associate_footprints(list_of_events, satellite)

    functions.insert_ingestion_progress(session_progress, general_source_progress, 90)
    
    data["operations"] = [{
        "mode": "insert",
        "dim_signature": {
            "name": "RECEPTION_" + satellite,
            "exec": os.path.basename(__file__),
            "version": version
        },
        "source": source,
        "explicit_references": list_of_explicit_references,
        "events": list_of_events_with_footprint,
        "annotations": list_of_annotations
    }]

    data["operations"] = data["operations"] + list_of_planning_operations

    functions.insert_ingestion_progress(session_progress, general_source_progress, 95)

    if len(session_id_xpath) > 0:
        # Generate the footprint of the events
        list_of_isp_validity_processing_completeness_events_with_footprint = functions.associate_footprints(list_of_isp_validity_processing_completeness_events, satellite)

        data["operations"].append({
            "mode": "insert",
            "dim_signature": {
                "name": "ISP_VALIDITY_PROCESSING_COMPLETENESS_" + satellite,
                "exec": os.path.basename(__file__),
                "version": version
            },
            "source": {
                "name": file_name,
                "reception_time": reception_time,
                "generation_time": validity_start,
                "validity_start": validity_start,
                "validity_stop": validity_stop,
                "reported_validity_start": reported_validity_start,
                "reported_validity_stop": reported_validity_stop,
                "priority": 10
            },
            "events": list_of_isp_validity_processing_completeness_events_with_footprint
        })
    # end if
        
    functions.insert_ingestion_progress(session_progress, general_source_progress, 100)

    query.close_session()

    new_file.close()
    
    return data
