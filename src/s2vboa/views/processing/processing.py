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

# Import vboa security
from vboa.security import auth_required, roles_accepted

bp = Blueprint("processing", __name__, url_prefix="/views")
query = Query()

@bp.route("/processing", methods=["GET", "POST"])
@auth_required()
@roles_accepted("administrator", "service_administrator", "operator", "analyst", "operator_observer", "observer")
def show_processing():
    """
    Processing view for the Sentinel-2 mission.
    """
    current_app.logger.debug("Processing view")

    filters = {}
    filters["limit"] = ["20"]    
    if request.method == "POST":
        filters = request.form.to_dict(flat=False).copy()
    # end if
    filters["offset"] = [""]

    # Initialize reporting period (now , now + 1 day)
    start_filter = {
        "date": (datetime.datetime.now()).isoformat(),
        "op": "<="
    }
    stop_filter = {
        "date": (datetime.datetime.now() - datetime.timedelta(days=1)).isoformat(),
        "op": ">="
    }
    mission = "S2_"

    show = {}
    show["map"]=True
    show["timeline"]=True

    if request.method == "POST":
        if not "show_processing_map" in request.form:
            show["map"] = False
        else:
            show["map"]=True
        # end if
        if not "show_processing_timeline" in request.form:
            show["timeline"] = False
        else:
            show["timeline"]=True
        # end if
    # end if

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

    return query_processing_and_render(start_filter, stop_filter, mission, show, filters = filters)

@bp.route("/specific-processing/<string:planned_playback_uuid>")
@auth_required()
@roles_accepted("administrator", "service_administrator", "operator", "analyst", "operator_observer", "observer")
def show_specific_processing(planned_playback_uuid):
    """
    Specific processing view for one playback related to the Sentinel-2 mission.
    """
    current_app.logger.debug("Specific processing view")

    # Get the events of the planned playback
    planned_playback = query.get_events(event_uuids = {"filter": planned_playback_uuid, "op": "=="})[0]
    
    filters = {}
    filters["limit"] = [""]
    filters["offset"] = [""]
    # Initialize reporting period
    start_filter = {
        "date": planned_playback.stop.isoformat(),
        "op": "<="
    }
    stop_filter = {
        "date": planned_playback.start.isoformat(),
        "op": ">="
    }
    mission = "S2_"

    show = {}
    show["map"]=True
    show["timeline"]=True

    filters["start"] = [stop_filter["date"]]
    filters["stop"] = [start_filter["date"]]
    filters["mission"] = [mission]
    filters["show"] = [show]

    return query_processing_and_render(start_filter, stop_filter, mission, show, filters = filters, planned_playback_uuid = planned_playback_uuid)

@bp.route("/processing-pages", methods=["POST"])
@auth_required()
@roles_accepted("administrator", "service_administrator", "operator", "analyst", "operator_observer", "observer")
def query_processing_pages():
    """
    Processing view for the Sentinel-2 mission using pages.
    """
    current_app.logger.debug("Processing view using pages")
    filters = request.json

    mission = filters["mission"][0]
    show = filters["show"][0]

    # window_size is not used, here only for using the same API
    window_size = None
    start_filter, stop_filter = s2vboa_functions.get_start_stop_filters(query, current_app, request, window_size, mission, filters)

    return query_processing_and_render(start_filter, stop_filter, mission, show, filters = filters)

@bp.route("/sliding-processing-parameters", methods=["GET", "POST"])
@auth_required()
@roles_accepted("administrator", "service_administrator", "operator", "analyst", "operator_observer", "observer")
def show_sliding_processing_parameters():
    """
    Processing sliding view for the Sentinel-2 mission.
    """
    current_app.logger.debug("Sliding processing view with parameters")

    window_delay = float(request.args.get("window_delay"))
    window_size = float(request.args.get("window_size"))
    repeat_cycle = float(request.args.get("repeat_cycle"))
    mission = request.args.get("mission")

    show = {}
    show["map"]=True
    show["timeline"]=True

    if request.method == "POST":
        if not "show_processing_map" in request.form:
            show["map"] = False
        else:
            show["map"]=True
        # end if
        if not "show_processing_timeline" in request.form:
            show["timeline"] = False
        else:
            show["timeline"]=True
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

    return query_processing_and_render(start_filter, stop_filter, mission, show, sliding_window)

