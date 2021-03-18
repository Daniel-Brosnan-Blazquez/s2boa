var datatake_completeness_geometries = [
    {% for event in events %}
    {% set planned_cut_imaging_uuids = event.eventLinks|selectattr("name", "equalto", "PLANNED_IMAGING")|map(attribute='event_uuid_link')|list %}
    {% set planned_cut_imaging = datatake_completeness_events["planned_cut_imaging"]|selectattr("event_uuid", "in", planned_cut_imaging_uuids)|first %}

    {# Obtain satellite #}
    {% set satellite = event.eventTexts|selectattr("name", "equalto", "satellite")|map(attribute='value')|first|string %}

    {# Obtain level #}
    {% set level = event.gauge.name[40:] %}

    {# Obtain imaging mode #}
    {% set imaging_mode = event.eventTexts|selectattr("name", "equalto", "imaging_mode")|map(attribute='value')|first|string %}
    {% if not imaging_mode %}
    {% set imaging_mode = "N/A" %}
    {% endif %}

    {# Obtain status #}
    {% set status = event.eventTexts|selectattr("name", "equalto", "status")|map(attribute='value')|first|string %}

    {# Obtain metadata of the datastrip depending on the status #}
    {% if status == "MISSING" %}
    {% set sensing_orbit = event.eventDoubles|selectattr("name", "equalto", "start_orbit")|map(attribute='value')|first|int %}
    {% set datastrip = "N/A" %}
    {% set status_class = "bold-red" %}
    {% set stroke_color = "red" %}
    {% set fill_color = "rgba(255,0,0,0.3)" %}
    {% else %}
    {% set sensing_orbit_values = event.eventDoubles|selectattr("name", "equalto", "sensing_orbit")|map(attribute='value')|list %}
    {% if sensing_orbit_values|length > 0 %}
    {% set sensing_orbit = sensing_orbit_values|first|int %}
    {% else %}
    {% set sensing_orbit = "N/A" %}
    {% endif %}
    {% set datastrip = event.explicitRef.explicit_ref %}
    {% if status == "INCOMPLETE" %}
    {% set status_class = "bold-orange" %}
    {% set stroke_color = "orange" %}
    {% set fill_color = "rgba(255,140,0,0.3)" %}
    {% else %}
    {% set status_class = "bold-green" %}
    {% set stroke_color = "green" %}
    {% set fill_color = "rgba(0,255,0,0.3)" %}
    {% endif %}
    {% endif %}

    {# Obtain start and stop #}
    {% set datastrip_start = event.start.isoformat() %}
    {% set datastrip_stop = event.stop.isoformat() %}
    {
        "id": "{{ event.event_uuid }}",
        "tooltip": create_datatake_completeness_tooltip_text("{{ event.event_uuid }}", "{{ satellite }}", "{{ level }}", "<a href='/eboa_nav/query-event-links/{{ planned_cut_imaging.event_uuid }}'>{{ sensing_orbit }}</a>", "<a href='/views/specific-datatake-completeness/{{ planned_cut_imaging.event_uuid }}' class={{ status_class }}>{{ status }}</a>", "<a href='/eboa_nav/query-event-links/{{ event.event_uuid }}'>{{ datastrip }}</a>", "{{ imaging_mode }}", "{{ datastrip_start }}", "{{ datastrip_stop }}"),
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
