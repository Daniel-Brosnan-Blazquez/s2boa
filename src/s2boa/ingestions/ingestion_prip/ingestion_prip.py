"""
Ingestion module for the REP_OPPRIP files of Sentinel-2

Written by DEIMOS Space S.L. (miaf)

module s2boa
"""
# Import python utilities
import os
import argparse
from dateutil import parser
import datetime
import json
import sys
import tempfile
import re

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

# Function for removing extension
def remove_extension(pdi_id_to_format):
    items = pdi_id_to_format.split(".")
    if len(items) > 1 and re.match("[^a-zA-Z]*[a-zA-Z]+", items[-1]):
            items.pop(len(items)-1)
    # end if
    if len(items) > 1:
            product_id = '.'.join(map(str, items))
    else:
            product_id = items[0]
    # end if
    return product_id

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
    list_of_explicit_references = []

    # Obtain the creation date
    reported_generation_date = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Source/Creation_Date")[0].text.split("=")[1]
    # Obtain validity period
    reported_validity_start = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Validity_Period/Validity_Start")[0].text.split("=")[1]
    reported_validity_stop = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Validity_Period/Validity_Stop")[0].text.split("=")[1]
    
    
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
      
    for archived_product in xpath_xml("/Earth_Explorer_File/Data_Block/List_Of_ArchivedProducts/ArchivedProduct"):
        # Obtain the Pdi_Id without extension
        pdi_id = archived_product.xpath("Pdi-Id")[0].text
        pdi_id_without_extension = remove_extension(pdi_id)
        # Obtain the Inventory Date
        inventory_date = archived_product.xpath("InventoryDate")[0].text.replace("Z", "")
        # Obtain the parent id
        parent_id = archived_product.xpath("ParentId")[0].text

        # MSI product level
        level = None
        if "_MSI_" in pdi_id_without_extension:
            level = pdi_id_without_extension[13:16].replace("_", "")
        # end if

        # Values for the anotations
        prip_values = [
                {"name": "prip_archiving_time",
                 "type": "timestamp",
                 "value": inventory_date
                }]
        
        # Generate annotation
        archiving_to_prip_annotation = {
            "explicit_reference": pdi_id_without_extension,
            "annotation_cnf": {
                "name": "PRIP_ARCHIVING_TIME",
                "insertion_type": "INSERT_and_ERASE_with_PRIORITY"
                },
            "values": prip_values
            }
        list_of_annotations.append(archiving_to_prip_annotation)

        # Link tiles to datastrips
        if "_TL_" in pdi_id_without_extension:

            explicit_reference = {
                "group": level + "_TL",
                "links": [{
                    "back_ref": "DATASTRIP",
                    "link": parent_id,
                    "name": "TILE"
                    }
                ],
                "name": pdi_id_without_extension
            }
            list_of_explicit_references.append(explicit_reference)

        # Link true colour to datastrips
        elif "_TC_" in pdi_id_without_extension:

            explicit_reference = {
                "group": level + "_TC",
                "links": [{
                    "back_ref": "DATASTRIP",
                    "link": parent_id,
                    "name": "TCI"
                    }
                ],
                "name": pdi_id_without_extension
            }
            list_of_explicit_references.append(explicit_reference)       

        # # Link granules to datastrips
        # elif "_GR_" in pdi_id_without_extension:

        #     explicit_reference = {
        #         "group": level + "_GR",
        #         "links": [{
        #             "back_ref": "DATASTRIP",
        #             "link": parent_id,
        #             "name": "GRANULE"
        #             }
        #         ],
        #         "name": pdi_id_without_extension
        #     }
        #     list_of_explicit_references.append(explicit_reference)
        
        # Associate group to datastrips
        elif "_DS_" in pdi_id_without_extension:

            explicit_reference =  {
                "group": level + "_DS",
                "name": pdi_id_without_extension
            }
            list_of_explicit_references.append(explicit_reference)  

        # Associate group to HKTM
        elif "_HKTM_" in pdi_id_without_extension:

            explicit_reference =  {
                "group": "HKTM",
                "name": pdi_id_without_extension
            }
            list_of_explicit_references.append(explicit_reference)           

        # Associate group to GIP
        elif "_GIP_" in pdi_id_without_extension:

            explicit_reference = {
                "group": "GIP",
                "name": pdi_id_without_extension
            }
            list_of_explicit_references.append(explicit_reference)

        # Associate group to AUXILIARY data
        else: 
            explicit_reference = {
                "group": "AUXILIARY_DATA",
                "name": pdi_id_without_extension
            }
            list_of_explicit_references.append(explicit_reference)
        # end if
    # end for

    functions.insert_ingestion_progress(session_progress, general_source_progress, 90)

    data = {"operations": [{
                "mode": "insert",
                "dim_signature": {
                    "name": "PRIP_ARCHIVING",
                    "exec": os.path.basename(__file__),
                    "version": version
                },
                "source": {
                    "name": file_name,
                    "reception_time": reception_time,
                    "generation_time": reported_generation_date,
                    "validity_start": reported_validity_start,
                    "validity_stop": reported_validity_stop,
                    "reported_validity_start": reported_validity_start,
                    "reported_validity_stop": reported_validity_stop,
                    "priority": 20
                },
                "annotations": list_of_annotations,
                "explicit_references": list_of_explicit_references
                }]}
 
    functions.insert_ingestion_progress(session_progress, general_source_progress, 100)
    
    query.close_session()

    new_file.close()
    
    return data
