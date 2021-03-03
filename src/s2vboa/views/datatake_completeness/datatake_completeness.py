"""
datatake-completeness view for s2boa

Written by DEIMOS Space S.L. (jubv)

module s2vboa
"""
# Import python utilities
import sys
import json
import datetime
import re
from dateutil import parser

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

bp = Blueprint("datatake-completeness", __name__, url_prefix="/views")
query = Query()

@bp.route("/datatake-completeness", methods=["GET", "POST"])
def show_datatake_completeness():
    """
    Datatake completeness view for the Sentinel-2 mission.
    """
    current_app.logger.debug("Datatake completeness view")

    filters = {}
    filters["limit"] = ["20"]    
    if request.method == "POST":
        filters = request.form.to_dict(flat=False).copy()
    # end if
    filters["offset"] = [""]

    # Initialize reporting period (now , now + 1 day)
    start_filter = {
        "date": (datetime.datetime.now()).isoformat(),
        "op": "<="
    }
    stop_filter = {
        "date": (datetime.datetime.now() - datetime.timedelta(days=1)).isoformat(),
        "op": ">="
    }
    mission = "S2_"

    show = {}
    show["map"]=True
    show["timeline"]=True

    if request.method == "POST":
        if not "show_datatake_completeness_map" in request.form:
            show["map"] = False
        else:
            show["map"]=True
        # end if
        if not "show_datatake_completeness_timeline" in request.form:
            show["timeline"] = False
        else:
            show["timeline"]=True
        # end if
    # end if

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
    filters["show"] = [show]

    return query_datatake_completeness_and_render(start_filter, stop_filter, mission, show, filters = filters)

@bp.route("/specific-datatake-completeness/<string:planned_cut_imaging_uuid>")
def show_specific_datatake_completeness(planned_cut_imaging_uuid):
    """
    Specific datatake completeness view for one cut_imaging related to the Sentinel-2 mission.
    """
    current_app.logger.debug("Specific datatake completeness view")

    # Get the events of the planned cut imaging
    planned_cut_imaging = query.get_events(event_uuids = {"filter": planned_cut_imaging_uuid, "op": "=="})[0]
    
    filters = {}
    filters["limit"] = [""]
    filters["offset"] = [""]
    # Initialize reporting period
    start_filter = {
        "date": planned_cut_imaging.stop.isoformat(),
        "op": "<="
    }
    stop_filter = {
        "date": planned_cut_imaging.start.isoformat(),
        "op": ">="
    }
    mission = "S2_"

    show = {}
    show["map"]=True
    show["timeline"]=True

    filters["start"] = [stop_filter["date"]]
    filters["stop"] = [start_filter["date"]]
    filters["mission"] = [mission]
    filters["show"] = [show]

    return query_datatake_completeness_and_render(start_filter, stop_filter, mission, show, filters = filters, planned_cut_imaging_uuid = planned_cut_imaging_uuid)

@bp.route("/datatake-completeness-pages", methods=["POST"])
def query_datatake_completeness_pages():
    """
    Datatake completeness view for the Sentinel-2 mission using pages.
    """
    current_app.logger.debug("Datatake completeness view using pages")
    filters = request.json

    mission = filters["mission"][0]
    show = filters["show"][0]

    # window_size is not used, here only for using the same API
    window_size = None
    start_filter, stop_filter = s2vboa_functions.get_start_stop_filters(query, current_app, request, window_size, mission, filters)

    return query_datatake_completeness_and_render(start_filter, stop_filter, mission, show, filters = filters)

@bp.route("/sliding-datatake-completeness-parameters", methods=["GET", "POST"])
def show_sliding_datatake_completeness_parameters():
    """
    Datatake completeness sliding view for the Sentinel-2 mission.
    """
    current_app.logger.debug("Sliding datatake completeness view with parameters")

    window_delay = float(request.args.get("window_delay"))
    window_size = float(request.args.get("window_size"))
    repeat_cycle = float(request.args.get("repeat_cycle"))
    mission = request.args.get("mission")

    show = {}
    show["map"]=True
    show["timeline"]=True

    if request.method == "POST":
        if not "show_datatake_completeness_map" in request.form:
            show["map"] = False
        else:
            show["map"]=True
        # end if
        if not "show_datatake_completeness_timeline" in request.form:
            show["timeline"] = False
        else:
            show["timeline"]=True
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

    return query_datatake_completeness_and_render(start_filter, stop_filter, mission, show, sliding_window)

@bp.route("/sliding-datatake-completeness", methods=["GET", "POST"])
def show_sliding_datatake_completeness():
    """
    Datatake completeness sliding view for the Sentinel-2 mission.
    """
    current_app.logger.debug("Sliding datatake completeness view")

    window_delay=0
    window_size=1
    repeat_cycle=1

    mission = "S2_"

    show = {}
    show["map"]=True
    show["timeline"]=True

    if request.method == "POST":

        if request.form["mission"] != "":
            mission = request.form["mission"]
        # end if

        if request.form["datatake_completeness_window_delay"] != "":
            window_delay = float(request.form["datatake_completeness_window_delay"])
        # end if

        if request.form["datatake_completeness_window_size"] != "":
            window_size = float(request.form["datatake_completeness_window_size"])
        # end if

        if request.form["datatake_completeness_repeat_cycle"] != "":
            repeat_cycle = float(request.form["datatake_completeness_repeat_cycle"])
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

    return query_datatake_completeness_and_render(start_filter, stop_filter, mission, show, sliding_window)

