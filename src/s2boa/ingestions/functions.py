"""
Helper module for the ingestion_functions. of files of Sentinel-2

Written by DEIMOS Space S.L. (dibb)

module eboa
"""

# Import python utilities
import math
import datetime
from dateutil import parser
import subprocess
import os
from tempfile import mkstemp

# Import astropy
from astropy.time import Time

import eboa.ingestion.functions as ingestion_functions
import eboa.engine.functions as eboa_functions

# Import eboa query
from eboa.engine.query import Query

# Import debugging
from eboa.debugging import debug

# Import logging
from eboa.logging import Log
import logging

logging_module = Log(name = __name__)
logger = logging_module.logger

###########
# Functions for helping with geometries
###########
def correct_list_of_coordinates_for_ds (list_of_coordinates):
    """
    Method to correct the format of a given list of coordinates for a datastrip
    :param list_of_coordinates: list with coordinates
    :type list_of_coordinates: list

    :return: list_of_coordinates
    :rtype: str

    """
    if type(list_of_coordinates) != list:
        raise
    # end if
    result_list_of_coordinates = []
    # Minimum accpeted number of coordinates is 2
    if len(list_of_coordinates) > 1:
        first_longitude = list_of_coordinates[0]
        first_latitude = list_of_coordinates[1]
        result_list_of_coordinates.append(first_longitude)
        result_list_of_coordinates.append(first_latitude)
        i = 1
        while i < len(list_of_coordinates)/2:
            longitude = list_of_coordinates[i*2]
            if longitude == first_longitude:
                break
            elif ((i*2) + 1) < len(list_of_coordinates):
                latitude = list_of_coordinates[(i*2) + 1]
                result_list_of_coordinates.append(longitude)
                result_list_of_coordinates.append(latitude)
            # end if
            i += 1
        # end while
        result_list_of_coordinates.append(first_longitude)
        result_list_of_coordinates.append(first_latitude)
    # end if
        
    return result_list_of_coordinates

def correct_list_of_coordinates_for_gr_tl (list_of_coordinates):
    """
    Method to correct the format of a given list of coordinates for a granule or a tile
    :param list_of_coordinates: list with coordinates
    :type list_of_coordinates: list

    :return: list_of_coordinates
    :rtype: str

    """
    if type(list_of_coordinates) != list:
        raise
    # end if
    result_list_of_coordinates = []
    # Minimum accpeted number of coordinates is 2
    if len(list_of_coordinates) > 1:
        first_longitude = list_of_coordinates[0]
        first_latitude = list_of_coordinates[1]
        result_list_of_coordinates.append(first_longitude)
        result_list_of_coordinates.append(first_latitude)
        i = 1
        while i < len(list_of_coordinates)/2:
            longitude = list_of_coordinates[i*3]
            if longitude == first_longitude:
                break
            elif ((i*3) + 1) < len(list_of_coordinates):
                latitude = list_of_coordinates[(i*3) + 1]
                result_list_of_coordinates.append(longitude)
                result_list_of_coordinates.append(latitude)
            # end if
            i += 1
        # end while
        result_list_of_coordinates.append(first_longitude)
        result_list_of_coordinates.append(first_latitude)
    # end if
        
    return result_list_of_coordinates

def list_of_coordinates_to_str_geometry (list_of_coordinates):
    """
    Method to receive a string of coordinates and return the same list but with a correct format
    :param list_of_coordinates: list with coordinates
    :type list_of_coordinates: list

    :return: geometry
    :rtype: str

    """
    result_geometry = ""
    i = 0
    for coordinate in list_of_coordinates:
        if i == 0:
            result_geometry = coordinate
        else:
            result_geometry = result_geometry + " " + coordinate
        # end if
        i += 1
    # end for
        
    return result_geometry

###
# Acquisition ingestion_functions.' helpers
###

# Uncomment for debugging reasons
#@debug
def convert_from_gps_to_utc(date):
    """
    Method to convert a date in GPS precission to UTC
    :param date: date in GPS precission and ISO format
    :type date: str

    :return: date coverted in ISO 8601
    :rtype: str

    """

    date_datetime = parser.parse(date)

    if date_datetime > datetime.datetime(2015, 6, 30, 23, 59, 59) and date_datetime <= datetime.datetime(2016, 12, 31, 23, 59, 59):
        correction = -17
    elif date_datetime > datetime.datetime(2016, 12, 31, 23, 59, 59):
        correction = -18
    else:
        correction = -16

    return (date_datetime + datetime.timedelta(seconds=correction)).isoformat()

# Uncomment for debugging reasons
#@debug
def convert_from_datetime_gps_to_datetime_utc(date):
    """
    Method to convert a date in GPS precission to UTC
    :param date: date in GPS precission and ISO format
    :type date: str

    :return: date coverted in ISO 8601
    :rtype: str

    """

    if date > datetime.datetime(2015, 6, 30, 23, 59, 59) and date <= datetime.datetime(2016, 12, 31, 23, 59, 59):
        correction = -17
    elif date > datetime.datetime(2016, 12, 31, 23, 59, 59):
        correction = -18
    else:
        correction = -16

    return date + datetime.timedelta(seconds=correction)

# Uncomment for debugging reasons
#@debug
def get_vcid_mode(vcid):
    """
    Method to convert the VCID number into the storage mode
    :param vcid: VCID number
    :type vcid: str

    :return: mode
    :rtype: str

    """

    correspondence = {
        "2": "SAD",
        "3": "HKTM",
        "4": "NOMINAL",
        "5": "NRT",
        "6": "RT",
        "20": "NOMINAL",
        "21": "NRT",
        "22": "RT"
    }

    return correspondence[vcid]


# Uncomment for debugging reasons
#@debug
def get_vcid_apid_configuration(vcid):
    """
    Method to obtain the APID configuration related to the VCID number
    :param vcid: VCID number
    :type vcid: str

    :return: apid_configuration
    :rtype: dict

    """

    # Second half swath
    apids_second_half_swath = {
        "min_apid": 0,
        "max_apid": 92,
    }
    # First half swath
    apids_first_half_swath = {
        "min_apid": 256,
        "max_apid": 348,
    }

    correspondence = {
        "4": apids_second_half_swath,
        "5": apids_second_half_swath,
        "6": apids_second_half_swath,
        "20": apids_first_half_swath,
        "21": apids_first_half_swath,
        "22": apids_first_half_swath
    }

    return correspondence[vcid]

# Uncomment for debugging reasons
#@debug
def get_band_detector(apid):
    """
    Method to obtain the band and detector numbers related to the APID number

    The detector and the bands are determined from APID
        APID RANGE     DETECTOR
           0-15           12
           16-31           11
           32-47           10
           48-63           9
           64-79           8
           80-95           7

           256-271           6
           272-287           5
           288-303           4
           304-319           3
           320-335           2
           336-351           1

        APID MOD 16     BAND
             0           1
             1           2
             2           3
             3           4
             4           5
             5           6
             6           7
             7           8
             8           8a
             9           9
             10          10
             11          11
             12          12

    :param apid: APID number
    :type vcid: str

    :return: band_detector_configuration
    :rtype: dict

    """

    if int(apid) < 256:
        detector = 12 - math.floor(int(apid)/16)
    else:
        detector = 12 - (math.floor((int(apid) - 256)/16) + 6)
    # end if

    raw_band = (int(apid) % 16) + 1
    if raw_band == 9:
        band = "8a"
    elif raw_band > 9:
        band = raw_band - 1
    else:
        band = raw_band
    # end if

    return {"detector": str(detector), "band": str(band)}

