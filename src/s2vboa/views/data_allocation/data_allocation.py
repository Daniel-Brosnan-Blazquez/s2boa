"""
Processing view for s2boa

Written by DEIMOS Space S.L. (jubv)

module s2vboa
"""
# Import python utilities
import sys
import json
import datetime
import re
from dateutil import parser
import pdb
import math

# Import flask utilities
from flask import Blueprint, flash, g, current_app, redirect, render_template, request, url_for
from flask_debugtoolbar import DebugToolbarExtension
from flask import jsonify

# Import eboa utilities
from eboa.engine.query import Query
import eboa.engine.engine as eboa_engine
from eboa.engine.engine import Engine

# Import views functions
from s2vboa.views import functions as s2vboa_functions

bp = Blueprint("data-allocation", __name__, url_prefix="/views")
query = Query()

@bp.route("/data-allocation", methods=["GET", "POST"])
def show_data_allocation():
    """
    Data Allocation view for the Sentinel-2 mission.
    """
    current_app.logger.debug("Data allocation view")

    filters = {}
    filters["limit"] = ["100"]    
    if request.method == "POST":
        filters = request.form.to_dict(flat=False).copy()
    # end if
    filters["offset"] = [""]

    # Initialize reporting period (now - 1 days, now)
    start_filter = {
        "date": (datetime.datetime.now()).isoformat(),
        "op": "<="
    }
    stop_filter = {
        "date": (datetime.datetime.now() - datetime.timedelta(days=1)).isoformat(),
        "op": ">="
    }
    mission = "S2_"

    window_size = 1
    start_filter_calculated, stop_filter_calculated = s2vboa_functions.get_start_stop_filters(query, current_app, request, window_size, mission, filters)

    if start_filter_calculated != None:
        start_filter = start_filter_calculated
    # end if

    if stop_filter_calculated != None:
        stop_filter = stop_filter_calculated
    # end if

    if request.method == "POST":

        if request.form["mission"] != "":
            mission = request.form["mission"]
        # end if

    # end if

    filters["start"] = [stop_filter["date"]]
    filters["stop"] = [start_filter["date"]]
    filters["mission"] = [mission]

    return query_data_allocation_and_render(start_filter, stop_filter, mission, filters = filters)

@bp.route("/data-allocation-pages", methods=["POST"])
def query_data_allocation_pages():
    """
    Data allocation view for the Sentinel-2 mission using pages.
    """
    current_app.logger.debug("Data allocation view using pages")
    filters = request.json

    mission = filters["mission"][0]
    mission = filters["mission"][0]

    # window_size is not used, here only for using the same API
    window_size = None
    start_filter, stop_filter = s2vboa_functions.get_start_stop_filters(query, current_app, request, window_size, mission, filters)

    return query_data_allocation_and_render(start_filter, stop_filter, mission, filters = filters)

@bp.route("/sliding-data-allocation-parameters", methods=["GET", "POST"])
def show_sliding_data_allocation_parameters():
    """
    Data allocation sliding view for the Sentinel-2 mission.
    """
    current_app.logger.debug("Sliding data allocation view with parameters")

    window_delay = float(request.args.get("window_delay"))
    window_size = float(request.args.get("window_size"))
    repeat_cycle = float(request.args.get("repeat_cycle"))
    mission = request.args.get("mission")
    
    start_filter = {
        "date": (datetime.datetime.now() - datetime.timedelta(days=window_delay)).isoformat(),
        "op": "<="
    }
    stop_filter = {
        "date": (datetime.datetime.now() - datetime.timedelta(days=(window_delay+window_size))).isoformat(),
        "op": ">="
    }

    sliding_window = {
        "window_delay": window_delay,
        "window_size": window_size,
        "repeat_cycle": repeat_cycle,
        "mission": mission
    }

    return query_data_allocation_and_render(start_filter, stop_filter, mission, sliding_window)

