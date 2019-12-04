"""
Data size view for s2boa

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

bp = Blueprint("data_size", __name__, url_prefix="/views")
query = Query()

@bp.route("/data-size", methods=["GET", "POST"])
def show_data_size():
    """
    Data size view for the Sentinel-2 mission.
    """
    current_app.logger.debug("Data size view")

    filters = {}
    filters["limit"] = ["100"]    
    if request.method == "POST":
        filters = request.form.to_dict(flat=False).copy()
    # end if
    filters["offset"] = [""]

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
    define_what_to_show_data_size(show)

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

    return query_datastrips_and_render(start_filter, stop_filter, mission, show, filters = filters)

@bp.route("/data-size-pages", methods=["POST"])
def query_data_size_pages():
    """
    Data size view for the Sentinel-2 mission using pages.
    """
    current_app.logger.debug("Data size view using pages")
    filters = request.json

    mission = filters["mission"][0]
    show = filters["show"][0]
    mission = filters["mission"][0]

    # window_size is not used, here only for using the same API
    window_size = None
    start_filter, stop_filter = s2vboa_functions.get_start_stop_filters(query, current_app, request, window_size, mission, filters)

    return query_datastrip_and_render(start_filter, stop_filter, mission, show, filters = filters)

@bp.route("/sliding-data-size-parameters", methods=["GET", "POST"])
def show_sliding_data_size_parameters():
    """
    Data size sliding view for the Sentinel-2 mission.
    """
    current_app.logger.debug("Sliding data size view with parameters")

    window_delay = float(request.args.get("window_delay"))
    window_size = float(request.args.get("window_size"))
    repeat_cycle = float(request.args.get("repeat_cycle"))
    mission = request.args.get("mission")

    show = {}
    define_what_to_show_data_size(show)

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

    return query_datastrip_and_render(start_filter, stop_filter, mission, show, sliding_window)

@bp.route("/sliding-data-size", methods=["GET", "POST"])
def show_sliding_data_size():
    """
    Data size sliding view for the Sentinel-2 mission.
    """
    current_app.logger.debug("Sliding data size view")

    window_delay=0
    window_size=1
    repeat_cycle=1

    mission = "S2_"

    show = {}
    define_what_to_show_data_size(show)

    if request.method == "POST":

        if request.form["mission"] != "":
            mission = request.form["mission"]
        # end if

        if request.form["data_size_window_delay"] != "":
            window_delay = float(request.form["data_size_window_delay"])
        # end if

        if request.form["data_size_window_size"] != "":
            window_size = float(request.form["data_size_window_size"])
        # end if

        if request.form["data_size_repeat_cycle"] != "":
            repeat_cycle = float(request.form["data_size_repeat_cycle"])
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

    return query_datastrip_and_render(start_filter, stop_filter, mission, show, sliding_window)

def define_what_to_show_data_size(show):

    show["table_details"]=True
    show["map"]=True
    show["evolution"]=True

    if request.method == "POST":
        if not "show_data_size_table_details" in request.form:
            show["table_details"] = False
        else:
            show["table_details"]=True
        # end if
        if not "show_data_size_map" in request.form:
            show["map"] = False
        else:
            show["map"]=True
        # end if
        if not "show_data_size_evolution" in request.form:
            show["evolution"] = False
        else:
            show["evolution"]=True
        # end if
    # end if

def query_datastrips_and_render(start_filter = None, stop_filter = None, mission = None, show = None, sliding_window = None, filters = None):

    datastrip_events = query_datastrip_events(start_filter, stop_filter, mission, filters)

    orbpre_events = s2vboa_functions.query_orbpre_events(query, current_app, start_filter, stop_filter, mission)

    reporting_start = stop_filter["date"]
    reporting_stop = start_filter["date"]

    return render_template("views/data_size/data_size.html", datastrip_events=datastrip_events, orbpre_events=orbpre_events, request=request, show=show, reporting_start=reporting_start, reporting_stop=reporting_stop, sliding_window=sliding_window, filters = filters)

def query_datastrip_events(start_filter = None, stop_filter = None, mission = None, filters = None):
    """
    Query datastrip events.
    """
    current_app.logger.debug("Query datastrip events")

    kwargs = {}

    # Set offset and limit for the query
    if filters and "offset" in filters and filters["offset"][0] != "":
        kwargs["offset"] = filters["offset"][0]
    # end if
    if filters and "limit" in filters and filters["limit"][0] != "":
        kwargs["limit"] = filters["limit"][0]
    # end if

    # Set order by reception_time descending
    kwargs["order_by"] = {"field": "start", "descending": False}

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
        kwargs["value_filters"] = [{"name": {"op": "==", "filter": "satellite"},
                                    "type": "text",
                                    "value": {"op": "like", "filter": mission}
                                }]
    # end if

    ####
    # Query datastrips
    ####
    # Specify the main query parameters
    kwargs["gauge_names"] = {"filter": "PROCESSING_VALIDITY", "op": "=="}

    events = query.get_events(**kwargs)

    return events