# Uncomment for debugging reasons
#@debug
def get_counter_threshold(band):
    """
    Method to obtain the counter threshold related to the band number
        BAND     COUNTER THRESHOLD    METRES
           1              23            60
           2-4           143            10
           5-7            71            20
           8             143            10
           8a             71            20
           9-10           23            60
           11-12          71            20

    :param band: band number
    :type band: str

    :return: counter_threshold
    :rtype: int

    """

    if band == "2" or band == "3" or band == "4" or band == "8":
        counter_threshold = 143
    elif band == "1" or band == "9" or band == "10":
        counter_threshold = 23
    else:
        counter_threshold = 71
    # end if

    return counter_threshold

# Uncomment for debugging reasons
#@debug
def get_counter_threshold_from_apid(apid):
    """
    Method to obtain the counter threshold related to the apid number

    :param apid: apid number
    :type apid: str

    :return: counter_threshold
    :rtype: int

    """

    band_detector = get_band_detector(apid)

    return get_counter_threshold(band_detector["band"])

def get_apid_numbers():
    """
    Method to obtain the APID numbers used

    :return: list of APID numbers
    :rtype: list

    """
    apids = []
    for i in range(6):
        for j in range (13):
            apids.append(i*16 + j)
        # end for
    # end for
    for i in range(6):
        for j in range (13):
            apids.append((i*16 + j) + 256)
        # end for
    # end for
    return apids

###
# Date helpers
###

# Uncomment for debugging reasons
#@debug
def three_letter_to_iso_8601(date):
    """
    Method to convert a date in three letter format to a date in ISO 8601 format
    :param date: date in three letter format (DD-MMM-YYYY HH:MM:SS.ssssss)
    :type date: str

    :return: date in ISO 8601 format (YYYY-MM-DDTHH:MM:SS)
    :rtype: str

    """
    month = {
        "JAN": "01",
        "FEB": "02",
        "MAR": "03",
        "APR": "04",
        "MAY": "05",
        "JUN": "06",
        "JUL": "07",
        "AUG": "08",
        "SEP": "09",
        "OCT": "10",
        "NOV": "11",
        "DEC": "12"
    }
    year = date[7:11]
    month = month[date[3:6]]
    day = date[0:2]
    hours = date[12:14]
    minutes = date[15:17]
    seconds = date[18:20]
    microseconds = date[21:27]

    return year + "-" + month + "-" + day + "T" + hours + ":" + minutes + ":" + seconds + "." + microseconds

