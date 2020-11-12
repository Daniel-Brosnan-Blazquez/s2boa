"""
Ingestion module for the REP_ARC files of Sentinel-2 with the flag
to false to wait for the upper levels to be ingested (this is for
testing purposes)

Written by DEIMOS Space S.L. (femd)

module eboa

"""

import s2boa.ingestions.ingestion_rep_arc.ingestion_rep_arc as ingestion_rep_arc

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

    data = ingestion_rep_arc.process_file(file_path, engine, query, reception_time, wait_previous_levels = False)
    
    return data
