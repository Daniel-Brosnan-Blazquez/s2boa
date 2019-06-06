
var imaging_events = [
    {% for event in events %}
    {% set original_imaging_uuid = event.eventLinks|selectattr("name", "equalto", "PLANNED_EVENT")|map(attribute='event_uuid_link')|first %}
    {% set original_imaging = planning_events["imaging"]["linked_events"]|selectattr("event_uuid", "equalto", original_imaging_uuid)|first %}
    {% set satellite = event.eventTexts|selectattr("name", "equalto", "satellite")|map(attribute='value')|first|string %}
    {% set orbit = event.eventDoubles|selectattr("name", "equalto", "start_orbit")|map(attribute='value')|first|int %}
    {% set imaging_mode = event.eventTexts|selectattr("name", "equalto", "imaging_mode")|map(attribute='value')|first|string %}
    {% set record_type = event.eventTexts|selectattr("name", "equalto", "record_type")|map(attribute='value')|first|string %}
    {
        "id": "{{ original_imaging.event_uuid }}",
        "group": "{{ satellite }}",
        "x": "{{ event.start }}",
        "y": "{{ event.get_duration() / 60 }}",
        "tooltip": create_imaging_tooltip_text("{{ satellite }}", "{{ orbit }}", "{{ event.start.isoformat() }}", "{{ event.stop.isoformat() }}", "{{ imaging_mode }}", "{{ record_type }}", "{{ original_imaging.source.name }}", "{{ original_imaging.event_uuid }}", "/eboa_nav/query-event-links/{{ original_imaging.event_uuid }}")
    },
    {% endfor %}
]