def query_datatake_completeness_and_render(start_filter = None, stop_filter = None, mission = None, show = None, sliding_window = None, filters = None, planned_cut_imaging_uuid = None):

    datatake_completeness_events = query_datatake_completeness_events(start_filter, stop_filter, mission, filters)

    orbpre_events = s2vboa_functions.query_orbpre_events(query, current_app, start_filter, stop_filter, mission)

    reporting_start = stop_filter["date"]
    reporting_stop = start_filter["date"]
    
    template = "views/datatake_completeness/datatake_completeness.html"
    if planned_cut_imaging_uuid != None:
        template = "views/datatake_completeness/specific_datatake_completeness.html"
    # end if

    return render_template(template, datatake_completeness_events=datatake_completeness_events, orbpre_events=orbpre_events, show=show, reporting_start=reporting_start, reporting_stop=reporting_stop, sliding_window=sliding_window, filters = filters)

def query_datatake_completeness_events(start_filter = None, stop_filter = None, mission = None, filters = None, planned_cut_imaging_uuid = None):
    """
    Query planned datatake completeness events.
    """
    current_app.logger.debug("Query planned datatake completeness events")

    kwargs = {}
    events = {}
    
    if planned_cut_imaging_uuid == None:
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
        if start_filter:
            kwargs["start_filters"] = [{"date": start_filter["date"], "op": start_filter["op"]}]
        # end if

        # Stop filter
        if stop_filter:
            kwargs["stop_filters"] = [{"date": stop_filter["date"], "op": stop_filter["op"]}]
        # end if

        # Mission
        kwargs["value_filters"] = [{"name": {"op": "==", "filter": "satellite"},
                                            "type": "text",
                                            "value": {"op": "like", "filter": mission}
                                            }]
        
        kwargs["gauge_names"] = {"filter": ["PLANNED_CUT_IMAGING_CORRECTION"], "op": "in"}

        # Query planned_imaging_processing_completeness
        planned_cut_imaging_correction_events = query.get_events(**kwargs)
        events["planned_cut_imaging_correction"] = planned_cut_imaging_correction_events
        planned_cut_imaging_correction_links_events = query.get_linked_events(event_uuids = {"filter": [event.event_uuid for event in planned_cut_imaging_correction_events], "op": "in"},
                                                                              link_names = {"filter": "TIME_CORRECTION", "op": "=="},
                                                                              return_prime_events = False)
        events["planned_cut_imaging"] = [event for event in planned_cut_imaging_correction_links_events["linked_events"]]
    else:
        events_linking_to_planned_cut_imaging_events = query.get_linking_events_group_by_link_name(event_uuids = {"filter": planned_cut_imaging_uuid, "op": "=="},
                                                                                                   link_names = {"filter": "TIME_CORRECTION", "op": "=="}, 
                                                                                                   return_prime_events = True)
        events["planned_cut_imaging"] = events_linking_to_planned_cut_imaging_events["linking_events"]["PRIME"]
        events["planned_cut_imaging_correction"] = events_linking_to_planned_cut_imaging_events["linking_events"]["TIME_CORRECTION"]
        
    planned_cut_imaging_links_events = query.get_linking_events_group_by_link_name(event_uuids = {"filter": [event.event_uuid for event in events["planned_cut_imaging"]], "op": "in"},
                                                                                    link_names = {"filter": ["PLANNED_COMPLETE_IMAGING", "PROCESSING_COMPLETENESS"], "op": "in"},
                                                                                    return_prime_events = False)
    events["planned_imaging"] = [event for event in planned_cut_imaging_links_events["linking_events"]["PLANNED_COMPLETE_IMAGING"]]

    events["planned_imaging_processing_completeness"] = [event for event in planned_cut_imaging_links_events["linking_events"]["PROCESSING_COMPLETENESS"]]
    events["planned_imaging_processing_completeness_l0"] = [event for event in events["planned_imaging_processing_completeness"] if event.gauge.name == "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L0"]
    events["planned_imaging_processing_completeness_l1a"] = [event for event in events["planned_imaging_processing_completeness"] if event.gauge.name == "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L1A"]
    events["planned_imaging_processing_completeness_l1b"] = [event for event in events["planned_imaging_processing_completeness"] if event.gauge.name == "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L1B"]
    events["planned_imaging_processing_completeness_l1c"] = [event for event in events["planned_imaging_processing_completeness"] if event.gauge.name == "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L1C"]
    events["planned_imaging_processing_completeness_l2a"] = [event for event in events["planned_imaging_processing_completeness"] if event.gauge.name == "PLANNED_IMAGING_PROCESSING_COMPLETENESS_L2A"]
    
    return events
