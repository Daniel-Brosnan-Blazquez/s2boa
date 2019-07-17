"""
Views functions definition

Written by DEIMOS Space S.L. (dibb)

module s2vboa
"""
# Import python utilities
import sys
import json
import datetime
from dateutil import parser

def query_orbpre_events(query, current_app, start_filter = None, stop_filter = None, mission = None):
    """
    Query predicted orbit events.
    """

    kwargs = {}

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
        kwargs["value_filters"] = [{"name": {"op": "like", "str": "satellite"},
                                    "type": "text",
                                    "value": {"op": "like", "value": mission}
                                }]
    # end if

    ####
    # Query predicted orbit events
    ####
    kwargs["gauge_names"] = {"filter": ["ORBIT_PREDICTION"], "op": "in"}
    events = query.get_events(**kwargs)

    return events

def get_start_stop_filters(query, current_app, request, window_size, mission):

    start_filter = None
    stop_filter = None

    if request.method == "POST":

        if request.form["start"] != "":
            stop_filter = {
                "date": request.form["start"],
                "operator": ">="
            }
            if request.form["stop"] == "":
                start_filter = {
                    "date": (parser.parse(request.form["start"]) + datetime.timedelta(days=window_size)).isoformat(),
                    "operator": "<="
                }
            # end if
        elif request.form["start_orbit"] != "":
            orbpre_events = query.get_events(gauge_names = {"filter": ["ORBIT_PREDICTION"], "op": "in"},
                                            value_filters = [{"name": {"op": "like", "str": "orbit"},
                                                              "type": "double",
                                                              "value": {"op": "==", "value": request.form["start_orbit"]}
                                                          },
                                                             {"name": {"op": "like", "str": "satellite"},
                                                              "type": "text",
                                                              "value": {"op": "like", "value": mission}
                                                          }])

            if len(orbpre_events) > 0:
                orbpre_event = orbpre_events[0]
                stop_filter = {
                    "date": orbpre_event.start.isoformat(),
                    "operator": ">="
                }
            # end if
            if len(orbpre_events) > 0 and request.form["stop_orbit"] == "":
                start_filter = {
                    "date": (orbpre_event.start + datetime.timedelta(days=window_size)).isoformat(),
                    "operator": "<="
                }
            # end if
        # end if

        if request.form["stop"] != "":
            start_filter = {
                "date": request.form["stop"],
                "operator": "<="
            }
            if request.form["start"] == "":
                stop_filter = {
                    "date": (parser.parse(request.form["stop"]) - datetime.timedelta(days=window_size)).isoformat(),
                    "operator": ">="
                }
            # end if
        elif request.form["stop_orbit"] != "":
            orbpre_events = query.get_events(gauge_names = {"filter": ["ORBIT_PREDICTION"], "op": "in"},
                                            value_filters = [{"name": {"op": "like", "str": "orbit"},
                                                              "type": "double",
                                                              "value": {"op": "==", "value": request.form["stop_orbit"]}
                                                          },
                                                             {"name": {"op": "like", "str": "satellite"},
                                                              "type": "text",
                                                              "value": {"op": "like", "value": mission}
                                                          }])

            if len(orbpre_events) > 0:
                orbpre_event = orbpre_events[0]
                start_filter = {
                    "date": orbpre_event.stop.isoformat(),
                    "operator": "<="
                }
            # end if
            if len(orbpre_events) > 0 and request.form["start_orbit"] == "":
                stop_filter = {
                    "date": (orbpre_event.stop - datetime.timedelta(days=window_size)).isoformat(),
                    "operator": ">="
                }
            # end if
        # end if

    # end if

    return start_filter, stop_filter
