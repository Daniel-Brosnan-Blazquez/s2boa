"""
Ingestion module for the REP_OPDC files of Sentinel-2

Written by DEIMOS Space S.L. (femd)

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
from eboa.engine.functions import get_resources_path

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
    list_of_events_hktm = {}
    list_of_explicit_references_hktm = {}
    list_of_operations = []
    
    # Obtain the station
    system = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Source/System")[0].text
    # Obtain the creation date from the file name as the annotation creation date is not always correct
    creation_date = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Source/Creation_Date")[0].text.split("=")[1]
    # Obtain the validity start
    validity_start = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Validity_Period/Validity_Start")[0].text.split("=")[1]
    # Obtain the validity stop
    validity_stop = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Validity_Period/Validity_Stop")[0].text.split("=")[1]

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

    # Get the centres configuration
    centres_xpath = functions.get_centres_conf()

    hktm_products = {}
    
    # Loop over the circulated items
    # for item in xpath_xml("/Earth_Explorer_File/Data_Block/List_of_CirculatedItems/CirculatedItem[boolean(Result[text() = 'Success']) and  " +
    #                       "(contains(ProductId, 'OPER_CNF') or " +
    #                       "contains(ProductId, 'OPER_GIP') or " +
    #                       "contains(ProductId, 'PRD_HKTM__') or " +
    #                       "contains(ProductId, 'OPER_REP') or " +
    #                       "contains(ProductId, 'OPER_SRA') or " +
    #                       "contains(ProductId, 'OPER_TLM__REQ') or " +
    #                       "contains(ProductId, 'MPL_ORBPRE') or " +
    #                       "contains(ProductId, '_DS_') or " +
    #                       "contains(ProductId, 'AUX_SADATA') or " +
    #                       "contains(ProductId, 'MPL_TLEPRE') or " +
    #                       "(contains(ProductId, 'MPL_FS') and not(contains(ProductId, 'MPL_FSACK'))) or " +
    #                       "contains(ProductId, 'MPL_SP'))]"):
    # For the moment, the majority of reports are not treated
    for item in xpath_xml("/Earth_Explorer_File/Data_Block/List_of_CirculatedItems/CirculatedItem[boolean(Result[text() = 'Success']) and  " +
                          "(contains(ProductId, 'OPER_CNF') or " +
                          "contains(ProductId, 'OPER_GIP') or " +
                          "contains(ProductId, 'PRD_HKTM__') or " +
                          "contains(ProductId, '_DS_') or " +
                          "contains(ProductId, 'AUX_SADATA') or " +
                          "contains(ProductId, 'MPL_TLEPRE') or " +
                          "(contains(ProductId, 'MPL_FS') and not(contains(ProductId, 'MPL_FSACK'))) or " +
                          "contains(ProductId, 'MPL_SP'))]"):
        # Obtain the product ID
        product_id = item.xpath("ProductId")[0].text.replace(".tar", "").replace(".LIST", "")

        # Obtain the circulation_time
        circulation_time = item.xpath("DeliveryTime")[0].text[:-1]

        # Obtain the source of the circulation
        source = item.xpath("Centre")[0].text

        # Obtain the destination of the circulation
        destination_location = item.xpath("DestinationLocation")[0].text

        # Obtain the destination of the circulation
        destinations = centres_xpath("/centres_configuration/centre[boolean(uris/uri[contains($destination_location, text())])]", destination_location = destination_location)
        if len(destinations) > 0:
            destination = destinations[0].xpath("name")[0].text
        else:
            destination = "UNKN"
        # end if

        # Obtain the product size
        product_size = item.xpath("ProductSize")[0].text

        circulation_annotation = {
            "explicit_reference" : product_id,
            "annotation_cnf": {
                "name": "CIRCULATION_TIME",
                "system": source + "_to_" + destination
            },
            "values": [
                {"name": "circulation_time",
                 "type": "timestamp",
                 "value": circulation_time
                },
                {"name": "source",
                 "type": "text",
                 "value": source
                },
                {"name": "destination",
                 "type": "text",
                 "value": destination
                },
                {"name": "destination_location",
                 "type": "text",
                 "value": destination_location
                },
                {"name": "product_size",
                 "type": "double",
                 "value": product_size
                }]
        }
        list_of_annotations.append(circulation_annotation)

        if "PRD_HKTM__" in product_id and source == "PDMC" and destination == "FOS_":
            circulation_annotation["annotation_cnf"]["insertion_type"] = "INSERT_and_ERASE"
        # end if
        
        if "PRD_HKTM__" in product_id and not product_id in hktm_products:
            event_production_playback_validity_ddbb = query.get_events(explicit_refs = {"op": "==", "filter": product_id}, gauge_names = {"op": "==", "filter": "HKTM_PRODUCTION_PLAYBACK_VALIDITY"})

            if len(event_production_playback_validity_ddbb) == 0:
                hktm_products[product_id] = None
                explicit_reference = {
                    "group": "HKTM",
                    "name": product_id
                }
                satellite = product_id[0:3]

                if satellite not in list_of_explicit_references_hktm:
                    list_of_explicit_references_hktm[satellite] = []
                # end if
                list_of_explicit_references_hktm[satellite].append(explicit_reference)

                # Obtain the planned playback to associate the orbit number and link the production
                start_hktm_playback = product_id[20:35]
                stop_hktm_playback = product_id[36:51]
                start_planned_playback = (parser.parse(start_hktm_playback) - datetime.timedelta(seconds=30)).isoformat()
                stop_planned_playback = (parser.parse(stop_hktm_playback) + datetime.timedelta(seconds=30)).isoformat()

                # Build event
                orbit = -1
                links = []
                values = [
                    {"name": "satellite",
                     "type": "text",
                     "value": satellite
                }]

                corrected_planned_playbacks = query.get_events(gauge_names = {"op": "==", "filter": "PLANNED_PLAYBACK_CORRECTION"},
                                                               gauge_systems = {"op": "==", "filter": satellite},
                                                               value_filters = [{"name": {"op": "==", "filter": "playback_type"}, "type": "text", "value": {"op": "in", "filter": ["HKTM", "HKTM_SAD"]}}],
                                                               start_filters = [{"date": stop_planned_playback, "op": "<"}],
                                                               stop_filters = [{"date": start_planned_playback, "op": ">"}])

                if len(corrected_planned_playbacks) > 0:
                    orbit = [value.value for playback in corrected_planned_playbacks for value in playback.eventDoubles if value.name == "start_orbit"][0]
                    link_planned_playback = [link for link in corrected_planned_playbacks[0].eventLinks if link.name == "PLANNED_EVENT"]
                    if len(link_planned_playback) > 0:
                        links.append({
                            "link": str(link_planned_playback[0].event_uuid_link),
                            "link_mode": "by_uuid",
                            "name": "HKTM_PRODUCTION",
                            "back_ref": "PLANNED_PLAYBACK"
                        })
                    # end if
                # end if

                # Obtain the executed playback to link the information
                hktm_playbacks = query.get_events(gauge_names = {"op": "==", "filter": "PLAYBACK_VALIDITY_3"},
                                                               value_filters = [{"name": {"op": "==", "filter": "satellite"}, "type": "text", "value": {"op": "==", "filter": satellite}}],
                                                               start_filters = [{"date": stop_planned_playback, "op": "<"}],
                                                               stop_filters = [{"date": start_planned_playback, "op": ">"}])
                if len(hktm_playbacks) > 0:
                    if orbit == -1:
                        orbit = [value.value for playback in hktm_playbacks for value in playback.eventDoubles if value.name == "downlink_orbit"][0]
                    # end if
                    links.append({
                        "link": str(hktm_playbacks[0].event_uuid),
                        "link_mode": "by_uuid",
                        "name": "HKTM_PRODUCTION",
                        "back_ref": "PLAYBACK_VALIDITY"
                    })
                # end if

                # Add orbit value
                if orbit != -1:
                    values.append({"name": "downlink_orbit",
                                   "type": "double",
                                   "value": str(orbit)
                    })
                # end if

                # Production playback validity
                event_production_playback_validity = {
                    "key": product_id,
                    "explicit_reference": product_id,
                    "gauge": {
                        "insertion_type": "EVENT_KEYS",
                        "name": "HKTM_PRODUCTION_PLAYBACK_VALIDITY",
                        "system": system
                    },
                    "links": links,
                    "start": parser.parse(start_hktm_playback).isoformat(),
                    "stop": parser.parse(stop_hktm_playback).isoformat(),
                    "values": values
                }
                if satellite not in list_of_events_hktm:
                    list_of_events_hktm[satellite] = []
                # end if
                list_of_events_hktm[satellite].append(event_production_playback_validity)
            # end if
        # end if
    #end for

    if len(list_of_events_hktm.keys()) > 0:
        for satellite in list_of_events_hktm.keys():
            event_starts = [event["start"] for event in list_of_events_hktm[satellite]]
            event_starts.sort()
            validity_start_hktm = event_starts[0]

            event_stops = [event["stop"] for event in list_of_events_hktm[satellite]]
            event_stops.sort()
            validity_stop_hktm = event_stops[-1]

            list_of_operations.append({
                "mode": "insert",
                "dim_signature": {
                    "name": "PROCESSING_" + satellite,
                    "exec": os.path.basename(__file__),
                    "version": version
                },
                "source": {
                    "name": file_name,
                    "reception_time": reception_time,
                    "generation_time": creation_date,
                    "validity_start": validity_start_hktm,
                    "validity_stop": validity_stop_hktm
                },
                "events": list_of_events_hktm[satellite],
                "explicit_references": list_of_explicit_references_hktm[satellite]
            })
        # end for
    # end if

    functions.insert_ingestion_progress(session_progress, general_source_progress, 90)

    list_of_operations.append({
        "mode": "insert",
        "dim_signature": {
            "name": "CIRCULATION",
            "exec": os.path.basename(__file__),
            "version": version
        },
        "source": {
            "name": file_name,
            "reception_time": reception_time,
            "generation_time": creation_date,
            "validity_start": validity_start,
            "validity_stop": validity_stop
        },
        "annotations": list_of_annotations
    })
    
    data = {"operations": list_of_operations}

    functions.insert_ingestion_progress(session_progress, general_source_progress, 100)

    query.close_session()

    new_file.close()
    
    return data
