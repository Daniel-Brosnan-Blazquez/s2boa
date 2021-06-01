
var processing_geometries_complete = [
    {% for event in events %}
    {% set processing_validity_uuids = event.eventLinks|selectattr("name", "equalto", "PROCESSING_VALIDITY")|map(attribute='event_uuid_link')|list %}
    {% set processing_validity = processing_events["processing_validity"]|selectattr("event_uuid", "in", processing_validity_uuids)|first %}
    {% set original_isp_validity_uuids = event.eventLinks|selectattr("name", "equalto", "ISP_VALIDITY")|map(attribute='event_uuid_link')|list %}
    {% set original_isp_validity = processing_events["isp_validity_channel_2"]|selectattr("event_uuid", "in", original_isp_validity_uuids)|first %}
    {% set original_playback_validity_uuids = original_isp_validity.eventLinks|selectattr("name", "equalto", "PLAYBACK_VALIDITY")|map(attribute='event_uuid_link')|list %}
    {% set original_playback_validity = processing_events["playback_validity_channel_2"]|selectattr("event_uuid", "in", original_playback_validity_uuids)|first %}
    {% set original_planned_playback_uuids = original_playback_validity.eventLinks|selectattr("name", "equalto", "PLANNED_PLAYBACK")|map(attribute='event_uuid_link')|list %}
    {% set original_planned_playback = processing_events["playback"]|selectattr("event_uuid", "in", original_planned_playback_uuids)|first %}
    {% set original_planned_playback_correction_uuid = original_planned_playback.eventLinks|selectattr("name", "equalto", "TIME_CORRECTION")|map(attribute='event_uuid_link')|first %}
    {% set satellite = event.eventTexts|selectattr("name", "equalto", "satellite")|map(attribute='value')|first|string %}
    {% set downlink_orbit = event.eventDoubles|selectattr("name", "equalto", "downlink_orbit")|map(attribute='value')|first|string %}
    {% set station = original_isp_validity.eventTexts|selectattr("name", "equalto", "reception_station")|map(attribute='value')|first|string %}
    {% set level = event.eventTexts|selectattr("name", "equalto", "level")|map(attribute='value')|first|string %}
    {% set sensing_orbit_values = event.eventDoubles|selectattr("name", "equalto", "sensing_orbit")|map(attribute='value')|list %}
    {% if sensing_orbit_values|length > 0 %}
    {% set sensing_orbit = sensing_orbit_values|first|int %}
    {% else %}
    {% set sensing_orbit = "N/A" %}
    {% endif %}
    {% set status = event.eventTexts|selectattr("name", "equalto", "status")|map(attribute='value')|first|string %}
    {% set datastrip = "<a href='/eboa_nav/query-event-links/" + event.event_uuid|string + "'>" + event.explicitRef.explicit_ref + "</a>" %}
    {% set imaging_mode = event.eventTexts|selectattr("name", "equalto", "imaging_mode")|map(attribute='value')|first|string %}
    {% if not imaging_mode %}
    {% set imaging_mode = "N/A" %}
    {% endif %}

    {% if processing_validity %}
    {% set datastrip_start = processing_validity.start.isoformat() %}
    {% set datastrip_stop = processing_validity.stop.isoformat() %}
    {% set duration = (((processing_validity.stop - processing_validity.start).total_seconds()) / 60)|round(3) %}
    {% else %}
    {% set datastrip_start = event.start.isoformat() %}
    {% set datastrip_stop = event.stop.isoformat() %}
    {% set duration = (((event.stop - event.start).total_seconds()) / 60)|round(3) %}
    {% endif %}

    {% set sad_data_uuids = original_isp_validity.eventLinks|selectattr("name", "equalto", "SAD_DATA")|map(attribute='event_uuid_link')|list %}
    {% set sad_data_info = "N/A" %}
    {% if sad_data_uuids|length > 0 %}
    {% set sad_data = processing_events["sad_data"]|selectattr("event_uuid", "in", sad_data_uuids)|first %}
    {% set sad_data_info = "<a href='/eboa_nav/query-event-links/" + sad_data.event_uuid|string + "'>" + sad_data.start.isoformat() + "_" + sad_data.stop.isoformat() + "</a>" %}
    {% endif %}
    {
        "id": "{{ event.event_uuid }}",
        "tooltip": create_processing_tooltip_text("{{ event.event_uuid }}", "{{ satellite }}", "<a href='/views/specific-acquisition/{{ original_planned_playback_correction_uuid }}'>{{ downlink_orbit }}</a>", "{{ station }}", "{{ level }}", "{{ sensing_orbit }}", "<a href='/views/specific-processing/{{ original_planned_playback.event_uuid }}' class=bold-green>{{ status }}</a>", "{{ datastrip }}", "{{ imaging_mode }}", "{{ datastrip_start }}", "{{ datastrip_stop }}", "{{ duration }}", "{{ sad_data_info }}"),
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
