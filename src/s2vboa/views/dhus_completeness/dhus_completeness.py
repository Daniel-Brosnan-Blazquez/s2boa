"""
Data availability in DHUS (completeness from planning) view for s2boa

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

# Import vboa security
from vboa.security import auth_required, roles_accepted

bp = Blueprint("dhus-completeness", __name__, url_prefix="/views")
query = Query()

@bp.route("/dhus-completeness", methods=["GET", "POST"])
@auth_required()
@roles_accepted("administrator", "service_administrator", "operator", "analyst", "operator_observer", "observer")
def show_dhus_completeness():
    """
    DHUS completeness view for the Sentinel-2 mission.
    """
    current_app.logger.debug("DHUS completeness view")

    filters = {}
    filters["limit"] = ["2"]    
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
    levels = "ALL"

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
        if request.form["levels"] != "":
                levels = request.form["levels"]
        # end if

    # end if

    filters["start"] = [stop_filter["date"]]
    filters["stop"] = [start_filter["date"]]
    filters["mission"] = [mission]
    filters["levels"] = levels

    return query_dhus_completeness_and_render(start_filter, stop_filter, mission, levels, filters = filters)

@bp.route("/dhus-completeness-by-datatake/<string:corrected_planned_imaging_uuid>")
@auth_required()
@roles_accepted("administrator", "service_administrator", "operator", "analyst", "operator_observer", "observer")
def show_specific_datatake(corrected_planned_imaging_uuid):
    """
    Specific dhus completeness view for one datatake related to the Sentinel-2 mission.
    """
    current_app.logger.debug("Specific dhus completeness view")

    # Get the events of the datatake
    corrected_planned_imaging = query.get_events(event_uuids = {"filter": corrected_planned_imaging_uuid, "op": "=="})[0]
    
    filters = {}
    filters["limit"] = [""]
    filters["offset"] = [""]
    start_filter = {
        "date": corrected_planned_imaging.stop.isoformat(),
        "op": "<="
    }
    stop_filter = {
        "date": corrected_planned_imaging.start.isoformat(),
        "op": ">="
    }
    mission = "S2_"
    levels = "ALL"

    filters["start"] = [stop_filter["date"]]
    filters["stop"] = [start_filter["date"]]
    filters["mission"] = [mission]

    filters["start"] = [stop_filter["date"]]
    filters["stop"] = [start_filter["date"]]
    filters["mission"] = [mission]
    filters["levels"] = levels

    return query_dhus_completeness_and_render(start_filter, stop_filter, mission, levels, filters = filters, corrected_planned_imaging_uuid = corrected_planned_imaging_uuid)

@bp.route("/dhus-completeness-pages", methods=["POST"])
@auth_required()
@roles_accepted("administrator", "service_administrator", "operator", "analyst", "operator_observer", "observer")
def query_dhus_completeness_pages():
    """
    DHUS completeness view for the Sentinel-2 mission using pages.
    """
    current_app.logger.debug("DHUS completeness view using pages")
    filters = request.json

    mission = filters["mission"][0]
    levels = filters["levels"]

    # window_size is not used, here only for using the same API
    window_size = None
    start_filter, stop_filter = s2vboa_functions.get_start_stop_filters(query, current_app, request, window_size, mission, filters)

    return query_dhus_completeness_and_render(start_filter, stop_filter, mission, levels, filters = filters)

@bp.route("/sliding-dhus-completeness-parameters", methods=["GET", "POST"])
@auth_required()
@roles_accepted("administrator", "service_administrator", "operator", "analyst", "operator_observer", "observer")
def show_sliding_dhus_completeness_parameters():
    """
    DHUS completeness sliding view for the Sentinel-2 mission.
    """
    current_app.logger.debug("Sliding acquistion view with parameters")

    window_delay = float(request.args.get("window_delay"))
    window_size = float(request.args.get("window_size"))
    repeat_cycle = float(request.args.get("repeat_cycle"))
    mission = request.args.get("mission")
    levels = "ALL"
    if request.args.get("levels") != "":
        levels = request.args.get("levels")
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
        "mission": mission,
        "levels": levels
    }

    return query_dhus_completeness_and_render(start_filter, stop_filter, mission, levels, sliding_window)

@bp.route("/sliding-dhus-completeness", methods=["GET", "POST"])
@auth_required()
@roles_accepted("administrator", "service_administrator", "operator", "analyst", "operator_observer", "observer")
def show_sliding_dhus_completeness():
    """
    DHUS completeness sliding view for the Sentinel-2 mission.
    """
    current_app.logger.debug("Sliding acquisition view")

    window_delay=0
    window_size=1
    repeat_cycle=1

    mission = "S2_"
    levels = "ALL"
    
    if request.method == "POST":

        if request.form["mission"] != "":
            mission = request.form["mission"]
        # end if

        if request.form["levels"] != "":
            levels = request.form["levels"]
        # end if

        if request.form["dhus_completeness_window_delay"] != "":
            window_delay = float(request.form["dhus_completeness_window_delay"])
        # end if

        if request.form["dhus_completeness_window_size"] != "":
            window_size = float(request.form["dhus_completeness_window_size"])
        # end if

        if request.form["dhus_completeness_repeat_cycle"] != "":
            repeat_cycle = float(request.form["dhus_completeness_repeat_cycle"])
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
        "mission": mission,
        "levels": levels
    }

    return query_dhus_completeness_and_render(start_filter, stop_filter, mission, levels, sliding_window)

def query_dhus_completeness_and_render(start_filter, stop_filter, mission, levels, sliding_window = None, filters = None, corrected_planned_imaging_uuid = None):

    info = query_dhus_completeness_events(start_filter, stop_filter, mission, levels, filters, corrected_planned_imaging_uuid)

    orbpre_events = s2vboa_functions.query_orbpre_events(query, current_app, start_filter, stop_filter, mission)

    reporting_start = stop_filter["date"]
    reporting_stop = start_filter["date"]

    route = "views/dhus_completeness/dhus_completeness.html"
    if corrected_planned_imaging_uuid != None:
        route = "views/dhus_completeness/dhus_completeness_datatake.html"
    # end if

    return render_template(route, info=info, orbpre_events=orbpre_events, request=request, reporting_start=reporting_start, reporting_stop=reporting_stop, levels=levels, sliding_window=sliding_window, filters=filters)

def query_dhus_completeness_events(start_filter, stop_filter, mission, levels, filters, corrected_planned_imaging_uuid = None):
    """
    Query planned acquisition events.
    """
    current_app.logger.debug("Query planned acquisition events")

    kwargs = {}

    if corrected_planned_imaging_uuid == None:
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
        kwargs["gauge_names"] = {"filter": "PLANNED_CUT_IMAGING_CORRECTION", "op": "=="}
    else:
        kwargs["event_uuids"] = {"filter": corrected_planned_imaging_uuid, "op": "=="}
    # end if
    
    ####
    # Query planned imagings
    ####
    planned_imaging_correction_events = query.get_events(**kwargs)
    planned_nominal_imaging_correction_events = [event for event in planned_imaging_correction_events for value in event.eventTexts if value.name == "imaging_mode" and value.value == "NOMINAL"]
    planned_imaging_correction_and_linked_events = query.get_linked_events(event_uuids = {"filter": [event.event_uuid for event in planned_nominal_imaging_correction_events], "op": "in"}, link_names = {"filter": ["TIME_CORRECTION"], "op": "in"}, return_prime_events = False)
    planned_imaging_events = query.get_linking_events_group_by_link_name(event_uuids = {"filter": [event.event_uuid for event in planned_imaging_correction_and_linked_events["linked_events"]], "op": "in"}, link_names = {"filter": ["PROCESSING_COMPLETENESS"], "op": "in"}, return_prime_events = False)

    info = {}
    info["imaging_correction_limit"] = planned_imaging_correction_events
    info["imaging_correction"] = planned_nominal_imaging_correction_events
    info["imaging"] = planned_imaging_correction_and_linked_events["linked_events"]

    info["processing_completeness"] = {}
    info["tls"] = {}

    parsed_levels = ["L1C", "L2A"]
    if levels != "ALL":
        parsed_levels = [levels]
    # end if
    
    for level in parsed_levels:
        info["processing_completeness"][level] = [event for event in planned_imaging_events["linking_events"]["PROCESSING_COMPLETENESS"] if event.gauge.name == "PLANNED_IMAGING_PROCESSING_COMPLETENESS_" + level]
        dss = [event.explicitRef.explicit_ref for event in info["processing_completeness"][level] if event.explicitRef != None]
        info["tls"][level] = query.get_linking_explicit_refs(explicit_refs = {"filter": dss, "op": "in"}, link_names = {"filter": ["TILE"], "op": "in"}, return_prime_explicit_refs = False)["linking_explicit_refs"]
    # end for

    return info
