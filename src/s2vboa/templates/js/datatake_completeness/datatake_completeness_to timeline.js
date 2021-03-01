
var datatake_completeness_timeline = [
    {% for event in events %}
    {% set satellite = event.eventTexts|selectattr("name", "equalto", "satellite")|map(attribute='value')|first|string %}
    {% set level = event.eventTexts|selectattr("name", "equalto", "level")|map(attribute='value')|first|string %}
    {% set sensing_orbit = event.eventDoubles|selectattr("name", "equalto", "sensing_orbit")|map(attribute='value')|first|int %}
    {% set imaging_mode = event.eventTexts|selectattr("name", "equalto", "imaging_mode")|map(attribute='value')|first|string %}
    {% if not imaging_mode %}
    {% set imaging_mode = "N/A" %}
    {% endif %}
    {% set status = event.eventTexts|selectattr("name", "equalto", "status")|map(attribute='value')|first|string %}
    {% if status == "MISSING" %}
    {% set status_class = "bold-red" %}
    {% set class_name = "fill-border-red" %}
    {% elif status == "INCOMPLETE" %}
    {% set status_class = "bold-orange" %}
    {% set class_name = "fill-border-orange" %}
    {% else %}
    {% set status_class = "bold-green" %}
    {% set class_name = "fill-border-green" %}
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
        "group": "{{ satellite }}",
        "timeline": "{{ level }}",
        "start": "{{ event.start.isoformat() }}",
        "stop": "{{ event.stop.isoformat() }}",
        "tooltip": create_datatake_completeness_tooltip_text("{{ event.event_uuid }}", "{{ satellite }}", "{{ station }}", "{{ level }}", "{{ sensing_orbit }}", "<span class={{ status_class }}>{{ status }}</span>", "{{ datastrip }}", "{{ imaging_mode }}", "{{ datastrip_start }}", "{{ datastrip_stop }}"),
        "className": "{{ class_name }}"
    },
    {% endfor %}
]
