
var missing_processing_timeline = [
    {% for event in events %}
    {% set downlink_orbit = event.eventDoubles|selectattr("name", "equalto", "downlink_orbit")|map(attribute='value')|first|string %}
    {% set satellite = event.eventTexts|selectattr("name", "equalto", "satellite")|map(attribute='value')|first|string %}
    {% set station = event.eventTexts|selectattr("name", "equalto", "station")|map(attribute='value')|first|string %}
    {% set level = event.eventTexts|selectattr("name", "equalto", "level")|map(attribute='value')|first|string %}
    {% set sensing_orbit = event.eventDoubles|selectattr("name", "equalto", "sensing_orbit")|map(attribute='value')|first|int %}
    {% set status = event.eventTexts|selectattr("name", "equalto", "status")|map(attribute='value')|first|string %}
    {
        "id": "{{ event.event_uuid }}",
        "group": "{{ satellite }}",
        "timeline": "{{ level }}",
        "start": "{{ event.start.isoformat() }}",
        "stop": "{{ event.stop.isoformat() }}",
        "tooltip": "",
        "className": "fill-border-red"
    },
    {% endfor %}
]
