"""
Planning view definition

Written by DEIMOS Space S.L. (dibb)

module s2vboa
"""
# Import python utilities
import sys
import json
import datetime
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

bp = Blueprint("planning", __name__, url_prefix="/views")
query = Query()

@bp.route("/planning", methods=["GET", "POST"])
def show_planning():
    """
    Planning view for the Sentinel-2 mission.
    """
    current_app.logger.debug("Planning view")

    filters = {}
    filters["limit"] = ["100"]    
    if request.method == "POST":
        filters = request.form.to_dict(flat=False).copy()
    # end if
    filters["offset"] = [""]

    # Initialize reporting period (now - 2 days, now + 5 days)
    start_filter = {
        "date": (datetime.datetime.now() + datetime.timedelta(days=5)).isoformat(),
        "operator": "<="
    }
    stop_filter = {
        "date": (datetime.datetime.now() - datetime.timedelta(days=2)).isoformat(),
        "operator": ">="
    }
    mission = "S2_"

    show = {}
    define_what_to_show_planning(show)

    window_size=7
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

    return query_planning_and_render(start_filter, stop_filter, mission, show, filters = filters)

@bp.route("/planning-pages", methods=["POST"])
def query_planning_pages():
    """
    Planning view for the Sentinel-2 mission using pages.
    """
    current_app.logger.debug("Planning view using pages")
    filters = json.loads(request.form["json"])

    mission = filters["mission"][0]
    show = filters["show"][0]
    mission = filters["mission"][0]

    # window_size is not used, here only for using the same API
    window_size = None
    start_filter, stop_filter = s2vboa_functions.get_start_stop_filters(query, current_app, request, window_size, mission, filters)

    return query_planning_and_render(start_filter, stop_filter, mission, show, filters = filters)

@bp.route("/sliding_planning_parameters", methods=["GET", "POST"])
def show_sliding_planning_parameters():
    """
    Planning view for the Sentinel-2 mission.
    """
    current_app.logger.debug("Sliding planning view with parameters")

    window_delay = float(request.args.get("window_delay"))
    window_size = float(request.args.get("window_size"))
    repeat_cycle = float(request.args.get("repeat_cycle"))
    mission = request.args.get("mission")

    show = {}
    define_what_to_show_planning(show)

    start_filter = {
        "date": (datetime.datetime.now() - datetime.timedelta(days=window_delay)).isoformat(),
        "operator": "<="
    }
    stop_filter = {
        "date": (datetime.datetime.now() - datetime.timedelta(days=(window_delay+window_size))).isoformat(),
        "operator": ">="
    }

    sliding_window = {
        "window_delay": window_delay,
        "window_size": window_size,
        "repeat_cycle": repeat_cycle,
        "mission": mission
    }

    return query_planning_and_render(start_filter, stop_filter, mission, show, sliding_window)

@bp.route("/sliding_planning", methods=["GET", "POST"])
def show_sliding_planning():
    """
    Planning view for the Sentinel-2 mission.
    """
    current_app.logger.debug("Sliding planning view")

    window_delay=-5
    window_size=7
    repeat_cycle=1

    mission = "S2_"

    show = {}
    define_what_to_show_planning(show)

    if request.method == "POST":

        if request.form["mission"] != "":
            mission = request.form["mission"]
        # end if

        if request.form["planning_window_delay"] != "":
            window_delay = float(request.form["planning_window_delay"])
        # end if

        if request.form["planning_window_size"] != "":
            window_size = float(request.form["planning_window_size"])
        # end if

        if request.form["planning_repeat_cycle"] != "":
            repeat_cycle = float(request.form["planning_repeat_cycle"])
        # end if

    # end if

    start_filter = {
        "date": (datetime.datetime.now() - datetime.timedelta(days=window_delay)).isoformat(),
        "operator": "<="
    }
    stop_filter = {
        "date": (datetime.datetime.now() - datetime.timedelta(days=(window_delay+window_size))).isoformat(),
        "operator": ">="
    }

    sliding_window = {
        "window_delay": window_delay,
        "window_size": window_size,
        "repeat_cycle": repeat_cycle,
        "mission": mission
    }

    return query_planning_and_render(start_filter, stop_filter, mission, show, sliding_window)

