"""
Ingestion module for the DPC files of Sentinel-2

Written by DEIMOS Space S.L. (femd)

module eboa
"""

import s2boa.ingestions.ingestion_dpc.ingestion_dpc as ingestion_dpc

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

    data = ingestion_dpc.process_file(file_path, engine, query, reception_time, wait_previous_levels = False)
    
    return data
