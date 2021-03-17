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

def query_orbpre_events(query, current_app, start_filter = None, stop_filter = None, mission = None, limit = None, offset = None, descending = False):
    """
    Query predicted orbit events.
    """

    kwargs = {}

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

    # Offset
    if offset != None:
        kwargs["offset"] = offset
    # end if

    # Limit
    if limit != None:
        kwargs["limit"] = limit
    # end if

    kwargs["order_by"] = {"field": "start", "descending": descending}
    
    ####
    # Query predicted orbit events
    ####
    kwargs["gauge_names"] = {"filter": ["ORBIT_PREDICTION"], "op": "in"}
    events = query.get_events(**kwargs)

    return events

def get_start_stop_filters(query, current_app, request, window_size, mission, filters):

    start_filter = None
    stop_filter = None

    if request.method == "POST":

        if filters["start"][0] != "":
            stop_filter = {
                "date": filters["start"][0],
                "op": ">="
            }
            if filters["stop"][0] == "":
                start_filter = {
                    "date": (parser.parse(filters["start"][0]) + datetime.timedelta(days=window_size)).isoformat(),
                    "op": "<="
                }
            # end if
        elif filters["start_orbit"][0] != "":
            orbpre_events = query.get_events(gauge_names = {"filter": ["ORBIT_PREDICTION"], "op": "in"},
                                            value_filters = [{"name": {"op": "==", "filter": "orbit"},
                                                              "type": "double",
                                                              "value": {"op": "==", "filter": filters["start_orbit"][0]}
                                                          },
                                                             {"name": {"op": "==", "filter": "satellite"},
                                                              "type": "text",
                                                              "value": {"op": "like", "filter": mission}
                                                          }])

            orbpre_events.sort(key=lambda x: x.start)
            if len(orbpre_events) > 0:
                orbpre_event = orbpre_events[0]
                stop_filter = {
                    "date": orbpre_event.start.isoformat(),
                    "op": ">="
                }
            # end if
            if len(orbpre_events) > 0 and filters["stop_orbit"][0] == "":
                start_filter = {
                    "date": (orbpre_event.start + datetime.timedelta(days=window_size)).isoformat(),
                    "op": "<="
                }
            # end if
        # end if

        if filters["stop"][0] != "":
            start_filter = {
                "date": filters["stop"][0],
                "op": "<="
            }
            if filters["start"][0] == "":
                stop_filter = {
                    "date": (parser.parse(filters["stop"][0]) - datetime.timedelta(days=window_size)).isoformat(),
                    "op": ">="
                }
            # end if
        elif filters["stop_orbit"][0] != "":
            orbpre_events = query.get_events(gauge_names = {"filter": ["ORBIT_PREDICTION"], "op": "in"},
                                            value_filters = [{"name": {"op": "==", "filter": "orbit"},
                                                              "type": "double",
                                                              "value": {"op": "==", "filter": filters["stop_orbit"][0]}
                                                          },
                                                             {"name": {"op": "==", "filter": "satellite"},
                                                              "type": "text",
                                                              "value": {"op": "like", "filter": mission}
                                                          }])

            orbpre_events.sort(key=lambda x: x.start)
            if len(orbpre_events) > 0:
                orbpre_event = orbpre_events[-1]
                start_filter = {
                    "date": orbpre_event.stop.isoformat(),
                    "op": "<="
                }
            # end if
            if len(orbpre_events) > 0 and filters["start_orbit"][0] == "":
                stop_filter = {
                    "date": (orbpre_event.stop - datetime.timedelta(days=window_size)).isoformat(),
                    "op": ">="
                }
            # end if
        # end if

    # end if

    return start_filter, stop_filter
