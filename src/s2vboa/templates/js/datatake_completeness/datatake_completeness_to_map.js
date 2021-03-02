var datatake_completeness_geometries = [
    {% for event in events %}
    {% set satellite = event.eventTexts|selectattr("name", "equalto", "satellite")|map(attribute='value')|first|string %}
    {% set level = event.eventTexts|selectattr("name", "equalto", "level")|map(attribute='value')|first|string %}
    {% if not level %}
    {% set level = "N/A" %}
    {% endif %}
    {# {% set sensing_orbit = event.eventDoubles|selectattr("name", "equalto", "sensing_orbit")|map(attribute='value')|first|int %} #}
    {% set imaging_mode = event.eventTexts|selectattr("name", "equalto", "imaging_mode")|map(attribute='value')|first|string %}
    {% if not imaging_mode %}
    {% set imaging_mode = "N/A" %}
    {% endif %}
    {% set status = event.eventTexts|selectattr("name", "equalto", "status")|map(attribute='value')|first|string %}
    {% if status == "MISSING" %}
    {% set status_class = "bold-red" %}
    {% set stroke_color = "red" %}
    {% set fill_color = "rgba(255,0,0,0.3)" %}
    {% elif status == "INCOMPLETE" %}
    {% set status_class = "bold-orange" %}
    {% set stroke_color = "orange" %}
    {% set fill_color = "rgba(255,140,0,0.3)" %}
    {% else %}
    {% set status_class = "bold-green" %}
    {% set stroke_color = "green" %}
    {% set fill_color = "rgba(0,255,0,0.3)" %}
    {% endif %}
    {% if status in ("COMPLETE", "INCOMPLETE") %}
    {% set datastrip = event.explicitRef.explicit_ref %}
    {% else %}
    {% set datastrip = "N/A" %}
    {% endif %}
    {% set datastrip_start = event.start.isoformat() %}
    {% set datastrip_stop = event.stop.isoformat() %}
    {
        "id": "{{ event.event_uuid }}",
        "tooltip": create_datatake_completeness_tooltip_text("{{ event.event_uuid }}", "{{ satellite }}", "{{ station }}", "{{ level }}", "{{ sensing_orbit }}", "<span class={{ status_class }}>{{ status }}</span>", "{{ datastrip }}", "{{ imaging_mode }}", "{{ datastrip_start }}", "{{ datastrip_stop }}"),
        "geometries": [
            {% for geometry in event.eventGeometries %}
            {{ geometry.to_wkt() }},
            {% endfor %}
        ],
        "style": {
            "stroke_color": "{{ stroke_color }}",
            "fill_color": "{{ fill_color }}",
        }
    },
    {% endfor %}
]
