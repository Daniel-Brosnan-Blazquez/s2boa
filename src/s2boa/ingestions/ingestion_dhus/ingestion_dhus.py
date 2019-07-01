"""
Ingestion module for the REP_OPDHUS files of Sentinel-2

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
from tempfile import mkstemp

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
    (_, new_file_path) = new_file = mkstemp()
    ingestion_functions.remove_namespaces(file_path, new_file_path)

    # Parse file
    parsed_xml = etree.parse(new_file_path)
    xpath_xml = etree.XPathEvaluator(parsed_xml)

    list_of_annotations = []
    list_of_datastrips = []

    system = "DHUS"
    # Obtain the creation date from the file name as the annotation creation date is not always correct
    creation_date = file_name[25:40]
    # Obtain the validity start
    validity_start = creation_date
    # Obtain the validity stop
    validity_stop = creation_date

    # Source for the main operation
    source= {
        "name": file_name,
        "reception_time": reception_time,
        "generation_time": creation_date,
        "validity_start": validity_start,
        "validity_stop": validity_stop
    }

    for tile in xpath_xml("/Earth_Explorer_File/Data_Block/Products/Product/PDI[contains(text(),'_TL')]"):
            #Obtain the product ID
            tile_id = tile.text
            product_name = str(tile.xpath("../@name")[0])

            tile_dhus_dissemination_annotation = {
                "explicit_reference" : tile_id,
                "annotation_cnf": {
                    "name": "DHUS_DISSEMINATION_TIME",
                    "system": system
                    },
                "values": [{
                    "name": "details",
                    "type": "object",
                    "values": [
                        {"name": "dhus_dissemination_time",
                         "type": "timestamp",
                         "value": creation_date
                         }]
                }]
            }
            list_of_annotations.append(tile_dhus_dissemination_annotation)

            tile_user_product_annotation = {
                "explicit_reference" : tile_id,
                "annotation_cnf": {
                    "name": "USER_PRODUCT",
                    "system": system
                    },
                "values": [{
                    "name": "details",
                    "type": "object",
                    "values": [
                        {"name": "product_name",
                         "type": "text",
                         "value": product_name
                         }]
                }]
            }
            list_of_annotations.append(tile_user_product_annotation)
    #end for

    for datastrip in xpath_xml("/Earth_Explorer_File/Data_Block/Products/Product/PDI[contains(text(),'_DS')]"):
        if datastrip.text not in list_of_datastrips:
            list_of_datastrips.append(datastrip.text)

            datastrip_dhus_dissemination_annotation = {
            "explicit_reference" : datastrip.text,
                "annotation_cnf": {
                    "name": "DHUS_DISSEMINATION_TIME",
                    "system": system
                    },
                "values": [{
                    "name": "details",
                    "type": "object",
                    "values": [
                        {"name": "dhus_dissemination_time",
                         "type": "timestamp",
                         "value": creation_date
                         }]
                }]
            }
            list_of_annotations.append(datastrip_dhus_dissemination_annotation)
        #end if
    #end for


    data = {"operations": [{
        "mode": "insert",
        "dim_signature": {
              "name": "DHUS_DISSEMINATION",
              "exec": os.path.basename(__file__),
              "version": version
        },
        "source": source,
        "annotations": list_of_annotations
        }]}

    os.remove(new_file_path)

    return data
