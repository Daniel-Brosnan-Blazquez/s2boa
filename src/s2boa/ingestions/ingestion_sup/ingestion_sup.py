"""
Ingestion module for the REP__SUP files of Sentinel-2

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
import pdb

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

    # Obtain the satellite ID
    satellite = file_name[0:3]
    # Obtain the creation date
    reported_generation_date = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Source/Creation_Date")[0].text.split("=")[1]
    # Obtain validity period
    reported_validity_start = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Validity_Period/Validity_Start")[0].text.split("=")[1]
    reported_validity_stop = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Validity_Period/Validity_Stop")[0].text.split("=")[1]
    if reported_validity_stop == "9999-99-99T99:99:99":
        reported_validity_stop = datetime.datetime.max.isoformat()
    # end if 
    
    # Obtain the unavailability reference
    unavailability_reference = xpath_xml("/Earth_Explorer_File/Data_Block/Unavailability_Reference")[0].text

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

    # Extract the useful information for the different impacted subsystems in order to create and insert the events
    list_of_events = []
      
    for subsystem_unavailability in xpath_xml("/Earth_Explorer_File/Data_Block/List_Of_Subsystem_Unavailabilities/Subsystem_Unavailability"):
        # Obtain the subsystem 
        subsystem = subsystem_unavailability.xpath("Subsystem")[0].text
        # Obtain the Start Time and the Start Orbit
        start_time = subsystem_unavailability.xpath("StartTime")[0].text.split("=")[1]
        start_orbit = subsystem_unavailability.xpath("StartOrbit")[0].text
        # Obtain the End Time and the End Orbit
        if reported_validity_stop == datetime.datetime.max.isoformat():
            end_time = datetime.datetime.max.isoformat()
            end_orbit = ""
        else:
            end_time = subsystem_unavailability.xpath("EndTime")[0].text.split("=")[1]
            end_orbit = subsystem_unavailability.xpath("EndOrbit")[0].text
        # end if
        # Obtain the key
        key = satellite + "-" + subsystem + "-" + unavailability_reference 

        # Obtain the unabailability comment
        comment = subsystem_unavailability.xpath("Comment")[0].text

        # Values for the event
        subsystem_unavailability_values = [
                {"name": "satellite",
                "type": "text",
                "value": satellite
                },
                {"name": "subsystem",
                "type": "text",
                "value": subsystem
                },
                {"name": "comment",
                "type": "text",
                "value": comment
                },
                {"name": "start_orbit",
                "type": "double",
                "value": start_orbit
                }]

        if end_orbit != "":
            subsystem_unavailability_values.append({"name": "stop_orbit",
                                                    "type": "double",
                                                    "value": end_orbit})
        # end if
                    
        # Obtain the unavailability links
        # If subsystem is MSI / MMFU-A / MMFU-B link to PLANNED_CUT_IMAGING through the PLANNED_CUT_IMAGING_CORRECTION events
        if ("MSI" in subsystem) or ("MMFU" in subsystem):
            system_unavailability_links = []

            # Obtain the planned cut imaging events impacted by the system unavailability
            linking_planned_cut_imaging_to_planned_cut_imaging_correction = query.get_linking_events(gauge_names = {"filter": "PLANNED_CUT_IMAGING_CORRECTION", "op": "=="},
                                                                            gauge_systems = {"filter": satellite, "op": "=="},
                                                                            start_filters = [{"date": end_time, "op": "<"}], 
                                                                            stop_filters = [{"date": start_time, "op": ">"}], 
                                                                            link_names = {"filter": "PLANNED_EVENT", "op": "=="},
                                                                            return_prime_events = False)
        
            if len(linking_planned_cut_imaging_to_planned_cut_imaging_correction["linking_events"]) > 0:
                planned_cut_imaging = linking_planned_cut_imaging_to_planned_cut_imaging_correction["linking_events"]
                for link in planned_cut_imaging:
                    system_unavailability_links.append({
                        "link": str(link.event_uuid),
                        "link_mode": "by_uuid",
                        "name": "SYSTEM_UNAVAILABILITY",
                        "back_ref": "PLANNED_CUT_IMAGING"
                    })
                # end for
            # end if
        # end if
    
        # If subsystem is X-BAND link to PLANNED_PLAYBACK with playback_mean X_BAND
        if "X-BAND" in subsystem:
            xband_planned_playbacks = []
            system_unavailability_links = []

            xband_planned_playbacks = query.get_events(gauge_names = {"op": "==", "filter": "PLANNED_PLAYBACK"},
                                            gauge_systems = {"op": "==", "filter": satellite},
                                            start_filters = [{"date": end_time, "op": "<"}], 
                                            stop_filters = [{"date": start_time, "op": ">"}])

            if len(xband_planned_playbacks) > 0:
                planned_X_BAND_playbacks = [planned_playback for planned_playback in xband_planned_playbacks for event_text in planned_playback.eventTexts if event_text.name == "playback_mean" and event_text.value == "XBAND"]
                for link in planned_X_BAND_playbacks:
                    system_unavailability_links.append({
                        "link": str(link.event_uuid),
                        "link_mode": "by_uuid",
                        "name": "SYSTEM_UNAVAILABILITY",
                        "back_ref": "PLANNED_PLAYBACK"
                    })
                # end for
            # end if 
        # end if

        # If subsystem is OCP link to PLANNED_PLAYBACK with playback_mean OCP
        if "OCP" in subsystem:
            system_unavailability_links = []
            ocp_planned_playbacks = []

            ocp_planned_playbacks = query.get_events(gauge_names = {"op": "==", "filter": "PLANNED_PLAYBACK"},
                                            gauge_systems = {"op": "==", "filter": satellite},
                                            start_filters = [{"date": end_time, "op": "<"}], 
                                            stop_filters = [{"date": start_time, "op": ">"}])

            if len(ocp_planned_playbacks) > 0:
                planned_OCP_playbacks = [planned_playback for planned_playback in ocp_planned_playbacks for event_text in planned_playback.eventTexts if event_text.name == "playback_mean" and event_text.value == "OCP"]
                for link in planned_OCP_playbacks:
                    system_unavailability_links.append({
                        "link": str(link.event_uuid),
                        "link_mode": "by_uuid",
                        "name": "SYSTEM_UNAVAILABILITY",
                        "back_ref": "PLANNED_PLAYBACK"
                    })
                # end for
            # end if  
        # end if

        # Generate event
        subsystem_unavailability_event = {
                "key": key,
                "gauge": {
                    "insertion_type": "EVENT_KEYS",
                    "name": "SYSTEM_UNAVAILABILITY",
                    "system": satellite
                },
                "links": system_unavailability_links,
                "start": start_time,
                "stop": end_time,
                "values": subsystem_unavailability_values
                }
        list_of_events.append(subsystem_unavailability_event)

    # end for

    functions.insert_ingestion_progress(session_progress, general_source_progress, 70)

    data = {"operations": [{
                "mode": "insert",
                "dim_signature": {
                    "name": "SYSTEM_UNAVAILABILITY",
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
                },
                "events": list_of_events,
                }]}
 
    functions.insert_ingestion_progress(session_progress, general_source_progress, 100)
    
    query.close_session()

    new_file.close()
    
    return data
