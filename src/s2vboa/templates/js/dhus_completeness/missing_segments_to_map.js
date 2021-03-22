
var missing_segments = [
    {% for missing_processing_event_uuid in missing_processing_event_uuids[level] %}
    {% set missing_processing_event = info["processing_completeness"][level]|selectattr("event_uuid", "equalto", missing_processing_event_uuid)|first %}
    {% set planned_imaging_uuid = missing_processing_event.eventLinks|selectattr("name", "in", ["PLANNED_IMAGING", "PLANNED_EVENT"])|map(attribute="event_uuid_link")|first %}
    {% set planned_imaging = info["imaging"]|selectattr("event_uuid", "equalto", planned_imaging_uuid)|first %}

    {% set corrected_planned_imaging_uuid = planned_imaging.eventLinks|selectattr("name", "equalto", "TIME_CORRECTION")|map(attribute="event_uuid_link")|first %}
    
    {% set status = "MISSING PROCESSING" %}

    {% set satellite = missing_processing_event.eventTexts|selectattr("name", "equalto", "satellite")|map(attribute='value')|first|string %}
    {% set orbit = missing_processing_event.eventDoubles|selectattr("name", "equalto", "start_orbit")|map(attribute='value')|first|int %}
     
    {
        "id": "{{ missing_processing_event_uuid }}",
        "tooltip": create_processing_tooltip_text("{{ satellite }}", "{{ orbit }}", "<a class='bold-red' href='/views/dhus-completeness-by-datatake/{{ corrected_planned_imaging_uuid }}'>{{ status }}</a>", "N/A", "{{ missing_processing_event.start.isoformat() }}", "{{ missing_processing_event.stop.isoformat() }}", "{{ planned_imaging.source.name }}", "{{ missing_processing_event_uuid }}", "/eboa_nav/query-event-links/{{ planned_imaging_uuid }}"),
        "geometries": [
            {% for geometry in missing_processing_event.eventGeometries %}
            {{ geometry.to_wkt() }},
            {% endfor %}
        ],
        "style": {
            "stroke_color": "red",
            "fill_color": "rgba(255,0,0,0.3)",
        }
    },
    {% endfor %}
]
