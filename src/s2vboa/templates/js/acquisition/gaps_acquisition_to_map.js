
var acquisition_geometries_gaps = [
    {% for event in events %}
    {% set playback_validity_uuid = event.eventLinks|selectattr("name", "equalto", "PLAYBACK_VALIDITY")|map(attribute='event_uuid_link')|first %}
    {% set satellite = event.eventTexts|selectattr("name", "equalto", "satellite")|map(attribute='value')|first|string %}
    {% set orbit = event.eventDoubles|selectattr("name", "equalto", "downlink_orbit")|map(attribute='value')|first|int %}
    {% set station = event.eventTexts|selectattr("name", "equalto", "reception_station")|map(attribute='value')|first|string %}
    {% set playback_type = event.eventTexts|selectattr("name", "equalto", "playback_type")|map(attribute='value')|first|string %}
    {
        "id": "{{ event.event_uuid }}",
        "tooltip": create_acquisition_tooltip_text("{{ satellite }}", "{{ orbit }}", "{{ station }}", "<span class='bold-red'>GAPS</span>", "{{ event.start.isoformat() }}", "{{ event.stop.isoformat() }}", "{{ playback_type }}", "N/A", "{{ event.source.name }}", "{{ playback_validity_uuid }}", "/eboa_nav/query-event-links/{{ playback_validity_uuid }}"),
        "geometries": [
            {% for geometry in event.eventGeometries %}
            {{ geometry.to_wkt() }},
            {% endfor %}
        ],
        "style": {
            "stroke_color": "red",
            "fill_color": "rgba(255,0,0,0.3)",
        }
    },
    {% endfor %}
]
