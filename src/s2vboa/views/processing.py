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

bp = Blueprint("processing", __name__, url_prefix="/views")
query = Query()

@bp.route("/processing", methods=["GET", "POST"])
def show_processing():
    """
    Processing view for the Sentinel-2 mission.
    """
    current_app.logger.debug("Processing view")

    filters = {}
    filters["limit"] = ["100"]    
    if request.method == "POST":
        filters = request.form.to_dict(flat=False).copy()
    # end if
    filters["offset"] = [""]

    # Initialize reporting period (now - 2 days, now + 5 days)
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

    return query_processing_and_render(start_filter, stop_filter, mission, show, filters = filters)

@bp.route("/specific-processing/<string:isp_validity_uuid>")
def show_specific_processing(isp_validity_uuid):
    """
    Specific processing view for one playback related to the Sentinel-2 mission.
    """
    current_app.logger.debug("Specific processing view")

    # Get the events of the datastrip
    isp_validity = query.get_events(event_uuids = {"filter": isp_validity_uuid, "op": "=="})[0]
    
    filters = {}
    filters["limit"] = [""]
    filters["offset"] = [""]
    # Initialize reporting period (now - 2 days, now + 5 days)
    start_filter = {
        "date": isp_validity.stop.isoformat(),
        "op": "<="
    }
    stop_filter = {
        "date": isp_validity.start.isoformat(),
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

    return query_processing_and_render(start_filter, stop_filter, mission, show, filters = filters, isp_validity_uuid = isp_validity_uuid)

@bp.route("/processing-pages", methods=["POST"])
def query_processing_pages():
    """
    Processing view for the Sentinel-2 mission using pages.
    """
    current_app.logger.debug("Processing view using pages")
    filters = request.json

    mission = filters["mission"][0]
    show = filters["show"][0]
    mission = filters["mission"][0]

    # window_size is not used, here only for using the same API
    window_size = None
    start_filter, stop_filter = s2vboa_functions.get_start_stop_filters(query, current_app, request, window_size, mission, filters)

    return query_processing_and_render(start_filter, stop_filter, mission, show, filters = filters)

@bp.route("/sliding-processing-parameters", methods=["GET", "POST"])
def show_sliding_processing_parameters():
    """
    Processing sliding view for the Sentinel-2 mission.
    """
    current_app.logger.debug("Sliding acquistion view with parameters")

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

def query_processing_and_render(start_filter = None, stop_filter = None, mission = None, show = None, sliding_window = None, filters = None, isp_validity_uuid = None):

    processing_events = query_processing_events(start_filter, stop_filter, mission, filters, isp_validity_uuid)

    orbpre_events = s2vboa_functions.query_orbpre_events(query, current_app, start_filter, stop_filter, mission)

    reporting_start = stop_filter["date"]
    reporting_stop = start_filter["date"]
    
    template = "views/processing/processing.html"
    if isp_validity_uuid != None:
        template = "views/processing/specific_processing.html"
    # end if

    return render_template(template, processing_events=processing_events, orbpre_events=orbpre_events, show=show, reporting_start=reporting_start, reporting_stop=reporting_stop, sliding_window=sliding_window, filters = filters)

def query_processing_events(start_filter = None, stop_filter = None, mission = None, filters = None, isp_validity_uuid = None):
    """
    Query planned processing events.
    """
    current_app.logger.debug("Query planned processing events")

    kwargs_playback = {}
    
    if isp_validity_uuid == None:
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

        # Mission
        if mission:
            kwargs_playback["value_filters"] = [{"name": {"op": "==", "filter": "satellite"},
                                        "type": "text",
                                        "value": {"op": "like", "filter": mission}
                                    }]
        # end if
        kwargs_playback["gauge_names"] = {"filter": ["PLANNED_PLAYBACK_CORRECTION"], "op": "in"}

        # Specify the main query parameters
        kwargs_playback["link_names"] = {"filter": ["TIME_CORRECTION"], "op": "in"}
        
        # Query planned playbacks
        planned_playback_correction_events = query.get_linked_events(**kwargs_playback)
        planned_playback_events = query.get_linking_events_group_by_link_name(event_uuids = {"filter": [event.event_uuid for event in planned_playback_correction_events["linked_events"]], "op": "in"}, 
                                                                              link_names = {"filter": ["PLAYBACK_VALIDITY"], "op": "in"}, 
                                                                              return_prime_events = False)
    else:
        kwargs_playback["event_uuids"] = {"filter": isp_validity_uuid, "op": "=="}
        isp_validity_events = query.get_event_links(**kwargs_playback)
        planned_playback_events = query.get_linking_events_group_by_link_name(event_uuids = {"filter": [event.event_uuid for event in isp_validity_events], "op": "in"}, 
                                                                              link_names = {"filter": ["PLAYBACK_VALIDITY"], "op": "in"}, 
                                                                              return_prime_events = False)
    # end if
    
    events = {}
    events["playback_validity"] = [event for event in planned_playback_events["linking_events"]["PLAYBACK_VALIDITY"] if (event.gauge.name not in ("PLAYBACK_VALIDITY_3", "PLAYBACK_VALIDITY_2"))]
    events["playback_validity_channel_1"] = query.get_events(event_uuids = {"filter": [event.event_uuid for event in events["playback_validity"]], "op": "in"},
                                                             value_filters = [{"name": {"op": "==", "filter": "channel"},
                                                                              "type": "double",
                                                                              "value": {"op": "==", "filter": "1"}
                                                             }])
    
    # PLANNED_PLAYBACK channel 1 with a link to PLAYBACK_VALIDITY events not in PLAYBACK_VALIDITY_2 or PLAYBACK_VALIDITY_3 
    playback_validity_events = query.get_linked_events(event_uuids = {"filter": [event.event_uuid for event in events["playback_validity_channel_1"]], "op": "in"})
    events["playback"] = [event for event in playback_validity_events["linked_events"] if event.gauge.name == "PLANNED_PLAYBACK"]

    # ISP_VALIDITY, linked to the PLAYBACK_VALIDITY events with channel 1
    isp_validity_event_uuids = [link.event_uuid_link for event in events["playback_validity_channel_1"] for link in event.eventLinks if link.name == "ISP_VALIDITY"]
    unique_isp_validity_event_uuids = set(isp_validity_event_uuids)
    events["isp_validity_channel_1"] = query.get_events(event_uuids = {"filter": list(unique_isp_validity_event_uuids), "op": "in"})
    
    # ISP_VALIDITY_PROCESSING_COMPLETENESS_L[0_|1A|1B|1C|2A]_CHANNEL_1, linked to the ISP_VALIDITY events
    isp_validity_events_links = query.get_linked_events(event_uuids = {"filter": list(unique_isp_validity_event_uuids), "op": "in"})
    events["isp_validity_processing_completeness_channel_1"] = [event for event in isp_validity_events_links["linked_events"] if re.search("^ISP_VALIDITY_PROCESSING_COMPLETENESS.*CHANNEL_1$", event.gauge.name)]
    events["isp_validity_processing_completeness_l0_channel_1"] = [event for event in isp_validity_events_links["linked_events"] if event.gauge.name == "ISP_VALIDITY_PROCESSING_COMPLETENESS_L0_CHANNEL_1"]
    events["isp_validity_processing_completeness_l1a_channel_1"] = [event for event in isp_validity_events_links["linked_events"] if event.gauge.name == "ISP_VALIDITY_PROCESSING_COMPLETENESS_L1A_CHANNEL_1"]
    events["isp_validity_processing_completeness_l1b_channel_1"] = [event for event in isp_validity_events_links["linked_events"] if event.gauge.name == "ISP_VALIDITY_PROCESSING_COMPLETENESS_L1B_CHANNEL_1"]
    events["isp_validity_processing_completeness_l1c_channel_1"] = [event for event in isp_validity_events_links["linked_events"] if event.gauge.name == "ISP_VALIDITY_PROCESSING_COMPLETENESS_L1C_CHANNEL_1"]
    events["isp_validity_processing_completeness_l2a_channel_1"] = [event for event in isp_validity_events_links["linked_events"] if event.gauge.name == "ISP_VALIDITY_PROCESSING_COMPLETENESS_L2A_CHANNEL_1"]
    
    # SAD_DATA, linked to the ISP_VALIDITY events 
    events["sad_data"] = [event for event in isp_validity_events_links["linked_events"] if event.gauge.name == "SAD_DATA"]

    """ # Obtain processing status for each ISP_VALIDITY_PROCESSING_COMPLETENESS_L[0_|1A|1B|1C|2A]_CHANNEL_1 event
    events["isp_validity_processing_completeness_channel_1_with_processing_status"] = {}
    for isp_validity_event_uuid in list(unique_isp_validity_event_uuids):
        isp_validity_event_links = query.get_linked_events(event_uuids = {"filter": str(isp_validity_event_uuid), "op": "=="})
        isp_validity_processing_completeness_channel_1_events = [event for event in isp_validity_event_links["linked_events"] if re.search("^ISP_VALIDITY_PROCESSING_COMPLETENESS.*CHANNEL_1$", event.gauge.name)]
        isp_validity_processing_completeness_channel_1_event_not_missing = 0
        for isp_validity_processing_completeness_channel_1_event in isp_validity_processing_completeness_channel_1_events:
            for value in isp_validity_processing_completeness_channel_1_event.eventTexts:
                if value.name == "status" and value.value != "MISSING": isp_validity_processing_completeness_channel_1_event_not_missing += 1
            # end for
        # end for
        for isp_validity_processing_completeness_channel_1_event in isp_validity_processing_completeness_channel_1_events: 
            events["isp_validity_processing_completeness_channel_1_with_processing_status"][isp_validity_processing_completeness_channel_1_event.event_uuid] = [len(isp_validity_processing_completeness_channel_1_events), isp_validity_processing_completeness_channel_1_event_not_missing]
        # end for
    # end for """
    return events