def L0_L1A_L1B_processing(source, engine, query, granule_timeline, list_of_events, datastrip, granule_timeline_per_detector, list_of_operations, system, version, filename, satellite):
    """
    Method to generate the events for the levels L0 and L1B
    :param source: information of the source
    :type source: dict
    :param engine: object to access the engine of the EBOA
    :type engine: Engine
    :param query: object to access the query interface of the EBOA
    :type query: Query
    :param granule_timeline: list of granule segments to be processed
    :type granule_timeline: list
    :param list_of_events: list to store the events to be inserted into the eboa
    :type list_of_events: list
    :param datastrip: datastrip
    :type datastrip: str
    :param granule_timeline_per_detector: dict containing the granule segments per detector
    :type granule_timeline_per_detector: dict
    :param list_of_operations: list of operations to be inserted into EBOA
    :type list_of_operations: list
    :param level: level of the outputs being processed
    :type level: str
    :param system: center where data has been processed
    :type system: str
    :param version: version of the processor used
    :type version: str
    :param filename: name of the processor file
    :type version: str

    :return: None

    """
    general_status = "COMPLETE"
    granule_timeline_sorted = ingestion_functions.sort_timeline_by_start(granule_timeline)
    datablocks = ingestion_functions.merge_timeline(granule_timeline_sorted)

    # Obtain the production level from the datastrip
    level = datastrip[13:16].replace("_","")

    # Completeness operations for the completeness analysis of the plan
    planning_processing_completeness_operation = {
        "mode": "insert",
        "dim_signature": {
            "name": "PROCESSING_" + satellite,
            "exec": "planning_processing_" + filename,
            "version": version
        },
        "events": []
    }
    # Completeness operations for the completeness analysis of the received imaging
    isp_validity_processing_completeness_operation = {
        "mode": "insert",
        "dim_signature": {
            "name": "PROCESSING_" + satellite,
            "exec": "processing_received_" + filename,
            "version": version
        },
        "events": []
    }

    for datablock in datablocks:
        status = "COMPLETE"

        # Obtain the gaps from the processing per detector
        processing_gaps = {}
        granule_timeline_per_detector_sorted = {}
        datablocks_per_detector = {}
        intersected_datablock_per_detector = {}
        for detector in granule_timeline_per_detector:
            granule_timeline_per_detector_sorted[detector] = ingestion_functions.sort_timeline_by_start(granule_timeline_per_detector[detector])
            datablocks_per_detector[detector] = ingestion_functions.merge_timeline(granule_timeline_per_detector_sorted[detector])
            datablock_for_extracting_gaps = {
                "id": datablock["id"],
                "start": datablock["start"] + datetime.timedelta(seconds=6),
                "stop": datablock["stop"] - datetime.timedelta(seconds=6)
            }
            intersected_datablock_per_detector[detector] = ingestion_functions.intersect_timelines([datablock_for_extracting_gaps], datablocks_per_detector[detector])
            processing_gaps[detector] = ingestion_functions.difference_timelines(intersected_datablock_per_detector[detector],[datablock_for_extracting_gaps])
            if len(processing_gaps[detector]) == 0:
                del processing_gaps[detector]
            # end if
        # end for

        # Obtain the gaps existing during the reception per detector
        isp_gaps = query.get_events(gauge_names = {"filter": "ISP_GAP", "op": "like"},
                                    value_filters = [{"name": {"str": "satellite", "op": "like"}, "type": "text", "value": {"op": "like", "value": satellite}}],
                                    start_filters = [{"date": datablock["stop"].isoformat(), "op": "<"}],
                                    stop_filters = [{"date": datablock["start"].isoformat(), "op": ">"}])
        data_isp_gaps = {}
        for gap in isp_gaps:
            detector = [value.value for value in gap.eventDoubles if value.name == "detector"][0]
            if detector not in data_isp_gaps:
                data_isp_gaps[str(int(detector))] = []
            # end if
            data_isp_gaps[str(int(detector))].append({
                "id": gap.event_uuid,
                "start": gap.start,
                "stop": gap.stop
            })
        # end for

        # Merge gaps per detector
        data_merged_isp_gaps = {}
        for detector in data_isp_gaps:
            data_merged_isp_gaps[detector] = ingestion_functions.merge_timeline(data_isp_gaps[detector])
        # end for

        gaps_due_to_reception_issues = {}
        gaps_due_to_processing_issues = {}
        for detector in processing_gaps:
            status="INCOMPLETE"
            general_status = "INCOMPLETE"
            if detector in data_merged_isp_gaps:
                gaps_due_to_reception_issues[detector] = ingestion_functions.intersect_timelines(processing_gaps[detector], data_merged_isp_gaps[detector])
                gaps_due_to_processing_issues[detector] = ingestion_functions.difference_timelines(processing_gaps[detector], gaps_due_to_reception_issues[detector])
            else:
                gaps_due_to_processing_issues[detector] = processing_gaps[detector]
            # end if
        # end for

        processing_validity_link_ref = "PROCESSING_VALIDITY_" + datablock["start"].isoformat()
        # Create gap events
        def create_processing_gap_events(gaps, gap_source):
            for detector in gaps:
                for gap in gaps[detector]:
                    gap_event = {
                        "key": datastrip + "_" + "processing_validity",
                        "explicit_reference": datastrip,
                        "gauge": {
                            "insertion_type": "EVENT_KEYS",
                            "name": "PROCESSING_GAP",
                            "system": system
                        },
                        "links": [{
                                 "link": processing_validity_link_ref,
                                 "link_mode": "by_ref",
                                 "name": "PROCESSING_GAP",
                                 "back_ref": "PROCESSING_VALIDITY"
                                 }
                             ],
                         "start": gap["start"].isoformat(),
                         "stop": gap["stop"].isoformat(),
                         "values": [{
                             "name": "details",
                             "type": "object",
                             "values": [{
                                "type": "double",
                                "value": detector,
                                "name": "detector"
                                },{
                                "type": "text",
                                "value": gap_source,
                                "name": "source"
                            },{
                                "type": "text",
                                "value": level,
                                "name": "level"
                            },{
                                "type": "text",
                                "value": satellite,
                                "name": "satellite"
                            }]
                         }]
                    }
                    list_of_events.append(gap_event)
                # end for
            # end for
        # end def

        create_processing_gap_events(gaps_due_to_reception_issues, "reception")
        create_processing_gap_events(gaps_due_to_processing_issues, "processing")

        # Obtain the planned imaging
        corrected_planned_imagings = query.get_events(gauge_names = {"filter": "PLANNED_CUT_IMAGING_CORRECTION", "op": "like"},
                                                      gauge_systems = {"filter": satellite, "op": "like"},
                                                      start_filters = [{"date": datablock["stop"].isoformat(), "op": "<"}],
                                                      stop_filters = [{"date": datablock["start"].isoformat(), "op": ">"}])

        links_processing_validity = []
        links_planning_processing_completeness = []
        links_processing_reception_completeness = []
        planning_matching_status = "NO_MATCHED_PLANNED_IMAGING"
        reception_matching_status = "NO_MATCHED_ISP_VALIDITY"
        sensing_orbit = ""
        downlink_orbit = ""

        # Planning completeness
        if len(corrected_planned_imagings) > 0:
            corrected_planned_imaging = corrected_planned_imagings[0]
            planned_imaging_uuid = [event_link.event_uuid_link for event_link in corrected_planned_imaging.eventLinks if event_link.name == "PLANNED_EVENT"][0]
            planning_matching_status = "MATCHED_PLANNED_IMAGING"
            sensing_orbit_values = query.get_event_values_interface(value_type="double",
                                                                    value_filters=[{"name": {"op": "like", "str": "start_orbit"}, "type": "double"}],
                                                                    event_uuids = {"op": "in", "filter": [planned_imaging_uuid]})
            sensing_orbit = str(sensing_orbit_values[0].value)

            links_processing_validity.append({
                "link": str(planned_imaging_uuid),
                "link_mode": "by_uuid",
                "name": "PROCESSING_VALIDITY",
                "back_ref": "PLANNED_IMAGING"
            })
            links_planning_processing_completeness.append({
                "link": str(planned_imaging_uuid),
                "link_mode": "by_uuid",
                "name": "PROCESSING_COMPLETENESS",
                "back_ref": "PLANNED_IMAGING"
            })

            planned_imaging_event = query.get_events(event_uuids = {"op": "in", "filter": [planned_imaging_uuid]})
            planning_processing_completeness_generation_time = planned_imaging_event[0].source.generation_time.isoformat()

            # Insert the linked COMPLETENESS event for the automatic completeness check
            planning_event_values = corrected_planned_imaging.get_structured_values()
            planning_event_values[0]["values"] = planning_event_values[0]["values"] + [
                {"name": "status",
                 "type": "text",
                 "value": "MISSING"}
            ]

            # Add margin of 4 seconds to each side of the segment to avoid false alerts
            start = corrected_planned_imaging.start + datetime.timedelta(seconds=4)
            stop = corrected_planned_imaging.stop - datetime.timedelta(seconds=4)

            planning_processing_completeness_operation["events"].append({
                "gauge": {
                        "insertion_type": "INSERT_and_ERASE_per_EVENT",
                    "name": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_" + level,
                    "system": satellite
                },
                "start": start.isoformat(),
                "stop": stop.isoformat(),
                "links": [
                    {
                        "link": str(planned_imaging_uuid),
                        "link_mode": "by_uuid",
                        "name": "PROCESSING_COMPLETENESS",
                        "back_ref": "PLANNED_IMAGING"
                    }],
                "values": planning_event_values
            })
        # end if

        # Obtain ISP_VALIDITY events
        isp_validities = query.get_events(gauge_names = {"filter":"ISP_VALIDITY", "op":"like"},
                                          value_filters = [{"name": {"str": "satellite", "op": "like"}, "type": "text", "value": {"op": "like", "value": satellite}}],
                                          start_filters = [{"date": datablock["stop"].isoformat(), "op": "<"}],
                                          stop_filters = [{"date": datablock["start"].isoformat(), "op": ">"}])
        # Received Imaging Completeness
        if len(isp_validities) > 0:
            reception_matching_status = "MATCHED_ISP_VALIDITY"
            isp_validity_segments = ingestion_functions.convert_eboa_events_to_date_segments(isp_validities)
            intersected_isp_validities = ingestion_functions.get_intersected_timeline_with_idx(ingestion_functions.intersect_timelines([datablock], isp_validity_segments), 2)
            greater_isp_validity_segment = ingestion_functions.get_greater_segment(intersected_isp_validities)
            isp_validity = [isp_validity for isp_validity in isp_validities if isp_validity.event_uuid == greater_isp_validity_segment["id"]][0]

            isp_validity_uuid = isp_validity.event_uuid

            downlink_orbit_values = query.get_event_values_interface(value_type="double",
                                                                    value_filters=[{"name": {"op": "like", "str": "downlink_orbit"}, "type": "double"}],
                                                                     event_uuids = {"op": "in", "filter": [isp_validity_uuid]})
            downlink_orbit = str(downlink_orbit_values[0].value)

            links_processing_validity.append({
                "link": str(isp_validity_uuid),
                "link_mode": "by_uuid",
                "name": "PROCESSING_VALIDITY",
                "back_ref": "ISP_VALIDITY"
            })
            links_processing_reception_completeness.append({
                "link": str(isp_validity_uuid),
                "link_mode": "by_uuid",
                "name": "PROCESSING_COMPLETENESS",
                "back_ref": "ISP_VALIDITY"
            })

            isp_validity_processing_completeness_generation_time = isp_validity.source.generation_time.isoformat()

            # Insert the linked COMPLETENESS event for the automatic completeness check
            isp_validity_values = isp_validity.get_structured_values()
            isp_validity_values[0]["values"] = [value for value in isp_validity_values[0]["values"] if value["name"] != "status"] + [
                {"name": "status",
                 "type": "text",
                 "value": "MISSING"}
            ]

            # Add margin of 6 second to each side of the segment to avoid false alerts
            start = isp_validity.start + datetime.timedelta(seconds=6)
            stop = isp_validity.stop - datetime.timedelta(seconds=6)

            isp_validity_processing_completeness_operation["events"].append({
                "gauge": {
                        "insertion_type": "INSERT_and_ERASE_per_EVENT",
                    "name": "ISP_VALIDITY_PROCESSING_COMPLETENESS_" + level,
                    "system": satellite
                },
                "start": start.isoformat(),
                "stop": stop.isoformat(),
                "links": [
                    {
                        "link": str(isp_validity_uuid),
                        "link_mode": "by_uuid",
                        "name": "PROCESSING_COMPLETENESS",
                        "back_ref": "ISP_VALIDITY"
                    }],
                "values": isp_validity_values
            })

        # end if

        links_planning_processing_completeness.append({
            "link": processing_validity_link_ref,
            "link_mode": "by_ref",
            "name": "PROCESSING_COMPLETENESS",
            "back_ref": "PROCESSING_VALIDITY"
        })
        planning_processing_completeness_event = {
            "explicit_reference": datastrip,
            "gauge": {
                "insertion_type": "INSERT_and_ERASE_per_EVENT",
                "name": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_" + level,
                "system": satellite
            },
            "links": links_planning_processing_completeness,
             "start": datablock["start"].isoformat(),
             "stop": datablock["stop"].isoformat(),
             "values": [{
                 "name": "details",
                 "type": "object",
                 "values": [{
                    "type": "text",
                    "value": status,
                    "name": "status"
                 },{
                     "type": "text",
                     "value": level,
                     "name": "level"
                 },{
                     "type": "text",
                     "value": satellite,
                     "name": "satellite"
                 },{
                     "name": "processing_centre",
                     "type": "text",
                     "value": system
                 },{
                     "name": "matching_plan_status",
                     "type": "text",
                     "value": planning_matching_status
                 },{
                     "name": "matching_reception_status",
                     "type": "text",
                     "value": reception_matching_status
                 }]
             }]
        }
        if sensing_orbit != "":
            planning_processing_completeness_event["values"][0]["values"].append({
                "name": "sensing_orbit",
                "type": "double",
                "value": sensing_orbit
            })
        # end if
        if downlink_orbit != "":
            planning_processing_completeness_event["values"][0]["values"].append({
                "name": "downlink_orbit",
                "type": "double",
                "value": downlink_orbit
            })
        # end if
        list_of_events.append(planning_processing_completeness_event)

        links_processing_reception_completeness.append({
            "link": processing_validity_link_ref,
            "link_mode": "by_ref",
            "name": "PROCESSING_COMPLETENESS",
            "back_ref": "PROCESSING_VALIDITY"
        })
        processing_reception_completeness_event = {
            "explicit_reference": datastrip,
            "gauge": {
                "insertion_type": "INSERT_and_ERASE_per_EVENT",
                "name": "ISP_VALIDITY_PROCESSING_COMPLETENESS_" + level,
                "system": satellite
            },
            "links": links_processing_reception_completeness,
             "start": datablock["start"].isoformat(),
             "stop": datablock["stop"].isoformat(),
             "values": [{
                 "name": "details",
                 "type": "object",
                 "values": [{
                    "type": "text",
                    "value": status,
                    "name": "status"
                 },{
                     "type": "text",
                     "value": level,
                     "name": "level"
                 },{
                     "type": "text",
                     "value": satellite,
                     "name": "satellite"
                 },{
                     "name": "processing_centre",
                     "type": "text",
                     "value": system
                 },{
                     "name": "matching_plan_status",
                     "type": "text",
                     "value": planning_matching_status
                 },{
                     "name": "matching_reception_status",
                     "type": "text",
                     "value": reception_matching_status
                 }]
             }]
        }
        if sensing_orbit != "":
            processing_reception_completeness_event["values"][0]["values"].append({
                "name": "sensing_orbit",
                "type": "double",
                "value": sensing_orbit
            })
        # end if
        if downlink_orbit != "":
            processing_reception_completeness_event["values"][0]["values"].append({
                "name": "downlink_orbit",
                "type": "double",
                "value": downlink_orbit
            })
        # end if

        list_of_events.append(processing_reception_completeness_event)
        processing_validity_event = {
            "key": datastrip + "_" + "processing_validity",
            "link_ref": processing_validity_link_ref,
            "explicit_reference": datastrip,
            "gauge": {
                "insertion_type": "EVENT_KEYS",
                "name": "PROCESSING_VALIDITY",
                "system": system
            },
            "links": links_processing_validity,
             "start": datablock["start"].isoformat(),
             "stop": datablock["stop"].isoformat(),
             "values": [{
                 "name": "details",
                 "type": "object",
                 "values": [{
                    "type": "text",
                    "value": status,
                    "name": "status"
                 },{
                     "type": "text",
                     "value": level,
                     "name": "level"
                 },{
                     "type": "text",
                     "value": satellite,
                     "name": "satellite"
                 },{
                     "name": "processing_centre",
                     "type": "text",
                     "value": system
                 },{
                     "name": "matching_plan_status",
                     "type": "text",
                     "value": planning_matching_status
                 },{
                     "name": "matching_reception_status",
                     "type": "text",
                     "value": reception_matching_status
                 }],
             }]
        }

        if sensing_orbit != "":
            processing_validity_event["values"][0]["values"].append({
                "name": "sensing_orbit",
                "type": "double",
                "value": sensing_orbit
            })
        # end if
        if downlink_orbit != "":
            processing_validity_event["values"][0]["values"].append({
                "name": "downlink_orbit",
                "type": "double",
                "value": downlink_orbit
            })
        # end if

        list_of_events.append(processing_validity_event)

    # end for

    if len(planning_processing_completeness_operation["events"]) > 0:
        completeness_event_starts = [event["start"] for event in planning_processing_completeness_operation["events"]]
        completeness_event_starts.sort()
        completeness_event_stops = [event["stop"] for event in planning_processing_completeness_operation["events"]]
        completeness_event_stops.sort()

        # Source for the completeness planning operation adjusting the validity to the events
        planning_processing_completeness_operation["source"] = {
            "name": source["name"],
            "generation_time": planning_processing_completeness_generation_time,
            "validity_start": completeness_event_starts[0],
            "validity_stop": completeness_event_stops[-1]
        }

        list_of_operations.append(planning_processing_completeness_operation)
    # end if

    if len(isp_validity_processing_completeness_operation["events"]) > 0:
        completeness_event_starts = [event["start"] for event in isp_validity_processing_completeness_operation["events"]]
        completeness_event_starts.sort()
        completeness_event_stops = [event["stop"] for event in isp_validity_processing_completeness_operation["events"]]
        completeness_event_stops.sort()

        # Source for the completeness received imaging operation adjusting the validity to the events
        isp_validity_processing_completeness_operation["source"] = {
            "name": source["name"],
            "generation_time": isp_validity_processing_completeness_generation_time,
            "validity_start": completeness_event_starts[0],
            "validity_stop": completeness_event_stops[-1]
        }

        list_of_operations.append(isp_validity_processing_completeness_operation)
    # end if

    return general_status
