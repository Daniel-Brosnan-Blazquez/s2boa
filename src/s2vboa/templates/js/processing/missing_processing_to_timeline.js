
var missing_processing_timeline = [
    {% for event in events %}
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
    {% set sad_status = event.eventTexts|selectattr("name", "equalto", "sad_status")|map(attribute='value')|first|string %}
    {% if sad_status and sad_status == "MISSING" %}
    {% set status = "MISSING_SAD" %}
    {% elif sad_status and sad_status == "PARTIAL" %}
    {% set status = "PARTIAL_SAD" %}
    {% endif %}
    {% set datastrip = "<a href='/eboa_nav/query-event-links/" + event.event_uuid|string + "'>N/A</a>" %}
    {% set imaging_mode = event.eventTexts|selectattr("name", "equalto", "imaging_mode")|map(attribute='value')|first|string %}
    {% if not imaging_mode %}
    {% set imaging_mode = "N/A" %}
    {% endif %}
    {% set datastrip_start = event.start.isoformat() %}
    {% set datastrip_stop = event.stop.isoformat() %}
    {% set duration = (((event.stop - event.start).total_seconds()) / 60)|round(3) %}
    {% set sad_data_uuids = original_isp_validity.eventLinks|selectattr("name", "equalto", "SAD_DATA")|map(attribute='event_uuid_link')|list %}
    {% set sad_data_info = "N/A" %}
    {% if sad_data_uuids|length > 0 %}
    {% set sad_data = processing_events["sad_data"]|selectattr("event_uuid", "in", sad_data_uuids)|first %}
    {% set sad_data_info = "<a href='/eboa_nav/query-event-links/" + sad_data.event_uuid|string + "'>" + sad_data.start.isoformat() + "_" + sad_data.stop.isoformat() + "</a>" %}
    {% endif %}
    {
        "id": "{{ event.event_uuid }}",
        "group": "{{ satellite }};{{ station }}",
        "timeline": "{{ level }}",
        "start": "{{ event.start.isoformat() }}",
        "stop": "{{ event.stop.isoformat() }}",
        "tooltip": create_processing_tooltip_text("{{ event.event_uuid }}", "{{ satellite }}", "<a href='/views/specific-acquisition/{{ original_planned_playback_correction_uuid }}'>{{ downlink_orbit }}</a>", "{{ station }}", "{{ level }}", "{{ sensing_orbit }}", "<a href='/views/specific-processing/{{ original_planned_playback.event_uuid }}' class=bold-red>{{ status }}</a>", "{{ datastrip }}", "{{ imaging_mode }}", "{{ datastrip_start }}", "{{ datastrip_stop }}", "{{ duration }}", "{{ sad_data_info }}"),
        "className": "fill-border-red"
    },
    {% endfor %}
]
