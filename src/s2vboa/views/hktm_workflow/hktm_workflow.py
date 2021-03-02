"""
HKTM Workflow view for s2boa

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

bp = Blueprint("hktm_workflow", __name__, url_prefix="/views")
query = Query()

@bp.route("/hktm-workflow", methods=["GET", "POST"])
def show_hktm_workflow():
    """
    HKTM Workflow view for the Sentinel-2 mission.
    """
    current_app.logger.debug("HKTM Workflow view")

    filters = {}
    filters["limit"] = ["20"]
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

    if request.method == "POST":
        filters = request.form.to_dict(flat=False).copy()
        if request.form["mission"] != "":
            mission = request.form["mission"]
        # end if
    # end if
    filters["offset"] = [""]
    
    window_size = 1
    start_filter_calculated, stop_filter_calculated = s2vboa_functions.get_start_stop_filters(query, current_app, request, window_size, mission, filters)

    if start_filter_calculated != None:
        start_filter = start_filter_calculated
    # end if

    if stop_filter_calculated != None:
        stop_filter = stop_filter_calculated
    # end if

    filters["start"] = [stop_filter["date"]]
    filters["stop"] = [start_filter["date"]]
    filters["mission"] = [mission]

    return query_hktm_workflow_and_render(start_filter, stop_filter, mission, filters = filters)

@bp.route("/hktm-workflow-pages", methods=["POST"])
def query_hktm_workflow_pages():
    """
    Hktm Workflow view for the Sentinel-2 mission using pages.
    """
    current_app.logger.debug("Hktm Workflow view using pages")
    filters = request.json

    mission = filters["mission"][0]

    # window_size is not used, here only for using the same API
    window_size = None
    start_filter, stop_filter = s2vboa_functions.get_start_stop_filters(query, current_app, request, window_size, mission, filters)

    return query_hktm_workflow_and_render(start_filter, stop_filter, mission, filters = filters)

@bp.route("/sliding-hktm-workflow-parameters", methods=["GET", "POST"])
def show_sliding_hktm_workflow_parameters():
    """
    Hktm Workflow sliding view for the Sentinel-2 mission.
    """
    current_app.logger.debug("Sliding acquistion view with parameters")

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

    return query_hktm_workflow_and_render(start_filter, stop_filter, mission, sliding_window)

@bp.route("/sliding-hktm-workflow", methods=["GET", "POST"])
def show_sliding_hktm_workflow():
    """
    Hktm Workflow sliding view for the Sentinel-2 mission.
    """
    current_app.logger.debug("Sliding hktm workflow view")

    window_delay=0
    window_size=1
    repeat_cycle=1

    mission = "S2_"

    if request.method == "POST":

        if request.form["mission"] != "":
            mission = request.form["mission"]
        # end if

        if request.form["hktm_workflow_window_delay"] != "":
            window_delay = float(request.form["hktm_workflow_window_delay"])
        # end if

        if request.form["hktm_workflow_window_size"] != "":
            window_size = float(request.form["hktm_workflow_window_size"])
        # end if

        if request.form["hktm_workflow_repeat_cycle"] != "":
            repeat_cycle = float(request.form["hktm_workflow_repeat_cycle"])
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

    return query_hktm_workflow_and_render(start_filter, stop_filter, mission, sliding_window)

def query_hktm_workflow_and_render(start_filter = None, stop_filter = None, mission = None, sliding_window = None, filters = None):

    # Set offset and limit for the query
    offset = None
    if filters and "offset" in filters and filters["offset"][0] != "":
        offset = filters["offset"][0]
    # end if
    limit = None
    if filters and "limit" in filters and filters["limit"][0] != "":
        limit = filters["limit"][0]
    # end if
    
    orbpre_events = s2vboa_functions.query_orbpre_events(query, current_app, start_filter, stop_filter, mission)

    descending = True
    orbpre_events_limit = s2vboa_functions.query_orbpre_events(query, current_app, start_filter, stop_filter, mission, limit, offset, descending)

    reporting_start = stop_filter["date"]
    reporting_stop = start_filter["date"]

    hktm_workflow_events = query_hktm_workflow_events(orbpre_events_limit, filters)

    route = "views/hktm_workflow/hktm_workflow.html"

    return render_template(route, hktm_workflow_events=hktm_workflow_events, orbpre_events=orbpre_events, orbpre_events_limit=orbpre_events_limit, request=request, reporting_start=reporting_start, reporting_stop=reporting_stop, sliding_window=sliding_window, filters = filters)

def query_hktm_workflow_events(orbpre_events, filters = None):
    """
    Query planned hktm workflow events.
    """
    current_app.logger.debug("Query planned hktm workflow events")

    events = {}
    events["playback_correction"] = []
    events["playback"] = []
    events["playback_validity"] = []
    events["hktm_production_vgs"] = []
    events["station_report"] = []
    events["distribution_status"] = []
    events["dfep_acquisition_validity"] = []
    events["station_schedule"] = []
    
    missions = sorted(set([event.gauge.system for event in orbpre_events]))
    for mission in missions:
        orbpre_events_mission = [event for event in orbpre_events if event.gauge.system == mission]
        orbpre_events_mission.sort(key=lambda x: x.start)
        query_start = orbpre_events_mission[0].start.isoformat()
        query_stop = orbpre_events_mission[-1].stop.isoformat()
        kwargs_playback = {}

        # Set order by reception_time descending
        kwargs_playback["order_by"] = {"field": "start", "descending": True}

        # Set period for the query
        kwargs_playback["start_filters"] = [{"date": query_stop, "op": "<="}]
        kwargs_playback["stop_filters"] = [{"date": query_start, "op": ">="}]

        kwargs_playback["value_filters"] = [{"name": {"op": "==", "filter": "playback_type"},
                                             "type": "text",
                                             "value": {"op": "in", "filter": ["HKTM_SAD", "HKTM"]}
        }]
        kwargs_playback["gauge_names"] = {"filter": ["PLANNED_PLAYBACK_CORRECTION"], "op": "in"}

        # Specify the main query parameters
        kwargs_playback["link_names"] = {"filter": ["TIME_CORRECTION"], "op": "in"}

        ####
        # Query planned playbacks
        ####
        planned_playback_correction_events = query.get_linked_events(**kwargs_playback)
        # Mission
        if mission:
            kwargs = {"event_uuids": {"filter": [event.event_uuid for event in planned_playback_correction_events["prime_events"]], "op": "in"}}
            kwargs["value_filters"] = [{"name": {"op": "==", "filter": "satellite"},
                                        "type": "text",
                                        "value": {"op": "like", "filter": mission}
            }]
            planned_playback_correction_events = query.get_linked_events(**kwargs)
        # end if

        planned_playback_events = query.get_linking_events_group_by_link_name(event_uuids = {"filter": [event.event_uuid for event in planned_playback_correction_events["linked_events"]], "op": "in"}, link_names = {"filter": ["PLAYBACK_VALIDITY", "HKTM_PRODUCTION", "HKTM_PRODUCTION_VGS", "STATION_ACQUISITION_REPORT", "DISTRIBUTION_STATUS", "DFEP_ACQUISITION_VALIDITY", "STATION_SCHEDULE", "SLOT_REQUEST_EDRS"], "op": "in"}, return_prime_events = False)

        
        events["playback_correction"] += planned_playback_correction_events["prime_events"]
        events["playback"] += planned_playback_correction_events["linked_events"]
        events["playback_validity"] += planned_playback_events["linking_events"]["PLAYBACK_VALIDITY"]
        events["hktm_production_vgs"] += planned_playback_events["linking_events"]["HKTM_PRODUCTION_VGS"]
        events["station_report"] += planned_playback_events["linking_events"]["STATION_ACQUISITION_REPORT"]
        events["distribution_status"] += planned_playback_events["linking_events"]["DISTRIBUTION_STATUS"]
        events["dfep_acquisition_validity"] += planned_playback_events["linking_events"]["DFEP_ACQUISITION_VALIDITY"]
        events["station_schedule"] += planned_playback_events["linking_events"]["STATION_SCHEDULE"] + planned_playback_events["linking_events"]["SLOT_REQUEST_EDRS"]
    # end for
        
    return events
