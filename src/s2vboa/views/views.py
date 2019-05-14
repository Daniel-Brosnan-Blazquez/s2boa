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

@bp.route("/planning", methods=["GET", "POST"])
def show_planning():
    """
    Planning view for the Sentinel-2 mission.
    """
    current_app.logger.debug("Planning view")

    # Initialize reporting period (today - 2 days, today + 5 days)
    start_filter = {
        "date": (parser.parse(datetime.datetime.today().strftime("%Y-%m-%d")) - datetime.timedelta(days=2)).isoformat(),
        "operator": "<"
    }
    stop_filter = {
        "date": (parser.parse(datetime.datetime.today().strftime("%Y-%m-%d")) - datetime.timedelta(days=5)).isoformat(),
        "operator": ">"
    }
    mission = "S2_"

    show = {}
    show["timeline"]=True
    show["table_details"]=True
    show["map"]=True

    if request.method == "POST":

        if request.form["mission"] != "":
            mission = request.form["mission"]
        # end if

        if request.form["start"] != "":
            start_filter = {
                "date": request.form["stop"],
                "operator": "<"
            }
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
                    "operator": "<"
                }
            # end if
            if len(orbpre_events) > 0 and request.form["start_orbit"] == "":
                stop_filter = {
                    "date": (orbpre_event.stop - datetime.timedelta(days=5)).isoformat(),
                    "operator": ">"
                }
            # end if
        # end if
        if request.form["stop"] != "":
            stop_filter = {
                "date": request.form["start"],
                "operator": ">"
            }
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
                    "operator": ">"
                }
            # end if
            if len(orbpre_events) > 0 and request.form["stop_orbit"] == "":
                start_filter = {
                    "date": (orbpre_event.start + datetime.timedelta(days=5)).isoformat(),
                    "operator": "<"
                }
            # end if
        # end if

        if not "show_planning_timeline" in request.form:
            show["timeline"] = False
        else:
            show["timeline"]=True
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

    planning_events = query_planning_events(start_filter, stop_filter, mission)

    orbpre_events = query_orbpre_events(start_filter, stop_filter, mission)

    reporting_start = stop_filter["date"]
    reporting_stop = start_filter["date"]

    return render_template("views/planning.html", planning_events=planning_events, orbpre_events=orbpre_events, request=request, show=show, reporting_start=reporting_start, reporting_stop=reporting_stop)

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
