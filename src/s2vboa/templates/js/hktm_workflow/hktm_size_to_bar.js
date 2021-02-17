
var hktm_size_events = [
    {% for event in events %}

    {% set satellite = event.eventTexts|selectattr("name", "equalto", "satellite")|map(attribute='value')|first|string %}
    
    {% set orbit = event.eventDoubles|selectattr("name", "equalto", "start_orbit")|map(attribute='value')|first|int %}
    {% set station = event.eventTexts|selectattr("name", "equalto", "station")|map(attribute='value')|first|string %}
    {% set hktm_production_event_uuids = event.eventLinks|selectattr("name", "equalto", "HKTM_PRODUCTION_VGS")|map(attribute='event_uuid_link')|list %}

    {% if hktm_production_event_uuids|length > 0 %}
    {% set hktm_production_events = hktm_workflow_events["hktm_production_vgs"]|selectattr("event_uuid", "in", hktm_production_event_uuids)|list %}

    {% for hktm_production_event in hktm_production_events %}
    {% set successful_circulation_to_fos = [hktm_production_event]|map(attribute="explicitRef")|list|filter_references_by_annotation_text_value("CIRCULATION_TIME", "destination", "FOS_")|list %}

    {% set orbpre_segment = [event]|convert_eboa_events_to_date_segments|intersect_timelines(orbpre_events|filter_events_by_text_value("satellite", satellite)|convert_eboa_events_to_date_segments)|first %}

    {% if orbpre_segment %}
    {% set orbpre_event = orbpre_events|selectattr("event_uuid", "==", orbpre_segment["id2"])|first %}

    {% if successful_circulation_to_fos|length > 0 %}
    {% set circulation_time_to_fos_annotation = successful_circulation_to_fos|map(attribute="annotations")|flatten|filter_annotations("CIRCULATION_TIME")|filter_annotations_by_text_value("destination", "FOS_")|first %}
    {% set circulation_time_to_fos_datetime = circulation_time_to_fos_annotation.annotationTimestamps|selectattr("name", "equalto", "circulation_time")|map(attribute='value')|first %}
    {% set product_size_to_fos = circulation_time_to_fos_annotation.annotationDoubles|selectattr("name", "equalto", "product_size")|map(attribute='value')|first %}
    {% set circulation_time_to_fos = circulation_time_to_fos_datetime.isoformat() %}

    {% set delta_to_fos = ((circulation_time_to_fos_datetime - orbpre_event["start"]).total_seconds()/ 60)|round(3) %}
    {% set delta_to_fos_class = "bold-green" %}
    {% if delta_to_fos > 60 %}
    {% set delta_to_fos_class = "bold-red" %}
    {% endif %}
    {
        "id": "{{ hktm_production_event.event_uuid }}",
        "group": "{{ satellite }}",
        "x": "{{ orbpre_event.start.isoformat() }}",
        "y": "{{ product_size_to_fos }}",
        "tooltip": create_hktm_workflow_tooltip_text("<a href='/eboa_nav/query-er/{{ hktm_production_event.explicit_ref_uuid }}'>{{ hktm_production_event.explicitRef.explicit_ref }}</a>", "{{ satellite }}", "<a href='/eboa_nav/query-event-links/{{ event.event_uuid }}'>{{ orbit }}</a>", "{{ station }}", "{{ orbpre_event.start.isoformat() }}", "{{ circulation_time_to_fos }}", "<span class='{{ delta_to_fos_class }}'>{{ delta_to_fos }}</span>", "{{ product_size_to_fos }}")
    },
    {% endif %}
    {% endif %}
    {% endfor %}
    {% endif %}
    {% endfor %}
]
