"""
Module to allow change the footprint of an event when its timings changed

Written by DEIMOS Space S.L. (dibb)

module eboa
"""
# Import entities of the datamodel
from eboa.datamodel.events import EventObject, EventGeometry

# Import GEOalchemy entities
from geoalchemy2.shape import to_shape

# Import ingestion helpers
import s2boa.ingestions.functions as functions

def replicate_event_values(query, from_event_uuid, to_event_uuid, to_event, list_values_to_be_created):
    """
    Method to replicate the values associated to events that were overwritten partially by other events

    :param from_event_uuid: original event where to get the associated values from
    :type from_event_uuid: uuid
    :param to_event_uuid: new event to associate the values
    :type to_event_uuid: uuid
    :param list_values_to_be_created: list of values to be stored later inside the DDBB
    :type list_values_to_be_created: list
    """
    values = query.get_event_values(event_uuids = [str(from_event_uuid)])
    satellite_values = [value for value in values if value.name == "satellite"]
    geometric_values = [value for value in values if type(value) == EventGeometry]
    event = None
    satellite = None
    if len(geometric_values) > 0 and len(satellite_values):
        satellite = satellite_values[0].value
        event = {
            "start": to_event["start"].isoformat(),
            "stop": to_event["stop"].isoformat(),
            "values": [{
                "name": "details",
                "type": "object",
                "values": []
                }]
            }
    # end if
    for value in values:
        if not type(value) in list_values_to_be_created:
            list_values_to_be_created[type(value)] = []
        # end if
        value_to_insert = {"event_uuid": to_event_uuid,
                           "name": value.name,
                           "position": value.position,
                           "parent_level": value.parent_level,
                           "parent_position": value.parent_position
        }
        if not type(value) in (EventObject, EventGeometry):
            value_to_insert["value"] = value.value
        elif type(value) == EventGeometry:
            if event != None:
                functions.associate_footprints([event], satellite, return_polygon_format = True)
                value_to_insert["value"] = event["values"][0]["values"][0]["values"][0]["value"]
            else:
                value_to_insert["value"] = to_shape(value.value).wkt
            # end if
        # end if
        list_values_to_be_created[type(value)].append(value_to_insert)
    # end for

    return
