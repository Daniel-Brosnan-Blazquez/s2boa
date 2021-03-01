"""
Ingestion module for the REP_PASS_2|5 files of Sentinel-2

Written by DEIMOS Space S.L. (dibb)

module eboa
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
    station = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Source/System")[0].text

    # Obtain link session ID
    session_id = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/File_Type")[0].text + "_" + xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Validity_Period/Validity_Start")[0].text.split("UTC=",1)[1]

    # Obtain downlink orbit
    downlink_orbit = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Variable_Header/Downlink_Orbit")[0].text

    # List for the playback completeness analysis of the plan
    list_of_playback_completeness_events = []
    
    vcids = xpath_xml("/Earth_Explorer_File/Data_Block/*[contains(name(),'data_C')]/Status[NumFrames > 0 and (@VCID = 2 or @VCID = 3 or @VCID = 4 or @VCID = 5 or @VCID = 6 or @VCID = 20 or @VCID = 21 or @VCID = 22)]")
    for vcid in vcids:
        # Obtain channel
        channel = vcid.xpath("..")[0].tag[6:7]

        vcid_number = vcid.get("VCID")
        downlink_mode = functions.get_vcid_mode(vcid_number)
        # Acquisition segment
        acquisition_start = functions.three_letter_to_iso_8601(vcid.xpath("AcqStartTime")[0].text)
        acquisition_stop = functions.three_letter_to_iso_8601(vcid.xpath("AcqStopTime")[0].text)

        # Reference to the playback validity event
        playback_validity_event_link_ref = "PLAYBACK_" + downlink_mode + "_VALIDITY_" + vcid_number

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
                        "insertion_type": "EVENT_KEYS",
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

        matching_status = "NO_MATCHED_PLANNED_PLAYBACK"
        links_playback_validity = []
        links_playback_completeness = []
        query_start = acquisition_start
        # Obtain planned playbacks
        if downlink_mode in ["NOMINAL", "NRT"]:
            planned_playback_types = [downlink_mode, "REGULAR"]
        elif downlink_mode in ["SAD", "HKTM"]:
            # The SAD and HKTM playbacks have no duration because the duration is not set in the NPPF and can be modified, so in order to get the information from DDBB, the start value of the query is moved to start -11 seconds (correct margin as per mission specification there must be always 11 seconds between playbacks)
            query_start = str(parser.parse(acquisition_start) + datetime.timedelta(seconds=-11))
            planned_playback_types = [downlink_mode, "HKTM_SAD"]
        else:
            planned_playback_types = [downlink_mode]
        # end if
        corrected_planned_playbacks = query.get_events(gauge_names = {"op": "==", "filter": "PLANNED_PLAYBACK_CORRECTION"},
                                                       gauge_systems = {"op": "==", "filter": satellite},
                                                       value_filters = [{"name": {"op": "==", "filter": "playback_type"}, "type": "text", "value": {"op": "in", "filter": planned_playback_types}}],
                                                       start_filters = [{"date": acquisition_stop, "op": "<"}],
                                                       stop_filters = [{"date": query_start, "op": ">"}])

        # Get the links to the plan
        for corrected_planned_playback in corrected_planned_playbacks:
            matching_status = "MATCHED_PLANNED_PLAYBACK"

            planned_playback_uuid = [event_link.event_uuid_link for event_link in corrected_planned_playback.eventLinks if event_link.name == "PLANNED_EVENT"][0]

            links_playback_validity.append({
                "link": str(planned_playback_uuid),
                "link_mode": "by_uuid",
                "name": "PLAYBACK_VALIDITY",
                "back_ref": "PLANNED_PLAYBACK"
            })
            links_playback_completeness.append({
                "link": str(planned_playback_uuid),
                "link_mode": "by_uuid",
                "name": "PLAYBACK_COMPLETENESS",
                "back_ref": "PLANNED_PLAYBACK"
            })
        # end for

        playback_validity_event = {
            "link_ref": playback_validity_event_link_ref,
            "explicit_reference": session_id,
            "key": session_id,
            "gauge": {
                "insertion_type": "EVENT_KEYS",
                "name": "PLAYBACK_VALIDITY_" + vcid_number,
                "system": station
            },
            "links": links_playback_validity,
            "start": acquisition_start,
            "stop": acquisition_stop,
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
                {"name": "matching_plan_status",
                 "type": "text",
                 "value": matching_status}
            ]
        }
        # Insert playback_validity_event
        list_of_events.append(playback_validity_event)

        completeness_status = "RECEIVED"
        if status != "COMPLETE":
            completeness_status = status
        # end if

        playback_completeness_event = {
            "explicit_reference": session_id,
            "key": session_id + "_CHANNEL_" + channel,
            "gauge": {
                "insertion_type": "INSERT_and_ERASE_per_EVENT_with_PRIORITY",
                "name": "PLANNED_PLAYBACK_COMPLETENESS_CHANNEL_" + channel,
                "system": satellite
            },
            "links": links_playback_completeness,
            "start": acquisition_start,
            "stop": acquisition_stop,
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
                {"name": "playback_type",
                 "type": "text",
                 "value": downlink_mode},
            ]
        }

        # Insert playback_completeness_event
        list_of_playback_completeness_events.append(playback_completeness_event)
    # end for

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
    station = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Source/System")[0].text

    # Obtain link session ID
    session_id = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/File_Type")[0].text + "_" + xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Validity_Period/Validity_Start")[0].text.split("UTC=",1)[1]

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
            "key": session_id,
            "gauge": {
                "insertion_type": "EVENT_KEYS",
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

    isp_duration_received = 0
    links_raw_isp_validity = []
    
    vcids = xpath_xml("/Earth_Explorer_File/Data_Block/*[contains(name(),'data_C')]/Status[number(NumFrames) > 0 and (@VCID = 4 or @VCID = 5 or @VCID = 6)]")
    for vcid in vcids:
        # Iterator and timeline for the ISP gaps
        isp_gap_iterator = 0
        timeline_isp_gaps = []

        vcid_number = vcid.get("VCID")
        corresponding_vcid = xpath_xml("/Earth_Explorer_File/Data_Block/*[contains(name(),'data_C')]/Status[number(NumFrames) > 0 and (@VCID = $corresponding_vcid_number)]", corresponding_vcid_number = int(vcid_number) + 16)        

        downlink_mode = functions.get_vcid_mode(vcid_number)
        # Obtain the sensing segment received (EFEP reports only give information about the start date of the first and last scenes)
        sensing_starts = xpath_xml("/Earth_Explorer_File/Data_Block/*[contains(name(),'data_C')]/Status[number(NumFrames) > 0 and (number(@VCID) = $vcid_number or number(@VCID) = $corresponding_vcid_number)]/ISP_Status/Status/SensStartTime", vcid_number = int(vcid_number), corresponding_vcid_number = int(vcid_number) + 16)
        sensing_starts_in_iso_8601 = [functions.three_letter_to_iso_8601(sensing_start.text) for sensing_start in sensing_starts]

        # Sort list
        sensing_starts_in_iso_8601.sort()
        sensing_start = sensing_starts_in_iso_8601[0]
        corrected_sensing_start = functions.convert_from_gps_to_utc(sensing_start)

        sensing_stops = xpath_xml("/Earth_Explorer_File/Data_Block/*[contains(name(),'data_C')]/Status[number(NumFrames) > 0 and (number(@VCID) = $vcid_number or number(@VCID) = $corresponding_vcid_number)]/ISP_Status/Status/SensStopTime", vcid_number = int(vcid_number), corresponding_vcid_number = int(vcid_number) + 16)
        sensing_stops_in_iso_8601 = [functions.three_letter_to_iso_8601(sensing_stop.text) for sensing_stop in sensing_stops]

        # Sort list
        sensing_stops_in_iso_8601.sort()
        sensing_stop = sensing_stops_in_iso_8601[-1]
        # Add 1 scene at the end
        corrected_sensing_stop = functions.convert_from_gps_to_utc(sensing_stop)

        # The data comes in pairs of VCIDs
        # 4 - 20
        # 5 - 21
        # 6 - 22
        # Get all the APIDs which contain data
        apids = xpath_xml("/Earth_Explorer_File/Data_Block/*[contains(name(),'data_C')]/Status[number(@VCID) = $vcid_number or number(@VCID) = $corresponding_vcid_number]/ISP_Status/Status[NumPackets > 0]", vcid_number = int(vcid_number), corresponding_vcid_number = int(vcid_number) + 16)

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
            sensing_gaps = apid.xpath("Gaps/Gap[dates_difference(three_letter_to_iso_8601(string(PostSensTime)),three_letter_to_iso_8601(string(PreSensTime))) > 4 and number(PreCounter) = $counter_threshold and number(PostCounter) = 0]", counter_threshold=counter_threshold)
            for sensing_gap in sensing_gaps:
                sensing_gaps_per_apid[apid_number].append({
                    "id": apid_number,
                    "start": parser.parse(functions.convert_from_gps_to_utc(functions.three_letter_to_iso_8601(sensing_gap.xpath("string(PreSensTime)")))),
                    "stop": parser.parse(functions.convert_from_gps_to_utc(functions.three_letter_to_iso_8601(sensing_gap.xpath("string(PostSensTime)")))),
                })
            # end for
            if len(sensing_gaps_per_apid[apid_number]) > 0:
                timelines_of_sensing_gaps.append(sensing_gaps_per_apid[apid_number])
            # end if
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

        # Received datablocks
        covered_sensing = {
            "id": "covered_sensing",
            "start": parser.parse(corrected_sensing_start),
            "stop": parser.parse(corrected_sensing_stop)
        }
        received_datablocks = [segment for segment in ingestion_functions.difference_timelines([covered_sensing], sensing_gaps) if segment["id"] == "covered_sensing"]

        # Create ISP gaps for complete missing scenes
        for apid_number in functions.get_apid_numbers():
            gaps = []
            if str(apid_number) in received_datablocks_per_apid:
                gaps = ingestion_functions.difference_timelines(received_datablocks, received_datablocks_per_apid[str(apid_number)])
            else:
                gaps = received_datablocks
            # end if
            # end if
            for gap in gaps:
                start = gap["start"]
                stop = gap["stop"] + datetime.timedelta(seconds=3.608)
                status = "INCOMPLETE"
                band_detector = functions.get_band_detector(apid_number)

                isp_gap_event = {
                    "link_ref": "ISP_GAP_" + str(isp_gap_iterator),
                    "explicit_reference": session_id,
                    "key": session_id,
                    "gauge": {
                        "insertion_type": "EVENT_KEYS",
                        "name": "ISP_GAP",
                        "system": station
                    },
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
                "key": session_id,
                "gauge": {
                    "insertion_type": "EVENT_KEYS",
                    "name": "ISP_GAP",
                    "system": station
                },
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

        # Create ISP gaps for gaps smaller than a scene
        gaps_smaller_than_scene = xpath_xml("/Earth_Explorer_File/Data_Block/*[contains(name(),'data_C')]/Status[number(@VCID) = $vcid_number or number(@VCID) = $corresponding_vcid_number]/ISP_Status/Status[NumPackets > 0]/Gaps/Gap[(not (PreCounter = get_counter_threshold_from_apid(string(../../@APID))) and not (PostCounter = 0)) or not (PostCounter = 0)]", vcid_number = int(vcid_number), corresponding_vcid_number = int(vcid_number) + 16)

        for gap in gaps_smaller_than_scene:
            status = "INCOMPLETE"
            apid_number = gap.xpath("../../@APID")[0]
            band_detector = functions.get_band_detector(apid_number)

            counter_threshold = functions.get_counter_threshold(band_detector["band"])
            scene_start = parser.parse(functions.convert_from_gps_to_utc(functions.three_letter_to_iso_8601(gap.xpath("string(PreSensTime)"))))
            scene_stop = parser.parse(functions.convert_from_gps_to_utc(functions.three_letter_to_iso_8601(gap.xpath("string(PostSensTime)"))))

            number_missing_scenes = math.ceil((scene_stop - scene_start).total_seconds() / 3.608)

            counter_start = int(gap.xpath("string(PreCounter)"))

            counter_stop = int(gap.xpath("string(PostCounter)"))

            missing_packets = (counter_stop - counter_start) + number_missing_scenes * counter_threshold

            seconds_from_scene_start_to_gap_start = (counter_start / counter_threshold) * 3.608
            seconds_from_scene_stop_to_gap_stop = (counter_stop / counter_threshold) * 3.608

            start = scene_start + datetime.timedelta(seconds=seconds_from_scene_start_to_gap_start)
            stop = scene_stop + datetime.timedelta(seconds=seconds_from_scene_stop_to_gap_stop)

            isp_gap_event = {
                "link_ref": "ISP_GAP_" + str(isp_gap_iterator),
                "explicit_reference": session_id,
                "key": session_id,
                "gauge": {
                    "insertion_type": "EVENT_KEYS",
                    "name": "ISP_GAP",
                    "system": station
                },
                "start": start.isoformat(),
                "stop": stop.isoformat(),
                "values": [
                    {"name": "impact",
                     "type": "text",
                     "value": "SMALLER_THAN_A_SCENE"},
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

        # Create the ISP_VALIDITY events
        for received_datablock in received_datablocks:
            start = received_datablock["start"]
            stop = received_datablock["stop"] + datetime.timedelta(seconds=3.608)
            isp_duration_received += (stop - start).total_seconds()
            sensing_orbit = -1
            links_isp_validity = []
            links_isp_completeness = []
            intersected_planned_imagings_segments = ingestion_functions.intersect_timelines([received_datablock], corrected_planned_imagings_segments)
            matching_status = "NO_MATCHED_PLANNED_IMAGING"

            # ISP validity event reference
            isp_validity_event_link_ref = "ISP_VALIDITY_" + vcid_number + "_" + str(start)

            if len(intersected_planned_imagings_segments) > 0:
                matching_status = "MATCHED_PLANNED_IMAGING"
                intersected_planned_imagings_segment = intersected_planned_imagings_segments[0]
                corrected_planned_imaging = [event for event in corrected_planned_imagings if event.event_uuid == intersected_planned_imagings_segment["id2"]][0]
                planned_imaging_uuid = [event_link.event_uuid_link for event_link in corrected_planned_imaging.eventLinks if event_link.name == "PLANNED_EVENT"][0]
                sensing_orbit_values = query.get_event_values_interface(value_type="double",
                                                                        value_filters=[{"name": {"op": "==", "filter": "start_orbit"}, "type": "double"}],
                                                                        event_uuids = {"op": "in", "filter": [planned_imaging_uuid]})
                sensing_orbit = sensing_orbit_values[0].value
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

                # ISP validity processing completeness events
                imaging_mode_values = query.get_event_values_interface(value_type="text",
                                                                        value_filters=[{"name": {"op": "==", "filter": "imaging_mode"}, "type": "text"}],
                                                                        event_uuids = {"op": "in", "filter": [planned_imaging_uuid]})
                imaging_mode = imaging_mode_values[0].value

                for channel in ["1","2"]:

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
                            {"name": "playback_type",
                             "type": "text",
                             "value": downlink_mode},
                            {"name": "matching_plan_status",
                             "type": "text",
                             "value": matching_status},
                            {"name": "sensing_orbit",
                             "type": "double",
                             "value": sensing_orbit},
                            {"name": "imaging_mode",
                             "type": "text",
                             "value": imaging_mode}
                        ]
                    }

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
                    if stop_after_l0 > start_after_l0:

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
                                {"name": "playback_type",
                                 "type": "text",
                                 "value": downlink_mode},
                                {"name": "matching_plan_status",
                                 "type": "text",
                                 "value": matching_status},
                                {"name": "sensing_orbit",
                                 "type": "double",
                                 "value": sensing_orbit},
                                {"name": "imaging_mode",
                                 "type": "text",
                                 "value": imaging_mode}
                            ]
                        }

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
                                    {"name": "playback_type",
                                     "type": "text",
                                     "value": downlink_mode},
                                    {"name": "matching_plan_status",
                                     "type": "text",
                                     "value": matching_status},
                                    {"name": "sensing_orbit",
                                     "type": "double",
                                     "value": sensing_orbit},
                                    {"name": "imaging_mode",
                                     "type": "text",
                                     "value": imaging_mode}
                                ]
                            }

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
                                    {"name": "playback_type",
                                     "type": "text",
                                     "value": downlink_mode},
                                    {"name": "matching_plan_status",
                                     "type": "text",
                                     "value": matching_status},
                                    {"name": "sensing_orbit",
                                     "type": "double",
                                     "value": sensing_orbit},
                                    {"name": "imaging_mode",
                                     "type": "text",
                                     "value": imaging_mode}
                                ]
                            }

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
                                    {"name": "playback_type",
                                     "type": "text",
                                     "value": downlink_mode},
                                    {"name": "matching_plan_status",
                                     "type": "text",
                                     "value": matching_status},
                                    {"name": "sensing_orbit",
                                     "type": "double",
                                     "value": sensing_orbit},
                                    {"name": "imaging_mode",
                                     "type": "text",
                                     "value": imaging_mode}
                                ]
                            }

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
                # end for
            # end if

            isp_gaps_intersected = ingestion_functions.intersect_timelines([received_datablock], merged_timeline_isp_gaps)

            isp_validity_status = "COMPLETE"
            if len(isp_gaps_intersected) > 0:
                isp_validity_status = "INCOMPLETE"
            # end if

            links_isp_validity.append({
                "link": "PLAYBACK_" + downlink_mode + "_VALIDITY_" + vcid_number,
                "link_mode": "by_ref",
                "name": "ISP_VALIDITY",
                "back_ref": "PLAYBACK_VALIDITY"
            })
            if len(corresponding_vcid) > 0:
                links_isp_validity.append({
                    "link": "PLAYBACK_" + downlink_mode + "_VALIDITY_" + str(int(vcid_number) + 16),
                    "link_mode": "by_ref",
                    "name": "ISP_VALIDITY",
                    "back_ref": "PLAYBACK_VALIDITY"
                })
            # end if
            links_isp_validity.append({
                "link": "RAW_ISP_VALIDITY",
                "link_mode": "by_ref",
                "name": "ISP_VALIDITY",
                "back_ref": "RAW_ISP_VALIDITY"
            })
            links_raw_isp_validity.append({
                "link": "PLAYBACK_" + downlink_mode + "_VALIDITY_" + vcid_number,
                "link_mode": "by_ref",
                "name": "RAW_ISP_VALIDITY",
                "back_ref": "PLAYBACK_VALIDITY"
            })
            if len(corresponding_vcid) > 0:
                links_raw_isp_validity.append({
                    "link": "PLAYBACK_" + downlink_mode + "_VALIDITY_" + str(int(vcid_number) + 16),
                    "link_mode": "by_ref",
                    "name": "RAW_ISP_VALIDITY",
                    "back_ref": "PLAYBACK_VALIDITY"
                })
            # end if

            for isp_gap_intersected in isp_gaps_intersected:
                for id in isp_gap_intersected["id2"]:
                    links_isp_validity.append({
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
                "key": session_id,
                "gauge": {
                    "insertion_type": "EVENT_KEYS",
                    "name": "ISP_VALIDITY",
                    "system": station
                },
                "links": links_isp_validity,
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
                    {"name": "playback_type",
                     "type": "text",
                     "value": downlink_mode},
                    {"name": "matching_plan_status",
                     "type": "text",
                     "value": matching_status},
                    {"name": "sensing_orbit",
                     "type": "double",
                     "value": sensing_orbit}
                ]
            }

            if len(intersected_planned_imagings_segments) > 0:
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

            links_isp_completeness.append({
                "link": isp_validity_event_link_ref,
                "link_mode": "by_ref",
                "name": "PLANNED_COMPLETENESS",
                "back_ref": "ISP_VALIDITY"
            })

            for channel in ["1","2"]:

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
                    "links": links_isp_completeness,
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
                        {"name": "playback_type",
                         "type": "text",
                         "value": downlink_mode},
                        {"name": "sensing_orbit",
                         "type": "double",
                         "value": sensing_orbit}
                    ]
                }

                if len(intersected_planned_imagings_segments) > 0:
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

    # end for

    if len(xpath_xml("/Earth_Explorer_File/Data_Block/*[contains(name(),'data_C')]/Status[@VCID = 4 or @VCID = 5 or @VCID = 6 or @VCID = 20 or @VCID = 21 or @VCID = 22]/ISP_Status/Summary[number(NumPackets) > 0]")) > 0:

        # Covered period by the sensing
        sensing_starts = xpath_xml("/Earth_Explorer_File/Data_Block/*[contains(name(),'data_C')]/Status[@VCID = 4 or @VCID = 5 or @VCID = 6 or @VCID = 20 or @VCID = 21 or @VCID = 22]/ISP_Status/Summary[number(NumPackets) > 0]/SensStartTime")
        sensing_starts_in_iso_8601 = [functions.three_letter_to_iso_8601(sensing_start.text) for sensing_start in sensing_starts]

        # Sort list
        sensing_starts_in_iso_8601.sort()
        sensing_start = sensing_starts_in_iso_8601[0]
        corrected_sensing_start = functions.convert_from_gps_to_utc(sensing_start)

        sensing_stops = xpath_xml("/Earth_Explorer_File/Data_Block/*[contains(name(),'data_C')]/Status[@VCID = 4 or @VCID = 5 or @VCID = 6 or @VCID = 20 or @VCID = 21 or @VCID = 22]/ISP_Status/Summary[number(NumPackets) > 0]/SensStopTime")
        sensing_stops_in_iso_8601 = [functions.three_letter_to_iso_8601(sensing_stop.text) for sensing_stop in sensing_stops]

        # Sort list
        sensing_stops_in_iso_8601.sort()
        sensing_stop = sensing_stops_in_iso_8601[-1]
        # Add 1 scene at the end
        corrected_sensing_stop = functions.convert_from_gps_to_utc(sensing_stop)

        # Expected number of packets
        expected_number_scenes = round(isp_duration_received / 3.608)
        expected_number_packets = expected_number_scenes * 12960
        received_number_packets = sum([int(num_packets.text) for num_packets in xpath_xml("/Earth_Explorer_File/Data_Block/*[contains(name(),'data_C')]/Status[@VCID = 4 or @VCID = 5 or @VCID = 6 or @VCID = 20 or @VCID = 21 or @VCID = 22]/ISP_Status/Summary[number(NumPackets) > 0]/NumPackets")])

        if (expected_number_packets - received_number_packets) == 0:
            packet_status = "OK"
        else:
            packet_status = "MISSING"
        # end if

        sad_status = "MISSING"
        if len(sad_data) > 0 and (sad_start > corrected_sensing_start or sad_stop < corrected_sensing_stop):
            sad_status = "PARTIAL"
        elif len(sad_data) > 0:
            sad_status = "COMPLETE"
        # end if
        
        raw_isp_validity_event = {
            "link_ref": "RAW_ISP_VALIDITY",
            "explicit_reference": session_id,
            "key": session_id,
            "gauge": {
                "insertion_type": "EVENT_KEYS",
                "name": "RAW_ISP_VALIDITY",
                "system": station
            },
            "links": links_raw_isp_validity,
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
                {"name": "num_packets",
                 "type": "double",
                 "value": str(received_number_packets)},
                {"name": "num_frames",
                 "type": "double",
                 "value": vcid.xpath("NumFrames")[0].text},
                {"name": "expected_num_packets",
                 "type": "double",
                 "value": str(expected_number_packets)},
                {"name": "diff_expected_received",
                 "type": "double",
                 "value": str(expected_number_packets - received_number_packets)},
                {"name": "packet_status",
                 "type": "text",
                 "value": packet_status}
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
        
        list_of_events.append(raw_isp_validity_event)
    # end if
        
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
    station = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Source/System")[0].text

    # Obtain link session ID
    session_id = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/File_Type")[0].text + "_" + xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Validity_Period/Validity_Start")[0].text.split("UTC=",1)[1]

    # Obtain downlink orbit
    downlink_orbit = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Variable_Header/Downlink_Orbit")[0].text

    # Associate the explicit reference to the group STATION_LINK_SESSION_IDs
    explicit_reference = {
        "name": session_id,
        "group": "STATION_LINK_SESSION_IDs"
    }

    # Link session
    link_details_annotation = {
        "explicit_reference": session_id,
        "annotation_cnf": {
            "name": "LINK_DETAILS",
            "system": station
        },
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

@debug
def _generate_distribution_information(xpath_xml, source, engine, query, list_of_events):
    """
    Method to generate the events associated to the distribution information
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
    """

    # Obtain the satellite
    satellite = source["name"][0:3]

    # Obtain the station
    station = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Source/System")[0].text

    # Obtain link session ID
    session_id = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/File_Type")[0].text + "_" + xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Validity_Period/Validity_Start")[0].text.split("UTC=",1)[1]

    # Obtain downlink orbit
    downlink_orbit = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Variable_Header/Downlink_Orbit")[0].text
    
    # Obtain number of received packets and transfer frames
    number_of_received_isps_channel_1 = sum([int(num.text) for num in xpath_xml("/Earth_Explorer_File/Data_Block/data_C1/Status[NumFrames > 0 and (@VCID = 2 or @VCID = 4 or @VCID = 5 or @VCID = 6 or @VCID = 20 or @VCID = 21 or @VCID = 22)]/ISP_Status/Summary/NumPackets")])
    number_of_received_isps_channel_2 = sum([int(num.text) for num in xpath_xml("/Earth_Explorer_File/Data_Block/data_C2/Status[NumFrames > 0 and (@VCID = 2 or @VCID = 4 or @VCID = 5 or @VCID = 6 or @VCID = 20 or @VCID = 21 or @VCID = 22)]/ISP_Status/Summary/NumPackets")])
    number_of_received_transfer_frames_channel_1 = sum([int(num.text) for num in xpath_xml("/Earth_Explorer_File/Data_Block/data_C1/Status[NumFrames > 0 and @VCID = 3]/NumFrames")])
    number_of_received_transfer_frames_channel_2 = sum([int(num.text) for num in xpath_xml("/Earth_Explorer_File/Data_Block/data_C2/Status[NumFrames > 0 and @VCID = 3]/NumFrames")])

    # Obtain number of distributed packets and transfer frames    
    number_of_distributed_isps_channel_1 = sum([int(num.text) for num in xpath_xml("/Earth_Explorer_File/Data_Block/distribution_C1_ISP/NumberofPackets")])
    number_of_distributed_isps_channel_2 = sum([int(num.text) for num in xpath_xml("/Earth_Explorer_File/Data_Block/distribution_C2_ISP/NumberofPackets")])
    number_of_distributed_transfer_frames_channel_1 = sum([int(num.text) for num in xpath_xml("/Earth_Explorer_File/Data_Block/distribution_C1_TF/NumberofPackets")])
    number_of_distributed_transfer_frames_channel_2 = sum([int(num.text) for num in xpath_xml("/Earth_Explorer_File/Data_Block/distribution_C2_TF/NumberofPackets")])

    # Obtain the status of distribution
    status_distribution_isps_channel_1 = xpath_xml("/Earth_Explorer_File/Data_Block/distribution_C1_ISP[NumberofPackets > 0 or (NumberofPackets = 0 and not(Status = 'DELIVERED'))]/Status")
    status_distribution_isps_channel_2 = xpath_xml("/Earth_Explorer_File/Data_Block/distribution_C2_ISP[NumberofPackets > 0 or (NumberofPackets = 0 and not(Status = 'DELIVERED'))]/Status")
    status_distribution_transfer_frames_channel_1 = xpath_xml("/Earth_Explorer_File/Data_Block/distribution_C1_TF/Status")
    status_distribution_transfer_frames_channel_2 = xpath_xml("/Earth_Explorer_File/Data_Block/distribution_C2_TF/Status")        
    
    if len(status_distribution_isps_channel_1) > 0 or len(status_distribution_isps_channel_2) > 0 or len(status_distribution_transfer_frames_channel_1) > 0 or len(status_distribution_transfer_frames_channel_2) > 0:

        # Get the acquisition timings for getting the covered planned playbacks
        acquisition_starts = xpath_xml("/Earth_Explorer_File/Data_Block/*[contains(name(),'data_C')]/Status/AcqStartTime")
        acquisition_starts_in_iso_8601 = [functions.three_letter_to_iso_8601(acquisition_start.text) for acquisition_start in acquisition_starts]
        acquisition_starts_in_iso_8601.sort()
        query_start = (parser.parse(acquisition_starts_in_iso_8601[0]) - datetime.timedelta(seconds=10)).isoformat()

        acquisition_stops = xpath_xml("/Earth_Explorer_File/Data_Block/*[contains(name(),'data_C')]/Status/AcqStopTime")
        acquisition_stops_in_iso_8601 = [functions.three_letter_to_iso_8601(acquisition_stop.text) for acquisition_stop in acquisition_stops]
        acquisition_stops_in_iso_8601.sort()
        query_stop = acquisition_stops_in_iso_8601[-1]

        # Get planned playbacks covered by the acquisition timings
        corrected_planned_playbacks_isps = query.get_events(gauge_names = {"op": "==", "filter": "PLANNED_PLAYBACK_CORRECTION"},
                                                            gauge_systems = {"op": "==", "filter": satellite},
                                                            value_filters = [{"name": {"op": "==", "filter": "playback_type"}, "type": "text", "value": {"op": "notin", "filter": ["HKTM", "HKTM_SAD"]}}],
                                                            start_filters = [{"date": query_start, "op": ">="}],
                                                            stop_filters = [{"date": query_stop, "op": "<="}])
        corrected_planned_playbacks_hktm = query.get_events(gauge_names = {"op": "==", "filter": "PLANNED_PLAYBACK_CORRECTION"},
                                                            gauge_systems = {"op": "==", "filter": satellite},
                                                            value_filters = [{"name": {"op": "==", "filter": "playback_type"}, "type": "text", "value": {"op": "in", "filter": ["HKTM", "HKTM_SAD"]}}],
                                                            start_filters = [{"date": query_start, "op": ">="}],
                                                            stop_filters = [{"date": query_stop, "op": "<="}])

        links_isps = []
        for corrected_planned_playback in corrected_planned_playbacks_isps:
            planned_playback_uuid = [event_link.event_uuid_link for event_link in corrected_planned_playback.eventLinks if event_link.name == "PLANNED_EVENT"][0]            
            links_isps.append({
                "link": str(planned_playback_uuid),
                "link_mode": "by_uuid",
                "name": "DISTRIBUTION_STATUS",
                "back_ref": "PLANNED_PLAYBACK"
            })
        # end for

        links_hktm = []
        for corrected_planned_playback in corrected_planned_playbacks_hktm:
            planned_playback_uuid = [event_link.event_uuid_link for event_link in corrected_planned_playback.eventLinks if event_link.name == "PLANNED_EVENT"][0]            
            links_hktm.append({
                "link": str(planned_playback_uuid),
                "link_mode": "by_uuid",
                "name": "DISTRIBUTION_STATUS",
                "back_ref": "PLANNED_PLAYBACK"
            })
        # end for
        
        if len(status_distribution_isps_channel_1) > 0:
            vcids = xpath_xml("/Earth_Explorer_File/Data_Block/data_C1/Status[number(NumFrames) > 0 and (@VCID = 2 or @VCID = 4 or @VCID = 5 or @VCID = 6)]")
            links_isps_channel_1 = links_isps.copy()
            for vcid in vcids:
                vcid_number = vcid.get("VCID")
                downlink_mode = functions.get_vcid_mode(vcid_number)
                links_isps_channel_1.append({
                    "link": "PLAYBACK_" + downlink_mode + "_VALIDITY_" + vcid_number,
                    "link_mode": "by_ref",
                    "name": "DISTRIBUTION_STATUS",
                    "back_ref": "PLAYBACK_VALIDITY"
                })
            # end for
            completeness_status = "OK"
            if number_of_distributed_isps_channel_1 != number_of_received_isps_channel_1:
                completeness_status = "NOK"
            # end if
            distribution_status_event = {
                "explicit_reference": session_id,
                "key": session_id,
                "gauge": {
                    "insertion_type": "EVENT_KEYS",
                    "name": "PLAYBACK_ISP_DISTRIBUTION_STATUS_CHANNEL_1",
                    "system": station
                },
                "links": links_isps_channel_1,
                "start": acquisition_starts_in_iso_8601[0],
                "stop": acquisition_stops_in_iso_8601[-1],
                "values": [
                    {"name": "status",
                     "type": "text",
                     "value": status_distribution_isps_channel_1[0].text},
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
                     "value": 1},
                    {"name": "completeness_status",
                     "type": "text",
                     "value": completeness_status},
                    {"name": "number_of_received_isps",
                     "type": "double",
                     "value": number_of_received_isps_channel_1},
                    {"name": "number_of_distributed_isps",
                     "type": "double",
                     "value": number_of_distributed_isps_channel_1},
                    {"name": "completeness_difference",
                     "type": "double",
                     "value": number_of_received_isps_channel_1 - number_of_distributed_isps_channel_1}
                ]
            }
            # Insert playback_validity_event
            list_of_events.append(distribution_status_event)
        # end if

        if len(status_distribution_isps_channel_2) > 0:
            vcids = xpath_xml("/Earth_Explorer_File/Data_Block/data_C2/Status[number(NumFrames) > 0 and (@VCID = 2 or @VCID = 20 or @VCID = 21 or @VCID = 22)]")
            links_isps_channel_2 = links_isps.copy()
            for vcid in vcids:
                vcid_number = vcid.get("VCID")
                downlink_mode = functions.get_vcid_mode(vcid_number)
                links_isps_channel_2.append({
                    "link": "PLAYBACK_" + downlink_mode + "_VALIDITY_" + vcid_number,
                    "link_mode": "by_ref",
                    "name": "DISTRIBUTION_STATUS",
                    "back_ref": "PLAYBACK_VALIDITY"
                })
            # end for
            completeness_status = "OK"
            if number_of_distributed_isps_channel_2 != number_of_received_isps_channel_2:
                completeness_status = "NOK"
            # end if
            distribution_status_event = {
                "explicit_reference": session_id,
                "key": session_id,
                "gauge": {
                    "insertion_type": "EVENT_KEYS",
                    "name": "PLAYBACK_ISP_DISTRIBUTION_STATUS_CHANNEL_2",
                    "system": station
                },
                "links": links_isps_channel_2,
                "start": acquisition_starts_in_iso_8601[0],
                "stop": acquisition_stops_in_iso_8601[-1],
                "values": [
                    {"name": "status",
                     "type": "text",
                     "value": status_distribution_isps_channel_2[0].text},
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
                     "value": 2},
                    {"name": "completeness_status",
                     "type": "text",
                     "value": completeness_status},
                    {"name": "number_of_received_isps",
                     "type": "double",
                     "value": number_of_received_isps_channel_2},
                    {"name": "number_of_distributed_isps",
                     "type": "double",
                     "value": number_of_distributed_isps_channel_2},
                    {"name": "completeness_difference",
                     "type": "double",
                     "value": number_of_received_isps_channel_2 - number_of_distributed_isps_channel_2}
                ]
            }
            # Insert playback_validity_event
            list_of_events.append(distribution_status_event)
        # end if

        if len(status_distribution_transfer_frames_channel_1) > 0:
            vcids = xpath_xml("/Earth_Explorer_File/Data_Block/data_C1/Status[number(NumFrames) > 0 and @VCID = 3]")
            links_hktm_channel_1 = links_hktm.copy()
            for vcid in vcids:
                vcid_number = vcid.get("VCID")
                downlink_mode = functions.get_vcid_mode(vcid_number)
                links_hktm_channel_1.append({
                    "link": "PLAYBACK_" + downlink_mode + "_VALIDITY_" + vcid_number,
                    "link_mode": "by_ref",
                    "name": "DISTRIBUTION_STATUS",
                    "back_ref": "PLAYBACK_VALIDITY"
                })
            # end for
            completeness_status = "OK"
            if number_of_distributed_transfer_frames_channel_1 != number_of_received_transfer_frames_channel_1:
                completeness_status = "NOK"
            # end if
            distribution_status_event = {
                "explicit_reference": session_id,
                "key": session_id,
                "gauge": {
                    "insertion_type": "EVENT_KEYS",
                    "name": "PLAYBACK_HKTM_DISTRIBUTION_STATUS_CHANNEL_1",
                    "system": station
                },
                "links": links_hktm_channel_1,
                "start": acquisition_starts_in_iso_8601[0],
                "stop": acquisition_stops_in_iso_8601[-1],
                "values": [
                    {"name": "status",
                     "type": "text",
                     "value": status_distribution_transfer_frames_channel_1[0].text},
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
                     "value": 1},
                    {"name": "completeness_status",
                     "type": "text",
                     "value": completeness_status},
                    {"name": "number_of_received_transfer_frames",
                     "type": "double",
                     "value": number_of_received_transfer_frames_channel_1},
                    {"name": "number_of_distributed_transfer_frames",
                     "type": "double",
                     "value": number_of_distributed_transfer_frames_channel_1},
                    {"name": "completeness_difference",
                     "type": "double",
                     "value": number_of_received_transfer_frames_channel_1 - number_of_distributed_transfer_frames_channel_1}
                ]
            }
            # Insert playback_validity_event
            list_of_events.append(distribution_status_event)
        # end if

        if len(status_distribution_transfer_frames_channel_2) > 0:
            vcids = xpath_xml("/Earth_Explorer_File/Data_Block/data_C2/Status[number(NumFrames) > 0 and @VCID = 3]")
            links_hktm_channel_2 = links_hktm.copy()
            for vcid in vcids:
                vcid_number = vcid.get("VCID")
                downlink_mode = functions.get_vcid_mode(vcid_number)
                links_hktm_channel_2.append({
                    "link": "PLAYBACK_" + downlink_mode + "_VALIDITY_" + vcid_number,
                    "link_mode": "by_ref",
                    "name": "DISTRIBUTION_STATUS",
                    "back_ref": "PLAYBACK_VALIDITY"
                })
            # end for
            completeness_status = "OK"
            if number_of_distributed_transfer_frames_channel_2 != number_of_received_transfer_frames_channel_2:
                completeness_status = "NOK"
            # end if
            distribution_status_event = {
                "explicit_reference": session_id,
                "key": session_id,
                "gauge": {
                    "insertion_type": "EVENT_KEYS",
                    "name": "PLAYBACK_HKTM_DISTRIBUTION_STATUS_CHANNEL_2",
                    "system": station
                },
                "links": links_hktm_channel_2,
                "start": acquisition_starts_in_iso_8601[0],
                "stop": acquisition_stops_in_iso_8601[-1],
                "values": [
                    {"name": "status",
                     "type": "text",
                     "value": status_distribution_transfer_frames_channel_2[0].text},
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
                     "value": 2},
                    {"name": "completeness_status",
                     "type": "text",
                     "value": completeness_status},
                    {"name": "number_of_received_transfer_frames",
                     "type": "double",
                     "value": number_of_received_transfer_frames_channel_2},
                    {"name": "number_of_distributed_transfer_frames",
                     "type": "double",
                     "value": number_of_distributed_transfer_frames_channel_2},
                    {"name": "completeness_difference",
                     "type": "double",
                     "value": number_of_received_transfer_frames_channel_2 - number_of_distributed_transfer_frames_channel_2}
                ]
            }
            # Insert playback_validity_event
            list_of_events.append(distribution_status_event)
        # end if

    # end if

@debug
def _generate_acquisition_coverage(xpath_xml, source, engine, query, list_of_events):
    """
    Method to generate the events for associating the planned playbacks even if there is no acquisition
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
    """

    # Obtain the satellite
    satellite = source["name"][0:3]

    # Obtain the station
    station = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Source/System")[0].text

    # Obtain link session ID
    session_id = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/File_Type")[0].text + "_" + xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Validity_Period/Validity_Start")[0].text.split("UTC=",1)[1]

    # Obtain downlink orbit
    downlink_orbit = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Variable_Header/Downlink_Orbit")[0].text

    validity_start = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Validity_Period/Validity_Start")[0].text.split("=")[1]

    validity_stop = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Validity_Period/Validity_Stop")[0].text.split("=")[1]

    # Get planned playbacks covered by the acquisition timings
    corrected_planned_playbacks = query.get_events(gauge_names = {"op": "==", "filter": "PLANNED_PLAYBACK_CORRECTION"},
                                                        gauge_systems = {"op": "==", "filter": satellite},
                                                        start_filters = [{"date": validity_start, "op": ">="}],
                                                        stop_filters = [{"date": validity_stop, "op": "<="}])

    links = []
    for corrected_planned_playback in corrected_planned_playbacks:
        planned_playback_uuid = [event_link.event_uuid_link for event_link in corrected_planned_playback.eventLinks if event_link.name == "PLANNED_EVENT"][0]            
        links.append({
            "link": str(planned_playback_uuid),
            "link_mode": "by_uuid",
            "name": "DFEP_ACQUISITION_VALIDITY",
            "back_ref": "PLANNED_PLAYBACK"
        })
    # end for
    distribution_status_event = {
        "explicit_reference": session_id,
        "key": session_id,
        "gauge": {
            "insertion_type": "EVENT_KEYS",
            "name": "DFEP_ACQUISITION_VALIDITY",
            "system": station
        },
        "links": links,
        "start": validity_start,
        "stop": validity_stop,
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
    # Insert playback_validity_event
    list_of_events.append(distribution_status_event)
    
@debug
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
    # Set the validity start to be the first sensing received to avoid error ingesting
    sensing_starts = xpath_xml("/Earth_Explorer_File/Data_Block/*[contains(name(),'data_C')]/Status[@VCID = 2 or @VCID = 4 or @VCID = 5 or @VCID = 6 or @VCID = 20 or @VCID = 21 or @VCID = 22]/ISP_Status/Status/SensStartTime")

    acquisition_starts = xpath_xml("/Earth_Explorer_File/Data_Block/*[contains(name(),'data_C')]/Status/AcqStartTime")
    
    reported_validity_start = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Validity_Period/Validity_Start")[0].text.split("=")[1]
    validity_starts = [reported_validity_start]
    if len(sensing_starts) > 0:
        # Set the validity start to be the first sensing timing acquired to avoid error ingesting
        sensing_starts_in_iso_8601 = [functions.three_letter_to_iso_8601(sensing_start.text) for sensing_start in sensing_starts]

        # Sort list
        sensing_starts_in_iso_8601.sort()
        corrected_sensing_start = functions.convert_from_gps_to_utc(sensing_starts_in_iso_8601[0])
        validity_starts.append(corrected_sensing_start)
    # end if

    if len(acquisition_starts) > 0:
        # Set the validity start to be the first acquisition timing registered to avoid error ingesting
        acquisition_starts_in_iso_8601 = [functions.three_letter_to_iso_8601(acquisition_start.text) for acquisition_start in acquisition_starts]

        # Sort list
        acquisition_starts_in_iso_8601.sort()
        validity_starts.append(acquisition_starts_in_iso_8601[0])
    # end if

    validity_starts.sort()
    validity_start = validity_starts[0]

    acquisition_stops = xpath_xml("/Earth_Explorer_File/Data_Block/*[contains(name(),'data_C')]/Status/AcqStopTime")
    reported_validity_stop = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Validity_Period/Validity_Stop")[0].text.split("=")[1]
    validity_stops = [reported_validity_stop]
    if len(acquisition_stops) > 0:
        # Set the validity stop to be the last acquisition timing registered to avoid error ingesting
        acquisition_stops_in_iso_8601 = [functions.three_letter_to_iso_8601(acquisition_stop.text) for acquisition_stop in acquisition_stops]

        # Sort list
        acquisition_stops_in_iso_8601.sort()
        validity_stops.append(acquisition_stops_in_iso_8601[-1])
    # end if

    validity_stops.sort()
    validity_stop = validity_stops[-1]

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

    # Extract the information of the received data
    list_of_isp_validity_processing_completeness_events = []
    isp_status = _generate_received_data_information(xpath_xml, source, engine, query, list_of_events, list_of_isp_validity_processing_completeness_events, list_of_planning_operations)

    functions.insert_ingestion_progress(session_progress, general_source_progress, 30)

    # Extract the information of the received data
    acquisition_status = _generate_acquisition_data_information(xpath_xml, source, engine, query, list_of_events, list_of_planning_operations)

    functions.insert_ingestion_progress(session_progress, general_source_progress, 45)

    # Extract the information of the pass
    _generate_pass_information(xpath_xml, source, engine, query, list_of_annotations, list_of_explicit_references, isp_status, acquisition_status)

    functions.insert_ingestion_progress(session_progress, general_source_progress, 70)

    # Extract the information of the distribution
    _generate_distribution_information(xpath_xml, source, engine, query, list_of_events)

    functions.insert_ingestion_progress(session_progress, general_source_progress, 80)

    # Extract the information of the distribution
    _generate_acquisition_coverage(xpath_xml, source, engine, query, list_of_events)

    functions.insert_ingestion_progress(session_progress, general_source_progress, 85)

    # Build the xml
    data = {}

    # Generate the footprint of the events
    list_of_events_with_footprint = functions.associate_footprints(list_of_events, satellite)

    functions.insert_ingestion_progress(session_progress, general_source_progress, 95)

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

    functions.insert_ingestion_progress(session_progress, general_source_progress, 97)

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
    
    functions.insert_ingestion_progress(session_progress, general_source_progress, 100)

    query.close_session()

    new_file.close()

    return data
