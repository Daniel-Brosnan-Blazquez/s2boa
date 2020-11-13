
{% set complete_processing_events = info["processing_completeness"][level]|rejectattr("event_uuid", "in", missing_processing_event_uuids[level])|list %}

var e2e_timeliness_tiles_published_in_dhus = [
    {% for complete_processing_event in complete_processing_events %}
    {% set datastrip_uuid = complete_processing_event.explicitRef.explicit_ref_uuid %}
    {% set datastrip = complete_processing_event.explicitRef.explicit_ref %}
    
    {% set planned_imaging_uuid = complete_processing_event.eventLinks|selectattr("name", "equalto", "PLANNED_IMAGING")|map(attribute="event_uuid_link")|first %}
    {% set planned_imaging = info["imaging"]|selectattr("event_uuid", "equalto", planned_imaging_uuid)|first %}

    {% set corrected_planned_imaging_uuid = planned_imaging.eventLinks|selectattr("name", "equalto", "TIME_CORRECTION")|map(attribute="event_uuid_link")|first %}
    {% set corrected_planned_imaging = info["imaging_correction"]|selectattr("event_uuid", "equalto", corrected_planned_imaging_uuid)|first %}

    {% set satellite = complete_processing_event.eventTexts|selectattr("name", "equalto", "satellite")|map(attribute='value')|first|string %}
    {% set orbit = complete_processing_event.eventDoubles|selectattr("name", "equalto", "sensing_orbit")|map(attribute='value')|first|int %}

    {% set tile_uuids = complete_processing_event.explicitRef.explicitRefLinks|selectattr("name", "equalto", "TILE")|map(attribute="explicit_ref_uuid_link")|list %}

    {% set tile_infos = info["tls"][level]|selectattr("explicit_ref_uuid", "in", tile_uuids)|list %}

    {% set times_to_dhus_publication = [] %}
    {% for tile_info in tile_infos %}

    {% set tile_uuid = tile_info.explicit_ref_uuid %}
    {% set tile = tile_info.explicit_ref %}
    {% set dhus_publication_annotations = tile_info.annotations|selectattr("annotationCnf.name", "equalto", "DHUS_PUBLICATION_TIME")|list %}
    {% set dhus_product_annotation = tile_info.annotations|selectattr("annotationCnf.name", "equalto", "USER_PRODUCT")|first %}

    {% set dhus_publication_status = dhus_publication_annotations|map(attribute="annotationTexts")|flatten|selectattr("name", "equalto", "status")|map(attribute="value")|first %}

    {% set dhus_product = "N/A" %}
    {% if dhus_product_annotation %}
    {% set dhus_product = dhus_product_annotation.annotationTexts|selectattr("name", "equalto", "product_name")|map(attribute="value")|first|string %}
    {% endif %}
    
    {% if dhus_publication_annotations|length > 0 and "MISSING" != dhus_publication_status  %}
    {% set dhus_publication_time_datetime = dhus_publication_annotations|map(attribute="annotationTimestamps")|flatten|selectattr("name", "equalto", "dhus_publication_time")|map(attribute="value")|sort|first %}
    {% set dhus_publication_time = dhus_publication_time_datetime|string %}
    {% set sensing_to_dhus_publication = ((dhus_publication_time_datetime - corrected_planned_imaging.stop).total_seconds() / 60)|round(3) %}
    {% do times_to_dhus_publication.append(((dhus_publication_time_datetime - corrected_planned_imaging.stop).total_seconds() / 60)) %}

    {% endif %}

    {% endfor %}
    {% if times_to_dhus_publication|length > 0 %}

    {% set datatake_annotations = complete_processing_event.explicitRef.annotations|selectattr("annotationCnf.name", "equalto", "DATATAKE")|list %}
    {% if datatake_annotations|length > 0 %}
    {% set datatake = datatake_annotations|map(attribute="annotationTexts")|flatten|selectattr("name", "equalto", "datatake_identifier")|map(attribute="value")|first %}
    {% else %}
    {% set datatake = "N/A" %}
    {% endif %}

    {% set mean_sensing_to_dhus_publication = (times_to_dhus_publication|sum / times_to_dhus_publication|length)|round(3) %}
    {
        "id": "{{ datastrip_uuid }}",
        "group": "{{ satellite }}",
        "x": "{{ complete_processing_event.start.isoformat() }}",
        "y": "{{ mean_sensing_to_dhus_publication }}",
        "tooltip": create_datastrip_e2e_timeliness_tooltip_text("{{ satellite }}", "{{ orbit }}", "{{ datatake }}", "<a href='/eboa_nav/query-er/{{ datastrip_uuid }}'>{{ datastrip }}</a>", "{{ mean_sensing_to_dhus_publication }}", "{{ planned_imaging.source.name }}", "/eboa_nav/query-event-links/{{ planned_imaging_uuid }}")
    },
    {% endif %}
    
    {% endfor %}
]
