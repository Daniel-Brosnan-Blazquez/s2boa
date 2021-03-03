
var acquisition_geometries_received = [
    {% for event in events %}
    {% set original_playback_uuids = event.eventLinks|selectattr("name", "equalto", "PLANNED_PLAYBACK")|map(attribute='event_uuid_link')|list %}
    {% if not original_playback_uuids %}
    {% set original_playback_uuid = event.eventLinks|selectattr("name", "equalto", "PLANNED_EVENT")|map(attribute='event_uuid_link')|list %}
    {% endif %}
    {% set original_playback_uuid = original_playback_uuids|first %}
    {% set original_playback = acquisition_events["playback"]|selectattr("event_uuid", "in", original_playback_uuids)|first %}
    {% set corrected_planned_playback_uuid = original_playback.eventLinks|selectattr("name", "equalto", "TIME_CORRECTION")|map(attribute='event_uuid_link')|first %}
    {% set satellite = original_playback.eventTexts|selectattr("name", "equalto", "satellite")|map(attribute='value')|first|string %}
    {% set orbit = original_playback.eventDoubles|selectattr("name", "equalto", "start_orbit")|map(attribute='value')|first|int %}
    {% set station = "N/A" %}
    {% set station_schedule_uuid = original_playback.eventLinks|selectattr("name", "in", ["STATION_SCHEDULE", "SLOT_REQUEST_EDRS"])|map(attribute='event_uuid_link')|first %}
    {% if station_schedule_uuid %}
    {% set station_schedule = acquisition_events["station_and_edrs_schedule"]|selectattr("event_uuid", "equalto", station_schedule_uuid)|first %}
    {% set station = station_schedule.eventTexts|selectattr("name", "equalto", "station")|map(attribute='value')|first|string %}
    {% endif %}
    {% set playback_type = original_playback.eventTexts|selectattr("name", "equalto", "playback_type")|map(attribute='value')|first|string %}
    {% set playback_mean = original_playback.eventTexts|selectattr("name", "equalto", "playback_mean")|map(attribute='value')|first|string %}
    {% set status = event.eventTexts|selectattr("name", "equalto", "status")|map(attribute='value')|first|string %}
    {
        "id": "{{ event.event_uuid }}",
        "tooltip": create_acquisition_tooltip_text("{{ satellite }}", "{{ orbit }}", "{{ station }}", "<a href='/views/specific-acquisition/{{ corrected_planned_playback_uuid }}'><span class='bold-green'>RECEIVED</span></a>", "{{ event.start.isoformat() }}", "{{ event.stop.isoformat() }}", "{{ playback_type }}", "{{ playback_mean }}", "{{ original_playback.source.name }}", "{{ original_playback.event_uuid }}", "/eboa_nav/query-event-links/{{ original_playback.event_uuid }}"),
        "geometries": [
            {% for geometry in event.eventGeometries %}
            {{ geometry.to_wkt() }},
            {% endfor %}
        ],
        "style": {
            "stroke_color": "green",
            "fill_color": "rgba(0,255,0,0.3)",
        }
    },
    {% endfor %}
]
