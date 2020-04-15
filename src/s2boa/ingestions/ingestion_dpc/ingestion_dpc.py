"""
Ingestion module for the DPC files of Sentinel-2

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
import time
import massedit

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
    # Remove wrong namespace
    massedit.edit_files([file_path], ["re.sub(r'^.*<Earth_Explorer_File.*>', '<Earth_Explorer_File>', line)"], dry_run=False)
                        
    # Remove namespaces
    new_file = tempfile.NamedTemporaryFile()
    new_file_path = new_file.name

    ingestion_functions.remove_namespaces(file_path, new_file_path)

    # Parse file
    parsed_xml = etree.parse(new_file_path)
    xpath_xml = etree.XPathEvaluator(parsed_xml)

    list_of_explicit_references = []
    list_of_annotations = []
    list_of_indexing_annotations = []
    list_of_ai_annotations = []
    list_of_dam_annotations = []
    list_of_lta_annotations = []
    list_of_dc_annotations = []
    list_of_dhus_annotations = []
    list_of_events = []
    list_of_timelines = []
    list_of_configuration_events = []
    list_of_configuration_explicit_references = []
    list_of_operations = []
    processed_datastrips = {}

    # Obtain the satellite
    satellite = file_name[0:3]
    # Obtain the station
    system = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Source/System")[0].text
    # Obtain the creation date
    creation_date = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Source/Creation_Date")[0].text.split("=")[1]
    # Obtain the validity start
    validity_start = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Validity_Period/Validity_Start")[0].text.split("=")[1]
    # Obtain the validity stop
    validity_stop = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Validity_Period/Validity_Stop")[0].text.split("=")[1]
    # Obtain the workplan current status
    workplan_current_status = xpath_xml("/Earth_Explorer_File/Data_Block/SUP_WORKPLAN_REPORT/SPECIFIC_HEADER/SUPERVISION_INFO/WORKPLAN_CURRENT_STATUS")[0].text
    # Obtain the workplan message
    workplan_message = xpath_xml("/Earth_Explorer_File/Data_Block/SUP_WORKPLAN_REPORT/SPECIFIC_HEADER/SUPERVISION_INFO/WORKPLAN_MESSAGE")[0].text
    # Obtain the workplan start datetime
    workplan_start_datetime = xpath_xml("/Earth_Explorer_File/Data_Block/SUP_WORKPLAN_REPORT/SPECIFIC_HEADER/SUPERVISION_INFO/WORKPLAN_START_DATETIME")[0].text
    # Obtain the workplan end datetime
    workplan_end_datetime = xpath_xml("/Earth_Explorer_File/Data_Block/SUP_WORKPLAN_REPORT/SPECIFIC_HEADER/SUPERVISION_INFO/WORKPLAN_END_DATETIME")[0].text
    # Obtain a list of the mrfs
    mrf_list = xpath_xml("/Earth_Explorer_File/Data_Block/SUP_WORKPLAN_REPORT/SPECIFIC_HEADER/SYNTHESIS_INFO/Product_Report/List_Of_MRFs/MRF")
    # Obtain a list of the steps
    steps_list = xpath_xml("/Earth_Explorer_File/Data_Block/SUP_WORKPLAN_REPORT/DATA/STEP_INFO")
    # Source for the main operation
    source = {
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
    
    # Loop through each output node that contains a datastrip (excluding the auxiliary data)
    for output_msi in xpath_xml("/Earth_Explorer_File/Data_Block/SUP_WORKPLAN_REPORT/SPECIFIC_HEADER/SYNTHESIS_INFO/Product_Report/*[contains(name(),'Output_Products') and boolean(child::DATA_STRIP_ID)]") :

        granule_timeline_per_detector = {}
        granule_timeline = []
        # Obtain the datastrip
        ds_output = output_msi.find("DATA_STRIP_ID").text
        # Obtain the sensing identifier from the datastrip
        sensing_identifier = ds_output[41:57]
        # Obtain the baseline from the datastrip
        baseline = ds_output[58:]
        # Obtain the production level from the datastrip
        level = ds_output[13:16].replace("_","")

        # Obtain the input datastrip if exists
        input = xpath_xml("/Earth_Explorer_File/Data_Block/SUP_WORKPLAN_REPORT/SPECIFIC_HEADER/SYNTHESIS_INFO/Product_Report/Input_Products/DATA_STRIP_ID")
        ds_input = input[0].text

        # Loop over each granule in the ouput
        for granule in output_msi.xpath("*[name() = 'GRANULES_ID' and contains(text(),'_GR_')]"):
            # Obtain the granule id
            granule_t = granule.text
            level_gr = granule_t[13:16].replace("_","")
            granule_sensing_date = granule_t[42:57]
            detector = granule_t[59:61]

            # Create a segment for each granule with a margin calculated to get whole scenes
            start= parser.parse(granule_sensing_date)
            stop = start + datetime.timedelta(seconds=5)
            granule_segment = {
                "start": start,
                "stop": stop,
                "id": granule_t
            }

            # Create a dictionary containing all the granules for each detector
            granule_timeline.append(granule_segment)
            if detector not in granule_timeline_per_detector:
                granule_timeline_per_detector[detector] = []
            # end if
            granule_timeline_per_detector[detector].append(granule_segment)

            ### Commented on 2019/11/27 to avoid inserting granule information due to its heavy weight
            # explicit_reference = {
            #     "group": level_gr + "_GR",
            #     "links": [{
            #         "back_ref": "DATASTRIP",
            #         "link": ds_output,
            #         "name": "GRANULE"
            #         }
            #     ],
            #     "name": granule_t
            # }
            # list_of_explicit_references.append(explicit_reference)

            # archiving_annotation = {
            # "explicit_reference": granule_t,
            # "annotation_cnf": {
            #     "name": "ARCHIVING_TIME",
            #     "system": "EPA_",
            #     "insertion_type": "INSERT_and_ERASE"
            #     },
            # "values": [
            #     {"name": "status",
            #      "type": "text",
            #      "value": "MISSING"
            #     }]
            # }
            # list_of_ai_annotations.append(archiving_annotation)

            # if system != "EPA_":
            #     archiving_annotation = {
            #     "explicit_reference": granule_t,
            #     "annotation_cnf": {
            #         "name": "ARCHIVING_TIME",
            #         "system": system,
            #         "insertion_type": "INSERT_and_ERASE"
            #         },
            #     "values": [
            #         {"name": "status",
            #          "type": "text",
            #          "value": "MISSING"
            #         }]
            #     }
            #     list_of_ai_annotations.append(archiving_annotation)
            # # end if

            # cataloging_annotation = {
            # "explicit_reference": granule_t,
            # "annotation_cnf": {
            #     "name": "CATALOGING_TIME",
            #     "insertion_type": "INSERT_and_ERASE"
            #     },
            # "values": [
            #     {"name": "status",
            #      "type": "text",
            #      "value": "MISSING"
            #     }]
            # }
            # list_of_dam_annotations.append(cataloging_annotation)
            
            ### End Commented on 2019/11/27
            
        # end for

        # Loop over each tile in the output
        for tile in output_msi.xpath("*[name() = 'GRANULES_ID' and contains(text(),'_TL_')]"):
            # Obtain the tile id
            tile_t = tile.text
            level_tl = tile_t[13:16]
            level_tl.replace("_","")

            explicit_reference = {
                "group": level_tl + "_TL",
                "links": [{
                    "back_ref": "DATASTRIP",
                    "link": ds_output,
                    "name": "TILE"
                    }
                ],
                "name": tile_t
            }
            list_of_explicit_references.append(explicit_reference)

            archiving_annotation = {
            "explicit_reference": tile_t,
            "annotation_cnf": {
                "name": "ARCHIVING_TIME",
                "system": "EPA_",
                "insertion_type": "INSERT_and_ERASE"
                },
            "values": [
                {"name": "status",
                 "type": "text",
                 "value": "MISSING"
                }]
            }
            list_of_ai_annotations.append(archiving_annotation)

            if system != "EPA_":
                archiving_annotation = {
                "explicit_reference": tile_t,
                "annotation_cnf": {
                    "name": "ARCHIVING_TIME",
                    "system": system,
                    "insertion_type": "INSERT_and_ERASE"
                    },
                "values": [
                    {"name": "status",
                     "type": "text",
                     "value": "MISSING"
                    }]
                }
                list_of_ai_annotations.append(archiving_annotation)
            # end if

            lta_archiving_annotation = {
            "explicit_reference": tile_t,
            "annotation_cnf": {
                "name": "LONG_TERM_ARCHIVING_TIME",
                "system": "EPA_",
                "insertion_type": "INSERT_and_ERASE"
                },
            "values": [
                {"name": "status",
                 "type": "text",
                 "value": "MISSING"
                }]
            }
            list_of_lta_annotations.append(lta_archiving_annotation)

            cataloging_annotation = {
            "explicit_reference": tile_t,
            "annotation_cnf": {
                "name": "CATALOGING_TIME",
                "insertion_type": "INSERT_and_ERASE"
                },
            "values": [
                {"name": "status",
                 "type": "text",
                 "value": "MISSING"
                }]
            }
            list_of_dam_annotations.append(cataloging_annotation)

            dhus_dissemination_status_annotation = {
            "explicit_reference": tile_t,
            "annotation_cnf": {
                "name": "DHUS_DISSEMINATION_TIME",
                "insertion_type": "INSERT_and_ERASE"
                },
            "values": [
                {"name": "status",
                 "type": "text",
                 "value": "MISSING"
                }]
            }
            list_of_dhus_annotations.append(dhus_dissemination_status_annotation)
        # end for

        # Loop over each TCI in the ouput
        for true_color in output_msi.xpath("*[name() = 'GRANULES_ID' and contains(text(),'_TC_')]"):
            # Obtain the true color imaging id
            true_color_t = true_color.text
            level_tc = true_color_t[13:16]
            level_tc.replace("_","")

            explicit_reference = {
                "group": level_tc + "_TC",
                "links": [{
                    "back_ref": "DATASTRIP",
                    "link": ds_output,
                    "name": "TCI"
                    }
                ],
                "name": true_color_t
            }
            list_of_explicit_references.append(explicit_reference)

            archiving_annotation = {
            "explicit_reference": true_color_t,
            "annotation_cnf": {
                "name": "ARCHIVING_TIME",
                "system": "EPA_",
                "insertion_type": "INSERT_and_ERASE"
                },
            "values": [
                {"name": "status",
                 "type": "text",
                 "value": "MISSING"
                }]
            }
            list_of_ai_annotations.append(archiving_annotation)

            if system != "EPA_":
                archiving_annotation = {
                "explicit_reference": true_color_t,
                "annotation_cnf": {
                    "name": "ARCHIVING_TIME",
                    "system": system,
                    "insertion_type": "INSERT_and_ERASE"
                    },
                "values": [
                    {"name": "status",
                     "type": "text",
                     "value": "MISSING"
                    }]
                }
                list_of_ai_annotations.append(archiving_annotation)
            # end if

            lta_archiving_annotation = {
            "explicit_reference": true_color_t,
            "annotation_cnf": {
                "name": "LONG_TERM_ARCHIVING_TIME",
                "system": "EPA_",
                "insertion_type": "INSERT_and_ERASE"
                },
            "values": [
                {"name": "status",
                 "type": "text",
                 "value": "MISSING"
                }]
            }
            list_of_lta_annotations.append(lta_archiving_annotation)
        # end_for

        if ds_output not in processed_datastrips:

            baseline_annotation = {
            "explicit_reference": ds_output,
            "annotation_cnf": {
                "name": "PRODUCTION_BASELINE",
                "system": satellite
                },
            "values": [
                {"name": "baseline",
                 "type": "text",
                 "value": baseline
                },
                {"name": "satellite",
                 "type": "text",
                 "value": satellite
                }]
            }
            list_of_annotations.append(baseline_annotation)

            sensing_identifier_annotation = {
            "explicit_reference": ds_output,
            "annotation_cnf": {
                "name": "SENSING_IDENTIFIER",
                "system": satellite
                },
            "values": [
                {"name": "sensing_identifier",
                 "type": "text",
                 "value": sensing_identifier
                },
                {"name": "satellite",
                 "type": "text",
                 "value": satellite
                }]
            }
            list_of_annotations.append(sensing_identifier_annotation)

            indexing_time_annotation = {
            "explicit_reference": ds_output,
            "annotation_cnf": {
                "name": "INDEXING_TIME",
                "system": "EPA_"
            },
                "values": [
                    {"name": "status",
                     "type": "text",
                     "value": "MISSING"
                    }]
            }
            list_of_indexing_annotations.append(indexing_time_annotation)

            if system != "EPA_":
                indexing_time_annotation = {
                "explicit_reference": ds_output,
                "annotation_cnf": {
                    "name": "INDEXING_TIME",
                    "system": system
                },
                    "values": [
                        {"name": "status",
                         "type": "text",
                         "value": "MISSING"
                        }]
                }
                list_of_indexing_annotations.append(indexing_time_annotation)
            # end if
            
            archiving_annotation = {
            "explicit_reference": ds_output,
            "annotation_cnf": {
                "name": "ARCHIVING_TIME",
                "system": "EPA_",
                "insertion_type": "INSERT_and_ERASE"
                },
            "values": [
                {"name": "status",
                 "type": "text",
                 "value": "MISSING"
                }]
            }
            list_of_ai_annotations.append(archiving_annotation)

            if system != "EPA_":
                archiving_annotation = {
                "explicit_reference": ds_output,
                "annotation_cnf": {
                    "name": "ARCHIVING_TIME",
                    "system": system,
                    "insertion_type": "INSERT_and_ERASE"
                    },
                "values": [
                    {"name": "status",
                     "type": "text",
                     "value": "MISSING"
                    }]
                }
                list_of_ai_annotations.append(archiving_annotation)
            # end if

            cataloging_annotation = {
            "explicit_reference": ds_output,
            "annotation_cnf": {
                "name": "CATALOGING_TIME",
                "insertion_type": "INSERT_and_ERASE"
                },
            "values": [
                {"name": "status",
                 "type": "text",
                 "value": "MISSING"
                }]
            }
            list_of_dam_annotations.append(cataloging_annotation)

            lta_archiving_annotation = {
            "explicit_reference": ds_output,
            "annotation_cnf": {
                "name": "LONG_TERM_ARCHIVING_TIME",
                "system": "EPA_",
                "insertion_type": "INSERT_and_ERASE"
                },
            "values": [
                {"name": "status",
                 "type": "text",
                 "value": "MISSING"
                }]
            }
            list_of_lta_annotations.append(lta_archiving_annotation)
            
            explicit_reference = {
                "group": level + "_DS",
                "links": [{
                    "back_ref": "INPUT_DATASTRIP",
                    "link": ds_input,
                    "name": "OUTPUT_DATASTRIP"
                },{
                    "back_ref": "SENSING_IDENTIFIER",
                    "link": sensing_identifier,
                    "name": "DATASTRIP"
                }],
                "name": ds_output
            }
            list_of_explicit_references.append(explicit_reference)

            if level == "L0" or level == "L1A" or level == "L1B":
                functions.L0_L1A_L1B_processing(source, engine, query, granule_timeline,list_of_events,ds_output,granule_timeline_per_detector, list_of_operations, system, version, os.path.basename(__file__), satellite)
            elif (level == "L1C" or level == "L2A"):
                def get_upper_level_ers():
                    upper_level_ers = query.get_explicit_refs(annotation_cnf_names = {"filter": "SENSING_IDENTIFIER", "op": "=="},
                                                              annotation_cnf_systems = {"filter": satellite, "op": "=="},
                                                              groups = {"filter": ["L0_DS", "L1B_DS"], "op": "in"},
                                                              annotation_value_filters = [{"name": {"filter": "sensing_identifier", "op": "=="}, "type": "text", "value": {"op": "==", "filter": sensing_identifier}}])

                    upper_level_ers_same_satellite = [er.explicit_ref for er in upper_level_ers if er.explicit_ref[0:3] == satellite]
                    
                    return [er.explicit_ref for er in upper_level_ers]
                # end def
                i = 0
                upper_level_ers = get_upper_level_ers()
                # Wait till the upper level production has been processed 10 minutes
                while len(upper_level_ers) == 0 and i < 10*60:
                    time.sleep(10)
                    i += 10
                    upper_level_ers = get_upper_level_ers()
                # end while
                upper_level_er = [er for er in upper_level_ers if er[13:16] == "L1B"]
                if len(upper_level_er) == 0:
                    upper_level_er = [er for er in upper_level_ers if er[13:16] == "L0_"]
                # end if
                if len(upper_level_er) > 0:
                    er = upper_level_er[0]

                    processing_validity_events = query.get_events(gauge_names = {"filter": ["PROCESSING_VALIDITY"], "op": "in"},
                                                                          explicit_refs = {"filter": er, "op": "=="})

                    functions.L1C_L2A_processing(source, engine, query, list_of_events, processing_validity_events, ds_output, list_of_operations, system, version, os.path.basename(__file__), satellite)
                # end if
            # end if

            event_timeliness = {
                "explicit_reference": ds_output,
                "gauge": {
                    "insertion_type": "SIMPLE_UPDATE",
                    "name": "TIMELINESS",
                    "system": system
                },
                "start": steps_list[0].find("PROCESSING_START_DATETIME").text[:-1],
                "stop": steps_list[-1].find("PROCESSING_END_DATETIME").text[:-1],
                "values": [
                    {"name": "satellite",
                     "type": "text",
                     "value": satellite
                    }]
            }
            list_of_events.append(event_timeliness)

            # Steps
            for step in steps_list:
                if step.find("EXEC_STATUS").text == 'COMPLETED':
                    values = [
                        {
                            "name": "id",
                            "type": "text",
                            "value": step.get("id")
                        },
                        {
                            "name": "satellite",
                            "type": "text",
                            "value": satellite
                        }]
                    event_step = {
                        "explicit_reference": ds_output,
                        "gauge": {
                            "insertion_type": "SIMPLE_UPDATE",
                            "name": "STEP_INFO",
                            "system": system
                        },
                        "start": step.find("PROCESSING_START_DATETIME").text[:-1],
                        "stop": step.find("PROCESSING_END_DATETIME").text[:-1],
                        "values": values
                    }
                    exec_mode_node = step.find("SUBSYSTEM_INFO/STEP_REPORT/GENERAL_INFO/EXEC_MODE")
                    if exec_mode_node is not None:
                        values.append({
                            "name": "exec_mode",
                            "type": "text",
                            "value": exec_mode_node.text
                        })
                    list_of_events.append(event_step)
                # end if
            # end for

            for mrf in mrf_list:
                explicit_reference = {
                    "group": "MISSION_CONFIGURATION",
                    "links": [{
                        "back_ref": "DATASTRIP",
                        "link": ds_output,
                        "name": "CONFIGURATION"
                        }
                    ],
                    "name": mrf.find("Id").text
                }
                list_of_explicit_references.append(explicit_reference)
            # end for
        # end if

        processed_datastrips[ds_output] = None
    # end for

    functions.insert_ingestion_progress(session_progress, general_source_progress, 50)
    
    for mrf in mrf_list:
        # Only if the mrf does not exist in the DB
        mrfsDB = query.get_events(explicit_refs = {"op": "==", "filter": mrf.find("Id").text})
        if len(mrfsDB) is 0:
            # If the date is correct, else the date is set to a maximum value
            try:
                stop = str(parser.parse(mrf.find("ValidityStop").text[:-1]))
            # end if
            except:
                stop = str(datetime.datetime.max)
            # end except
            event_mrf={
                "key":mrf.find("Id").text,
                "explicit_reference": mrf.find("Id").text,
                "gauge": {
                    "insertion_type": "EVENT_KEYS",
                    "name": "MRF_VALIDITY",
                    "system": system
                },
                "start": mrf.find("ValidityStart").text[:-1],
                "stop": stop,
                "values": [{
                    "name": "generation_time",
                    "type": "timestamp",
                    "value": mrf.find("Id").text[25:40]
                }]
                }
            list_of_configuration_events.append(event_mrf)
        # end if
    # end for

    # Loop through each output node that contains a HKTM (excluding the auxiliary data)
    for hktm in xpath_xml("/Earth_Explorer_File/Data_Block/SUP_WORKPLAN_REPORT/SPECIFIC_HEADER/SYNTHESIS_INFO/Product_Report/*[contains(name(),'Output_Products') and contains(GRANULES_ID, 'PRD_HKTM__')]/GRANULES_ID"):
        hktm_name = hktm.text.replace(".SAFE", "")
        event_production_playback_validity_ddbb = query.get_events(explicit_refs = {"op": "==", "filter": hktm_name}, gauge_names = {"op": "==", "filter": "HKTM_PRODUCTION_PLAYBACK_VALIDITY"})
        explicit_reference = {
            "group": "HKTM",
            "name": hktm_name
        }
        list_of_explicit_references.append(explicit_reference)

        # Build events
        values = [
            {"name": "satellite",
             "type": "text",
             "value": satellite
            }]
        orbit = -1
        links = []

        # Obtain the planned playback to associate the orbit number and link the production
        start_hktm_playback = hktm_name[20:35]
        stop_hktm_playback = hktm_name[36:51]
        start_planned_playback = (parser.parse(start_hktm_playback) - datetime.timedelta(seconds=30)).isoformat()
        stop_planned_playback = (parser.parse(stop_hktm_playback) + datetime.timedelta(seconds=30)).isoformat()
        corrected_planned_playbacks = query.get_events(gauge_names = {"op": "==", "filter": "PLANNED_PLAYBACK_CORRECTION"},
                                                       gauge_systems = {"op": "==", "filter": satellite},
                                                       value_filters = [{"name": {"op": "==", "filter": "playback_type"}, "type": "text", "value": {"op": "in", "filter": ["HKTM", "HKTM_SAD"]}}],
                                                       start_filters = [{"date": stop_planned_playback, "op": "<"}],
                                                       stop_filters = [{"date": start_planned_playback, "op": ">"}])
            
        if len(corrected_planned_playbacks) > 0:
            orbit = [value.value for playback in corrected_planned_playbacks for value in playback.eventDoubles if value.name == "start_orbit"][0]
            link_planned_playback = [link for link in corrected_planned_playbacks[0].eventLinks if link.name == "PLANNED_EVENT"]
            if len(link_planned_playback) > 0:
                links.append({
                    "link": str(link_planned_playback[0].event_uuid_link),
                    "link_mode": "by_uuid",
                    "name": "HKTM_PRODUCTION",
                    "back_ref": "PLANNED_PLAYBACK"
                })
            # end if
        # end if

        if len(event_production_playback_validity_ddbb) == 0:

            # Obtain the executed playback to link the information
            hktm_playbacks = query.get_events(gauge_names = {"op": "==", "filter": "PLAYBACK_VALIDITY_3"},
                                                           value_filters = [{"name": {"op": "==", "filter": "satellite"}, "type": "text", "value": {"op": "==", "filter": satellite}}],
                                                           start_filters = [{"date": stop_planned_playback, "op": "<"}],
                                                           stop_filters = [{"date": start_planned_playback, "op": ">"}])
            if len(hktm_playbacks) > 0:
                if orbit == -1:
                    orbit = [value.value for playback in hktm_playbacks for value in playback.eventDoubles if value.name == "downlink_orbit"][0]
                # end if
                links.append({
                    "link": str(hktm_playbacks[0].event_uuid),
                    "link_mode": "by_uuid",
                    "name": "HKTM_PRODUCTION",
                    "back_ref": "PLAYBACK_VALIDITY"
                })
            # end if

            # Production playback validity
            event_production_playback_validity = {
                "key": hktm_name,
                "explicit_reference": hktm_name,
                "gauge": {
                    "insertion_type": "EVENT_KEYS",
                    "name": "HKTM_PRODUCTION_PLAYBACK_VALIDITY"
                },
                "links": links,
                "start": parser.parse(start_hktm_playback).isoformat(),
                "stop": parser.parse(stop_hktm_playback).isoformat(),
                "values": values
            }
            list_of_events.append(event_production_playback_validity)

            circulation_annotation = {
                "explicit_reference" : hktm_name,
                "annotation_cnf": {
                    "name": "CIRCULATION_TIME",
                    "system": "PDMC_to_FOS_"
                },
                "values": [
                    {"name": "status",
                     "type": "text",
                     "value": "MISSING"
                    }]
            }
            list_of_dc_annotations.append(circulation_annotation)
            
            archiving_annotation = {
            "explicit_reference": hktm_name,
            "annotation_cnf": {
                "name": "ARCHIVING_TIME",
                "system": "EPA_",
                "insertion_type": "INSERT_and_ERASE"
                },
            "values": [
                {"name": "status",
                 "type": "text",
                 "value": "MISSING"
                }]
            }
            list_of_ai_annotations.append(archiving_annotation)

            if system != "EPA_":
                archiving_annotation = {
                "explicit_reference": hktm_name,
                "annotation_cnf": {
                    "name": "ARCHIVING_TIME",
                    "system": system,
                    "insertion_type": "INSERT_and_ERASE"
                    },
                "values": [
                    {"name": "status",
                     "type": "text",
                     "value": "MISSING"
                    }]
                }
                list_of_ai_annotations.append(archiving_annotation)
            # end if

            lta_archiving_annotation = {
            "explicit_reference": hktm_name,
            "annotation_cnf": {
                "name": "LONG_TERM_ARCHIVING_TIME",
                "system": "EPA_",
                "insertion_type": "INSERT_and_ERASE"
                },
            "values": [
                {"name": "status",
                 "type": "text",
                 "value": "MISSING"
                }]
            }
            list_of_lta_annotations.append(lta_archiving_annotation)
            
        # end if

        # Timeliness
        event_timeliness = {
            "key": hktm_name,
            "explicit_reference": hktm_name,
            "gauge": {
                "insertion_type": "EVENT_KEYS",
                "name": "TIMELINESS"
            },
            "start": steps_list[0].find("PROCESSING_START_DATETIME").text[:-1],
            "stop": steps_list[-1].find("PROCESSING_END_DATETIME").text[:-1],
            "values": values
        }
        list_of_events.append(event_timeliness)

        # Add orbit value
        if orbit != -1:
            values.append({"name": "downlink_orbit",
                           "type": "double",
                           "value": str(orbit)
            })
        # end if
    # end for
    
    functions.insert_ingestion_progress(session_progress, general_source_progress, 70)

    main_operation = {
        "mode": "insert",
        "dim_signature": {
            "name": "PROCESSING_" + satellite,
            "exec": os.path.basename(__file__),
            "version": version
        },
        "source": source
    }
    list_of_operations.append(main_operation)
    
    # Adjust the validity period to the events in the operation
    if len(list_of_events) > 0:
        event_starts = [event["start"] for event in list_of_events]
        event_starts.sort()
        if source["validity_start"] > event_starts[0]:
            source["validity_start"] = event_starts[0]
        # end if
        event_stops = [event["stop"] for event in list_of_events]
        event_stops.sort()
        if source["validity_stop"] < event_stops[-1]:
            source["validity_stop"] = event_stops[-1]
        # end if

        # Generate the footprint of the events
        list_of_events_with_footprint = functions.associate_footprints(list_of_events, satellite)
        
        main_operation["annotations"] = list_of_annotations
        main_operation["explicit_references"] = list_of_explicit_references
        main_operation["events"] = list_of_events_with_footprint

    # end if

    functions.insert_ingestion_progress(session_progress, general_source_progress, 80)

    # Adjust the validity period to the events in the operation
    if len(list_of_configuration_events) > 0:
        source = {
            "name": file_name,
            "reception_time": reception_time,
            "generation_time": creation_date
        }

        event_starts = [event["start"] for event in list_of_configuration_events]
        event_starts.sort()
        source["validity_start"] = event_starts[0]
        event_stops = [event["stop"] for event in list_of_configuration_events]
        event_stops.sort()
        source["validity_stop"] = event_stops[-1]
        list_of_operations.append({
            "mode": "insert",
            "dim_signature": {
                  "name": "PROCESSING_"  + satellite,
                  "exec": "configuration_" + os.path.basename(__file__),
                  "version": version
            },
            "source": source,
            "events": list_of_configuration_events,
        })

    # end if

    functions.insert_ingestion_progress(session_progress, general_source_progress, 90)

    if len(list_of_indexing_annotations) > 0:
        list_of_operations.append({
            "mode": "insert",
            "dim_signature": {
                  "name": "INDEXING_" + satellite,
                  "exec": "indexing_" + os.path.basename(__file__),
                  "version": version
            },
            "source": source,
            "annotations": list_of_indexing_annotations,
        })

    # end if

    functions.insert_ingestion_progress(session_progress, general_source_progress, 91)

    if len(list_of_ai_annotations) > 0:
        list_of_operations.append({
            "mode": "insert",
            "dim_signature": {
                  "name": "ARCHIVING",
                  "exec": "archiving_" + os.path.basename(__file__),
                  "version": version
            },
            "source": source,
            "annotations": list_of_ai_annotations,
        })

    # end if

    functions.insert_ingestion_progress(session_progress, general_source_progress, 92)
    
    if len(list_of_dam_annotations) > 0:
        list_of_operations.append({
            "mode": "insert",
            "dim_signature": {
                  "name": "CATALOGING",
                  "exec": "cataloging_" + os.path.basename(__file__),
                  "version": version
            },
            "source": source,
            "annotations": list_of_dam_annotations,
        })

    # end if

    functions.insert_ingestion_progress(session_progress, general_source_progress, 93)

    if len(list_of_lta_annotations) > 0:
        list_of_operations.append({
            "mode": "insert",
            "dim_signature": {
                  "name": "LONG_TERM_ARCHIVING",
                  "exec": "lta_" + os.path.basename(__file__),
                  "version": version
            },
            "source": source,
            "annotations": list_of_lta_annotations,
        })

    # end if

    functions.insert_ingestion_progress(session_progress, general_source_progress, 95)

    if len(list_of_dhus_annotations) > 0:
        list_of_operations.append({
            "mode": "insert",
            "dim_signature": {
                  "name": "DHUS_DISSEMINATION",
                  "exec": "dhus_dissemination_" + os.path.basename(__file__),
                  "version": version
            },
            "source": source,
            "annotations": list_of_dhus_annotations,
        })

    # end if

    functions.insert_ingestion_progress(session_progress, general_source_progress, 97)

    if len(list_of_dc_annotations) > 0:
        list_of_operations.append({
            "mode": "insert",
            "dim_signature": {
                  "name": "CIRCULATION",
                  "exec": "circulation_" + os.path.basename(__file__),
                  "version": version
            },
            "source": source,
            "annotations": list_of_dc_annotations,
        })

    # end if

    functions.insert_ingestion_progress(session_progress, general_source_progress, 98)

    data = {"operations": list_of_operations}

    functions.insert_ingestion_progress(session_progress, general_source_progress, 100)

    query.close_session()

    new_file.close()
    
    return data
