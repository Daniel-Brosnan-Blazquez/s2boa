"""
Detailed processing timeliness view for s2boa

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

bp = Blueprint("detailed_processing_timeliness", __name__, url_prefix="/views")
query = Query()

@bp.route("/detailed-processing-timeliness", methods=["GET", "POST"])
def show_detailed_processing_timeliness():
    """
    Detailed Processing Timeliness view for the Sentinel-2 mission.
    """
    current_app.logger.debug("Detailed Processing Timeliness view")

    kwargs = {}
    
    filters = {}
    filters["limit"] = ["10"]
    if request.method == "POST":
        filters = request.form.to_dict(flat=False).copy()
    # end if
    
    # Default query parameters (now - 6 hours, now - 3 hours, S2_)
    if not("datastrip" in filters) or ("datastrip" in filters and filters["datastrip"][0] == ""):
        kwargs["generation_start_filter"] = {
            "date": (datetime.datetime.now() - datetime.timedelta(hours=3)).isoformat(),
            "op": "<="
        }
        kwargs["generation_stop_filter"] = {
            "date": (datetime.datetime.now() - datetime.timedelta(hours=6)).isoformat(),
            "op": ">="
        }
    # end if
    mission = "S2_"
    
    window_size = 0.125
    if request.method == "POST":

        if request.form["mission"] != "":
            mission = request.form["mission"]
        # end if

        # Sensing start
        if filters["sensing_start"][0] != "":
            kwargs["sensing_stop_filter"] = {
                "date": filters["sensing_start"][0],
                "op": ">="
            }
            if filters["sensing_stop"][0] == "":
                kwargs["sensing_start_filter"] = {
                    "date": (parser.parse(filters["sensing_start"][0]) + datetime.timedelta(days=window_size)).isoformat(),
                    "op": "<="
                }
            # end if
        elif filters["sensing_start_orbit"][0] != "":
            orbpre_events = query.get_events(gauge_names = {"filter": ["ORBIT_PREDICTION"], "op": "in"},
                                            value_filters = [{"name": {"op": "==", "filter": "orbit"},
                                                              "type": "double",
                                                              "value": {"op": "==", "filter": filters["sensing_start_orbit"][0]}
                                                          },
                                                             {"name": {"op": "==", "filter": "satellite"},
                                                              "type": "text",
                                                              "value": {"op": "like", "filter": mission}
                                                          }])

            if len(orbpre_events) > 0:
                orbpre_event = orbpre_events[0]
                kwargs["sensing_stop_filter"] = {
                    "date": orbpre_event.start.isoformat(),
                    "op": ">="
                }
            # end if
            if len(orbpre_events) > 0 and filters["sensing_stop_orbit"][0] == "":
                kwargs["sensing_start_filter"] = {
                    "date": (orbpre_event.start + datetime.timedelta(days=window_size)).isoformat(),
                    "op": "<="
                }
            # end if
        # end if

        # Generation start
        if filters["generation_start"][0] != "":
            kwargs["generation_stop_filter"] = {
                "date": filters["generation_start"][0],
                "op": ">="
            }
            if filters["generation_stop"][0] == "":
                kwargs["generation_start_filter"] = {
                    "date": (parser.parse(filters["generation_start"][0]) + datetime.timedelta(days=window_size)).isoformat(),
                    "op": "<="
                }
            # end if
        # end if
        
        # Sensing stop
        if filters["sensing_stop"][0] != "":
            kwargs["sensing_start_filter"] = {
                "date": filters["sensing_stop"][0],
                "op": "<="
            }
            if filters["sensing_start"][0] == "":
                kwargs["sensing_stop_filter"] = {
                    "date": (parser.parse(filters["sensing_stop"][0]) - datetime.timedelta(days=window_size)).isoformat(),
                    "op": ">="
                }
            # end if
        elif filters["sensing_stop_orbit"][0] != "":
            orbpre_events = query.get_events(gauge_names = {"filter": ["ORBIT_PREDICTION"], "op": "in"},
                                            value_filters = [{"name": {"op": "==", "filter": "orbit"},
                                                              "type": "double",
                                                              "value": {"op": "==", "filter": filters["sensing_stop_orbit"][0]}
                                                          },
                                                             {"name": {"op": "==", "filter": "satellite"},
                                                              "type": "text",
                                                              "value": {"op": "like", "filter": mission}
                                                          }])

            if len(orbpre_events) > 0:
                orbpre_event = orbpre_events[0]
                kwargs["sensing_start_filter"] = {
                    "date": orbpre_event.stop.isoformat(),
                    "op": "<="
                }
            # end if
            if len(orbpre_events) > 0 and filters["sensing_start_orbit"][0] == "":
                kwargs["sensing_stop_filter"] = {
                    "date": (orbpre_event.stop - datetime.timedelta(days=window_size)).isoformat(),
                    "op": ">="
                }
            # end if
        # end if

        # Generation stop
        if filters["generation_stop"][0] != "":
            kwargs["generation_start_filter"] = {
                "date": filters["generation_stop"][0],
                "op": "<="
            }
            if filters["generation_start"][0] == "":
                kwargs["generation_stop_filter"] = {
                    "date": (parser.parse(filters["generation_stop"][0]) - datetime.timedelta(days=window_size)).isoformat(),
                    "op": ">="
                }
            # end if
        # end if

        # Datastrips
        if filters["datastrip"][0] != "":
            kwargs["datastrips"] = {"filter": filters["datastrip"][0], "op": filters["datastrip_operator"][0]}
        # end if
        elif "datastrips" in filters and filters["datastrips"][0] != "":
            op="notin"
            if not "datastrip_notin_check" in filters:
                op="in"
            # end if
            kwargs["datastrips"] = {"filter": [], "op": op}
            i = 0
            for datastrip in filters["datastrips"]:
                kwargs["datastrips"]["filter"].append(datastrip)
                i+=1
            # end for
        # end if

    # end if
    filters["offset"] = [""]
    
    kwargs["mission"] = mission
    
    return query_detailed_processing_timeliness_and_render(kwargs = kwargs, filters = filters)

def query_detailed_processing_timeliness_and_render(kwargs = None, filters = None):

    # Set offset and limit for the query
    offset = None
    if filters and "offset" in filters and filters["offset"][0] != "":
        offset = filters["offset"][0]
    # end if
    limit = None
    if filters and "limit" in filters and filters["limit"][0] != "":
        limit = filters["limit"][0]
    # end if

    if "sensing_start_filter" in kwargs or "sensing_stop_filter" in kwargs or ("datastrips" in kwargs and not "generation_start_filter" in kwargs):
        #############################
        # Query processing validity #
        #############################
        query_kwargs = {}
        if "sensing_start_filter" in kwargs:
            query_kwargs["start_filters"] = [kwargs["sensing_start_filter"]]
        # end if

        if "sensing_stop_filter" in kwargs:
            query_kwargs["stop_filters"] = [kwargs["sensing_stop_filter"]]
        # end if

        if "datastrips" in kwargs:
            query_kwargs["explicit_refs"] = kwargs["datastrips"]
        # end if

        query_kwargs["gauge_names"] = {"filter": "PROCESSING_VALIDITY", "op": "=="}
        query_kwargs["value_filters"] = [{"name": {"op": "==", "filter": "satellite"},
                                    "type": "text",
                                    "value": {"op": "like", "filter": kwargs["mission"]}
                                    }]

        query_kwargs["limit"] = limit
        query_kwargs["offset"] = offset

        processing_validity_events = query.get_events(**query_kwargs)
        datastrips = [event.explicitRef for event in processing_validity_events]
        timeliness_events = query.get_events(gauge_names = {"filter": "TIMELINESS", "op": "=="},
                                             explicit_refs = {"filter": [er.explicit_ref for er in datastrips], "op": "in"})
    elif "generation_start_filter" in kwargs or "generation_stop_filter" in kwargs:
        ####################
        # Query timeliness #
        ####################
        query_kwargs = {}
        if "generation_start_filter" in kwargs:
            query_kwargs["start_filters"] = [kwargs["generation_start_filter"]]
        # end if

        if "generation_stop_filter" in kwargs:
            query_kwargs["stop_filters"] = [kwargs["generation_stop_filter"]]
        # end if

        if "datastrips" in kwargs:
            query_kwargs["explicit_refs"] = kwargs["datastrips"]
        # end if

        query_kwargs["gauge_names"] = {"filter": "TIMELINESS", "op": "=="}
        query_kwargs["gauge_systems"] = {"filter": "", "op": "!="}
        query_kwargs["value_filters"] = [{"name": {"op": "==", "filter": "satellite"},
                                    "type": "text",
                                    "value": {"op": "like", "filter": kwargs["mission"]}
                                    }]

        query_kwargs["limit"] = limit
        query_kwargs["offset"] = offset

        timeliness_events = query.get_events(**query_kwargs)
        datastrips = [event.explicitRef for event in timeliness_events]
        processing_validity_events = query.get_events(gauge_names = {"filter": "PROCESSING_VALIDITY", "op": "=="},
                                             explicit_refs = {"filter": [er.explicit_ref for er in datastrips], "op": "in"})

    # end if

    step_info_events = query.get_events(gauge_names = {"filter": "STEP_INFO", "op": "=="},
                                             explicit_refs = {"filter": [er.explicit_ref for er in datastrips], "op": "in"})

    if "sensing_start_filter" in kwargs:
        start_filter = kwargs["sensing_start_filter"]
    elif "generation_start_filter" in kwargs:
        start_filter = kwargs["generation_start_filter"]
    elif "datastrips" in kwargs:
        if len(processing_validity_events) > 0:
            sorted_processing_validity_events = processing_validity_events.copy()
            sorted_processing_validity_events.sort(key=lambda x: x.start)
            start_filter = {
                "date": sorted_processing_validity_events[-1].stop.isoformat(),
                "op": "<="
            }
            stop_filter = {
                "date": sorted_processing_validity_events[0].start.isoformat(),
                "op": ">="
            }
        else:
            start_filter = {
                "date": (datetime.datetime.now() - datetime.timedelta(hours=3)).isoformat(),
                "op": "<="
            }
            stop_filter = {
                "date": (datetime.datetime.now() - datetime.timedelta(hours=6)).isoformat(),
                "op": ">="
            }
    # end if

    if "sensing_stop_filter" in kwargs:
        stop_filter = kwargs["sensing_stop_filter"]
    elif "generation_stop_filter" in kwargs:
        stop_filter = kwargs["generation_stop_filter"]
    # end if
    
    orbpre_events = s2vboa_functions.query_orbpre_events(query, current_app, start_filter, stop_filter, kwargs["mission"])

    reporting_start = stop_filter["date"]
    reporting_stop = start_filter["date"]
    
    events = {}
    events["timeliness"] = timeliness_events
    events["processing_validity"] = processing_validity_events
    events["step_info"] = step_info_events

    route = "views/detailed_processing_timeliness/detailed_processing_timeliness.html"

    return render_template(route, events = events, datastrips = datastrips, orbpre_events=orbpre_events, request=request, reporting_start=reporting_start, reporting_stop=reporting_stop, filters = filters)
