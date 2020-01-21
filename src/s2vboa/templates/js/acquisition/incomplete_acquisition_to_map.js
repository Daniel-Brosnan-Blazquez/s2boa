
var acquisition_geometries_incomplete = [
    {% for event in events %}
    {% set original_playback_uuids = event.eventLinks|selectattr("name", "equalto", "PLANNED_PLAYBACK")|map(attribute='event_uuid_link')|list %}
    {% if not original_playback_uuids %}
    {% set original_playback_uuid = event.eventLinks|selectattr("name", "equalto", "PLANNED_EVENT")|map(attribute='event_uuid_link')|list %}
    {% endif %}
    {% set original_playback_uuid = original_playback_uuids|first %}
    {% set original_playback = acquisition_events["playback"]|selectattr("event_uuid", "in", original_playback_uuids)|first %}
    {% set satellite = original_playback.eventTexts|selectattr("name", "equalto", "satellite")|map(attribute='value')|first|string %}
    {% set orbit = original_playback.eventDoubles|selectattr("name", "equalto", "start_orbit")|map(attribute='value')|first|int %}
    {% set station = original_playback.eventTexts|selectattr("name", "equalto", "station")|map(attribute='value')|first|string %}
    {% set playback_type = original_playback.eventTexts|selectattr("name", "equalto", "playback_type")|map(attribute='value')|first|string %}
    {% set playback_mean = original_playback.eventTexts|selectattr("name", "equalto", "playback_mean")|map(attribute='value')|first|string %}
    {% set status = event.eventTexts|selectattr("name", "equalto", "status")|map(attribute='value')|first|string %}
    {
        "id": "{{ event.event_uuid }}",
        "tooltip": create_acquisition_tooltip_text("{{ satellite }}", "{{ orbit }}", "{{ station }}", "<span class='bold-orange'>INCOMPLETE</span>", "{{ event.start.isoformat() }}", "{{ event.stop.isoformat() }}", "{{ playback_type }}", "{{ playback_mean }}", "{{ original_playback.source.name }}", "{{ original_playback.event_uuid }}", "/eboa_nav/query-event-links/{{ original_playback.event_uuid }}"),
        "geometries": [
            {% for geometry in event.eventGeometries %}
            {{ geometry.to_wkt() }},
            {% endfor %}
        ],
        "style": {
            "stroke_color": "orange",
            "fill_color": "rgba(255,140,0,0.3)",
        }
    },
    {% endfor %}
]
