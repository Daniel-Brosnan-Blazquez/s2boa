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

    planned_playback_correction_events_filtered_by_satellite = query.get_linked_events(event_uuids = {"filter": [event.event_uuid for event in planned_playback_correction_events], "op": "in"},
                                                                                       link_names = {"filter": "TIME_CORRECTION", "op": "=="},
                                                                                       value_filters = [{"name": {"op": "==", "filter": "satellite"},
                                                                                                         "type": "text",
                                                                                                         "value": {"op": "like", "filter": mission}}
                                                                                                        ])

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
        first_isp_validity_with_status_complete = isp_validity_with_status_complete[0]

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

    
    ######
    # Data allocation algorithm
    ######
    #pdb.set_trace()

    return structure