@bp.route("/sliding-data-allocation", methods=["GET", "POST"])
def show_sliding_data_allocation():
    """
    Data allocation sliding view for the Sentinel-2 mission.
    """
    current_app.logger.debug("Sliding data allocation view")

    window_delay=0
    window_size=1
    repeat_cycle=1

    mission = "S2_"

    if request.method == "POST":

        if request.form["mission"] != "":
            mission = request.form["mission"]
        # end if

        if request.form["processing_window_delay"] != "":
            window_delay = float(request.form["processing_window_delay"])
        # end if

        if request.form["processing_window_size"] != "":
            window_size = float(request.form["processing_window_size"])
        # end if

        if request.form["processing_repeat_cycle"] != "":
            repeat_cycle = float(request.form["processing_repeat_cycle"])
        # end if

    # end if

    start_filter = {
        "date": (datetime.datetime.now() - datetime.timedelta(days=window_delay)).isoformat(),
        "op": "<="
    }
    stop_filter = {
        "date": (datetime.datetime.now() - datetime.timedelta(days=(window_delay+window_size))).isoformat(),
        "op": ">="
    }

    sliding_window = {
        "window_delay": window_delay,
        "window_size": window_size,
        "repeat_cycle": repeat_cycle,
        "mission": mission
    }

    return query_data_allocation_and_render(start_filter, stop_filter, mission, sliding_window)

def query_data_allocation_and_render(start_filter = None, stop_filter = None, mission = None, sliding_window = None, filters = None):

    data_allocation_structure = build_data_allocation_structure(start_filter, stop_filter, mission, filters)

    orbpre_events = s2vboa_functions.query_orbpre_events(query, current_app, start_filter, stop_filter, mission)

    reporting_start = stop_filter["date"]
    reporting_stop = start_filter["date"]
    
    template = "views/data_allocation/data_allocation.html"

    return render_template(template, data_allocation_structure=data_allocation_structure, orbpre_events=orbpre_events, reporting_start=reporting_start, reporting_stop=reporting_stop, sliding_window=sliding_window, filters = filters)