# end def

def L1C_L2A_processing(source, engine, query, list_of_events, processing_validity_events, datastrip, list_of_operations, system, version, filename, satellite):
    """
    Method to generate the events for the levels L1C and L2A
    :param source: information of the source
    :type source: dict
    :param engine: object to access the engine of the EBOA
    :type engine: Engine
    :param query: object to access the query interface of the EBOA
    :type query: Query
    :param list_of_events: list to store the events to be inserted into the eboa
    :type list_of_events: list
    :param processing_validity_events: dict containing the events linked to the sensing date from the datablock analysed
    :type processing_validity_events: dict
    :param datastrip: datastrip
    :type datastrip: str
    :param list_of_operations: list of operations to be inserted into EBOA
    :type list_of_operations: list
    :param system: center where data has been processed
    :type system: str
    :param version: version of the processor used
    :type version: str
    :param filename: name of the processor file
    :type version: str

    :return: None

    """
    gaps = []
    planned_cut_imagings = []
    isp_validities = []
    general_status = "COMPLETE"

    # Obtain the production level from the datastrip
    level = datastrip[13:16].replace("_","")

    # Completeness operations for the completeness analysis of the plan
    planning_processing_completeness_operation = {
        "mode": "insert",
        "dim_signature": {
            "name": "PROCESSING_" + satellite,
            "exec": "planning_processing_" + filename,
            "version": version
        },
        "events": []
    }
    # Completeness operations for the completeness analysis of the received imaging
    isp_validity_processing_completeness_operation = {
        "mode": "insert",
        "dim_signature": {
            "name": "PROCESSING_" + satellite,
            "exec": "processing_received_" + filename,
            "version": version
        },
        "events": []
    }

    # Classify the events obtained from the datatrip linked events
    for processing_validity_event in processing_validity_events:
        status = "COMPLETE"
        linking_to_processing_validity_events = query.get_linking_events(event_uuids = {"filter": [processing_validity_event.event_uuid], "op": "in"},
                                                              link_names = {"filter": ["PROCESSING_GAP", "PLANNED_IMAGING", "ISP_VALIDITY"], "op": "in"})

        for event in linking_to_processing_validity_events["linking_events"]:
            if event.gauge.name.startswith("PROCESSING_GAP"):
                gaps.append(event)
            # end if
            if event.gauge.name.startswith("PLANNED_CUT_IMAGING"):
                planned_cut_imagings.append(event)
            # end elif
            if event.gauge.name.startswith("ISP_VALIDITY"):
                isp_validities.append(event)
        # end for

        # If gaps, status is incomplete
        processing_validity_link_ref = "PROCESSING_VALIDITY_" + processing_validity_event.start.isoformat()
        if len(gaps) > 0:
            status = "INCOMPLETE"
            general_status = "INCOMPLETE"

            for gap in gaps:
                values = gap.get_structured_values()
                value_level = [value for value in values[0]["values"] if value["name"] == "level"][0]
                value_level["value"] = level
                gap_event = {
                    "key": datastrip + "_" + "processing_validity",
                    "explicit_reference": datastrip,
                    "gauge": {
                        "insertion_type": "EVENT_KEYS",
                        "name": "PROCESSING_GAP",
                        "system": system
                    },
                    "links": [{
                             "link": processing_validity_link_ref,
                             "link_mode": "by_ref",
                             "name": "PROCESSING_GAP",
                             "back_ref": "PROCESSING_VALIDITY"
                             }
                         ],
                     "start": gap.start.isoformat(),
                     "stop": gap.stop.isoformat(),
                     "values": values
                }
                list_of_events.append(gap_event)
            # end for
        # end if

        links_processing_validity = []
        links_planning_processing_completeness = []
        links_processing_reception_completeness = []
        planning_matching_status = "NO_MATCHED_PLANNED_IMAGING"
        reception_matching_status = "NO_MATCHED_ISP_VALIDITY"
        sensing_orbit = ""
        downlink_orbit = ""

        # Planning completeness
        if len(planned_cut_imagings) > 0:
            planned_imaging = planned_cut_imagings[0]
            planned_imaging_uuid = planned_imaging.event_uuid
            planning_matching_status = "MATCHED_PLANNED_IMAGING"
            sensing_orbit_values = query.get_event_values_interface(value_type="double",
                                                                    value_filters=[{"name": {"op": "like", "str": "start_orbit"}, "type": "double"}],
                                                                    event_uuids = {"op": "in", "filter": [planned_imaging_uuid]})
            sensing_orbit = str(sensing_orbit_values[0].value)

            links_processing_validity.append({
                "link": str(planned_imaging_uuid),
                "link_mode": "by_uuid",
                "name": "PROCESSING_VALIDITY",
                "back_ref": "PLANNED_IMAGING"
            })
            links_planning_processing_completeness.append({
                "link": str(planned_imaging_uuid),
                "link_mode": "by_uuid",
                "name": "PROCESSING_COMPLETENESS",
                "back_ref": "PLANNED_IMAGING"
            })

            corrected_planned_imaging_uuid = [event_link.event_uuid_link for event_link in planned_imaging.eventLinks if event_link.name == "TIME_CORRECTION"][0]
            corrected_planned_imaging_event = query.get_events(event_uuids = {"op": "in", "filter": [corrected_planned_imaging_uuid]})

            planning_processing_completeness_generation_time = planned_imaging.source.generation_time.isoformat()

            planning_event_values = planned_imaging.get_structured_values()
            planning_event_values[0]["values"] = planning_event_values[0]["values"] + [
                {"name": "status",
                 "type": "text",
                 "value": "MISSING"}
            ]

            # Add margin of 4 seconds to each side of the segment to avoid false alerts
            start = corrected_planned_imaging_event[0].start + datetime.timedelta(seconds=4)
            stop = corrected_planned_imaging_event[0].stop - datetime.timedelta(seconds=4)

            planning_processing_completeness_operation["events"].append({
                "gauge": {
                        "insertion_type": "INSERT_and_ERASE_per_EVENT",
                    "name": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_" + level + "",
                    "system": satellite
                },
                "start": start.isoformat(),
                "stop": stop.isoformat(),
                "links": [
                    {
                        "link": str(planned_imaging_uuid),
                        "link_mode": "by_uuid",
                        "name": "PROCESSING_COMPLETENESS",
                        "back_ref": "PLANNED_IMAGING"
                    }],
                "values": planning_event_values
            })
        # end if

        # Received Imaging Completeness
        if len(isp_validities) > 0:
            reception_matching_status = "MATCHED_ISP_VALIDITY"
            isp_validity = isp_validities[0]

            isp_validity_uuid = isp_validity.event_uuid

            downlink_orbit_values = query.get_event_values_interface(value_type="double",
                                                                    value_filters=[{"name": {"op": "like", "str": "downlink_orbit"}, "type": "double"}],
                                                                     event_uuids = {"op": "in", "filter": [isp_validity_uuid]})
            downlink_orbit = str(downlink_orbit_values[0].value)

            links_processing_validity.append({
                "link": str(isp_validity_uuid),
                "link_mode": "by_uuid",
                "name": "PROCESSING_VALIDITY",
                "back_ref": "ISP_VALIDITY"
            })
            links_processing_reception_completeness.append({
                "link": str(isp_validity_uuid),
                "link_mode": "by_uuid",
                "name": "PROCESSING_COMPLETENESS",
                "back_ref": "ISP_VALIDITY"
            })

            isp_validity_processing_completeness_generation_time = isp_validity.source.generation_time.isoformat()

            # Insert the linked COMPLETENESS event for the automatic completeness check
            isp_validity_values = isp_validity.get_structured_values()
            isp_validity_values[0]["values"] = [value for value in isp_validity_values[0]["values"] if value["name"] != "status"] + [
                {"name": "status",
                 "type": "text",
                 "value": "MISSING"}
            ]

            # Add margin of 6 second to each side of the segment to avoid false alerts
            start = isp_validity.start + datetime.timedelta(seconds=6)
            stop = isp_validity.stop - datetime.timedelta(seconds=6)

            isp_validity_processing_completeness_operation["events"].append({
                "gauge": {
                        "insertion_type": "INSERT_and_ERASE_per_EVENT",
                    "name": "ISP_VALIDITY_PROCESSING_COMPLETENESS_" + level,
                    "system": satellite
                },
                "start": start.isoformat(),
                "stop": stop.isoformat(),
                "links": [
                    {
                        "link": str(isp_validity_uuid),
                        "link_mode": "by_uuid",
                        "name": "PROCESSING_COMPLETENESS",
                        "back_ref": "ISP_VALIDITY"
                    }],
                "values": isp_validity_values
            })

        # end if

        links_planning_processing_completeness.append({
            "link": processing_validity_link_ref,
            "link_mode": "by_ref",
            "name": "PROCESSING_COMPLETENESS",
            "back_ref": "PROCESSING_VALIDITY"
        })
        planning_processing_completeness_event = {
            "explicit_reference": datastrip,
            "gauge": {
                "insertion_type": "INSERT_and_ERASE_per_EVENT",
                "name": "PLANNED_IMAGING_PROCESSING_COMPLETENESS_" + level,
                "system": satellite
            },
            "links": links_planning_processing_completeness,
             "start": processing_validity_event.start.isoformat(),
             "stop": processing_validity_event.stop.isoformat(),
             "values": [{
                 "name": "details",
                 "type": "object",
                 "values": [{
                    "type": "text",
                    "value": status,
                    "name": "status"
                 },{
                     "type": "text",
                     "value": level,
                     "name": "level"
                 },{
                     "type": "text",
                     "value": satellite,
                     "name": "satellite"
                 },{
                     "name": "processing_centre",
                     "type": "text",
                     "value": system
                 },{
                     "name": "matching_plan_status",
                     "type": "text",
                     "value": planning_matching_status
                 },{
                     "name": "matching_reception_status",
                     "type": "text",
                     "value": reception_matching_status
                 }]
             }]
        }

        if sensing_orbit != "":
            planning_processing_completeness_event["values"][0]["values"].append({
                "name": "sensing_orbit",
                "type": "double",
                "value": sensing_orbit
            })
        # end if
        if downlink_orbit != "":
            planning_processing_completeness_event["values"][0]["values"].append({
                "name": "downlink_orbit",
                "type": "double",
                "value": downlink_orbit
            })
        # end if

        list_of_events.append(planning_processing_completeness_event)

        links_processing_reception_completeness.append({
            "link": processing_validity_link_ref,
            "link_mode": "by_ref",
            "name": "PROCESSING_COMPLETENESS",
            "back_ref": "PROCESSING_VALIDITY"
        })
        processing_reception_completeness_event = {
            "explicit_reference": datastrip,
            "gauge": {
                "insertion_type": "INSERT_and_ERASE_per_EVENT",
                "name": "ISP_VALIDITY_PROCESSING_COMPLETENESS_" + level,
                "system": satellite
            },
            "links": links_processing_reception_completeness,
             "start": processing_validity_event.start.isoformat(),
             "stop": processing_validity_event.stop.isoformat(),
             "values": [{
                 "name": "details",
                 "type": "object",
                 "values": [{
                    "type": "text",
                    "value": status,
                    "name": "status"
                 },{
                     "type": "text",
                     "value": level,
                     "name": "level"
                 },{
                     "type": "text",
                     "value": satellite,
                     "name": "satellite"
                 },{
                     "name": "processing_centre",
                     "type": "text",
                     "value": system
                 },{
                     "name": "matching_plan_status",
                     "type": "text",
                     "value": planning_matching_status
                 },{
                     "name": "matching_reception_status",
                     "type": "text",
                     "value": reception_matching_status
                 }]
             }]
        }

        if sensing_orbit != "":
            processing_reception_completeness_event["values"][0]["values"].append({
                "name": "sensing_orbit",
                "type": "double",
                "value": sensing_orbit
            })
        # end if
        if downlink_orbit != "":
            processing_reception_completeness_event["values"][0]["values"].append({
                "name": "downlink_orbit",
                "type": "double",
                "value": downlink_orbit
            })
        # end if

        list_of_events.append(processing_reception_completeness_event)

        processing_validity_event = {
            "key": datastrip + "_" + "processing_validity",
            "link_ref": processing_validity_link_ref,
            "explicit_reference": datastrip,
            "gauge": {
                "insertion_type": "EVENT_KEYS",
                "name": "PROCESSING_VALIDITY",
                "system": system
            },
            "links": links_processing_validity,
             "start": processing_validity_event.start.isoformat(),
             "stop": processing_validity_event.stop.isoformat(),
             "values": [{
                 "name": "details",
                 "type": "object",
                 "values": [{
                    "type": "text",
                    "value": status,
                    "name": "status"
                 },{
                     "type": "text",
                     "value": level,
                     "name": "level"
                 },{
                     "type": "text",
                     "value": satellite,
                     "name": "satellite"
                 },{
                     "name": "processing_centre",
                     "type": "text",
                     "value": system
                 },{
                     "name": "matching_plan_status",
                     "type": "text",
                     "value": planning_matching_status
                 },{
                     "name": "matching_reception_status",
                     "type": "text",
                     "value": reception_matching_status
                 }],
             }]
        }

        if sensing_orbit != "":
            processing_validity_event["values"][0]["values"].append({
                "name": "sensing_orbit",
                "type": "double",
                "value": sensing_orbit
            })
        # end if
        if downlink_orbit != "":
            processing_validity_event["values"][0]["values"].append({
                "name": "downlink_orbit",
                "type": "double",
                "value": downlink_orbit
            })
        # end if

        list_of_events.append(processing_validity_event)

        if len(planning_processing_completeness_operation["events"]) > 0:
            completeness_event_starts = [event["start"] for event in planning_processing_completeness_operation["events"]]
            completeness_event_starts.sort()
            completeness_event_stops = [event["stop"] for event in planning_processing_completeness_operation["events"]]
            completeness_event_stops.sort()

            # Source for the completeness planning operation adjusting the validity to the events
            planning_processing_completeness_operation["source"] = {
                "name": source["name"],
                "generation_time": planning_processing_completeness_generation_time,
                "validity_start": completeness_event_starts[0],
                "validity_stop": completeness_event_stops[-1]
            }

            list_of_operations.append(planning_processing_completeness_operation)
        # end if

        if len(isp_validity_processing_completeness_operation["events"]) > 0:
            completeness_event_starts = [event["start"] for event in isp_validity_processing_completeness_operation["events"]]
            completeness_event_starts.sort()
            completeness_event_stops = [event["stop"] for event in isp_validity_processing_completeness_operation["events"]]
            completeness_event_stops.sort()

            # Source for the completeness received imaging operation adjusting the validity to the events
            isp_validity_processing_completeness_operation["source"] = {
                "name": source["name"],
                "generation_time": isp_validity_processing_completeness_generation_time,
                "validity_start": completeness_event_starts[0],
                "validity_stop": completeness_event_stops[-1]
            }

            list_of_operations.append(isp_validity_processing_completeness_operation)
        # end if


    # end if


    return general_status
