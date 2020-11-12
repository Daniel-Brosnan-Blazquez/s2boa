"""
Ingestion module for the REP_ARC files of Sentinel-2

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

# Import xml parser
from lxml import etree

# Import ingestion_functions
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

def process_file(file_path, engine, query, reception_time, wait_previous_levels = True):
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

    list_of_explicit_references = []
    list_of_explicit_references_for_processing = []
    list_of_annotations = []
    list_of_annotations_for_processing = []
    list_of_ai_annotations = []
    list_of_dam_annotations = []
    list_of_lta_annotations = []
    list_of_dhus_annotations = []
    list_of_events_for_processing = []
    list_of_timelines = []
    list_of_operations = []
    granule_timeline_per_detector = {}
    granule_timeline = []

    # Obtain the station
    system = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Source/System")[0].text
    # Obtain the creation date from the file name as the annotation creation date is not always correct
    creation_date = file_name[25:40]
    # Obtain the validity start
    reported_validity_start = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Validity_Period/Validity_Start")[0].text.split("=")[1]
    # Obtain the validity stop
    reported_validity_stop = xpath_xml("/Earth_Explorer_File/Earth_Explorer_Header/Fixed_Header/Validity_Period/Validity_Stop")[0].text.split("=")[1]
    # Obtain the datastrip
    datastrip_info = xpath_xml("/Earth_Explorer_File/Data_Block/List_of_ItemMetadata/ItemMetadata[Catalogues/S2CatalogueReport/S2EarthObservation/Inventory_Metadata/File_Type[contains(text(),'_DS')]]")[0]
    # Obtain the datastrip ID
    datastrip_id = datastrip_info.xpath("Catalogues/S2CatalogueReport/S2EarthObservation/Inventory_Metadata/File_ID")[0].text
    # Obtain the generation time of the datastrip
    datastrip_generation_time = datastrip_info.xpath("Catalogues/S2CatalogueReport/S2EarthObservation/Inventory_Metadata/Generation_Time")[0].text.split("=")[1]
    datastrip_generation_time_minus_1 = (parser.parse(datastrip_info.xpath("Catalogues/S2CatalogueReport/S2EarthObservation/Inventory_Metadata/Generation_Time")[0].text.split("=")[1]) - datetime.timedelta(seconds=1)).isoformat()
    # Obtain the satellite
    satellite = datastrip_id[0:3]
    # Obtain the datatake ID
    datatake_id = datastrip_info.xpath("CentralIndex/Datatake-id")[0].text
    # Obtain the baseline
    baseline = datastrip_id[58:]
    # Obtain the production level from the datastrip
    level = datastrip_id[13:16].replace("_","")
    # Obtain the sensing identifier
    sensing_identifier = datastrip_id[41:57]
    # Source for the main operation
    source_indexing = {
        "name": file_name,
        "reception_time": reception_time,
        "generation_time": creation_date,
        "validity_start": reported_validity_start,
        "validity_stop": reported_validity_stop,
        "reported_validity_start": reported_validity_start,
        "reported_validity_stop": reported_validity_stop
    }
    source_processing = {
        "name": file_name,
        "reception_time": reception_time,
        "generation_time": datastrip_generation_time_minus_1,
        "validity_start": reported_validity_start,
        "validity_stop": reported_validity_stop,
        "reported_validity_start": reported_validity_start,
        "reported_validity_stop": reported_validity_stop
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
    
    # Insert the datatake_annotation
    datatake_annotation = {
    "explicit_reference": datastrip_id,
    "annotation_cnf": {
        "name": "DATATAKE",
        "system": satellite
        },
        "values": [
            {"name": "datatake_identifier",
             "type": "text",
             "value": datatake_id
            },
            {"name": "satellite",
             "type": "text",
             "value": satellite
            }]
    }
    list_of_annotations.append(datatake_annotation)

    functions.insert_ingestion_progress(session_progress, general_source_progress, 20)

    ### Corrections made on 2019/11/27 to avoid inserting information regarding granules
    # Loop over all the ItemMetadata
    for item in xpath_xml("/Earth_Explorer_File/Data_Block/List_of_ItemMetadata/ItemMetadata[not(contains(Catalogues/S2CatalogueReport/S2EarthObservation/Inventory_Metadata/File_ID, '_GR_'))]"):
        ### End Corrections made on 2019/11/27 to avoid inserting information regarding granules

        item_id = item.xpath("Catalogues/S2CatalogueReport/S2EarthObservation/Inventory_Metadata/File_ID")[0].text
        data_size = item.xpath("Catalogues/S2CatalogueReport/S2EarthObservation/Inventory_Metadata/Data_Size")[0].text
        cloud_percentage = item.xpath("Catalogues/S2CatalogueReport/S2EarthObservation/Inventory_Metadata/CloudPercentage")[0].text
        physical_url = item.xpath("CentralIndex/PDIPhysicalUrl")[0].text
        # Obtain the footprint values
        footprint = item.xpath("Catalogues/S2CatalogueReport/S2EarthObservation/Product_Metadata/Footprint/EXT_POS_LIST")[0].text

        # Insert the footprint_annotation
        list_of_lat_long_coordinates = footprint.split(" ")
        if "" in list_of_lat_long_coordinates:
            list_of_lat_long_coordinates.remove("")
        # end if

        if "_DS_" in item_id:
            corrected_list_of_coordinates = list(reversed(functions.correct_list_of_coordinates_for_ds(list_of_lat_long_coordinates)))
        else:
            corrected_list_of_coordinates = list(reversed(functions.correct_list_of_coordinates_for_gr_tl(list_of_lat_long_coordinates)))
        # end if

        corrected_footprint = functions.list_of_coordinates_to_str_geometry(corrected_list_of_coordinates)
        corrected_footprint_split = corrected_footprint.split(" ")
        corrected_footprint_with_commas = ""
        for i, coordinate in enumerate(corrected_footprint_split):
            corrected_footprint_with_commas += coordinate
            if i % 2 == 0:
                corrected_footprint_with_commas += ","
            elif i < len(corrected_footprint_split) - 1:
                corrected_footprint_with_commas += " "
            # end if
        # end for

        corrected_antimeridian_footprints = functions.correct_footprint(corrected_footprint_with_commas)

        footprint_values = []
        for i, footprint in enumerate(corrected_antimeridian_footprints):
            footprint_object_name = "footprint_details"
            if len(corrected_antimeridian_footprints) > 1:
                footprint_object_name = "footprint_details_" + str(i)
            # end if

            footprint_value = [{"name": "footprint",
                                 "type": "geometry",
                                 "value": footprint}]
            footprint_values.append({
                "name": footprint_object_name,
                "type": "object",
                "values": footprint_value
            })
        # end for
        
        if corrected_footprint != "":
            footprint_annotation = {
            "explicit_reference": item_id,
            "annotation_cnf": {
                "name": "FOOTPRINT",
                "system": satellite
                },
                "values": footprint_values
            }
            list_of_annotations.append(footprint_annotation)
            # end if

        # Insert the data_size_annotation per datastrip
        data_size_annotation = {
        "explicit_reference": item_id,
        "annotation_cnf": {
            "name": "SIZE",
            "system": satellite
        },
        "values": [
            {"name": "size",
             "type": "double",
             "value": data_size
            }]
        }
        list_of_annotations.append(data_size_annotation)

        # Associate aggregated size to the datastrip
        if "_DS_" in item_id:
            sizes = xpath_xml("/Earth_Explorer_File/Data_Block/List_of_ItemMetadata/ItemMetadata/Catalogues/S2CatalogueReport/S2EarthObservation/Inventory_Metadata/Data_Size")
            aggregated_size = sum([int(size.text) for size in sizes])
            data_size_annotation["values"].append(
                {"name": "aggregated_size",
                 "type": "double",
                 "value": aggregated_size
                })
        # end if

        # Insert the cloud percentage_annotation per datastrip
        cloud_percentage_annotation = {
        "explicit_reference": item_id,
        "annotation_cnf": {
            "name": "CLOUD_PERCENTAGE",
            "system": satellite
            },
        "values": [
            {"name": "cloud_percentage",
             "type": "double",
             "value": cloud_percentage
            }]
        }
        list_of_annotations.append(cloud_percentage_annotation)
        # end if

        # Insert the physical url_annotation per datastrip
        physical_url_annotation = {
        "explicit_reference": item_id,
        "annotation_cnf": {
            "name": "PHYSICAL_URL",
            "system": satellite
            },
        "values": [
            {"name": "physical_url",
             "type": "text",
             "value": physical_url
            }]
        }
        list_of_annotations.append(physical_url_annotation)
        
        # Insert the indexing time_annotation per datastrip
        indexing_time_annotation = {
        "explicit_reference": item_id,
        "annotation_cnf": {
            "name": "INDEXING_TIME",
            "system": system
        },
            "values": [
                {"name": "indexing_time",
                 "type": "timestamp",
                 "value": creation_date
                }]
        }
        list_of_annotations.append(indexing_time_annotation)

        if "_DS_" in item_id:
            indexing_time_annotation["annotation_cnf"]["insertion_type"] = "INSERT_and_ERASE"
        # end if
    # end for

    functions.insert_ingestion_progress(session_progress, general_source_progress, 40)
    
    processing_validity_db = query.get_events(explicit_refs = {"op": "==", "filter": datastrip_id},
                                              gauge_names = {"op": "==", "filter": "PROCESSING_VALIDITY"})

    # Execute processing completeness if not done before
    if len(processing_validity_db) < 1:
        baseline_annotation = {
        "explicit_reference": datastrip_id,
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
        list_of_annotations_for_processing.append(baseline_annotation)

        datastrip_sensing_explicit_ref= {
            "group": level + "_DS",
            "links": [{
                "back_ref": "SENSING_IDENTIFIER",
                "link": sensing_identifier,
                "name": "DATASTRIP"
                }
            ],
            "name": datastrip_id
        }
        list_of_explicit_references_for_processing.append(datastrip_sensing_explicit_ref)

        sensing_identifier_annotation = {
        "explicit_reference": datastrip_id,
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
        list_of_annotations_for_processing.append(sensing_identifier_annotation)

        archiving_annotation = {
        "explicit_reference": datastrip_id,
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
            "explicit_reference": datastrip_id,
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
        "explicit_reference": datastrip_id,
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
        "explicit_reference": datastrip_id,
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
        
        for item in xpath_xml("/Earth_Explorer_File/Data_Block/List_of_ItemMetadata/ItemMetadata"):
            item_id = item.xpath("Catalogues/S2CatalogueReport/S2EarthObservation/Inventory_Metadata/File_ID")[0].text
            if '_GR' in item.xpath("CentralIndex/FileType")[0].text:

                # Obtain the granule id
                granule_t = item_id
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
                # # Insert the granule explicit reference
                # granule_explicit_reference = {
                #     "group": level + "_GR",
                #     "links": [{
                #         "back_ref": "DATASTRIP",
                #         "link": datastrip_id,
                #         "name": "GRANULE"
                #         }
                #     ],
                #     "name": item_id
                # }
                # list_of_explicit_references_for_processing.append(granule_explicit_reference)

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
            # end if

            if '_TL' in item.xpath("CentralIndex/FileType")[0].text:
                # Insert the tile explicit reference
                tile_explicit_reference = {
                    "group": level + "_TL",
                    "links": [{
                        "back_ref": "DATASTRIP",
                        "link": datastrip_id,
                        "name": "TILE"
                        }
                    ],
                    "name": item_id
                }
                list_of_explicit_references_for_processing.append(tile_explicit_reference)

                archiving_annotation = {
                "explicit_reference": item_id,
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
                    "explicit_reference": item_id,
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
                "explicit_reference": item_id,
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
                "explicit_reference": item_id,
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
                "explicit_reference": item_id,
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

            # end if
        # end for

        if level == "L0" or level == "L1A" or level == "L1B":
            functions.L0_L1A_L1B_processing(source_processing, engine, query, granule_timeline,list_of_events_for_processing,datastrip_id,granule_timeline_per_detector, list_of_operations, system, version, os.path.basename(__file__), satellite, 30)
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
            while wait_previous_levels and len(upper_level_ers) == 0 and i < 10*60:
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

                functions.L1C_L2A_processing(source_processing, engine, query, list_of_events_for_processing, processing_validity_events, datastrip_id, list_of_operations, system, version, os.path.basename(__file__), satellite, 30)
            # end if
        # end if

    # end if

    functions.insert_ingestion_progress(session_progress, general_source_progress, 80)
    
    data = {"operations": [{
        "mode": "insert",
        "dim_signature": {
              "name": "INDEXING_" + satellite,
              "exec": os.path.basename(__file__),
              "version": version
        },
        "source": source_indexing,
        "annotations": list_of_annotations,
        "explicit_references": list_of_explicit_references
        }]
    }
    
    functions.insert_ingestion_progress(session_progress, general_source_progress, 90)
    
    # Adjust sources / operations
    if len(list_of_events_for_processing) > 0:
        event_starts = [event["start"] for event in list_of_events_for_processing]
        event_starts.sort()
        if source_processing["validity_start"] > event_starts[0]:
            source_processing["validity_start"] = event_starts[0]
        # end if
        event_stops = [event["stop"] for event in list_of_events_for_processing]
        event_stops.sort()
        if source_processing["validity_stop"] < event_stops[-1]:
            source_processing["validity_stop"] = event_stops[-1]
        # end if

        # Generate the footprint of the events
        list_of_events_for_processing_with_footprint = functions.associate_footprints(list_of_events_for_processing, satellite)
        
        data["operations"].append({
            "mode": "insert",
            "dim_signature": {
                "name": "PROCESSING_" + satellite,
                "exec": os.path.basename(__file__),
                "version": version
            },
            "source": source_processing,
            "annotations": list_of_annotations_for_processing,
            "explicit_references": list_of_explicit_references_for_processing,
            "events": list_of_events_for_processing_with_footprint
        })
    # end if

    functions.insert_ingestion_progress(session_progress, general_source_progress, 91)
    
    data["operations"] = data["operations"] + list_of_operations    
            
    if len(list_of_ai_annotations) > 0:
        data["operations"].append({
            "mode": "insert",
            "dim_signature": {
                  "name": "ARCHIVING",
                  "exec": os.path.basename(__file__),
                  "version": version
            },
            "source": source_processing,
            "annotations": list_of_ai_annotations,
        })

    # end if

    functions.insert_ingestion_progress(session_progress, general_source_progress, 92)
    
    if len(list_of_dam_annotations) > 0:
        data["operations"].append({
            "mode": "insert",
            "dim_signature": {
                  "name": "CATALOGING",
                  "exec": os.path.basename(__file__),
                  "version": version
            },
            "source": source_processing,
            "annotations": list_of_dam_annotations,
        })

    # end if

    functions.insert_ingestion_progress(session_progress, general_source_progress, 93)

    if len(list_of_lta_annotations) > 0:
        data["operations"].append({
            "mode": "insert",
            "dim_signature": {
                  "name": "LONG_TERM_ARCHIVING",
                  "exec": os.path.basename(__file__),
                  "version": version
            },
            "source": source_processing,
            "annotations": list_of_lta_annotations,
        })

    # end if

    functions.insert_ingestion_progress(session_progress, general_source_progress, 95)

    if len(list_of_dhus_annotations) > 0:
        data["operations"].append({
            "mode": "insert",
            "dim_signature": {
                  "name": "DHUS_DISSEMINATION",
                  "exec": os.path.basename(__file__),
                  "version": version
            },
            "source": source_processing,
            "annotations": list_of_dhus_annotations,
        })

    # end if

    functions.insert_ingestion_progress(session_progress, general_source_progress, 100)

    query.close_session()

    new_file.close()
    
    return data