def build_data_allocation_structure(start_filter, stop_filter, mission, filters = None):
    """
    Build data allocation structure.
    """

    kwargs = {}
    events = {}
    output = []
    #output["playbacks"]=[]
    #output["datastrips"]=[]

    #Flags for initializing algorithm


    #antes de nada
    scene_duration = 3.608
    number_of_packets_per_scene = 12960 
    downlink_rate = 520
    imaging_rate = 490
    downlink_scene_duration = scene_duration * (imaging_rate / downlink_rate)
    extra_scenes = 2
    rewind_scenes = 3


    # Set offset and limit for the query
    if filters and "offset" in filters and filters["offset"][0] != "":
        kwargs["offset"] = filters["offset"][0]
    # end if
    if filters and "limit" in filters and filters["limit"][0] != "":
        kwargs["limit"] = filters["limit"][0]
    # end if

    # Set order by reception_time descending
    kwargs["order_by"] = {"field": "start", "descending": True}

    # Start filter
    kwargs["start_filters"] = [{"date": start_filter["date"], "op": start_filter["op"]}]

    # Stop filter
    kwargs["stop_filters"] = [{"date": stop_filter["date"], "op": stop_filter["op"]}]

    # Playback type
    kwargs["value_filters"] = [{"name": {"op": "==", "filter": "playback_type"},
                                "type": "text",
                                "value": {"op": "in", "filter": ["NOMINAL", "REGULAR", "RT"]}
                                }]
    
    kwargs["gauge_names"] = {"filter": ["PLANNED_PLAYBACK_CORRECTION"], "op": "in"}

    # Query corrected planned playbacks and planned playbacks
    planned_playback_correction_events = query.get_events(**kwargs)
    #planned_playback_correction_events = query.get_events(gauge_names = {"filter": ["PLANNED_PLAYBACK_CORRECTION"], "op":"in"}, 
                                       # value_filters = [{"name": {"op": "==", "filter": "playback_type"}, 
                                       #             "type": "text",
                                       #             "value": {"op": "in", "filter": ["NOMINAL", "REGULAR", "RT"]}}
                                       #             ])

    planned_playback_correction_events_filtered_by_satellite = query.get_linked_events(event_uuids = {"filter": [event.event_uuid for event in planned_playback_correction_events], "op": "in"},
                                                                                       link_names = {"filter": "TIME_CORRECTION", "op": "=="})
                                                                                       #value_filters = [{"name": {"op": "==", "filter": "satellite"},
                                                                                       #                  "type": "text",
                                                                                       #                  "value": {"op": "like", "filter": mission}}
                                                                                       #                 ])

    # Query playback validity, last scenes replayed and memory occupation events
    planned_playback_events = query.get_linking_events_group_by_link_name(event_uuids = {"filter": [event.event_uuid for event in planned_playback_correction_events_filtered_by_satellite["linked_events"]], "op": "in"}, 
                                                                          link_names = {"filter": ["PLAYBACK_VALIDITY", "LAST_REPLAYED_SCENE_AT_START", "LAST_REPLAYED_SCENE_AT_STOP",
                                                                                                   "NOMINAL_MEMORY_OCCUPATION_AT_START", "NOMINAL_MEMORY_OCCUPATION_AT_STOP",
                                                                                                   "NRT_MEMORY_OCCUPATION_AT_START", "NRT_MEMORY_OCCUPATION_AT_STOP"], "op": "in"}, 
                                                                          return_prime_events = False)
    
    events["corrected_planned_playback"] = planned_playback_correction_events_filtered_by_satellite["prime_events"]
    events["planned_playback"] = planned_playback_correction_events_filtered_by_satellite["linked_events"]
    events["playback_validity"] = [event for event in planned_playback_events["linking_events"]["PLAYBACK_VALIDITY"] for value in event.eventDoubles if (value.name == "channel" and value.value == 2)]
    events["last_replayed_scene"] = planned_playback_events["linking_events"]["LAST_REPLAYED_SCENE_AT_START"] + planned_playback_events["linking_events"]["LAST_REPLAYED_SCENE_AT_STOP"]
    events["nominal_memory_occupation"] = planned_playback_events["linking_events"]["NOMINAL_MEMORY_OCCUPATION_AT_START"] + planned_playback_events["linking_events"]["NOMINAL_MEMORY_OCCUPATION_AT_STOP"]
    events["nrt_memory_occupation"] = planned_playback_events["linking_events"]["NRT_MEMORY_OCCUPATION_AT_START"] + planned_playback_events["linking_events"]["NRT_MEMORY_OCCUPATION_AT_STOP"]

    planned_playbacks_nominal = [event for event in events["planned_playback"] for value in event.eventTexts if value.name == "playback_type" and value.value == "NOMINAL"]
    planned_playbacks_nrt = [event for event in events["planned_playback"] for value in event.eventTexts if value.name == "playback_type" and value.value == "NRT"]

    # Query isp validity linked to the playback validity events
    isp_validity_event_uuids = [link.event_uuid_link for event in events["playback_validity"] for link in event.eventLinks if link.name == "ISP_VALIDITY"]
    events["isp_validity"] = query.get_events(event_uuids = {"filter": isp_validity_event_uuids, "op": "in"})

    # Query raw isp validity linked to the playback validity events
    raw_isp_validity_event_uuids = [link.event_uuid_link for event in events["isp_validity"] for link in event.eventLinks if link.name == "RAW_ISP_VALIDITY"]
    events["raw_isp_validity"] = query.get_events(event_uuids = {"filter": raw_isp_validity_event_uuids, "op": "in"})


    # Obtain first isp validity with status complete
    # Note: if this is not available, the algorithm cannot start
    structure = {}
    structure["events"] = events
    structure["data_allocation"] = {}
    events["planned_cut_imaging"] = {}

    isp_validity_with_status_complete = [event for event in events["isp_validity"] for value in event.eventTexts if value.name == "status" and value.value == "COMPLETE"]

    events["planned_cut_imaging_correction"] = []
    events["planned_cut_imaging"] = []

    # Start filter for memory occupation
    start_filters_memory_occupation = [{"date": start_filter["date"], "op": start_filter["op"]}]

    # Stop filter for memory occupation
    stop_filters_memory_occupation = [{"date": stop_filter["date"], "op": stop_filter["op"]}]

    if len(isp_validity_with_status_complete) > 0:
        isp_validity_with_status_complete.sort(key = lambda x: x.start)

        isp_validity_with_nominal_msi = [event for event in isp_validity_with_status_complete for value in event.eventTexts if value.name == "playback_type" and value.value == "NOMINAL"]
        if len(isp_validity_with_nominal_msi) > 0:
            first_isp_validity_with_status_complete_nominal_msi = isp_validity_with_nominal_msi[0]

            raw_isp_validity_linking_to_first_isp_validity_with_nominal_msi = query.get_linking_events(event_uuids = {"filter": str(first_isp_validity_with_status_complete_nominal_msi.event_uuid), "op": "=="},
                                                                                     link_names = {"filter": "RAW_ISP_VALIDITY", "op": "=="}, 
                                                                                     return_prime_events = False)
        # end if 

        isp_validity_with_nrt_msi = [event for event in isp_validity_with_status_complete for value in event.eventTexts if value.name == "playback_type" and value.value == "NRT"]
        if len(isp_validity_with_nrt_msi) > 0:
            first_isp_validity_with_status_complete_nrt_msi = isp_validity_with_nrt_msi[0]

            raw_isp_validity_linking_to_first_isp_validity_with_nrt_msi = query.get_linking_events(event_uuids = {"filter": str(first_isp_validity_with_status_complete_nrt_msi.event_uuid), "op": "=="},
                                                                                     link_names = {"filter": "RAW_ISP_VALIDITY", "op": "=="}, 
                                                                                     return_prime_events = False)
        # end if 

        first_isp_validity_with_status_complete = isp_validity_with_status_complete[0]

        # Query the raw_isp_validity corresponding to the first isp validity event with status complete
        raw_isp_validity_linking_to_first_isp_validity = query.get_linking_events(event_uuids = {"filter": str(first_isp_validity_with_status_complete.event_uuid), "op": "=="},
                                                                                     link_names = {"filter": "RAW_ISP_VALIDITY", "op": "=="}, 
                                                                                     return_prime_events = False)
        # Query planned playback linked to the first isp validity event with status complete
        playback_validity_20_linking_to_first_isp_validity = query.get_linking_events(event_uuids = {"filter": str(first_isp_validity_with_status_complete.event_uuid), "op": "=="},
                                                                                     link_names = {"filter": "PLAYBACK_VALIDITY", "op": "=="}, 
                                                                                     return_prime_events = False)

        planned_playback_linking_to_first_isp_validity = query.get_linking_events(event_uuids = {"filter": str(playback_validity_20_linking_to_first_isp_validity["linking_events"][0].event_uuid), "op": "=="},
                                                                                     link_names = {"filter": "PLANNED_PLAYBACK", "op": "=="}, 
                                                                                     return_prime_events = False)

        planned_playback_correction_linking_to_executed_planned_playback = query.get_linking_events(event_uuids = {"filter": str(planned_playback_linking_to_first_isp_validity["linking_events"][0].event_uuid), "op": "=="},
                                                                                     link_names = {"filter": "TIME_CORRECTION", "op": "=="}, 
                                                                                     return_prime_events = False)
        
        # Query planned cut imaging linked to the first isp validity event with status complete
        planned_cut_imaging_linking_to_first_isp_validity = query.get_linking_events(event_uuids = {"filter": str(first_isp_validity_with_status_complete.event_uuid), "op": "=="},
                                                                                     link_names = {"filter": "PLANNED_IMAGING", "op": "=="}, 
                                                                                     return_prime_events = False)

        
        if len(planned_cut_imaging_linking_to_first_isp_validity["linking_events"]) > 0:
            # Query associated planned cut imaging correction linked to the planned cut imaging event
            associated_planned_cut_imaging_correction = query.get_linking_events(event_uuids = {"filter": str(planned_cut_imaging_linking_to_first_isp_validity["linking_events"][0].event_uuid), "op": "=="},
                                                                                 link_names = {"filter": "TIME_CORRECTION", "op": "=="}, 
                                                                                 return_prime_events = False)

            if len(associated_planned_cut_imaging_correction["linking_events"]) > 0:
                # Query corrected planned cut imaging
                # Note: stop_filter is associated to the stop of the coverage of the window (start_filter value as they are swapped)
                planned_cut_imaging_correction = query.get_linked_events(gauge_names = {"filter": "PLANNED_CUT_IMAGING_CORRECTION", "op": "=="},
                                                                         start_filters = [{"date": start_filter["date"], "op": "<="}],
                                                                         stop_filters = [{"date": associated_planned_cut_imaging_correction["linking_events"][0].start.isoformat(), "op": ">="}],
                                                                         link_names = {"filter": "TIME_CORRECTION", "op": "=="})

                events["planned_cut_imaging_correction"] = planned_cut_imaging_correction["prime_events"]
                events["planned_cut_imaging"] = planned_cut_imaging_correction["linked_events"]
                cut_imaging_correction_events_nominal = [event for event in events["planned_cut_imaging_correction"] for value in event.eventTexts if 
                                                            value.name == "record_type" and value.value == "NOMINAL"]
                cut_imaging_correction_events_nrt = [event for event in events["planned_cut_imaging_correction"] for value in event.eventTexts if 
                                                            value.name == "record_type" and value.value == "NRT"]
            # end if
        # end if

        # Start filter for memory occupation
        start_filters_memory_occupation = [{"date": start_filter["date"], "op": "<="}]
        
        # Stop filter for memory occupation
        stop_filters_memory_occupation = [{"date": isp_validity_with_status_complete[0].start.isoformat(), "op": ">="}]

    # end if

    # Query memory occupation events with number of scenes equal to 0
    # during the corresponding period
    events["nominal_memory_occupation_0"] = query.get_events(gauge_names = {"filter": "NOMINAL_MEMORY_OCCUPATION", "op": "=="},
                                                             value_filters = [{"name": {"op": "==", "filter": "satellite"},
                                                                               "type": "text",
                                                                               "value": {"op": "like", "filter": mission}
                                                                               },
                                                                              {"name": {"op": "==", "filter": "number_of_scenes"},
                                                                               "type": "double",
                                                                               "value": {"op": "==", "filter": "0"}}
                                                                               ],
                                                             start_filters = start_filters_memory_occupation,
                                                             stop_filters = stop_filters_memory_occupation)
    events["nrt_memory_occupation_0"] = query.get_events(gauge_names = {"filter": "NRT_MEMORY_OCCUPATION", "op": "=="},
                                                             value_filters = [{"name": {"op": "==", "filter": "satellite"},
                                                                               "type": "text",
                                                                               "value": {"op": "like", "filter": mission}
                                                                               },
                                                                              {"name": {"op": "==", "filter": "number_of_scenes"},
                                                                               "type": "double",
                                                                               "value": {"op": "==", "filter": "0"}}
                                                                               ],
                                                             start_filters = start_filters_memory_occupation,
                                                             stop_filters = stop_filters_memory_occupation)

    list_of_datastrips = []
    list_of_playbacks=[]
    ######
    # Data allocation algorithm
    ######
    
    # Step 1: making sure that we can initalize: telemetry not available
    if len(isp_validity_with_status_complete) > 0: 
        #Algorithm initialized, case: executed playback found. Will have to do this for each event in planned_playback
        for i in range(len(events["planned_playback"])):
            print("i es igual a:")
            print(i)
            if i == 0:
                pointer_to_following_playback = planned_playback_correction_linking_to_executed_planned_playback["linking_events"][i]
            else:
                pointer_to_following_playback = planned_playback_correction_events[i]
            # end if
            telemetry_available = False
            if telemetry_available:
                #caso de telemetry available
                print("ya vemos")
            #Telemetry not available: step 6
            else:
                            
                #CASE: NOMINAL MSI
                if len(planned_playbacks_nominal) > 0:
                    if i == 0:
                        pointer_to_last_downloaded_msi_nominal = raw_isp_validity_linking_to_first_isp_validity_with_nominal_msi["linking_events"][0]
                    #esto queremos que solo ocurra una vez, no puede estar dentro del bucle
                    # end if
                    cut_imaging_events_nominal = [event for event in cut_imaging_correction_events_nominal if 
                                                event.start.isoformat()  <= pointer_to_following_playback.stop.isoformat() and event.stop.isoformat() >= pointer_to_last_downloaded_msi_nominal.start.isoformat()]           #event.start.isoformat()  <= start_period and 
                    
                    nominal_msi_duration_before_playback_stop = datetime.timedelta(0, 0, 0)
                    for event in cut_imaging_events_nominal:
                        if event.start.isoformat() <= pointer_to_last_downloaded_msi_nominal.start.isoformat():
                            cut_imaging_event_duration = event.stop - pointer_to_last_downloaded_msi_nominal.start
                        else:
                            cut_imaging_event_duration = event.stop - event.start
                        # end if
                        nominal_msi_duration_before_playback_stop = nominal_msi_duration_before_playback_stop + cut_imaging_event_duration
                    # end for
                    number_of_scenes_available_in_nominal_memory = round(nominal_msi_duration_before_playback_stop.total_seconds()/scene_duration)
                    raw_isp = False

                    #if telemetry / if raw_isp / if none
                    if telemetry_available:
                        #Step 7a
                        for value in pointer_to_following_playback.eventDoubles:
                            if value.name == "SCN_RWD":
                                rewind_flag = value.value
                            # end if
                        # end for
                        if rewind_flag == 1:
                            number_of_scenes_really_downloaded = last_replayed_scene_at_stop - last_replayed_scene_at_start + rewind_scenes
                        else:
                            number_of_scenes_really_downloaded = last_replayed_scene_at_stop - last_replayed_scene_at_start
                        # end if
                        number_of_scenes_to_be_downloaded = number_of_scenes_really_downloaded
                    elif raw_isp:
                        #Step 7b
                        for value in raw_isp_validity_linking_to_first_isp_validity_with_nominal_msi["linking_events"][0].eventDoubles:
                            if value.name == "num_packets":
                                number_of_packets_raw_isps = value.value
                            # end if
                        # end for
                        msi_duration = math.floor(number_of_packets_raw_isps / number_of_packets_per_scene) * scene_duration
                        number_of_scenes_really_downloaded = msi_duration / scene_duration
                        number_of_scenes_to_be_downloaded = number_of_scenes_really_downloaded
                    else:
                        #Step 7c
                        planned_playback_correction_duration = pointer_to_following_playback.stop - pointer_to_following_playback.start
                        msi_duration =(round(planned_playback_correction_duration.total_seconds() / downlink_scene_duration) + extra_scenes) * scene_duration
                        number_of_scenes_to_be_downloaded = msi_duration / scene_duration
                    # end if

                    #Step 8
                    # because this is the nominal case:
                    number_of_scenes_available_in_memory = number_of_scenes_available_in_nominal_memory
                    # Characterize the playback and set the number of scenes downloaded:
                    if number_of_scenes_available_in_memory == 0:
                        playback_status = "EMPTY"
                        number_of_scenes_downloaded = 0
                    elif number_of_scenes_available_in_memory >= number_of_scenes_to_be_downloaded:
                        playback_status = "OK"
                        number_of_scenes_downloaded = number_of_scenes_to_be_downloaded
                    else:
                        playback_status = "WASTED"
                        number_of_scenes_downloaded = number_of_scenes_available_in_memory
                    # end if

                    #Step 9
                    #because this is the nominal case:
                    number_of_nominal_scenes_downloaded = number_of_scenes_downloaded
                    number_of_nrt_scenes_downloaded = 0

                    #Extract datastrips by the covered MSI to be downloaded by the period {PointerToLastDownloadedMsiNominal, pointer to the next NOMINAL scene moving the pointer NumberOfScenesDownloaded} 
                    j=0
                    new_pointer_to_last_downloaded_msi_nominal = pointer_to_last_downloaded_msi_nominal
                    datastrip_start = pointer_to_last_downloaded_msi_nominal.start
                    for i in range(int(number_of_scenes_downloaded)):
                        new_pointer_to_last_downloaded_msi_nominal.start = new_pointer_to_last_downloaded_msi_nominal.start + datetime.timedelta(seconds=scene_duration)
                        print("CUT IMAGING STOP: " + cut_imaging_correction_events_nominal[j].stop.isoformat())
                        print("POINTER STOP: "+ new_pointer_to_last_downloaded_msi_nominal.start.isoformat())
                        if cut_imaging_correction_events_nominal[j].stop.isoformat() <= new_pointer_to_last_downloaded_msi_nominal.start.isoformat():
                            datastrip_stop = pointer_to_last_downloaded_msi_nominal.stop

                            print("we have a datastrip")
                            #For each datastrip, associate latency: Latency = playback stop - datastrip start
                            latency = pointer_to_following_playback.stop - pointer_to_last_downloaded_msi_nominal.start
                            
                            for value in pointer_to_last_downloaded_msi_nominal.eventDoubles:
                                if value.name == "downlink_orbit":
                                    datastrip_orbit = value.value 
                                #end if
                            #end for
                            datastrip =[{
                                "start": datastrip_start.isoformat(),
                                "stop": datastrip_stop.isoformat(),
                                "orbit": datastrip_orbit,
                                "duration": (datastrip_stop - datastrip_start).total_seconds(),
                                "number_of_scenes": number_of_scenes_downloaded,
                                "latency": latency.total_seconds(),
                                "acquisition_type": "NOMINAL",
                                "packet_store": "NOMINAL"
                            }]
                            list_of_datastrips.append(datastrip)
                            j = j + 1
                            new_pointer_to_last_downloaded_msi_nominal = cut_imaging_correction_events_nominal[j]
                            datastrip_start = new_pointer_to_last_downloaded_msi_nominal.start
                        # end if
                    # end for
                    latency = pointer_to_following_playback.stop - pointer_to_last_downloaded_msi_nominal.start
                    for value in pointer_to_last_downloaded_msi_nominal.eventDoubles:
                        if value.name == "downlink_orbit":
                            datastrip_orbit = value.value 
                        #end if
                    #end for
                    datastrip_stop = pointer_to_last_downloaded_msi_nominal.stop
                    datastrip =[{
                        "start": datastrip_start.isoformat(),
                        "stop": datastrip_stop.isoformat(),
                        "orbit": datastrip_orbit, #puedo usar el pointer to last downloaded msi con name downlink_orbit
                        "duration": (datastrip_stop - datastrip_start).total_seconds(),
                        "number_of_scenes": number_of_scenes_downloaded,
                        "latency": latency.total_seconds(),
                        "acquisition_type": "NOMINAL",
                        "packet_store": "NOMINAL"
                    }]        
                    list_of_datastrips.append(datastrip)
                    # Set the pointer to the NOMINAL MSI: PointerToLastDownloadedMsiNominal =pointer to the next NOMINAL scene moving the pointer NumberOfScenesDownloaded
                    for value in pointer_to_following_playback.eventDoubles:
                        if value.name == "SCN_RWD":
                            rewind_flag = value.value
                        # end if
                    # end for
                    pdb.set_trace()
                    if rewind_flag == 1.0: #REVISA ESTO NO VAYA A SER
                        pointer_to_last_downloaded_msi_nominal.start = new_pointer_to_last_downloaded_msi_nominal.start - datetime.timedelta(seconds=rewind_scenes*scene_duration)
                    else:
                        pointer_to_last_downloaded_msi_nominal.start = new_pointer_to_last_downloaded_msi_nominal.start 
                                
                    # end if
                # end if









                #CASO NRT:
                if len(planned_playbacks_nrt) > 0:
                    pointer_to_last_downloaded_msi_nrt = raw_isp_validity_linking_to_first_isp_validity_with_nrt_msi["linking_events"][0].start

                    cut_imaging_correction_events_nrt = [event for event in events["planned_cut_imaging_correction"] for value in event.eventTexts if 
                                                            value.name == "record_type" and value.value == "NRT"]
                    #quizá esto podría ir arriba donde se hacen todas las queries

                    cut_imaging_events_nrt = [event for event in cut_imaging_correction_events_nrt if 
                                                event.start.isoformat()  <= pointer_to_following_playback.stop.isoformat() and event.stop.isoformat() >= pointer_to_last_downloaded_msi_nrt.isoformat()]           #event.start.isoformat()  <= start_period and 
                    
                    nrt_msi_duration_before_playback_stop = datetime.timedelta(0, 0, 0)
                    for event in cut_imaging_events_nrt:
                        if event.start.isoformat() <= pointer_to_last_downloaded_msi_nrt.isoformat():
                            cut_imaging_event_duration = event.stop - pointer_to_last_downloaded_msi_nrt
                        else:
                            cut_imaging_event_duration = event.stop - event.start
                        # end if
                        nrt_msi_duration_before_playback_stop = nrt_msi_duration_before_playback_stop + cut_imaging_event_duration
                    # end for
                    number_of_scenes_available_in_nrt_memory = round(nrt_msi_duration_before_playback_stop.total_seconds()/scene_duration)
                    raw_isp = True

                    #if telemetry / if raw_isp 
                    if telemetry_available:
                        #Step 7a
                        msi_duration = scene_duration
                    elif raw_isp:
                        #Step 7b
                        #number of packets? in total? for that planned playback?
                        #msi_duration_really_downloaded = floor(number_of_packets_raw_isps / number_of_packets_per_scene) * scene_duration
                        #Step 7c
                        planned_playback_correction_duration = pointer_to_following_playback.stop - pointer_to_following_playback.start
                        msi_duration =(round(planned_playback_correction_duration.total_seconds() / downlink_scene_duration) + extra_scenes) * scene_duration
                        number_of_scenes_to_be_downloaded = msi_duration / scene_duration
                    # end if

                    #Step 8
                    # because this is the nrt case:
                    number_of_scenes_available_in_memory = number_of_scenes_available_in_nrt_memory
                    # Characterize the playback and set the number of scenes downloaded:
                    if number_of_scenes_available_in_memory == 0:
                        playback_status = "EMPTY"
                        number_of_scenes_downloaded = 0
                    elif number_of_scenes_available_in_memory >= number_of_scenes_to_be_downloaded:
                        playback_status = "OK"
                        number_of_scenes_downloaded = number_of_scenes_to_be_downloaded
                    else:
                        playback_status = "WASTED"
                        number_of_scenes_downloaded = number_of_scenes_available_in_memory
                    # end if

                    #Step 9
                    #because this is the nrt case:
                    number_of_nrt_scenes_downloaded = number_of_scenes_downloaded
                    number_of_nominal_scenes_downloaded = 0

                    #Extract datastrips by the covered MSI to be downloaded by the period {PointerToLastDownloadedMsiNominal, pointer to the next NOMINAL scene moving the pointer NumberOfScenesDownloaded} 
                    j=0
                    new_pointer_to_last_downloaded_msi_nrt = pointer_to_last_downloaded_msi_nrt
                    for i in range(int(number_of_scenes_downloaded)):
                        new_pointer_to_last_downloaded_msi_nrt = new_pointer_to_last_downloaded_msi_nrt + datetime.timedelta(seconds=scene_duration)
                        if cut_imaging_correction_events_nrt[j].stop.isoformat() <= pointer_to_last_downloaded_msi_nrt.isoformat():
                            #hay que tener en cuenta que puede haber salto de datastrip y aquí eso no se está contemplando
                            print("we have a datastrip")
                            #For each datastrip, associate latency: Latency = playback stop - datastrip start
                            latency = pointer_to_following_playback.stop - pointer_to_last_downloaded_msi_nrt
                            j = j +1
                        # end if
                    # end for
                    #Set the pointer to the NOMINAL MSI: PointerToLastDownloadedMsiNominal =pointer to the next NOMINAL scene moving the pointer NumberOfScenesDownloaded
                    for value in pointer_to_following_playback.eventDoubles:
                        if value.name == "SCN_RWD":
                            rewind_flag = value.value
                        # end if
                    # end for
                    pdb.set_trace()
                    if rewind_flag == 1:
                        pointer_to_last_downloaded_msi_nrt = new_pointer_to_last_downloaded_msi_nrt - datetime.timedelta(seconds=rewind_scenes*scene_duration)
                    else:
                        pointer_to_last_downloaded_msi_nrt = new_pointer_to_last_downloaded_msi_nrt 
                                
                    # end if
                # end if
            # end if

            playback = {
                "playback": [{
                    "uuid": pointer_to_following_playback.event_uuid,
                    "status": playback_status, 
                    "number_of_scenes_downloaded":{
                        "nominal": number_of_nominal_scenes_downloaded,
                        "nrt": number_of_nrt_scenes_downloaded
                    },
                    "number_of_scenes_to_be_downloaded":{
                        "nominal": number_of_scenes_to_be_downloaded,
                        "nrt": 0 #mejorar esto
                    },
                    "datastrips": list_of_datastrips
                }]
            }
            list_of_playbacks.append(playback)
            output = list_of_playbacks
        # end for 
    elif telemetry_available:
        print("telemetry")
    else:
        print("Cannot initialize")
    # end if
    pdb.set_trace()
    return output


#Output = {
#“Playbacks”: [{
#“Uuid”:
#“Status”:
#“Number_of_scenes_downloaded”:{
#“Nominal”:
#“nrt”:
#},
#“Number_of_scenes_to_be_downloaded”:{
#“Nominal”:
#“nrt”:
#}
#“Datastrips”:[
#{
#Start:
#Stop:
#orbit:
#duration: 
#number_of_scenes:
#Latency: 
#Acquisition_type
#packet_storeoutput
#}
#]
#}
#]