@bp.route("/sliding-processing", methods=["GET", "POST"])
@auth_required()
@roles_accepted("administrator", "service_administrator", "operator", "analyst", "operator_observer", "observer")
def show_sliding_processing():
    """
    Processing sliding view for the Sentinel-2 mission.
    """
    current_app.logger.debug("Sliding processing view")

    window_delay=0
    window_size=1
    repeat_cycle=1

    mission = "S2_"

    show = {}
    show["map"]=True
    show["timeline"]=True

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

    return query_processing_and_render(start_filter, stop_filter, mission, show, sliding_window)

def query_processing_and_render(start_filter = None, stop_filter = None, mission = None, show = None, sliding_window = None, filters = None, planned_playback_uuid = None):

    processing_events = query_processing_events(start_filter, stop_filter, mission, filters, planned_playback_uuid)

    orbpre_events = s2vboa_functions.query_orbpre_events(query, current_app, start_filter, stop_filter, mission)

    reporting_start = stop_filter["date"]
    reporting_stop = start_filter["date"]
    
    template = "views/processing/processing.html"
    if planned_playback_uuid != None:
        template = "views/processing/specific_processing.html"
    # end if

    return render_template(template, processing_events=processing_events, orbpre_events=orbpre_events, show=show, reporting_start=reporting_start, reporting_stop=reporting_stop, sliding_window=sliding_window, filters = filters)

