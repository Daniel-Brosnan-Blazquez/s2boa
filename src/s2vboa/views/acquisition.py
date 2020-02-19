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
    define_what_to_show_acquisition(show)

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

    return query_acquisition_and_render(start_filter, stop_filter, mission, show, filters = filters)

@bp.route("/specific-acquisition/<string:corrected_planned_playback_uuid>")
def show_specific_acquisition(corrected_planned_playback_uuid):
    """
    Specific acquisition view for one playback related to the Sentinel-2 mission.
    """
    current_app.logger.debug("Specific acquisition view")

    # Get the events of the playback
    corrected_planned_playback = query.get_events(event_uuids = {"filter": corrected_planned_playback_uuid, "op": "=="})[0]
    
    filters = {}
    filters["limit"] = [""]
    filters["offset"] = [""]
    # Initialize reporting period (now - 2 days, now + 5 days)
    start_filter = {
        "date": corrected_planned_playback.stop.isoformat(),
        "operator": "<="
    }
    stop_filter = {
        "date": corrected_planned_playback.start.isoformat(),
        "operator": ">="
    }
    mission = "S2_"

    show = {}
    define_what_to_show_acquisition(show)

    filters["start"] = [stop_filter["date"]]
    filters["stop"] = [start_filter["date"]]
    filters["mission"] = [mission]
    filters["show"] = [show]

    return query_acquisition_and_render(start_filter, stop_filter, mission, show, filters = filters, corrected_planned_playback_uuid = corrected_planned_playback_uuid)

@bp.route("/acquisition-pages", methods=["POST"])
def query_acquisition_pages():
    """
    Acquisition view for the Sentinel-2 mission using pages.
    """
    current_app.logger.debug("Acquisition view using pages")
    filters = request.json

    mission = filters["mission"][0]
    show = filters["show"][0]
    mission = filters["mission"][0]

    # window_size is not used, here only for using the same API
    window_size = None
    start_filter, stop_filter = s2vboa_functions.get_start_stop_filters(query, current_app, request, window_size, mission, filters)

    return query_acquisition_and_render(start_filter, stop_filter, mission, show, filters = filters)

@bp.route("/sliding-acquisition-parameters", methods=["GET", "POST"])
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

@bp.route("/sliding-acquisition", methods=["GET", "POST"])
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

def query_acquisition_and_render(start_filter = None, stop_filter = None, mission = None, show = None, sliding_window = None, filters = None, corrected_planned_playback_uuid = None):

    acquisition_events = query_acquisition_events(start_filter, stop_filter, mission, filters, corrected_planned_playback_uuid)

    reporting_start = stop_filter["date"]
    reporting_stop = start_filter["date"]

    route = "views/acquisition/acquisition.html"
    if corrected_planned_playback_uuid != None:
        route = "views/acquisition/specific_acquisition.html"
    # end if

    return render_template(route, acquisition_events=acquisition_events, request=request, show=show, reporting_start=reporting_start, reporting_stop=reporting_stop, sliding_window=sliding_window, filters = filters)

def query_acquisition_events(start_filter = None, stop_filter = None, mission = None, filters = None, corrected_planned_playback_uuid = None):
    """
    Query planned acquisition events.
    """
    current_app.logger.debug("Query planned acquisition events")

    kwargs_playback = {}

    if corrected_planned_playback_uuid == None:
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
        kwargs_playback["gauge_names"] = {"filter": ["PLANNED_PLAYBACK_CORRECTION"], "op": "in"}
    else:
        kwargs_playback["event_uuids"] = {"filter": corrected_planned_playback_uuid, "op": "=="}
    # end if

    # Specify the main query parameters
    kwargs_playback["link_names"] = {"filter": ["TIME_CORRECTION"], "op": "in"}
    
    ####
    # Query planned playbacks
    ####
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

    ## Get PLANNED_PLAYBACK events with gaps at reception
    incomplete_playbacks = [event for event in events["playback_completeness_channel"] for value in event.eventTexts if value.name == "status" and value.value == "INCOMPLETE"]
    incomplete_planned_playback_uuids = [link.event_uuid_link for event in incomplete_playbacks for link in event.eventLinks if link.name == "PLANNED_PLAYBACK"]
    unique_incomplete_planned_playback_uuids = set(incomplete_planned_playback_uuids)
    events["planned_playbacks_gaps_reception"] = [event for event in events["playback"] if event.event_uuid in unique_incomplete_planned_playback_uuids]

    ## Get PLAYBACK_GAP events
    # Get ISP_VALIDITY events assciated to the PLAYBACK_VALIDITY events
    playback_gap_event_uuids = [link.event_uuid_link for event in events["playback_validity"] for link in event.eventLinks if link.name == "PLAYBACK_GAP"]
    unique_playback_gap_event_uuids = set(playback_gap_event_uuids)
    # Get PLAYBACK_GAP events
    events["playback_gaps"] = query.get_events(event_uuids = {"filter": list(unique_playback_gap_event_uuids), "op": "in"})
    
    ## Get PLANNED_PLAYBACK events with gaps at MSI
    # Get ISP_VALIDITY events assciated to the PLAYBACK_VALIDITY events
    isp_validity_event_uuids = [link.event_uuid_link for event in events["playback_validity"] for link in event.eventLinks if link.name == "ISP_VALIDITY"]
    unique_isp_validity_event_uuids = set(isp_validity_event_uuids)
    # Get ISP_VALIDITY events with gaps
    isp_validity_events_with_gaps = query.get_events(event_uuids = {"filter": list(unique_isp_validity_event_uuids), "op": "in"},
                                                     value_filters = [{"name": {"op": "==", "filter": "status"},
                                                                       "type": "text",
                                                                       "value": {"op": "==", "filter": "INCOMPLETE"}
                                                     }])
    # Get PLAYBACK_VALIDITY events associated to the ISP_VALIDITY events with gaps at MSI
    playback_validity_with_msi_gaps_uuids = [link.event_uuid_link for event in isp_validity_events_with_gaps for link in event.eventLinks if link.name == "PLAYBACK_VALIDITY"]
    unique_playback_validity_with_msi_gaps_uuids = set(playback_validity_with_msi_gaps_uuids)
    playback_validities_with_msi_gaps = [event for event in events["playback_validity"] if event.event_uuid in unique_playback_validity_with_msi_gaps_uuids]
    planned_playback_with_msi_gaps_uuids = [link.event_uuid_link for event in playback_validities_with_msi_gaps for link in event.eventLinks if link.name == "PLANNED_PLAYBACK"]
    unique_planned_playback_with_msi_gaps_uuids = set(planned_playback_with_msi_gaps_uuids)
    # Get PLANNED_PLAYBACK events associated to the PLAYBACK_VALIDITY events with gaps at MSI
    events["planned_playbacks_gaps_msi"] = [event for event in events["playback"] if event.event_uuid in unique_planned_playback_with_msi_gaps_uuids]

    ## Get RAW_ISP_VALIDITY events with packet status != OK associated to the PLAYBACK_VALIDITY events
    unique_playback_validity_ers = set([event.explicitRef.explicit_ref for event in events["playback_validity"]])
    events["raw_isp_validity_events_with_packet_status_nok"] = query.get_events(explicit_refs = {"filter": list(unique_playback_validity_ers), "op": "in"},
                                                     value_filters = [{"name": {"op": "==", "filter": "packet_status"},
                                                                       "type": "text",
                                                                       "value": {"op": "!=", "filter": "OK"}
                                                     }])

    return events
