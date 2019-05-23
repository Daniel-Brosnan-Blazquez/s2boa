
/* Function to create the text for the tooltip of the playback event information */
function create_playback_tooltip_text(satellite, orbit, station, start, stop, playback_type, plan_file, uuid, link_to_details){
    const start_date = new Date(start);
    const stop_date = new Date(stop);
    const duration = ((stop_date.getTime() - start_date.getTime()) / (1000 * 60)).toFixed(3);

    return "<table border='1'>" +
            "<tr><td>UUID</td><td>" + uuid + "</td>" +
            "<tr><td>Satellite</td><td>" + satellite + "</td>" +
            "<tr><td>Orbit</td><td>" + orbit + "</td>" +
            "<tr><td>Station</td><td>" + station + "</td>" +
            "<tr><td>Start</td><td>" + start + "</td>" +
            "<tr><td>Stop</td><td>" + stop + "</td>" +
            "<tr><td>Duration(m)</td><td>" + duration + "</td>" +
            "<tr><td>Playback type</td><td>" + playback_type + "</td>" +
            "<tr><td>Plan file</td><td>" + plan_file + "</td>" +
            '<tr><td>Details</td><td><a href="' + link_to_details + '"><i class="fa fa-link"></i></a></td>' +
            "</tr></table>"
};

var playback_events = [
    {% for event in events %}
    {% set original_playback_uuid = event.eventLinks|selectattr("name", "equalto", "PLANNED_EVENT")|map(attribute='event_uuid_link')|first %}
    {% set original_playback = planning_events["playback"]["linked_events"]|selectattr("event_uuid", "equalto", original_playback_uuid)|first %}
    {% set satellite = event.eventTexts|selectattr("name", "equalto", "satellite")|map(attribute='value')|first|string %}
    {% set orbit = event.eventDoubles|selectattr("name", "equalto", "start_orbit")|map(attribute='value')|first|int %}
    {% set station = original_playback.eventTexts|selectattr("name", "equalto", "station")|map(attribute='value')|first|string %}
    {% set playback_type = event.eventTexts|selectattr("name", "equalto", "playback_type")|map(attribute='value')|first|string %}
    {% set record_type = event.eventTexts|selectattr("name", "equalto", "record_type")|map(attribute='value')|first|string %}
    {
        "id": "{{ original_playback.event_uuid }}",
        "group": "{{ satellite }}",
        "timeline": "{{ original_playback.gauge.name }}",
        "start": "{{ event.start }}",
        "stop": "{{ event.stop }}",
        "tooltip": create_playback_tooltip_text("{{ satellite }}", "{{ orbit }}", "{{ station }}", "{{ event.start.isoformat() }}", "{{ event.stop.isoformat() }}", "{{ playback_type }}", "{{ original_playback.source.name }}", "{{ original_playback.event_uuid }}", "/eboa_nav/query-event-links/{{ original_playback.event_uuid }}")
    },
    {% endfor %}
]

