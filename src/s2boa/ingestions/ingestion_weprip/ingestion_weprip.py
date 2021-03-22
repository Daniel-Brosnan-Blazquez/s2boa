"""
Ingestion module for the REP_WEPRIP files of Sentinel-2

Written by DEIMOS Space S.L. (dibb)

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
    i = 25
    reported_generation_date = file_name[i:i+4] + "-" + file_name[i+4:i+6] + "-" + file_name[i+6:i+8] + file_name[i+8:i+11] + ":" + file_name[i+11:i+13] + ":" + file_name[i+13:i+15]

    functions.insert_ingestion_progress(session_progress, general_source_progress, 30)
    
    # Obtain validity period
    i = 42
    reported_validity_start = file_name[i:i+4] + "-" + file_name[i+4:i+6] + "-" + file_name[i+6:i+8] + file_name[i+8:i+11] + ":" + file_name[i+11:i+13] + ":" + file_name[i+13:i+15]

    functions.insert_ingestion_progress(session_progress, general_source_progress, 60)

    i = 58
    reported_validity_stop = file_name[i:i+4] + "-" + file_name[i+4:i+6] + "-" + file_name[i+6:i+8] + file_name[i+8:i+11] + ":" + file_name[i+11:i+13] + ":" + file_name[i+13:i+15]

    functions.insert_ingestion_progress(session_progress, general_source_progress, 90)

    data = {"operations": [{
                "mode": "insert",
                "dim_signature": {
                    "name": "WEPRIP_ARCHIVING",
                    "exec": os.path.basename(__file__),
                    "version": version
                },
                "source": {
                    "name": file_name,
                    "reception_time": reception_time,
                    "generation_time": reported_generation_date,
                    "validity_start": reported_validity_start,
                    "validity_stop": reported_validity_stop,
                }
    }]}
 
    functions.insert_ingestion_progress(session_progress, general_source_progress, 100)

    query_general_source.close_session()
    
    return data
