
/* Function to create the text for the tooltip of the imaging event information */
function create_imaging_tooltip_text(satellite, orbit, start, stop, imaging_mode, record_type, plan_file, uuid, link_to_details){
    const start_date = new Date(start);
    const stop_date = new Date(stop);
    const duration = ((stop_date.getTime() - start_date.getTime()) / (1000 * 60)).toFixed(3);

    return "<table border='1'>" +
            "<tr><td>UUID</td><td>" + uuid + "</td>" +
            "<tr><td>Satellite</td><td>" + satellite + "</td>" +
            "<tr><td>Orbit</td><td>" + orbit + "</td>" +
            "<tr><td>Start</td><td>" + start + "</td>" +
            "<tr><td>Stop</td><td>" + stop + "</td>" +
            "<tr><td>Duration(m)</td><td>" + duration + "</td>" +
            "<tr><td>Imaging mode</td><td>" + imaging_mode + "</td>" +
            "<tr><td>Record type</td><td>" + record_type + "</td>" +
            "<tr><td>Plan file</td><td>" + plan_file + "</td>" +
            '<tr><td>Details</td><td><a href="' + link_to_details + '"><i class="fa fa-link"></i></a></td>' +
            "</tr></table>"
};

var imaging_events = [
    {% for event in planning_events["imaging"]["prime_events"] %}
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

