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

def build_data_allocation_structure(start_filter = None, stop_filter = None, mission = None, filters = None):
    """
    Build data allocation structure.
    """
    current_app.logger.debug("Build data allocation structure")

    kwargs = {}
    
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
    if mission:
        kwargs["value_filters"] = [{"name": {"op": "==", "filter": "satellite"},
                                    "type": "text",
                                    "value": {"op": "like", "filter": mission}
                                }]
    # end if

    structure = {}
    
    return structure