# end def

####
# EOP CFI
####
def build_orbpre_file(start, stop, satellite, orbpre_events = None):
    """
    Method to generate an orbpre file from data inside the DDBB
    """
    
    (_, orbpre_file_path) = mkstemp()

    f= open(orbpre_file_path,"w+")

    header = '''<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
    <Earth_Explorer_File>
    
    <Earth_Explorer_Header>
    <Fixed_Header>
    <File_Name>{}_OPER_MPL_ORBPRE_{}_{}_0001</File_Name>
    <File_Description>FOS Predicted Orbit File</File_Description>
    <Notes></Notes>
    <Mission>SENTINEL {}</Mission>
    <File_Class>OPER</File_Class>
    <File_Type>MPL_ORBPRE</File_Type>
    <Validity_Period>
    <Validity_Start>UTC={}</Validity_Start>
    <Validity_Stop>UTC={}</Validity_Stop>
    </Validity_Period>
    <File_Version>0001</File_Version>
    <Source>
    <System>FOS</System>
    <Creator>NAPEOS</Creator>
    <Creator_Version>3.0</Creator_Version>
    <Creation_Date>UTC={}</Creation_Date>
    </Source>
    </Fixed_Header>
    <Variable_Header>
    <Ref_Frame>EARTH_FIXED</Ref_Frame>
    <Time_Reference>UTC</Time_Reference>
    </Variable_Header>
    </Earth_Explorer_Header>
    '''.format(satellite, start, stop, satellite, start, stop, datetime.datetime.now().isoformat())

    f.write(header)
    
    if orbpre_events == None:
        query = Query()

        stop_query = (parser.parse(stop) + datetime.timedelta(minutes=100)).isoformat()

        orbpre_events = query.get_events(gauge_names = {"filter": "ORBIT_PREDICTION", "op": "like"},
                                         start_filters = [{"date": stop_query, "op": "<"}],
                                         stop_filters = [{"date": start, "op": ">"}],
                                         value_filters = [{"name": {"str": "satellite", "op": "like"},
                                                           "type": "text",
                                                           "value": {"value": satellite, "op": "=="}}])

        orbpre_events.sort(key=lambda x:x.start)

        logger.debug("The orbpre events cover from {} to {}".format(orbpre_events[0].start.isoformat(), orbpre_events[-1].start.isoformat()))
        
        number_of_orbpre_events = len(orbpre_events)

        datablock_begin = '''
        <Data_Block type="xml">
        <List_of_OSVs count="{}">
        '''.format(number_of_orbpre_events)

        f.write(datablock_begin)        

        for event in orbpre_events:
            tai = [value.value for value in event.eventTimestamps if value.name == "tai"][0].isoformat()
            utc = event.start.isoformat()
            ut1 = [value.value for value in event.eventTimestamps if value.name == "ut1"][0].isoformat()
            orbit = [value.value for value in event.eventDoubles if value.name == "orbit"][0]
            x = [value.value for value in event.eventDoubles if value.name == "x"][0]
            y = [value.value for value in event.eventDoubles if value.name == "y"][0]
            z = [value.value for value in event.eventDoubles if value.name == "z"][0]
            vx = [value.value for value in event.eventDoubles if value.name == "vx"][0]
            vy = [value.value for value in event.eventDoubles if value.name == "vy"][0]
            vz = [value.value for value in event.eventDoubles if value.name == "vz"][0]
            quality = [value.value for value in event.eventDoubles if value.name == "quality"][0]
            osv = '''
            <OSV>
            <TAI>TAI={}</TAI>
            <UTC>UTC={}</UTC>
            <UT1>UT1={}</UT1>
            <Absolute_Orbit>+{}</Absolute_Orbit>
            <X unit="m">{}</X>
            <Y unit="m">{}</Y>
            <Z unit="m">{}</Z>
            <VX unit="m/s">{}</VX>
            <VY unit="m/s">{}</VY>
            <VZ unit="m/s">{}</VZ>
            <Quality>{}</Quality>
            </OSV>
            '''.format(tai, utc, ut1, orbit, x, y, z, vx, vy, vz, quality)
            f.write(osv)        
        # end for

        query.close_session()
    else:
        number_of_orbpre_events = len(orbpre_events)

        datablock_begin = '''
        <Data_Block type="xml">
        <List_of_OSVs count="{}">
        '''.format(number_of_orbpre_events)

        f.write(datablock_begin)        

        logger.debug("The orbpre events cover from {} to {}".format(orbpre_events[0]["start"], orbpre_events[-1]["start"]))
        
        for event in orbpre_events:
            tai = [value["value"] for value in event["values"][0]["values"] if value["name"] == "tai"][0]
            utc = event["start"]
            ut1 = [value["value"] for value in event["values"][0]["values"] if value["name"] == "ut1"][0]
            orbit = [value["value"] for value in event["values"][0]["values"] if value["name"] == "orbit"][0]
            x = [value["value"] for value in event["values"][0]["values"] if value["name"] == "x"][0]
            y = [value["value"] for value in event["values"][0]["values"] if value["name"] == "y"][0]
            z = [value["value"] for value in event["values"][0]["values"] if value["name"] == "z"][0]
            vx = [value["value"] for value in event["values"][0]["values"] if value["name"] == "vx"][0]
            vy = [value["value"] for value in event["values"][0]["values"] if value["name"] == "vy"][0]
            vz = [value["value"] for value in event["values"][0]["values"] if value["name"] == "vz"][0]
            quality = [value["value"] for value in event["values"][0]["values"] if value["name"] == "quality"][0]
            osv = '''
            <OSV>
            <TAI>TAI={}</TAI>
            <UTC>UTC={}</UTC>
            <UT1>UT1={}</UT1>
            <Absolute_Orbit>+{}</Absolute_Orbit>
            <X unit="m">{}</X>
            <Y unit="m">{}</Y>
            <Z unit="m">{}</Z>
            <VX unit="m/s">{}</VX>
            <VY unit="m/s">{}</VY>
            <VZ unit="m/s">{}</VZ>
            <Quality>{}</Quality>
            </OSV>
            '''.format(tai, utc, ut1, orbit, x, y, z, vx, vy, vz, quality)
            f.write(osv)        
        # end for        
    # end if
        
    file_end = '''
    </List_of_OSVs>
    </Data_Block>
    </Earth_Explorer_File>
    '''

    f.write(file_end)
        
    f.close()

    return (number_of_orbpre_events, orbpre_file_path)

