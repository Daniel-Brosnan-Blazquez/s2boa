"""
Ingestion module for the REP_OPAI files of Sentinel-2

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

def process_file(file_path, engine, query):
    """
    Function to process the file and insert its relevant information
    into the DDBB of the eboa

    :param file_path: path to the file to be processed
    :type file_path: str
    :param engine: object to access the engine of the EBOA
    :type engine: Engine
    :param query: object to access the query interface of the EBOA
    :type query: Query
    """
    file_name = os.path.basename(file_path)

    # Remove namespaces
    (_, new_file_path) = new_file = mkstemp()
    ingestion_functions.remove_namespaces(file_path, new_file_path)

    # Parse file
    parsed_xml = etree.parse(new_file_path)
    xpath_xml = etree.XPathEvaluator(parsed_xml)

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
        "generation_time": creation_date,
        "validity_start": validity_start,
        "validity_stop": validity_stop
    }

    for request in xpath_xml("/Earth_Explorer_File/Data_Block/List_Of_ArchiveRequests/ArchiveRequest[RequestStatus[text() = 'Success']]"):
        #Obtain the product ID
        product_id = request.xpath("Pdi-Id")[0].text
        # Obtain the archiving_time
        archiving_time = request.xpath("RequestDate")[0].text[:-1]

        archiving_annotation = {
            "explicit_reference" : product_id,
            "annotation_cnf": {
                "name": "ARCHIVING_TIME",
                "system": system
                },
            "values": [{
                "name": "details",
                "type": "object",
                "values": [
                    {"name": "archiving_time",
                     "type": "timestamp",
                     "value": archiving_time
                     }]
            }]
        }
        list_of_annotations.append(archiving_annotation)
    #end for

    data = {"operations": [{
        "mode": "insert",
        "dim_signature": {
              "name": "ARCHIVING",
              "exec": os.path.basename(__file__),
              "version": version
        },
        "source": source,
        "annotations": list_of_annotations
        }]}

    os.remove(new_file_path)

    return data