def define_what_to_show_planning(show):

    show["timeline"]=True
    show["x_time"]=True
    show["table_details"]=True
    show["map"]=True

    if request.method == "POST":
        if not "show_planning_timeline" in request.form:
            show["timeline"] = False
        else:
            show["timeline"]=True
        # end if
        if not "show_planning_x_time_evolution" in request.form:
            show["x_time"] = False
        else:
            show["x_time"]=True
        # end if
        if not "show_planning_table_details" in request.form:
            show["table_details"] = False
        else:
            show["table_details"]=True
        # end if
        if not "show_planning_map" in request.form:
            show["map"] = False
        else:
            show["map"]=True
        # end if
    # end if

def query_planning_and_render(start_filter = None, stop_filter = None, mission = None, show = None, sliding_window = None, filters = None):

    planning_events = query_planning_events(start_filter, stop_filter, mission, filters)

    orbpre_events = s2vboa_functions.query_orbpre_events(query, current_app, start_filter, stop_filter, mission)

    reporting_start = stop_filter["date"]
    reporting_stop = start_filter["date"]

    return render_template("views/planning.html", planning_events=planning_events, orbpre_events=orbpre_events, request=request, show=show, reporting_start=reporting_start, reporting_stop=reporting_stop, sliding_window=sliding_window, filters = filters)

def query_planning_events(start_filter = None, stop_filter = None, mission = None, filters = None):
    """
    Query planning events.
    """
    current_app.logger.debug("Query planning events")

    # Check that the ORBPRE files cover the requested period

    kwargs_imaging = {}
    kwargs_playback = {}

    # Start filter
    if start_filter:
        kwargs_imaging["start_filters"] = [{"date": start_filter["date"], "op": start_filter["operator"]}]
        kwargs_playback["start_filters"] = [{"date": start_filter["date"], "op": start_filter["operator"]}]
    # end if

    # Stop filter
    if stop_filter:
        kwargs_imaging["stop_filters"] = [{"date": stop_filter["date"], "op": stop_filter["operator"]}]
        kwargs_playback["stop_filters"] = [{"date": stop_filter["date"], "op": stop_filter["operator"]}]
    # end if

    # Set offset and limit for the query
    if filters and "offset" in filters and filters["offset"][0] != "":
        kwargs_imaging["offset"] = filters["offset"][0]
        kwargs_playback["offset"] = filters["offset"][0]
    # end if
    if filters and "limit" in filters and filters["limit"][0] != "":
        kwargs_imaging["limit"] = filters["limit"][0]
        kwargs_playback["limit"] = filters["limit"][0]
    # end if

    # Set order by reception_time descending
    kwargs_imaging["order_by"] = {"field": "start", "descending": True}
    kwargs_playback["order_by"] = {"field": "start", "descending": True}

    # Mission
    if mission:
        kwargs_imaging["value_filters"] = [{"name": {"op": "==", "filter": "satellite"},
                                    "type": "text",
                                    "value": {"op": "like", "filter": mission}
                                }]
        kwargs_playback["value_filters"] = [{"name": {"op": "==", "filter": "satellite"},
                                    "type": "text",
                                    "value": {"op": "like", "filter": mission}
                                }]
    # end if


    ####
    # Query imaging
    ####
    # Specify the main query parameters
    kwargs_imaging["gauge_names"] = {"filter": ["PLANNED_CUT_IMAGING_CORRECTION"], "op": "in"}
    kwargs_imaging["link_names"] = {"filter": ["TIME_CORRECTION"], "op": "in"}
    imaging_events = query.get_linked_events(**kwargs_imaging)

    ####
    # Query playbacks
    ####
    # Specify the main query parameters
    kwargs_playback["gauge_names"] = {"filter": ["PLANNED_PLAYBACK_CORRECTION"], "op": "in"}
    kwargs_playback["link_names"] = {"filter": ["TIME_CORRECTION"], "op": "in"}
    playback_events = query.get_linked_events(**kwargs_playback)

    events = {}
    events["imaging"] = imaging_events
    events["playback"] = playback_events

    return events
