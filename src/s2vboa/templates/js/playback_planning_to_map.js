
var playback_geometries = [
    {% for event in events %}
    {% set original_playback_uuid = event.eventLinks|selectattr("name", "equalto", "PLANNED_EVENT")|map(attribute='event_uuid_link')|first %}
    {% set original_playback = planning_events["playback"]["linked_events"]|selectattr("event_uuid", "equalto", original_playback_uuid)|first %}
    {% set satellite = event.eventTexts|selectattr("name", "equalto", "satellite")|map(attribute='value')|first|string %}
    {% set orbit = event.eventDoubles|selectattr("name", "equalto", "start_orbit")|map(attribute='value')|first|int %}
    {% set station = original_playback.eventTexts|selectattr("name", "equalto", "station")|map(attribute='value')|first|string %}
    {% set playback_type = event.eventTexts|selectattr("name", "equalto", "playback_type")|map(attribute='value')|first|string %}
    {% set playback_mean = event.eventTexts|selectattr("name", "equalto", "playback_mean")|map(attribute='value')|first|string %}
    {
        "id": "{{ original_playback.event_uuid }}",
        "tooltip": create_playback_tooltip_text("{{ satellite }}", "{{ orbit }}", "{{ station }}", "{{ event.start.isoformat() }}", "{{ event.stop.isoformat() }}", "{{ playback_type }}", "{{ playback_mean }}", "{{ original_playback.source.name }}", "{{ original_playback.event_uuid }}", "/eboa_nav/query-event-links/{{ original_playback.event_uuid }}"),
        "geometries": [
            {% for geometry in event.eventGeometries %}
            {{ geometry.to_wkt() }},
            {% endfor %}
        ]
    },
    {% endfor %}
]
