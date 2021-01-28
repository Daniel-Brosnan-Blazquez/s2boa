
var processing_geometries_complete = [
    {% for event in events %}
    {% set downlink_orbit = event.eventDoubles|selectattr("name", "equalto", "downlink_orbit")|map(attribute='value')|first|string %}
    {% set satellite = event.eventTexts|selectattr("name", "equalto", "satellite")|map(attribute='value')|first|string %}
    {% set station = event.eventTexts|selectattr("name", "equalto", "station")|map(attribute='value')|first|string %}
    {% set level = event.eventTexts|selectattr("name", "equalto", "level")|map(attribute='value')|first|string %}
    {% if event.event_uuid in processing_events["isp_validity_processing_completeness_channel_1_with_downlink_status"] %}
        {% set total = processing_events["isp_validity_processing_completeness_channel_1_with_downlink_status"][event.event_uuid][0] %}
        {% set not_missing = processing_events["isp_validity_processing_completeness_channel_1_with_downlink_status"][event.event_uuid][1] %}
        {% if (total - not_missing) == 0 %}
        {% set downlink_status = "OK-(" ~ total ~ "/" ~ not_missing ~ ")"  %}
        {% else %}
        {% set downlink_status = "NOK-(" ~ total ~ "/" ~ not_missing ~ ")"  %}
        {% endif%}
    {% endif%}
    {% set sensing_orbit = event.eventDoubles|selectattr("name", "equalto", "sensing_orbit")|map(attribute='value')|first|int %}
    {% set status = event.eventTexts|selectattr("name", "equalto", "status")|map(attribute='value')|first|string %}
    {
        "id": "{{ event.event_uuid }}",
        "tooltip": "",
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
