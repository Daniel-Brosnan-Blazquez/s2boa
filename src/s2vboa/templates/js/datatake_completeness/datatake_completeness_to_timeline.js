var datatake_completeness_timeline = [
    {% for event in events %}
    {% set planned_cut_imaging_uuids = event.eventLinks|selectattr("name", "equalto", "PLANNED_IMAGING")|map(attribute='event_uuid_link')|list %}
    {% set planned_cut_imaging = datatake_completeness_events["planned_cut_imaging"]|selectattr("event_uuid", "in", planned_cut_imaging_uuids)|first %}
    {% set satellite = event.eventTexts|selectattr("name", "equalto", "satellite")|map(attribute='value')|first|string %}
    {% set level = event.eventTexts|selectattr("name", "equalto", "level")|map(attribute='value')|first|string %}
    {% if not level %}
    {% set level = "N/A" %}
    {% endif %}
    {% set imaging_mode = event.eventTexts|selectattr("name", "equalto", "imaging_mode")|map(attribute='value')|first|string %}
    {% if not imaging_mode %}
    {% set imaging_mode = "N/A" %}
    {% endif %}
    {% set status = event.eventTexts|selectattr("name", "equalto", "status")|map(attribute='value')|first|string %}
    {% if status == "MISSING" %}
    {% set orbit = event.eventDoubles|selectattr("name", "equalto", "start_orbit")|map(attribute='value')|first|int %}
    {% set datastrip = "N/A" %}
    {% set status_class = "bold-red" %}
    {% set class_name = "fill-border-red" %}
    {% elif status == "INCOMPLETE" %}
    {% set orbit = "N/A" %}
    {% set datastrip = event.explicitRef.explicit_ref %}
    {% set status_class = "bold-orange" %}
    {% set class_name = "fill-border-orange" %}
    {% else %}
    {% set orbit = event.eventDoubles|selectattr("name", "equalto", "sensing_orbit")|map(attribute='value')|first|int %}
    {% set datastrip = event.explicitRef.explicit_ref %}
    {% set status_class = "bold-green" %}
    {% set class_name = "fill-border-green" %}
    {% endif %}
    {% set datastrip_start = event.start.isoformat() %}
    {% set datastrip_stop = event.stop.isoformat() %}
    {
        "id": "{{ event.event_uuid }}",
        "group": "{{ satellite }}",
        "timeline": "{{ level }}",
        "start": "{{ event.start.isoformat() }}",
        "stop": "{{ event.stop.isoformat() }}",
        "tooltip": create_datatake_completeness_tooltip_text("{{ event.event_uuid }}", "{{ satellite }}", "{{ level }}", "{{ orbit }}", "<a href='/views/specific-datatake-completeness/{{ planned_cut_imaging.event_uuid }}' class={{ status_class }}>{{ status }}</a>", "{{ datastrip }}", "{{ imaging_mode }}", "{{ datastrip_start }}", "{{ datastrip_stop }}"),
        "className": "{{ class_name }}"
    },
    {% endfor %}
]
