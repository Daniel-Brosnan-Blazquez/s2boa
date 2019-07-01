"""
Views navigation section definition

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

bp = Blueprint("views", __name__, url_prefix="/views")
query = Query()
engine = Engine()

def query_orbpre_events(start_filter = None, stop_filter = None, mission = None):
    """
    Query predicted orbit events.
    """
    current_app.logger.debug("Query predicted orbit events")

    kwargs = {}

    # Start filter
    if start_filter:
        kwargs["start_filters"] = [{"date": start_filter["date"], "op": start_filter["operator"]}]
    # end if
    
    # Stop filter
    if stop_filter:
        kwargs["stop_filters"] = [{"date": stop_filter["date"], "op": stop_filter["operator"]}]
    # end if

    # Mission
    if mission:
        kwargs["value_filters"] = [{"name": {"op": "like", "str": "satellite"},
                                    "type": "text",
                                    "value": {"op": "like", "value": mission}
                                }]
    # end if

    ####
    # Query predicted orbit events
    ####
    kwargs["gauge_names"] = {"filter": ["ORBIT_PREDICTION"], "op": "in"}
    events = query.get_events(**kwargs)

    return events

def get_start_stop_filters(window_size, mission):

    start_filter = None
    stop_filter = None
    
    if request.method == "POST":

        if request.form["start"] != "":
            stop_filter = {
                "date": request.form["start"],
                "operator": ">="
            }
            if request.form["stop"] == "":
                start_filter = {
                    "date": (parser.parse(request.form["start"]) + datetime.timedelta(days=window_size)).isoformat(),
                    "operator": "<="
                }
            # end if            
        elif request.form["start_orbit"] != "":
            orbpre_events = query.get_events(gauge_names = {"filter": ["ORBIT_PREDICTION"], "op": "in"},
                                            value_filters = [{"name": {"op": "like", "str": "orbit"},
                                                              "type": "double",
                                                              "value": {"op": "==", "value": request.form["start_orbit"]}
                                                          },
                                                             {"name": {"op": "like", "str": "satellite"},
                                                              "type": "text",
                                                              "value": {"op": "like", "value": mission}
                                                          }])
            
            if len(orbpre_events) > 0:
                orbpre_event = orbpre_events[0]
                stop_filter = {
                    "date": orbpre_event.start.isoformat(),
                    "operator": ">="
                }
            # end if
            if len(orbpre_events) > 0 and request.form["stop_orbit"] == "":
                start_filter = {
                    "date": (orbpre_event.start + datetime.timedelta(days=window_size)).isoformat(),
                    "operator": "<="
                }
            # end if
        # end if

        if request.form["stop"] != "":
            start_filter = {
                "date": request.form["stop"],
                "operator": "<="
            }
            if request.form["start"] == "":
                stop_filter = {
                    "date": (parser.parse(request.form["stop"]) - datetime.timedelta(days=window_size)).isoformat(),
                    "operator": ">="
                }
            # end if
        elif request.form["stop_orbit"] != "":
            orbpre_events = query.get_events(gauge_names = {"filter": ["ORBIT_PREDICTION"], "op": "in"},
                                            value_filters = [{"name": {"op": "like", "str": "orbit"},
                                                              "type": "double",
                                                              "value": {"op": "==", "value": request.form["stop_orbit"]}
                                                          },
                                                             {"name": {"op": "like", "str": "satellite"},
                                                              "type": "text",
                                                              "value": {"op": "like", "value": mission}
                                                          }])
            
            if len(orbpre_events) > 0:
                orbpre_event = orbpre_events[0]
                start_filter = {
                    "date": orbpre_event.stop.isoformat(),
                    "operator": "<="
                }
            # end if
            if len(orbpre_events) > 0 and request.form["start_orbit"] == "":
                stop_filter = {
                    "date": (orbpre_event.stop - datetime.timedelta(days=window_size)).isoformat(),
                    "operator": ">="
                }
            # end if
        # end if

    # end if

    return start_filter, stop_filter


@bp.route("/planning", methods=["GET", "POST"])
def show_planning():
    """
    Planning view for the Sentinel-2 mission.
    """
    current_app.logger.debug("Planning view")

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

    start_filter_calculated, stop_filter_calculated = get_start_stop_filters(7, mission)

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

    return query_planning_and_render(start_filter, stop_filter, mission, show)

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
            window_delay = request.form["planning_window_delay"]
        # end if

        if request.form["planning_window_size"] != "":
            window_size = request.form["planning_window_size"]
        # end if

        if request.form["planning_repeat_cycle"] != "":
            repeat_cycle = request.form["planning_repeat_cycle"]
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
    
def query_planning_and_render(start_filter = None, stop_filter = None, mission = None, show = None, sliding_window = None):

    planning_events = query_planning_events(start_filter, stop_filter, mission)

    orbpre_events = query_orbpre_events(start_filter, stop_filter, mission)

    reporting_start = stop_filter["date"]
    reporting_stop = start_filter["date"]

    return render_template("views/planning.html", planning_events=planning_events, orbpre_events=orbpre_events, request=request, show=show, reporting_start=reporting_start, reporting_stop=reporting_stop, sliding_window=sliding_window)

def query_planning_events(start_filter = None, stop_filter = None, mission = None):
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


    # Mission
    if mission:
        kwargs_imaging["value_filters"] = [{"name": {"op": "like", "str": "satellite"},
                                    "type": "text",
                                    "value": {"op": "like", "value": mission}
                                }]
        kwargs_playback["value_filters"] = [{"name": {"op": "like", "str": "satellite"},
                                    "type": "text",
                                    "value": {"op": "like", "value": mission}
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