# Uncomment for debugging reasons
# @debug
def associate_footprints(events, satellite, orbpre_events = None):
    FNULL = open(os.devnull, 'w')
    
    if not type(events) == list:
        raise EventsStructureIncorrect("The parameter events has to be a list. Received events {}".format(events))
    # end if

    if len(events) == 0:
        logger.debug("There are no events for associating footprints")
        return []
    # end if
    logger.debug("There are {} events for associating footprints".format(len(events)))

    logger.debug("The events for associating footprints cover from {} to {}".format(events[0]["start"], events[-1]["stop"]))
    
    events_with_footprint = []
    
    t0 = Time("2000-01-01T00:00:00", format='isot', scale='utc')

    swath_definition_file_path = eboa_functions.get_resources_path() + "/SDF_MSI.xml"

    events.sort(key=lambda x:x["start"])    
    
    (number_of_orbpre_events, orbpre_file_path) = build_orbpre_file(events[0]["start"], events[-1]["stop"], satellite, orbpre_events)

    if number_of_orbpre_events > 1:
        for event in events:

            if not type(event) == dict:
                raise EventsStructureIncorrect("The items of the events list has to be a dict. Received item {}".format(event))
            # end if

            footprint_details = []
            if "values" in event.keys() and len(event["values"]) == 1 and "values" in event["values"][0]:
                footprint_details = [value for value in event["values"][0]["values"] if value["name"] == "footprint_details"]
            # end if
            event_with_footprint = event.copy()

            if len(footprint_details) == 0:
                start = Time(event["start"], format='isot', scale='utc')
                stop = Time(event["stop"], format='isot', scale='utc')
                start_mjd = start.mjd - t0.mjd
                stop_mjd = stop.mjd - t0.mjd
                # The footprint is created if the segment duration is less than 100 minutes (other segments are discarded as they are not interesting)
                if (stop_mjd - start_mjd) < 0.0695:
                    iterations = int(((stop_mjd - start_mjd) * 24 * 60 * 60) / 3.608) + 1
                    if iterations > 200:
                        iterations = 200
                    # end if
                    get_footprint_command = "get_footprint -b {} -e {} -o '{} {}' -s {} -n {}".format(start_mjd, stop_mjd, orbpre_file_path, orbpre_file_path, swath_definition_file_path, iterations)
                    try:
                        footprint = subprocess.check_output(get_footprint_command, shell=True, stderr=FNULL)

                        # Prepare footprint
                        coordinates = footprint.decode("utf-8").replace(" \n", "")
                        footprints = correct_footprint(coordinates)

                        for i, footprint in enumerate(footprints):
                            if len(footprint) > 0:

                                if not ("values" in event.keys() and len(event["values"]) == 1 and "values" in event["values"][0]):
                                    event_with_footprint["values"] = [{
                                        "name": "details",
                                        "type": "object",
                                        "values": []
                                    }]
                                # end if

                                footprint_object_name = "footprint_details"
                                if len(footprints) > 1:
                                    footprint_object_name = "footprint_details_" + str(i)
                                # end if

                                footprint_object = [{"name": "footprint",
                                                     "type": "geometry",
                                                     "value": footprint}]
                                event_with_footprint["values"][0]["values"].append({
                                    "name": footprint_object_name,
                                    "type": "object",
                                    "values": footprint_object
                                })

                                if logger.getEffectiveLevel() == logging.DEBUG:
                                    footprint_object.append({"name": "get_footprint_command",
                                                             "type": "text",
                                                             "value": get_footprint_command})
                                # end if
                            # end if
                        # end for
                    except subprocess.CalledProcessError:
                        logger.error("The footprint of the events could not be built because the command {} ended in error".format(get_footprint_command))
                    # end if
                else:
                    logger.debug("There event with start {} and stop {} is too large".format(event["start"], event["stop"]))
                # end if
            # end if
            events_with_footprint.append(event_with_footprint)

        # end for
    else:
        events_with_footprint = events
        logger.error("The footprint of the events could not be built because there is not enough orbit prediction information")
    # end if
    os.remove(orbpre_file_path)

    FNULL.close()

    logger.debug("The number of events generated after associating the footprint is {}".format(len(events_with_footprint)))
    
    return events_with_footprint

