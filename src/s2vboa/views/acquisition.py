"""
Acquistion view for s2boa

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

bp = Blueprint("acquisition", __name__, url_prefix="/views")
query = Query()

@bp.route("/acquisition", methods=["GET", "POST"])
def show_acquisition():
    """
    Acquisition view for the Sentinel-2 mission.
    """
    current_app.logger.debug("Acquisition view")

    # Initialize reporting period (now - 2 days, now + 5 days)
    start_filter = {
        "date": (datetime.datetime.now()).isoformat(),
        "operator": "<="
    }
    stop_filter = {
        "date": (datetime.datetime.now() - datetime.timedelta(days=1)).isoformat(),
        "operator": ">="
    }
    mission = "S2_"

    show = {}
    define_what_to_show_acquisition(show)

    window_size = 1
    start_filter_calculated, stop_filter_calculated = s2vboa_functions.get_start_stop_filters(query, current_app, request, window_size, mission)

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

    return query_acquisition_and_render(start_filter, stop_filter, mission, show)

@bp.route("/sliding_acquisition_parameters", methods=["GET", "POST"])
def show_sliding_acquisition_parameters():
    """
    Acquisition sliding view for the Sentinel-2 mission.
    """
    current_app.logger.debug("Sliding acquistion view with parameters")

    window_delay = float(request.args.get("window_delay"))
    window_size = float(request.args.get("window_size"))
    repeat_cycle = float(request.args.get("repeat_cycle"))
    mission = request.args.get("mission")

    show = {}
    define_what_to_show_acquisition(show)

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

    return query_acquisition_and_render(start_filter, stop_filter, mission, show, sliding_window)

@bp.route("/sliding_acquisition", methods=["GET", "POST"])
def show_sliding_acquisition():
    """
    Acquisition sliding view for the Sentinel-2 mission.
    """
    current_app.logger.debug("Sliding acquisition view")

    window_delay=0
    window_size=1
    repeat_cycle=1

    mission = "S2_"

    show = {}
    define_what_to_show_acquisition(show)

    if request.method == "POST":

        if request.form["mission"] != "":
            mission = request.form["mission"]
        # end if

        if request.form["acquisition_window_delay"] != "":
            window_delay = float(request.form["acquisition_window_delay"])
        # end if

        if request.form["acquisition_window_size"] != "":
            window_size = float(request.form["acquisition_window_size"])
        # end if

        if request.form["acquisition_repeat_cycle"] != "":
            repeat_cycle = float(request.form["acquisition_repeat_cycle"])
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

    return query_acquisition_and_render(start_filter, stop_filter, mission, show, sliding_window)

def define_what_to_show_acquisition(show):

    show["table_details"]=True
    show["map"]=True
    show["timeline"]=True
    show["station_reports"]=True

    if request.method == "POST":
        if not "show_acquisition_table_details" in request.form:
            show["table_details"] = False
        else:
            show["table_details"]=True
        # end if
        if not "show_acquisition_map" in request.form:
            show["map"] = False
        else:
            show["map"]=True
        # end if
        if not "show_acquisition_timeline" in request.form:
            show["timeline"] = False
        else:
            show["timeline"]=True
        # end if
        if not "show_station_reports" in request.form:
            show["station_reports"] = False
        else:
            show["station_reports"]=True
        # end if
    # end if

def query_acquisition_and_render(start_filter = None, stop_filter = None, mission = None, show = None, sliding_window = None):

    acquisition_events = query_acquisition_events(start_filter, stop_filter, mission)

    orbpre_events = s2vboa_functions.query_orbpre_events(query, current_app, start_filter, stop_filter, mission)

    reporting_start = stop_filter["date"]
    reporting_stop = start_filter["date"]

    return render_template("views/acquisition.html", acquisition_events=acquisition_events, orbpre_events=orbpre_events, request=request, show=show, reporting_start=reporting_start, reporting_stop=reporting_stop, sliding_window=sliding_window)

def query_acquisition_events(start_filter = None, stop_filter = None, mission = None):
    """
    Query planned acquisition events.
    """
    current_app.logger.debug("Query planned acquisition events")

    # Check that the ORBPRE files cover the requested period

    kwargs_playback = {}

    # Start filter
    if start_filter:
        kwargs_playback["start_filters"] = [{"date": start_filter["date"], "op": start_filter["operator"]}]
    # end if

    # Stop filter
    if stop_filter:
        kwargs_playback["stop_filters"] = [{"date": stop_filter["date"], "op": stop_filter["operator"]}]
    # end if


    # Mission
    if mission:
        kwargs_playback["value_filters"] = [{"name": {"op": "==", "filter": "satellite"},
                                    "type": "text",
                                    "value": {"op": "like", "filter": mission}
                                }]
    # end if

    ####
    # Query planned playbacks
    ####
    # Specify the main query parameters
    kwargs_playback["gauge_names"] = {"filter": ["PLANNED_PLAYBACK_CORRECTION"], "op": "in"}
    kwargs_playback["link_names"] = {"filter": ["TIME_CORRECTION"], "op": "in"}
    planned_playback_correction_events = query.get_linked_events(**kwargs_playback)
    planned_playback_events = query.get_linking_events_group_by_link_name(event_uuids = {"filter": [event.event_uuid for event in planned_playback_correction_events["linked_events"]], "op": "in"}, link_names = {"filter": ["PLAYBACK_VALIDITY", "PLAYBACK_COMPLETENESS", "DFEP_SCHEDULE", "STATION_SCHEDULE", "SLOT_REQUEST_EDRS", "STATION_ACQUISITION_REPORT"], "op": "in"}, return_prime_events = False)

    events = {}
    events["playback_correction"] = planned_playback_correction_events["prime_events"]
    events["playback"] = planned_playback_correction_events["linked_events"]
    events["playback_completeness_channel"] = planned_playback_events["linking_events"]["PLAYBACK_COMPLETENESS"]
    events["playback_validity"] = planned_playback_events["linking_events"]["PLAYBACK_VALIDITY"]
    events["station_report"] = planned_playback_events["linking_events"]["STATION_ACQUISITION_REPORT"]
    events["station_schedule"] = planned_playback_events["linking_events"]["STATION_SCHEDULE"]
    events["dfep_schedule"] = planned_playback_events["linking_events"]["DFEP_SCHEDULE"]
    events["slot_request_edrs"] = planned_playback_events["linking_events"]["SLOT_REQUEST_EDRS"]

    return events
