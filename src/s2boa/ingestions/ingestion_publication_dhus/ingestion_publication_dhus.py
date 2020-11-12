"""
Ingestion module for the publication timings on DHUS of tiles of Sentinel-2

Written by DEIMOS Space S.L. (dibb)

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
    list_of_datastrips = []

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
    
    # Obtain the creation date
    creation_date = xpath_xml("/feed/updated")[0].text

    # Obtain the list of complete single tile names
    complete_single_tile_names = [title.text + ".SAFE" for title in xpath_xml("/feed/entry/title")]

    functions.insert_ingestion_progress(session_progress, general_source_progress, 20)

    # Obtain the annotations USER_PRODUCT where the explicit reference is the associated tile name
    user_product_annotations = query.get_annotations(annotation_cnf_names = {"filter": "USER_PRODUCT", "op": "=="},
                                                     value_filters = [{"name": {"op": "==", "filter": "product_name"}, "type": "text", "value": {"op": "in", "filter": complete_single_tile_names}}])

    functions.insert_ingestion_progress(session_progress, general_source_progress, 40)

    # Iterate over entries of the file to annotation the DHUS publication time
    for user_product_annotation in user_product_annotations:
        user_product = [value.value for value in user_product_annotation.annotationTexts if value.name == "product_name"][0]

        dhus_publication_time = xpath_xml("/feed/entry[title = $user_product]/properties/CreationDate", user_product = user_product.split(".")[0])[0].text

        tile_dhus_publication_annotation = {
            "explicit_reference" : user_product_annotation.explicitRef.explicit_ref,
            "annotation_cnf": {
                "name": "DHUS_PUBLICATION_TIME",
                "insertion_type": "INSERT_and_ERASE"
                },
            "values": [
                {"name": "dhus_publication_time",
                 "type": "timestamp",
                 "value": dhus_publication_time
                }]
        }
        list_of_annotations.append(tile_dhus_publication_annotation)
    # end for
    
    functions.insert_ingestion_progress(session_progress, general_source_progress, 60)

    data = {"operations": [{
        "mode": "insert",
        "dim_signature": {
              "name": "DHUS_PUBLICATION",
              "exec": os.path.basename(__file__),
              "version": version
        },
        "source": {
            "name": file_name,
            "reception_time": reception_time,
            "generation_time": creation_date,
            "validity_start": creation_date,
            "validity_stop": creation_date
        },
        "annotations": list_of_annotations
    }]}
    
    functions.insert_ingestion_progress(session_progress, general_source_progress, 80)
    
    query.close_session()

    new_file.close()

    functions.insert_ingestion_progress(session_progress, general_source_progress, 100)
    
    return data