def query_processing_events(start_filter = None, stop_filter = None, mission = None, filters = None, planned_playback_uuid = None):
    """
    Query planned processing events.
    """
    current_app.logger.debug("Query planned processing events")

    kwargs_playback = {}
    events = {}
    
    if planned_playback_uuid == None:
        # Set offset and limit for the query
        if filters and "offset" in filters and filters["offset"][0] != "":
            kwargs_playback["offset"] = filters["offset"][0]
        # end if
        if filters and "limit" in filters and filters["limit"][0] != "":
            kwargs_playback["limit"] = filters["limit"][0]
        # end if

        # Set order by reception_time descending
        kwargs_playback["order_by"] = {"field": "start", "descending": True}

        # Start filter
        if start_filter:
            kwargs_playback["start_filters"] = [{"date": start_filter["date"], "op": start_filter["op"]}]
        # end if

        # Stop filter
        if stop_filter:
            kwargs_playback["stop_filters"] = [{"date": stop_filter["date"], "op": stop_filter["op"]}]
        # end if

        # Playback type
        kwargs_playback["value_filters"] = [{"name": {"op": "==", "filter": "playback_type"},
                                             "type": "text",
                                             "value": {"op": "in", "filter": ["NOMINAL", "REGULAR", "RT"]}
                                             }]
        
        kwargs_playback["gauge_names"] = {"filter": ["PLANNED_PLAYBACK_CORRECTION"], "op": "in"}
 
        # Query planned playbacks
        planned_playback_correction_events = query.get_events(**kwargs_playback)

        planned_playback_correction_events_filtered_by_satellite = query.get_linked_events(event_uuids = {"filter": [event.event_uuid for event in planned_playback_correction_events], "op": "in"},
                                                                                               link_names = {"filter": "TIME_CORRECTION", "op": "=="},
                                                                                               value_filters = [{"name": {"op": "==", "filter": "satellite"},
                                                                                                                 "type": "text",
                                                                                                                 "value": {"op": "like", "filter": mission}}
                                            ])
        planned_playback_events = query.get_linking_events_group_by_link_name(event_uuids = {"filter": [event.event_uuid for event in planned_playback_correction_events_filtered_by_satellite["linked_events"]], "op": "in"}, 
                                                                              link_names = {"filter": ["PLAYBACK_VALIDITY"], "op": "in"}, 
                                                                              return_prime_events = False)
        events["playback_validity_channel_2"] = [event for event in planned_playback_events["linking_events"]["PLAYBACK_VALIDITY"] for value in event.eventDoubles if (value.name == "channel" and value.value == 2)]
    else:
        events_linking_to_planned_playback_events = query.get_linking_events_group_by_link_name(event_uuids = {"filter": planned_playback_uuid, "op": "=="},
                                                                    link_names = {"filter": ["PLAYBACK_VALIDITY", "TIME_CORRECTION"], "op": "in"}, 
                                                                    return_prime_events = False)
        events["planned_playback_correction"] = events_linking_to_planned_playback_events["linking_events"]["TIME_CORRECTION"]
        events["playback_validity_channel_2"] = [event for event in events_linking_to_planned_playback_events["linking_events"]["PLAYBACK_VALIDITY"] for value in event.eventDoubles if (value.name == "channel" and value.value == 2)]
    # end if

    # PLANNED_PLAYBACK channel 2 with a link to PLAYBACK_VALIDITY events not in PLAYBACK_VALIDITY_2 or PLAYBACK_VALIDITY_3 
    playback_validity_events = query.get_linked_events(event_uuids = {"filter": [event.event_uuid for event in events["playback_validity_channel_2"]], "op": "in"})
    events["playback"] = [event for event in playback_validity_events["linked_events"] if event.gauge.name == "PLANNED_PLAYBACK"]

    # ISP_VALIDITY, linked to the PLAYBACK_VALIDITY events with channel 2
    isp_validity_event_uuids = [link.event_uuid_link for event in events["playback_validity_channel_2"] for link in event.eventLinks if link.name == "ISP_VALIDITY"]
    unique_isp_validity_event_uuids = set(isp_validity_event_uuids)
    events["isp_validity_channel_2"] = query.get_events(event_uuids = {"filter": list(unique_isp_validity_event_uuids), "op": "in"})
    
    # ISP_VALIDITY_PROCESSING_COMPLETENESS_L[0_|1A|1B|1C|2A]_channel_2, linked to the ISP_VALIDITY events
    isp_validity_events_links = query.get_linking_events(event_uuids = {"filter": list(unique_isp_validity_event_uuids), "op": "in"},
                                                        link_names = {"filter": ["PROCESSING_COMPLETENESS", "SAD_DATA"], "op": "in"}, 
                                                        return_prime_events = False)
    
    events["isp_validity_processing_completeness_channel_2"] = [event for event in isp_validity_events_links["linking_events"] if re.search("^ISP_VALIDITY_PROCESSING_COMPLETENESS.*CHANNEL_2$", event.gauge.name)]
    events["isp_validity_processing_completeness_l0_channel_2"] = [event for event in isp_validity_events_links["linking_events"] if event.gauge.name == "ISP_VALIDITY_PROCESSING_COMPLETENESS_L0_CHANNEL_2"]
    events["isp_validity_processing_completeness_l1a_channel_2"] = [event for event in isp_validity_events_links["linking_events"] if event.gauge.name == "ISP_VALIDITY_PROCESSING_COMPLETENESS_L1A_CHANNEL_2"]
    events["isp_validity_processing_completeness_l1b_channel_2"] = [event for event in isp_validity_events_links["linking_events"] if event.gauge.name == "ISP_VALIDITY_PROCESSING_COMPLETENESS_L1B_CHANNEL_2"]
    events["isp_validity_processing_completeness_l1c_channel_2"] = [event for event in isp_validity_events_links["linking_events"] if event.gauge.name == "ISP_VALIDITY_PROCESSING_COMPLETENESS_L1C_CHANNEL_2"]
    events["isp_validity_processing_completeness_l2a_channel_2"] = [event for event in isp_validity_events_links["linking_events"] if event.gauge.name == "ISP_VALIDITY_PROCESSING_COMPLETENESS_L2A_CHANNEL_2"]
    
    # SAD_DATA, linked to the ISP_VALIDITY events 
    events["sad_data"] = [event for event in isp_validity_events_links["linking_events"] if event.gauge.name == "SAD_DATA"]

    # PROCESSING_VALIDITY for the start stop values used in tables
    isp_validity_processing_completeness_channel_2_events_links = query.get_linking_events(event_uuids = {"filter": [event.event_uuid for event in events["isp_validity_processing_completeness_channel_2"]], "op": "in"},
                                                                                          link_names = {"filter": "PROCESSING_VALIDITY", "op": "=="}, 
                                                                                          return_prime_events = False)
    
    events["processing_validity"] = [event for event in isp_validity_processing_completeness_channel_2_events_links["linking_events"] if event.gauge.name == "PROCESSING_VALIDITY"]
    
    return events
