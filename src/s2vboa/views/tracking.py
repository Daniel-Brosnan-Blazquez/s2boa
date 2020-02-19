"""
Definition of tracking view

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

# Import s2boa functions
from s2boa.ingestions import functions as s2boa_functions

# Import views functions
from s2vboa.views import functions as s2vboa_functions

bp = Blueprint("tracking", __name__, url_prefix="/views")
query = Query()
engine = Engine()

@bp.route("/tracking", methods=["GET", "POST"])
def show_tracking():
    """
    Tracking view for the Sentinel-2 mission.
    """
    current_app.logger.debug("Tracking view")

    filters = {}
    if request.method == "POST":
        filters = request.form.to_dict(flat=False).copy()
    # end if

    # Initialize reporting period (now - 2 days, now + 5 days)
    window_size = 0.069
    start_filter = {
        "date": (datetime.datetime.now()).isoformat(),
        "operator": "<="
    }
    stop_filter = {
        "date": (datetime.datetime.now() - datetime.timedelta(days=window_size)).isoformat(),
        "operator": ">="
    }
    mission = "S2_"

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

    reporting_start = stop_filter["date"]
    reporting_stop = start_filter["date"]

    return render_template("views/tracking/tracking.html", reporting_start=reporting_start, reporting_stop=reporting_stop, mission=mission, sliding_window=None)

@bp.route("/sliding-tracking-parameters", methods=["GET", "POST"])
def show_sliding_tracking_parameters():
    """
    Tracking sliding view for the Sentinel-2 mission.
    """
    current_app.logger.debug("Sliding acquistion view with parameters")

    window_delay = float(request.args.get("window_delay"))
    window_size = float(request.args.get("window_size"))
    repeat_cycle = float(request.args.get("repeat_cycle"))
    mission = request.args.get("mission")

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

    reporting_start = stop_filter["date"]
    reporting_stop = start_filter["date"]

    return render_template("views/tracking/tracking.html", reporting_start=reporting_start, reporting_stop=reporting_stop, mission=mission, sliding_window = sliding_window)

@bp.route("/sliding-tracking", methods=["GET", "POST"])
def show_sliding_tracking():
    """
    Tracking sliding view for the Sentinel-2 mission.
    """
    current_app.logger.debug("Sliding tracking view")

    window_delay=0
    window_size=0.069
    repeat_cycle=1

    mission = "S2_"

    if request.method == "POST":

        if request.form["mission"] != "":
            mission = request.form["mission"]
        # end if

        if request.form["tracking_window_delay"] != "":
            window_delay = float(request.form["tracking_window_delay"])
        # end if

        if request.form["tracking_window_size"] != "":
            window_size = float(request.form["tracking_window_size"])
        # end if

        if request.form["tracking_repeat_cycle"] != "":
            repeat_cycle = float(request.form["tracking_repeat_cycle"])
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

    reporting_start = stop_filter["date"]
    reporting_stop = start_filter["date"]

    return render_template("views/tracking/tracking.html", reporting_start=reporting_start, reporting_stop=reporting_stop, mission=mission, sliding_window = sliding_window)

@bp.route("/query-tracking")
def query_tracking():
    """
    Tracking sliding view for the Sentinel-2 mission.
    """

    start = request.args.get("start")
    stop = request.args.get("stop")
    mission = request.args.get("mission")

    if mission == "S2_":
        missions = ["S2A", "S2B"]
    else:
        missions = [mission]
    # end if

    trackings = {}
    
    for mission_to_track in missions:

        events = [
            {
                "id": "COMPLETE",
                "start": start,
                "stop": stop
            },
            {
                "id": "HEAD",
                "start": (parser.parse(stop) - datetime.timedelta(seconds=30)).isoformat(),
                "stop": stop
            }            
        ]
        events_with_footprint = s2boa_functions.associate_footprints(events, mission_to_track, return_polygon_format = True)

        trackings[mission_to_track] = events_with_footprint
    # end for

    return jsonify(trackings)
