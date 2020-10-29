"""
Ingestion module for the REP_OPHKTM files of Sentinel-2

Written by DEIMOS Space S.L. (jubv)

module eboa
"""
# Import python utilities
import os
import argparse
from dateutil import parser
import datetime
import json
import sys
import tempfile

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

    list_of_annotations = []
    list_of_events = []
    htkm_links = []

    # Obtain the satellite
    satellite = file_name[0:3]
    # Obtain the station
    system = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Source/System")[0].text
    # Obtain the alias of the station
    station_alias = functions.get_centre_name_by_alias(system)
    # Obtain the creation date
    creation_date = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Source/Creation_Date")[0].text.split("=")[1]
    # Obtain the creation date
    creation_date = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Source/Creation_Date")[0].text.split("=")[1]
    # Obtain the acquisition_center
    acquisition_center = xpath_xml("/Earth_Explorer_File/Data_Block/IngestedProducts/IngestedProduct/acquisition_center")[0].text
    # Obtain the downlink_orbit
    downlink_orbit = xpath_xml("/Earth_Explorer_File/Data_Block/IngestedProducts/IngestedProduct/downlink_orbit")[0].text
    # Obtain the generation_date
    generation_date = xpath_xml("/Earth_Explorer_File/Data_Block/IngestedProducts/IngestedProduct/generation_date")[0].text
    # Obtain the product_id
    product_id = xpath_xml("/Earth_Explorer_File/Data_Block/IngestedProducts/IngestedProduct/product_id")[0].text
    product_id_without_extension = product_id.replace(".SAFE", "")
    # Obtain the key
    key = product_id_without_extension + "-" + satellite + "-" + station_alias + "-" + downlink_orbit

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

    # Obtain the planned playback to associate the orbit number and link the production
    linking_planned_playback_to_station_schedule = query.get_linking_events(gauge_names = {"op": "==", "filter": "STATION_SCHEDULE"},
                                                                          gauge_systems = {"op": "==", "filter": station_alias},
                                                                          value_filters = [{"name": {"op": "==", "filter": "satellite"}, "type": "text", "value": {"op": "==", "filter": satellite}},
                                                                                           {"name": {"op": "==", "filter": "orbit"}, "type": "double", "value": {"op": "==", "filter": downlink_orbit}}],
                                                                          link_names = {"op": "==", "filter": "PLANNED_PLAYBACK"},
                                                                          return_prime_events = False)

    functions.insert_ingestion_progress(session_progress, general_source_progress, 20)
    
    if len(linking_planned_playback_to_station_schedule["linking_events"]) > 0:
        planned_playbacks = linking_planned_playback_to_station_schedule["linking_events"]
        planned_hktm_playbacks = [planned_playback for planned_playback in planned_playbacks for event_text in planned_playback.eventTexts if event_text.name == "playback_type" and event_text.value in ["HKTM", "HKTM_SAD"]]
        if len(planned_hktm_playbacks) > 0:
            planned_hktm_playback = planned_hktm_playbacks[0]
            htkm_links.append({
                "link": str(planned_hktm_playback.event_uuid),
                "link_mode": "by_uuid",
                "name": "HKTM_PRODUCTION_VGS",
                "back_ref": "PLANNED_PLAYBACK"
            })
        # end if
    # end if

    functions.insert_ingestion_progress(session_progress, general_source_progress, 30)

    # Obtain the executed playback to link the information
    playbacks_validity_3 = query.get_events(gauge_names = {"op": "==", "filter": "PLAYBACK_VALIDITY_3"},
                                            gauge_systems = {"op": "==", "filter": station_alias},
                                            value_filters = [{"name": {"op": "==", "filter": "satellite"}, "type": "text", "value": {"op": "==", "filter": satellite}},
                                                             {"name": {"op": "==", "filter": "downlink_orbit"}, "type": "double", "value": {"op": "==", "filter": downlink_orbit}}])

    functions.insert_ingestion_progress(session_progress, general_source_progress, 40)
    
    if len(playbacks_validity_3) > 0:
        htkm_links.append({
            "link": str(playbacks_validity_3[0].event_uuid),
            "link_mode": "by_uuid",
            "name": "HKTM_PRODUCTION_VGS",
            "back_ref": "PLAYBACK_VALIDITY"
        })
    # end if

    functions.insert_ingestion_progress(session_progress, general_source_progress, 50)
    
    # Values for the event and annotation
    hktm_values = [
                {"name": "satellite",
                 "type": "text",
                 "value": satellite
                },
                {"name": "acquisition_center",
                 "type": "text",
                 "value": station_alias
                },
                {"name": "downlink_orbit",
                 "type": "double",
                 "value": downlink_orbit
                }]

    functions.insert_ingestion_progress(session_progress, general_source_progress, 60)

    # Generate annotation
    acquisition_details = {
            "explicit_reference": product_id_without_extension,
            "annotation_cnf": {
                "name": "ACQUISITION_DETAILS",
                "system": station_alias,
                "insertion_type": "SIMPLE_UPDATE"
                },
            "values": hktm_values
            }
    
    list_of_annotations.append(acquisition_details)

    functions.insert_ingestion_progress(session_progress, general_source_progress, 70)

    hktm_production_vgs_event = {
            "key": key,
            "explicit_reference": product_id_without_extension,
            "gauge": {
                "insertion_type": "EVENT_KEYS",
                "name": "HKTM_PRODUCTION_VGS",
                "system": station_alias
            },
            "links": htkm_links,
            "start": generation_date,
            "stop": generation_date,
            "values": hktm_values
            }
    
    list_of_events.append(hktm_production_vgs_event)
    
    functions.insert_ingestion_progress(session_progress, general_source_progress, 90)

    data = {"operations": [{
                "mode": "insert",
                "dim_signature": {
                    "name": "HKTM_PRODUCTION_VGS",
                    "exec": os.path.basename(__file__),
                    "version": version
                },
                "source": {
                    "name": file_name,
                    "reception_time": reception_time,
                    "generation_time": creation_date,
                    "validity_start": generation_date,
                    "validity_stop": generation_date
                },
                "annotations": list_of_annotations,
                "events": list_of_events
                }]}

    functions.insert_ingestion_progress(session_progress, general_source_progress, 100)

    query.close_session()

    new_file.close()
    
    return data