def correct_footprint(coordinates):

    longitude_latitudes = coordinates.split(" ")

    intersections_with_antimeridian=0
    polygon_before_first_intersection = []
    polygon_after_first_intersection = []
    polygons = [polygon_before_first_intersection]
    polygon = polygon_before_first_intersection
    for i, longitude_latitude  in enumerate(longitude_latitudes):
        if i == 0:
            j = len(longitude_latitudes) - 1
        else:
            j = i - 1
        # end if
        
        longitude, latitude = longitude_latitude.split(',')
        pre_longitude, pre_latitude = longitude_latitudes[j].split(',')

        longitude = float(longitude)
        latitude = float(latitude)

        pre_longitude = float(pre_longitude)
        pre_latitude = float(pre_latitude)
        # Check if the polygon crosses the antimeridian
        if (pre_longitude * longitude) <0 and (abs(longitude) + abs(pre_longitude)) > 270:
            if pre_longitude > 0:
                # Move the longitude coordinates to be around G meridian to calculate intersection 
                pre_longitude_g_meridian = pre_longitude - 180
                longitude_g_meridian = 180 + longitude
                latitude_med =  pre_latitude - pre_longitude_g_meridian * ((latitude - pre_latitude ) / (longitude_g_meridian - pre_longitude_g_meridian))
            else:
                pre_longitude_g_meridian = 180 + pre_longitude
                longitude_g_meridian = longitude - 180
                latitude_med =  pre_latitude - pre_longitude_g_meridian * ((latitude - pre_latitude ) / (longitude_g_meridian - pre_longitude_g_meridian))
            # end if
            if intersections_with_antimeridian == 0:
                new_longitude = 180.0
                if longitude > 0:
                    new_longitude = -180.0
                # end if
                polygon.append((new_longitude, latitude_med))
                polygons.append(polygon_after_first_intersection)
                polygon = polygon_after_first_intersection
                polygon.append((-1 * new_longitude, latitude_med))
                intersections_with_antimeridian = 1
            else:
                new_longitude = 180.0
                if longitude > 0:
                    new_longitude = -180.0
                # end if
                polygon.append((new_longitude, latitude_med))
                polygon = polygon_before_first_intersection
                polygon.append((-1 * new_longitude, latitude_med))
                intersections_with_antimeridian = 2
            # end if
        # end if            

        # Insert the current coordinate
        polygon.append((longitude, latitude))
    # end for

    # Postgis (for at least version 2.5.1) accepts a minimum number of 8 coordinates for a polygon. So, when the number of coordinates is 4 they are just duplicated
    if len(polygon_before_first_intersection) == 2:
        polygon_before_first_intersection.append(polygon_before_first_intersection[1])
        polygon_before_first_intersection.append(polygon_before_first_intersection[0])
    else:
        polygon_before_first_intersection.append(polygon_before_first_intersection[0])
    # end if    

    # Postgis (for at least version 2.5.1) accepts a minimum number of 8 coordinates for a polygon. So, when the number of coordinates is 4 they are just duplicated
    if intersections_with_antimeridian > 0 and len(polygon_after_first_intersection) == 2:
        polygon_after_first_intersection.append(polygon_after_first_intersection[1])
        polygon_after_first_intersection.append(polygon_after_first_intersection[0])
    elif intersections_with_antimeridian > 0:
        polygon_after_first_intersection.append(polygon_after_first_intersection[0])
    # end if    

    footprints = []
    for polygon in polygons:
        footprint = ""
        for i, coordinate in enumerate(polygon):
            if i == len(polygon) - 1:
                footprint = footprint + str(coordinate[0]) + " " + str(coordinate[1])
            else:
                footprint = footprint + str(coordinate[0]) + " " + str(coordinate[1]) + " "
            # end if
        # end for
        footprints.append(footprint)
    # end for

    return footprints
