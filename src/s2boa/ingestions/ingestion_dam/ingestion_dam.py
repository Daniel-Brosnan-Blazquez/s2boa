"""
Ingestion module for the REP_OPDAM files of Sentinel-2

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

    list_of_explicit_references = []
    list_of_annotations = []

    # Obtain the station
    system = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Source/System")[0].text
    # Obtain the creation date from the file name as the annotation creation date is not always correct
    creation_date = file_name[25:40]
    # Obtain the validity start
    validity_start = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Validity_Period/Validity_Start")[0].text.split("=")[1]
    # Obtain the validity stop
    validity_stop = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Validity_Period/Validity_Stop")[0].text.split("=")[1]

    # Source for the main operation
    source= {
        "name": file_name,
        "reception_time": reception_time,
        "generation_time": creation_date,
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

    ### Corrections made on 2019/11/27 to avoid inserting information regarding granules
    for product in xpath_xml("/Earth_Explorer_File/Data_Block/IngestedProducts/IngestedProduct[not(contains(product_id, '_GR_'))]"):
        ### Corrections made on 2019/11/27 to avoid inserting information regarding granules        
        #Obtain the product ID
        product_id = product.xpath("product_id")[0].text
        # Obtain the datastrip ID
        datastrip_id = product.xpath("parent_id")[0].text
        # Obtain the satellite
        satellite = datastrip_id[0:3]
        # Obtain the baseline
        baseline = datastrip_id[58:]
        # Obtain the production level from the datastrip
        level = datastrip_id[13:16].replace("_","")
        # Obtain the sensing identifier
        sensing_identifier = datastrip_id[41:57]
        # Obtain the datatake ID
        datatake_id = product.xpath("datatake_id")[0].text
        # Obtain the cataloging_time
        cataloging_time = product.xpath("insertion_time")[0].text


        datatake_exists = len(query.get_explicit_refs(annotation_cnf_names = {"filter": "DATATAKE", "op": "=="},
        annotation_value_filters = [{"name": {"filter": "datatake_identifier", "op": "=="}, "type": "text", "value": {"op": "==", "filter": datatake_id}}])) > 0
        cataloging_annotation = {
            "explicit_reference" : product_id,
            "annotation_cnf": {
                "name": "CATALOGING_TIME",
                "system": system
                },
            "values": [
                {"name": "cataloging_time",
                 "type": "timestamp",
                 "value": cataloging_time
                }]
        }
        list_of_annotations.append(cataloging_annotation)

        if not datatake_exists:

            # Insert the datatake_annotation
            datatake_annotation = {
            "explicit_reference": datastrip_id,
            "annotation_cnf": {
                "name": "DATATAKE",
                "system": satellite
                },
            "values": [
                {"name": "datatake_identifier",
                 "type": "text",
                 "value": datatake_id
                }]
            }
            list_of_annotations.append(datatake_annotation)

            baseline_annotation = {
            "explicit_reference": datastrip_id,
            "annotation_cnf": {
                "name": "BASELINE",
                "system": system
                },
            "values": [
                {"name": "baseline",
                 "type": "text",
                 "value": baseline
                }]
            }
            list_of_annotations.append(baseline_annotation)

            datastrip_sensing_explicit_ref= {
                "group": level + "_DS",
                "links": [{
                    "back_ref": "SENSING_IDENTIFIER",
                    "link": "DATASTRIP",
                    "name": sensing_identifier
                    }
                ],
                "name": datastrip_id
            }
            list_of_explicit_references.append(datastrip_sensing_explicit_ref)

            for granule in product.xpath("product_id[contains(text(),'_GR')]"):
                # Insert the granule explicit reference
                granule_explicit_reference = {
                    "group": level + "_GR",
                    "links": [{
                        "back_ref": "DATASTRIP",
                        "link": "GRANULE",
                        "name": datastrip_id
                        }
                    ],
                    "name": product_id
                }
                list_of_explicit_references.append(granule_explicit_reference)
            # end for

            for tile in product.xpath("product_id[contains(text(),'_TL')]"):
                # Insert the tile explicit reference
                tile_explicit_reference = {
                    "group": level + "_TL",
                    "links": [{
                        "back_ref": "DATASTRIP",
                        "link": "TILE",
                        "name": datastrip_id
                        }
                    ],
                    "name": product_id
                }
                list_of_explicit_references.append(tile_explicit_reference)
            # end if
        #end if
    # end for

    functions.insert_ingestion_progress(session_progress, general_source_progress, 90)
    
    data = {"operations": [{
        "mode": "insert",
        "dim_signature": {
              "name": "CATALOGING",
              "exec": os.path.basename(__file__),
              "version": version
        },
        "source": source,
        "annotations": list_of_annotations,
        "explicit_references": list_of_explicit_references,
        }]}

    functions.insert_ingestion_progress(session_progress, general_source_progress, 100)

    query.close_session()

    new_file.close()
    
    return data
