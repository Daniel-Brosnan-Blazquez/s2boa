
var complete_processing_timeline = [
    {% for event in events %}
    {% set original_isp_validity_uuids = event.eventLinks|selectattr("name", "equalto", "ISP_VALIDITY")|map(attribute='event_uuid_link')|list %}
    {% set original_isp_validity = processing_events["isp_validity_channel_1"]|selectattr("event_uuid", "in", original_isp_validity_uuids)|first %}
    {% set satellite = event.eventTexts|selectattr("name", "equalto", "satellite")|map(attribute='value')|first|string %}
    {% set downlink_orbit = event.eventDoubles|selectattr("name", "equalto", "downlink_orbit")|map(attribute='value')|first|string %}
    {% set station = original_isp_validity.eventTexts|selectattr("name", "equalto", "reception_station")|map(attribute='value')|first|string %}
    {% set level = event.eventTexts|selectattr("name", "equalto", "level")|map(attribute='value')|first|string %}
    {% set sensing_orbit = event.eventDoubles|selectattr("name", "equalto", "sensing_orbit")|map(attribute='value')|first|int %}
    {% set status = event.eventTexts|selectattr("name", "equalto", "status")|map(attribute='value')|first|string %}
    {% set datastrip = original_isp_validity.event_uuid %}
    {% set sad_data = original_isp_validity.eventLinks|selectattr("name", "equalto", "SAD_DATA")|map(attribute='event_uuid_link')|list|first %}
    {
        "id": "{{ event.event_uuid }}",
        "group": "{{ satellite }}",
        "timeline": "{{ level }}",
        "start": "{{ event.start.isoformat() }}",
        "stop": "{{ event.stop.isoformat() }}",
        "tooltip": create_processing_tooltip_text("{{ event.event_uuid }}", "{{ satellite }}", "{{ downlink_orbit }}", "{{ station }}", "{{ level }}", "{{ sensing_orbit }}", "<a class=bold-green>{{ status }}</a>", "/eboa_nav/query-event-links/{{ sad_data }}", "/eboa_nav/query-event-links/{{ datastrip }}"),
        "className": "fill-border-green"
    },
    {% endfor %}
]
