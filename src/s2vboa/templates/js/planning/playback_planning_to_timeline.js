
var playback_events = [
    {% for event in events %}
    {% set original_playback_uuid = event.eventLinks|selectattr("name", "equalto", "PLANNED_EVENT")|map(attribute='event_uuid_link')|first %}
    {% if original_playback_uuid %}
    {% set original_playback = planning_events["playback"]["linked_events"]|selectattr("event_uuid", "equalto", original_playback_uuid)|first %}
    {% else %}
    {% set original_playback = event %}
    {% endif %}
    {% set satellite = event.eventTexts|selectattr("name", "equalto", "satellite")|map(attribute='value')|first|string %}
    {% set orbit = event.eventDoubles|selectattr("name", "equalto", "start_orbit")|map(attribute='value')|first|int %}
    {% if original_playback_uuid %}
    {% set station = original_playback.eventTexts|selectattr("name", "equalto", "station")|map(attribute='value')|first|string %}
    {% else %}
    {% set station = "N/A" %}
    {% endif %}
    {% set playback_type = event.eventTexts|selectattr("name", "equalto", "playback_type")|map(attribute='value')|first|string %}
    {% set playback_mean = event.eventTexts|selectattr("name", "equalto", "playback_mean")|map(attribute='value')|first|string %}
    {
        "id": "{{ original_playback.event_uuid }}",
        "group": "{{ satellite }}",
        "timeline": "{{ original_playback.gauge.name }}",
        "start": "{{ event.start }}",
        "stop": "{{ event.stop }}",
        "tooltip": create_playback_tooltip_text("{{ satellite }}", "{{ orbit }}", "{{ station }}", "{{ event.start.isoformat() }}", "{{ event.stop.isoformat() }}", "{{ playback_type }}", "{{ playback_mean }}", "{{ original_playback.source.name }}", "{{ original_playback.event_uuid }}", "/eboa_nav/query-event-links/{{ original_playback.event_uuid }}")
    },
    {% endfor %}
]
