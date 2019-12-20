
var playback_geometries = [
    {% for playback in events %}
    {% set correction_uuid = playback.eventLinks|selectattr("name", "equalto", "TIME_CORRECTION")|map(attribute='event_uuid_link')|first %}
    {% if correction_uuid %}
    {% set event = planning_events["playback"]["linked_events"]|selectattr("event_uuid", "equalto", correction_uuid)|first %}
    {% else %}
    {% set event = playback %}
    {% endif %}
    {% set satellite = playback.eventTexts|selectattr("name", "equalto", "satellite")|map(attribute='value')|first|string %}
    {% set orbit = playback.eventDoubles|selectattr("name", "equalto", "start_orbit")|map(attribute='value')|first|int %}
    {% set station = playback.eventTexts|selectattr("name", "equalto", "station")|map(attribute='value')|first|string %}
    {% set playback_type = playback.eventTexts|selectattr("name", "equalto", "playback_type")|map(attribute='value')|first|string %}
    {% set playback_mean = playback.eventTexts|selectattr("name", "equalto", "playback_mean")|map(attribute='value')|first|string %}
    {
        "id": "{{ playback.event_uuid }}",
        "tooltip": create_playback_tooltip_text("{{ satellite }}", "{{ orbit }}", "{{ station }}", "{{ event.start.isoformat() }}", "{{ event.stop.isoformat() }}", "{{ playback_type }}", "{{ playback_mean }}", "{{ playback.source.name }}", "{{ playback.event_uuid }}", "/eboa_nav/query-event-links/{{ playback.event_uuid }}"),
        "geometries": [
            {% for geometry in event.eventGeometries %}
            {{ geometry.to_wkt() }},
            {% endfor %}
        ]
    },
    {% endfor %}
]
