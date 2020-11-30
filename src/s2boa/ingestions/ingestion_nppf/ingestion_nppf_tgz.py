"""
Ingestion module for the NPPF files in TGZ format of Sentinel-2

Written by DEIMOS Space S.L. (dibb)

module eboa
"""
# Import python utilities
import tarfile
import tempfile
import os

# Import NPPF ingestion
from s2boa.ingestions.ingestion_nppf import ingestion_nppf

# Import ingestion_functions.helpers
import eboa.ingestion.functions as ingestion_functions

# Import logging
from eboa.logging import Log

logging_module = Log(name = __name__)
logger = logging_module.logger

def process_file(file_path, engine, query, reception_time):
    """Function to process the file and insert its relevant information
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
    
    # Create temporary folder for extracting the files inside the tar into it
    temporary_folder = tempfile.TemporaryDirectory()

    tar = tarfile.open(file_path)
    tar.extractall(path=temporary_folder.name)

    # Merge HDR and DBL files into a EOF
    # Remove xml nodes and namespaces
    # HDR
    hdr = open(temporary_folder.name + "/FILE.HDR", "w+")
    ingestion_functions.remove_namespaces(temporary_folder.name + "/" + file_name.replace("TGZ", "HDR"), hdr.name, xml_declaration = False)
    hdr_content = hdr.read()

    # DBL
    dbl = open(temporary_folder.name + "/FILE.DBL", "w+")
    ingestion_functions.remove_namespaces(temporary_folder.name + "/" + file_name.replace("TGZ", "DBL"), dbl.name, xml_declaration = False)
    dbl_content = dbl.read()
    
    # Write EOF
    eof = open(temporary_folder.name + "/" + file_name.replace("TGZ", "EOF"), "w+")
    eof.write('<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n')
    eof.write('<Earth_Explorer_File>\n')
    eof.write(hdr_content)
    eof.write(dbl_content)
    eof.write('</Earth_Explorer_File>')

    eof_path = eof.name
    eof.close()

    data = ingestion_nppf.process_file(eof_path, engine, query, reception_time, tgz_filename = file_name)
    
    # Remove temporary folder
    temporary_folder.cleanup()
    
    return data
