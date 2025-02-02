"""
Ingestion module for the REP_PASS_E files of Sentinel-2

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

    # Obtain link session ID
    session_id = xpath_xml("/Earth_Explorer_File/Data_Block/input_files/input_file[1]")[0].text[7:31]

    # Obtain channel
    channel = xpath_xml("/Earth_Explorer_File/Data_Block/child::*[contains(name(),'data_')]")[0].tag[6:7]

    # Obtain downlink orbit
    downlink_orbit = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Variable_Header/Downlink_Orbit")[0].text

    edrs_slots = query.get_events(explicit_refs = {"op": "==", "filter": session_id},
                                  gauge_names = {"op": "==", "filter": "SLOT_REQUEST_EDRS"},
                                  gauge_systems = {"op": "==", "filter": satellite})

    planned_playbacks = []
    if len (edrs_slots) > 0:
        planned_playback_uuids = [link.event_uuid_link for link in edrs_slots[0].eventLinks if link.name == "PLANNED_PLAYBACK"]

        planned_playbacks = query.get_events(event_uuids = {"op": "in", "filter": planned_playback_uuids})
    # end if

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

        gaps = vcid.xpath("Gaps/Gap")
        for gap in gaps:
            general_status = "INCOMPLETE"
            status = "INCOMPLETE"
            start = functions.three_letter_to_iso_8601(gap.xpath("PreAcqTime")[0].text)
            stop = functions.three_letter_to_iso_8601(gap.xpath("PostAcqTime")[0].text)
            estimated_lost = gap.xpath("EstimatedLost")[0].text
            pre_counter = gap.xpath("PreCounter")[0].text
            post_counter = gap.xpath("PostCounter")[0].text
            gap_event = {
                "explicit_reference": session_id,
                "key": session_id + "_CHANNEL_" + channel,
                "gauge": {
                    "insertion_type": "EVENT_KEYS",
                    "name": "PLAYBACK_GAP",
                    "system": "EDRS"
                },
                "start": start,
                "stop": stop,
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
                     "value": "EDRS"},
                    {"name": "channel",
                     "type": "double",
                     "value": channel},
                    {"name": "vcid",
                     "type": "double",
                     "value": vcid_number},
                    {"name": "downlink_mode",
                     "type": "text",
                     "value": downlink_mode},
                    {"name": "estimated_lost",
                     "type": "double",
                     "value": estimated_lost},
                    {"name": "pre_counter",
                     "type": "double",
                     "value": pre_counter},
                    {"name": "post_counter",
                     "type": "double",
                     "value": post_counter}
                ]
            }

            # Insert gap_event
            list_of_events.append(gap_event)

        # end for

        matching_status = "NO_MATCHED_PLANNED_PLAYBACK"
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
                matching_status = "MATCHED_PLANNED_PLAYBACK"
                links.append({
                    "link": str(planned_playback.event_uuid),
                    "link_mode": "by_uuid",
                    "name": "PLAYBACK_VALIDITY",
                    "back_ref": "PLANNED_PLAYBACK"
                })

                completeness_status = "RECEIVED"
                if status != "COMPLETE":
                    completeness_status = status
                # end if

                list_of_events.append({
                    "explicit_reference": session_id,
                    "key": session_id + "_CHANNEL_" + channel,
                    "gauge": {
                        "insertion_type": "EVENT_KEYS",
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
                    "start": planned_playback.start.isoformat(),
                    "stop": planned_playback.stop.isoformat(),
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
                         "value": "EDRS"},
                        {"name": "channel",
                         "type": "double",
                         "value": channel},
                        {"name": "vcid",
                         "type": "double",
                         "value": vcid_number},
                        {"name": "downlink_mode",
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
                "insertion_type": "EVENT_KEYS",
                "name": "PLAYBACK_VALIDITY",
                "system": "EDRS"
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
                 "value": "EDRS"},
                {"name": "channel",
                 "type": "double",
                 "value": channel},
                {"name": "vcid",
                 "type": "double",
                 "value": vcid_number},
                {"name": "downlink_mode",
                 "type": "text",
                 "value": downlink_mode},
                {"name": "matching_plan_status",
                 "type": "text",
                 "value": matching_status},
                {"name": "status",
                 "type": "text",
                 "value": status}
            ]
        }

        # Insert playback_event
        list_of_events.append(playback_event)

    # end for

    return status

@debug
def _generate_received_data_information(xpath_xml, source, engine, query, list_of_events, list_of_planning_operations):
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

    # Obtain link session ID
    session_id = xpath_xml("/Earth_Explorer_File/Data_Block/input_files/input_file[1]")[0].text[7:31]

    # Obtain channel
    channel = xpath_xml("/Earth_Explorer_File/Data_Block/child::*[contains(name(),'data_')]")[0].tag[6:7]

    # Obtain downlink orbit
    downlink_orbit = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Variable_Header/Downlink_Orbit")[0].text

    # Completeness operation for the isp completeness analysis of the plan
    isp_planning_completeness_operation = {
        "mode": "insert",
        "dim_signature": {
            "name": "RECEPTION_" + satellite,
            "exec": "isp_planning_completeness_" + os.path.basename(__file__),
            "version": version
        },
        "events": []
    }

    isp_planning_completeness_generation_times = []

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
        corrected_sensing_stop = (parser.parse(functions.convert_from_gps_to_utc(sensing_stop)) + datetime.timedelta(seconds=3.608)).isoformat()

        # APID configuration
        apid_conf = functions.get_vcid_apid_configuration(vcid_number)

        # Reference to the raw ISP validity event
        raw_isp_validity_event_link_ref = "RAW_ISP_VALIDITY_" + vcid_number

        # Received number of packets
        # The packets registered in the APID 2047 have to be discarded
        received_number_packets_apid_2047 = 0
        received_number_packets_apid_2047_node = vcid.xpath("ISP_Status/Status[@APID = 2047]/NumPackets") 
        if len(received_number_packets_apid_2047_node) > 0:
            received_number_packets_apid_2047 = int(received_number_packets_apid_2047_node[0].text)
        # end if
        received_number_packets = int(vcid.xpath("ISP_Status/Summary/NumPackets")[0].text) - int(received_number_packets_apid_2047)

        # Obtain complete missing APIDs
        complete_missing_apids = vcid.xpath("ISP_Status/Status[number(NumPackets) = 0 and number(@APID) >= number($min_apid) and number(@APID) <= number($max_apid)]", min_apid = apid_conf["min_apid"], max_apid = apid_conf["max_apid"])
        for apid in complete_missing_apids:
            status = "INCOMPLETE"
            apid_number = apid.get("APID")
            band_detector = functions.get_band_detector(apid_number)
            isp_gap_event = {
                "link_ref": "ISP_GAP_" + str(isp_gap_iterator),
                "explicit_reference": session_id,
                "key": session_id + "_CHANNEL_" + channel,
                "gauge": {
                    "insertion_type": "EVENT_KEYS",
                    "name": "ISP_GAP",
                    "system": "EDRS"
                },
                "start": corrected_sensing_start,
                "stop": corrected_sensing_stop,
                "links": [
                    {
                        "link": raw_isp_validity_event_link_ref,
                        "link_mode": "by_ref",
                        "name": "ISP_GAP",
                        "back_ref": "RAW_ISP_VALIDITY"
                    }],
                "values": [
                    {"name": "impact",
                     "type": "text",
                     "value": "COMPLETE"},
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
                     "value": "EDRS"},
                    {"name": "channel",
                     "type": "double",
                     "value": channel},
                    {"name": "vcid",
                     "type": "double",
                     "value": vcid_number},
                    {"name": "downlink_mode",
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
                "start": parser.parse(corrected_sensing_start),
                "stop": parser.parse(corrected_sensing_stop)
            })

            isp_gap_iterator += 1
        # end for

        # Obtain ISP gaps at the beggining
        isp_missing_at_begin_apids = vcid.xpath("ISP_Status/Status[number(NumPackets) > 0 and number(@APID) >= number($min_apid) and number(@APID) <= number($max_apid) and not(three_letter_to_iso_8601(string(SensStartTime)) = $sensing_start)]", min_apid = apid_conf["min_apid"], max_apid = apid_conf["max_apid"], sensing_start = sensing_start)
        for apid in isp_missing_at_begin_apids:
            status = "INCOMPLETE"
            apid_number = apid.get("APID")
            band_detector = functions.get_band_detector(apid_number)

            stop = functions.three_letter_to_iso_8601(apid.xpath("SensStartTime")[0].text)
            corrected_stop = functions.convert_from_gps_to_utc(stop)
            isp_gap_event = {
                "link_ref": "ISP_GAP_" + str(isp_gap_iterator),
                "explicit_reference": session_id,
                "key": session_id + "_CHANNEL_" + channel,
                "gauge": {
                    "insertion_type": "EVENT_KEYS",
                    "name": "ISP_GAP",
                    "system": "EDRS"
                },
                "start": corrected_sensing_start,
                "stop": corrected_stop,
                "links": [
                    {
                        "link": raw_isp_validity_event_link_ref,
                        "link_mode": "by_ref",
                        "name": "ISP_GAP",
                        "back_ref": "RAW_ISP_VALIDITY"
                    }],
                "values": [
                    {"name": "impact",
                     "type": "text",
                     "value": "AT_THE_BEGINNING"},
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
                     "value": "EDRS"},
                    {"name": "channel",
                     "type": "double",
                     "value": channel},
                    {"name": "vcid",
                     "type": "double",
                     "value": vcid_number},
                    {"name": "downlink_mode",
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
                "start": parser.parse(corrected_sensing_start),
                "stop": parser.parse(corrected_stop)
            })

            isp_gap_iterator += 1

        # end for

        # Obtain ISP gaps at the end
        isp_missing_at_end_apids = vcid.xpath("ISP_Status/Status[number(NumPackets) > 0 and number(@APID) >= number($min_apid) and number(@APID) <= number($max_apid) and not(three_letter_to_iso_8601(string(SensStopTime)) = $sensing_stop)]", min_apid = apid_conf["min_apid"], max_apid = apid_conf["max_apid"], sensing_stop = sensing_stop)
        for apid in isp_missing_at_end_apids:
            status = "INCOMPLETE"
            apid_number = apid.get("APID")
            band_detector = functions.get_band_detector(apid_number)

            start = functions.three_letter_to_iso_8601(apid.xpath("SensStopTime")[0].text)
            corrected_start = functions.convert_from_gps_to_utc(start)

            isp_gap_event = {
                "link_ref": "ISP_GAP_" + str(isp_gap_iterator),
                "explicit_reference": session_id,
                "key": session_id + "_CHANNEL_" + channel,
                "gauge": {
                    "insertion_type": "EVENT_KEYS",
                    "name": "ISP_GAP",
                    "system": "EDRS"
                },
                "start": corrected_start,
                "stop": corrected_sensing_stop,
                "links": [
                    {
                        "link": raw_isp_validity_event_link_ref,
                        "link_mode": "by_ref",
                        "name": "ISP_GAP",
                        "back_ref": "RAW_ISP_VALIDITY"
                    }],
                "values": [
                    {"name": "impact",
                     "type": "text",
                     "value": "AT_THE_END"},
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
                     "value": "EDRS"},
                    {"name": "channel",
                     "type": "double",
                     "value": channel},
                    {"name": "vcid",
                     "type": "double",
                     "value": vcid_number},
                    {"name": "downlink_mode",
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
                "start": parser.parse(corrected_start),
                "stop": parser.parse(corrected_sensing_stop)
            })

            isp_gap_iterator += 1

        # end for

        raw_isp_validity_event = {
            "link_ref": raw_isp_validity_event_link_ref,
            "explicit_reference": session_id,
            "key": session_id + "_CHANNEL_" + channel,
            "gauge": {
                "insertion_type": "EVENT_KEYS",
                "name": "RAW_ISP_VALIDITY",
                "system": "EDRS"
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
                 "value": "EDRS"},
                {"name": "channel",
                 "type": "double",
                 "value": channel},
                {"name": "vcid",
                 "type": "double",
                 "value": vcid_number},
                {"name": "downlink_mode",
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

        # Obtain the expected number of packets and the packet status
        raw_isp_validity_date_segments = ingestion_functions.convert_input_events_to_date_segments([raw_isp_validity_event])
        planning_date_segments = ingestion_functions.convert_eboa_events_to_date_segments(corrected_planned_imagings)
        isp_validity_valid_segments = ingestion_functions.intersect_timelines(raw_isp_validity_date_segments, planning_date_segments)

        planning_timeline_duration = ingestion_functions.get_timeline_duration(isp_validity_valid_segments)
        # For calculating the number of expected scenes, for every datastrip expected, the duration of a scene is added to the total duration of the timeline of expected datastrips
        expected_number_scenes = round((planning_timeline_duration + 3.608 * len(isp_validity_valid_segments)) / 3.608)
        expected_number_packets = expected_number_scenes * 6480

        if (expected_number_packets - received_number_packets) == 0:
            packet_status = "OK"
        elif abs(expected_number_packets - received_number_packets) <= (len(isp_validity_valid_segments)*2) * 6480 and (expected_number_packets - received_number_packets) % 6480 == 0:
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

        # If there are no found planned imaging events, the MSI will not be linked to the plan and so it will be unexpected

        # If there are found planned imaging events, the MSI will be linked to the plan and its segment will be removed from the completeness
        if len(corrected_planned_imagings) > 0:
            for corrected_planned_imaging in corrected_planned_imagings:
                planned_imaging_uuid = [event_link.event_uuid_link for event_link in corrected_planned_imaging.eventLinks if event_link.name == "PLANNED_EVENT"][0]
                planned_imaging_event = query.get_events(event_uuids = {"op": "in", "filter": [planned_imaging_uuid]})
                isp_planning_completeness_generation_times.append(planned_imaging_event[0].source.generation_time)
                # Insert the linked COMPLETENESS event for the automatic completeness check
                planning_event_values = corrected_planned_imaging.get_structured_values()
                planning_event_values.append({"name": "status",
                                              "type": "text",
                                              "value": "MISSING"})

                isp_planning_completeness_operation["events"].append({
                    "gauge": {
                        "insertion_type": "INSERT_and_ERASE_per_EVENT",
                        "name": "PLANNED_IMAGING_ISP_COMPLETENESS_CHANNEL_" + channel,
                        "system": satellite
                    },
                    "start": corrected_planned_imaging.start.isoformat(),
                    "stop": corrected_planned_imaging.stop.isoformat(),
                    "links": [
                        {
                            "link": str(planned_imaging_uuid),
                            "link_mode": "by_uuid",
                            "name": "ISP_COMPLETENESS",
                            "back_ref": "PLANNED_IMAGING"
                        }],
                    "values": planning_event_values
                })
            # end for

            # Build the ISP_VALIDITY events
            for isp_validity_valid_segment in isp_validity_valid_segments:
                corrected_planned_imaging = [event for event in corrected_planned_imagings if event.event_uuid == isp_validity_valid_segment["id2"]][0]
                planned_imaging_uuid = [event_link.event_uuid_link for event_link in corrected_planned_imaging.eventLinks if event_link.name == "PLANNED_EVENT"][0]

                sensing_orbit_values = query.get_event_values_interface(value_type="double",
                                                                        value_filters=[{"name": {"op": "==", "filter": "start_orbit"}, "type": "double"}],
                                                                        event_uuids = {"op": "in", "filter": [planned_imaging_uuid]})
                sensing_orbit = sensing_orbit_values[0].value

                # ISP validity event
                isp_validity_event_link_ref = "ISP_VALIDITY_" + vcid_number + "_" + str(isp_validity_valid_segment["start"])

                isp_gaps_intersected = ingestion_functions.intersect_timelines([isp_validity_valid_segment], merged_timeline_isp_gaps)

                isp_validity_status = "COMPLETE"
                if len(isp_gaps_intersected) > 0:
                    isp_validity_status = "INCOMPLETE"
                # end if

                links = [
                    {
                        "link": str(planned_imaging_uuid),
                        "link_mode": "by_uuid",
                        "name": "ISP_VALIDITY",
                        "back_ref": "PLANNED_IMAGING"
                    },{
                        "link": str(isp_validity_valid_segment["id1"]),
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

                isp_validity_event = {
                    "link_ref": isp_validity_event_link_ref,
                    "explicit_reference": session_id,
                    "key": session_id + "_CHANNEL_" + channel,
                    "gauge": {
                        "insertion_type": "EVENT_KEYS",
                        "name": "ISP_VALIDITY",
                        "system": "EDRS"
                    },
                    "links": links,
                    "start": isp_validity_valid_segment["start"].isoformat(),
                    "stop": isp_validity_valid_segment["stop"].isoformat(),
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
                         "value": "EDRS"},
                        {"name": "channel",
                         "type": "double",
                         "value": channel},
                        {"name": "vcid",
                         "type": "double",
                         "value": vcid_number},
                        {"name": "downlink_mode",
                         "type": "text",
                         "value": downlink_mode},
                        {"name": "sensing_orbit",
                         "type": "double",
                         "value": sensing_orbit}
                    ]
                }
                
                # Insert isp_validity_event
                list_of_events.append(isp_validity_event)

                completeness_status = "RECEIVED"
                if isp_validity_status != "COMPLETE":
                    completeness_status = isp_validity_status
                # end if

                isp_validity_completeness_event = {
                    "explicit_reference": session_id,
                    "key": session_id + "_CHANNEL_" + channel,
                    "gauge": {
                        "insertion_type": "INSERT_and_ERASE_per_EVENT",
                        "name": "PLANNED_IMAGING_ISP_COMPLETENESS_CHANNEL_" + channel,
                        "system": satellite
                    },
                    "links": [
                        {
                            "link": str(planned_imaging_uuid),
                            "link_mode": "by_uuid",
                            "name": "ISP_COMPLETENESS",
                            "back_ref": "PLANNED_IMAGING"
                        },
                        {
                            "link": isp_validity_event_link_ref,
                            "link_mode": "by_ref",
                            "name": "COMPLETENESS",
                            "back_ref": "ISP_VALIDITY"
                        }],
                    "start": isp_validity_valid_segment["start"].isoformat(),
                    "stop": isp_validity_valid_segment["stop"].isoformat(),
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
                         "value": "EDRS"},
                        {"name": "channel",
                         "type": "double",
                         "value": channel},
                        {"name": "vcid",
                         "type": "double",
                         "value": vcid_number},
                        {"name": "downlink_mode",
                         "type": "text",
                         "value": downlink_mode},
                        {"name": "sensing_orbit",
                         "type": "double",
                         "value": sensing_orbit}
                    ]
                }

                # Insert isp_validity_event
                list_of_events.append(isp_validity_completeness_event)
            # end for
        # end if
    # end for

    # Insert completeness operation for the completeness analysis of the plan
    if len(isp_planning_completeness_operation["events"]) > 0:
        isp_planning_completeness_event_starts = [event["start"] for event in isp_planning_completeness_operation["events"]]
        isp_planning_completeness_event_starts.sort()
        isp_planning_completeness_event_stops = [event["stop"] for event in isp_planning_completeness_operation["events"]]
        isp_planning_completeness_event_stops.sort()

        isp_planning_completeness_generation_times.sort()
        generation_time = isp_planning_completeness_generation_times[0]

        isp_planning_completeness_operation["source"] = {
            "name": source["name"],
            "reception_time": source["reception_time"],
            "generation_time": generation_time.isoformat(),
            "validity_start": isp_planning_completeness_event_starts[0],
            "validity_stop": isp_planning_completeness_event_stops[-1]
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

    # Obtain link session ID
    session_id = xpath_xml("/Earth_Explorer_File/Data_Block/input_files/input_file[1]")[0].text[7:31]

    # Obtain channel
    channel = xpath_xml("/Earth_Explorer_File/Data_Block/child::*[contains(name(),'data_')]")[0].tag[6:7]

    # Obtain downlink orbit
    downlink_orbit = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Variable_Header/Downlink_Orbit")[0].text

    # Associate the explicit reference to the group
    explicit_reference = {
        "name": session_id,
        "group": "EDRS_LINK_SESSION_IDs"
    }

    list_of_explicit_references.append(explicit_reference)

    # Link session
    link_details_annotation = {
        "explicit_reference": session_id,
        "annotation_cnf": {
            "name": "LINK_DETAILS_CH" + channel,
            "system": "EDRS"
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
             "value": "EDRS"},
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
    xpath_xml = etree.XPathEvaluator(parsed_xml)

    satellite = file_name[0:3]
    generation_time = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Source/Creation_Date")[0].text.split("=")[1]
    # Set the validity start to be the first sensing received to avoid error ingesting
    sensing_starts = xpath_xml("/Earth_Explorer_File/Data_Block/*[contains(name(),'data_C')]/Status[@VCID = 2 or @VCID = 4 or @VCID = 5 or @VCID = 6 or @VCID = 20 or @VCID = 21 or @VCID = 22]/ISP_Status/Status/SensStartTime")

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
        validity_start = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Validity_Period/Validity_Start")[0].text.split("=")[1]
    # end if

    acquisition_stops = xpath_xml("/Earth_Explorer_File/Data_Block/*[contains(name(),'data_C')]/Status/AcqStopTime")
    if len(acquisition_stops) > 0:
        # Set the validity stop to be the last acquisition timing registered to avoid error ingesting
        acquisition_stops_in_iso_8601 = [functions.three_letter_to_iso_8601(acquisition_stop.text) for acquisition_stop in acquisition_stops]

        # Sort list
        acquisition_stops_in_iso_8601.sort()
        validity_stop = acquisition_stops_in_iso_8601[-1]
    else:
        validity_stop = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Validity_Period/Validity_Stop")[0].text.split("=")[1]
    # end if

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
    
    # Obtain link session ID
    session_id_xpath = xpath_xml("/Earth_Explorer_File/Data_Block/input_files/input_file[1]")

    if len(session_id_xpath) > 0:
        # Extract the information of the received data
        isp_status = _generate_received_data_information(xpath_xml, source, engine, query, list_of_events, list_of_planning_operations)

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
    data["operations"] = list_of_planning_operations

    # Generate the footprint of the events
    list_of_events_with_footprint = functions.associate_footprints(list_of_events, satellite)

    functions.insert_ingestion_progress(session_progress, general_source_progress, 90)
    
    data["operations"].append({
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
    })

    functions.insert_ingestion_progress(session_progress, general_source_progress, 100)

    query.close_session()

    new_file.close()
    
    return data
