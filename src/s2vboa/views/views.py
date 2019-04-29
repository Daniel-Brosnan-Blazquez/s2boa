"""
Views navigation section definition

Written by DEIMOS Space S.L. (dibb)

module s2vboa
"""
# Import python utilities
import sys
import json
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

def query_orbpre_events():
    """
    Query predicted orbit events.
    """
    current_app.logger.debug("Query predicted orbit events")

    kwargs = {}

    if request.method == "POST":

        if request.form["start"] != "":
            kwargs["start_filters"] = []
            i = 0
            operators = request.form.getlist("start_operator")
            for start in request.form.getlist("start"):
                kwargs["start_filters"].append({"date": start, "op": operators[i]})
                i+=1
            # end for
        # end if
        if request.form["stop"] != "":
            kwargs["stop_filters"] = []
            i = 0
            operators = request.form.getlist("stop_operator")
            for stop in request.form.getlist("stop"):
                kwargs["stop_filters"].append({"date": stop, "op": operators[i]})
                i+=1
            # end for
        # end if
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

    planning_events = query_planning_events()

    orbpre_events = query_orbpre_events()

    return render_template("views/planning.html", planning_events=planning_events, orbpre_events=orbpre_events, request=request)

def query_planning_events():
    """
    Query planning events.
    """
    current_app.logger.debug("Query planning events")

    # Check that the ORBPRE files cover the requested period

    kwargs_imaging = {}
    kwargs_playback = {}

    if request.method == "POST":
        if "nppfs" in request.form and request.form["nppfs"] != "":
            op="notin"
            if not "nppf_notin_check" in request.form:
                op="in"
            # end if
            kwargs["sources"] = {"filter": [], "op": op}
            i = 0
            for nppf in request.form.getlist("nppfs"):
                kwargs["sources"]["filter"].append(nppf)
                i+=1
            # end for
        # end if

        if request.form["start"] != "":
            kwargs_imaging["start_filters"] = []
            kwargs_playback["start_filters"] = []
            i = 0
            operators = request.form.getlist("start_operator")
            for start in request.form.getlist("start"):
                kwargs_imaging["start_filters"].append({"date": start, "op": operators[i]})
                kwargs_playback["start_filters"].append({"date": start, "op": operators[i]})
                i+=1
            # end for
        # end if
        if request.form["stop"] != "":
            kwargs_imaging["stop_filters"] = []
            kwargs_playback["stop_filters"] = []
            i = 0
            operators = request.form.getlist("stop_operator")
            for stop in request.form.getlist("stop"):
                kwargs_imaging["stop_filters"].append({"date": stop, "op": operators[i]})
                kwargs_playback["stop_filters"].append({"date": stop, "op": operators[i]})
                i+=1
            # end for
        # end if
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
