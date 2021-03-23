
var hktm_circulation_events = [
    {% for event in events %}

    {% set original_planned_playback_correction_uuid = event.eventLinks|selectattr("name", "equalto", "TIME_CORRECTION")|map(attribute='event_uuid_link')|first %}
    {% set satellite = event.eventTexts|selectattr("name", "equalto", "satellite")|map(attribute='value')|first|string %}
    
    {% set orbit = event.eventDoubles|selectattr("name", "equalto", "start_orbit")|map(attribute='value')|first|int %}

    {% set station = "N/A" %}
    {% set station_schedule_uuid = event.eventLinks|selectattr("name", "in", ["STATION_SCHEDULE", "SLOT_REQUEST_EDRS"])|map(attribute='event_uuid_link')|first %}
    {% if station_schedule_uuid %}
    {% set station_schedule = hktm_workflow_events["station_schedule"]|selectattr("event_uuid", "equalto", station_schedule_uuid)|first %}
    {% set station = station_schedule.eventTexts|selectattr("name", "equalto", "station")|map(attribute='value')|first|string %}
    {% endif %}

    {% set hktm_production_event_uuids = event.eventLinks|selectattr("name", "equalto", "HKTM_PRODUCTION_VGS")|map(attribute='event_uuid_link')|list %}

    {% set status = [] %}
    {% set status_class = [] %}     	 
    {% include "views/hktm_workflow/hktm_workflow_status.html" %}
    {% set distribution_status = [] %}
    {% set distribution_status_class = [] %}     	 
    {% include "views/hktm_workflow/hktm_workflow_distribution_status.html" %}
    {% set completeness_status = [] %}
    {% set completeness_status_class = [] %}     	 
    {% include "views/hktm_workflow/hktm_workflow_completeness_status.html" %}
    
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
        "y": "{{ delta_to_fos }}",
        "tooltip": create_hktm_workflow_tooltip_text("<a href='/eboa_nav/query-er/{{ hktm_production_event.explicit_ref_uuid }}'>{{ hktm_production_event.explicitRef.explicit_ref }}</a>", "{{ satellite }}", "<a href='/views/specific-acquisition/{{ original_planned_playback_correction_uuid }}'>{{ orbit }}</a>", "{{ station }}", "<a href='/views/specific-hktm-workflow/{{ event.event_uuid }}' class='{{ status_class[0] }}'>{{ status[0] }}</a>", "<span class='{{ distribution_status_class[0] }}'>{{ distribution_status[0] }}</span>", "<span class='{{ completeness_status_class[0] }}'>{{ completeness_status[0] }}</span>", "{{ orbpre_event.start.isoformat() }}", "{{ circulation_time_to_fos }}", "<span class='{{ delta_to_fos_class }}'>{{ delta_to_fos }}</span>", "{{ product_size_to_fos }}")
    },
    {% endif %}
    {% endif %}
    {% endfor %}
    {% endif %}
    {% endfor %}
]
