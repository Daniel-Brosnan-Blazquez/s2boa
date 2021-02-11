
var processing_geometries_complete = [
    {% for event in events %}
    {% set original_isp_validity_uuids = event.eventLinks|selectattr("name", "equalto", "ISP_VALIDITY")|map(attribute='event_uuid_link')|list %}
    {% set original_isp_validity = processing_events["isp_validity_channel_1"]|selectattr("event_uuid", "in", original_isp_validity_uuids)|first %}
    {% set original_playback_validity_uuids = original_isp_validity.eventLinks|selectattr("name", "equalto", "PLAYBACK_VALIDITY")|map(attribute='event_uuid_link')|list %}
    {% set original_playback_validity = processing_events["playback_validity_channel_1"]|selectattr("event_uuid", "in", original_playback_validity_uuids)|first %}
    {% set original_planned_playback_uuids = original_playback_validity.eventLinks|selectattr("name", "equalto", "PLANNED_PLAYBACK")|map(attribute='event_uuid_link')|list %}
    {% set original_planned_playback = processing_events["playback"]|selectattr("event_uuid", "in", original_planned_playback_uuids)|first %}
    {% set satellite = event.eventTexts|selectattr("name", "equalto", "satellite")|map(attribute='value')|first|string %}
    {% set downlink_orbit = event.eventDoubles|selectattr("name", "equalto", "downlink_orbit")|map(attribute='value')|first|string %}
    {% set station = original_isp_validity.eventTexts|selectattr("name", "equalto", "reception_station")|map(attribute='value')|first|string %}
    {% set level = event.eventTexts|selectattr("name", "equalto", "level")|map(attribute='value')|first|string %}
    {% set sensing_orbit = event.eventDoubles|selectattr("name", "equalto", "sensing_orbit")|map(attribute='value')|first|int %}
    {% set status = event.eventTexts|selectattr("name", "equalto", "status")|map(attribute='value')|first|string %}
    {% set datastrip_er = event.explicitRef.explicit_ref %}
    {% if datastrip_er %}
    {% set datastrip = "<a href='/eboa_nav/query-event-links/" + event.event_uuid|string + "'>" + datastrip_er + "</a>" %}
    {% else %}
    {% set datastrip = "N/A" %}
    {% endif %}
    {% set datastrip_start = original_isp_validity.start.isoformat() %}
    {% set datastrip_stop = original_isp_validity.stop.isoformat() %}
    {% set sad_data_uuids = original_isp_validity.eventLinks|selectattr("name", "equalto", "SAD_DATA")|map(attribute='event_uuid_link')|list %}
    {% set sad_data = processing_events["sad_data"]|selectattr("event_uuid", "in", sad_data_uuids)|first %}
    {
        "id": "{{ event.event_uuid }}",
        "tooltip": create_processing_tooltip_text("{{ event.event_uuid }}", "{{ satellite }}", "<a href='/views/specific-processing/{{ original_planned_playback.event_uuid }}'>{{ downlink_orbit }}</a>", "{{ station }}", "{{ level }}", "{{ sensing_orbit }}", "<span class=bold-green>{{ status }}</span>", "{{ datastrip }}", "{{ datastrip_start }}", "{{ datastrip_stop }}", "<a href='/eboa_nav/query-event-links/{{ sad_data.event_uuid }}'>{{ sad_data.start.isoformat() ~ "_" ~ sad_data.stop.isoformat() }}</a>"),
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
