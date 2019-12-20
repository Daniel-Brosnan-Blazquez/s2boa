
var imaging_events = [
    {% for imaging in events %}
    {% set correction_uuid = imaging.eventLinks|selectattr("name", "equalto", "TIME_CORRECTION")|map(attribute='event_uuid_link')|first %}
    {% if correction_uuid %}
    {% set event = planning_events["imaging"]["linked_events"]|selectattr("event_uuid", "equalto", correction_uuid)|first %}
    {% else %}
    {% set event = imaging %}
    {% endif %}
    {% set satellite = imaging.eventTexts|selectattr("name", "equalto", "satellite")|map(attribute='value')|first|string %}
    {% set orbit = imaging.eventDoubles|selectattr("name", "equalto", "start_orbit")|map(attribute='value')|first|int %}
    {% set imaging_mode = imaging.eventTexts|selectattr("name", "equalto", "imaging_mode")|map(attribute='value')|first|string %}
    {% set record_type = imaging.eventTexts|selectattr("name", "equalto", "record_type")|map(attribute='value')|first|string %}
    {
        "id": "{{ imaging.event_uuid }}",
        "group": "{{ satellite }}",
        "timeline": "{{ imaging.gauge.name }}",
        "start": "{{ event.start.isoformat() }}",
        "stop": "{{ event.stop.isoformat() }}",
        "tooltip": create_imaging_tooltip_text("{{ satellite }}", "{{ orbit }}", "{{ event.start.isoformat() }}", "{{ event.stop.isoformat() }}", "{{ imaging_mode }}", "{{ record_type }}", "{{ imaging.source.name }}", "{{ imaging.event_uuid }}", "/eboa_nav/query-event-links/{{ imaging.event_uuid }}")
    },
    {% endfor %}
]
