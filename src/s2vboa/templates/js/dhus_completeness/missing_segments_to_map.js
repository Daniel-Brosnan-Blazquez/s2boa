
var missing_segments = [
    {% for missing_processing_event_uuid in missing_processing_event_uuids[level] %}
    {% set missing_processing_event = info["processing_completeness"][level]|selectattr("event_uuid", "equalto", missing_processing_event_uuid)|first %}
    {% set planned_imaging_uuid = missing_processing_event.eventLinks|selectattr("name", "equalto", "PLANNED_EVENT")|map(attribute="event_uuid_link")|first %}
    {% set planned_imaging = info["imaging"]|selectattr("event_uuid", "equalto", planned_imaging_uuid)|first %}

    {% set isp_completeness_uuids = planned_imaging.eventLinks|selectattr("name", "equalto", "ISP_COMPLETENESS")|map(attribute="event_uuid_link")|list %}
    {% set isp_completeness_events = info["isp_completeness"]|selectattr("event_uuid", "in", isp_completeness_uuids)|list %}
    
    {% set intersected_isp_completeness_segments = [missing_processing_event]|convert_eboa_events_to_date_segments|intersect_timelines(isp_completeness_events|convert_eboa_events_to_date_segments) %}
    {% set intersected_isp_completeness_missing_events = [] %}
    {% for intersected_isp_completeness_segment in intersected_isp_completeness_segments %}
    {% set intersected_isp_completeness_event = isp_completeness_events|selectattr("event_uuid", "equalto", intersected_isp_completeness_segment["id2"])|first %}
    {% set intersected_isp_completeness_event_status = intersected_isp_completeness_event.eventTexts|selectattr("name", "equalto", "status")|map(attribute="value")|first|string %}
    {% if intersected_isp_completeness_event_status == "MISSING" %}
    {% do intersected_isp_completeness_missing_events.append(intersected_isp_completeness_event) %}
    {% endif %}
    {% endfor %}

    {% if intersected_isp_completeness_missing_events|length > 0 %}
    {% set status = "MISSING ACQUISITION" %}
    {% else %}
    {% set status = "MISSING PROCESSING" %}
    {% endif %}

    {% set satellite = missing_processing_event.eventTexts|selectattr("name", "equalto", "satellite")|map(attribute='value')|first|string %}
    {% set orbit = missing_processing_event.eventDoubles|selectattr("name", "equalto", "start_orbit")|map(attribute='value')|first|int %}
     
    {
        "id": "{{ missing_processing_event_uuid }}",
        "tooltip": create_processing_tooltip_text("{{ satellite }}", "{{ orbit }}", "<span class='bold-red'>{{ status }}</span>", "N/A", "{{ missing_processing_event.start.isoformat() }}", "{{ missing_processing_event.stop.isoformat() }}", "{{ planned_imaging.source.name }}", "{{ missing_processing_event_uuid }}", "/eboa_nav/query-event-links/{{ planned_imaging_uuid }}"),
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
