
{% set complete_processing_events = info["processing_completeness"][level]|rejectattr("event_uuid", "in", missing_processing_event_uuids[level])|list %}

var complete_segments = [
    {% for complete_processing_event in complete_processing_events %}
    {% set planned_imaging_uuid = complete_processing_event.eventLinks|selectattr("name", "equalto", "PLANNED_IMAGING")|map(attribute="event_uuid_link")|first %}
    {% set planned_imaging = info["imaging"]|selectattr("event_uuid", "equalto", planned_imaging_uuid)|first %}

    {% set corrected_planned_imaging_uuid = planned_imaging.eventLinks|selectattr("name", "equalto", "TIME_CORRECTION")|map(attribute="event_uuid_link")|first %}

    {% set satellite = complete_processing_event.eventTexts|selectattr("name", "equalto", "satellite")|map(attribute='value')|first|string %}

    {% set sensing_orbit_values = complete_processing_event.eventDoubles|selectattr("name", "equalto", "sensing_orbit")|map(attribute='value')|list %}
    {% if sensing_orbit_values|length > 0 %}
    {% set sensing_orbit = sensing_orbit_values|first|int %}
    {% else %}
    {% set sensing_orbit = "N/A" %}
    {% endif %}

    {% set missing_dissemination_tiles = [] %}
    {% set missing_publication_tiles = [] %}
    {% set tile_uuids = complete_processing_event.explicitRef.explicitRefLinks|selectattr("name", "equalto", "TILE")|map(attribute="explicit_ref_uuid_link")|list %}

    {% set tile_infos = info["tls"][level]|selectattr("explicit_ref_uuid", "in", tile_uuids)|list %}

    {% for tile_info in tile_infos %}

    {% set tile_uuid = tile_info.explicit_ref_uuid %}
    {% set tile = tile_info.explicit_ref %}
    {% set dam_publication_annotations = tile_info.annotations|selectattr("annotationCnf.name", "equalto", "CATALOGING_TIME")|list %}
    {% set dhus_dissemination_annotations = tile_info.annotations|selectattr("annotationCnf.name", "equalto", "DHUS_DISSEMINATION_TIME")|list %}
    {% set dhus_publication_annotations = tile_info.annotations|selectattr("annotationCnf.name", "equalto", "DHUS_PUBLICATION_TIME")|list %}
    {% set dhus_product_annotation = tile_info.annotations|selectattr("annotationCnf.name", "equalto", "USER_PRODUCT")|first %}
    {% set footprint_annotations = tile_info.annotations|selectattr("annotationCnf.name", "equalto", "FOOTPRINT")|list %}

    {% set dam_publication_status = dam_publication_annotations|map(attribute="annotationTexts")|flatten|selectattr("name", "equalto", "status")|map(attribute="value")|first %}
    {% set dhus_dissemination_status = dhus_dissemination_annotations|map(attribute="annotationTexts")|flatten|selectattr("name", "equalto", "status")|map(attribute="value")|first %}
    {% set dhus_publication_status = dhus_publication_annotations|map(attribute="annotationTexts")|flatten|selectattr("name", "equalto", "status")|map(attribute="value")|first %}

    {% set footprint = "N/A" %}
    {% if footprint_annotations|length > 0 %}
    {% set footprint = footprint_annotations|map(attribute="annotationGeometries")|flatten|selectattr("name", "equalto", "footprint")|first %}
    {% endif %}

    {% set dhus_product = "N/A" %}
    {% if dhus_product_annotation %}
    {% set dhus_product = dhus_product_annotation.annotationTexts|selectattr("name", "equalto", "product_name")|map(attribute="value")|first|string %}
    {% endif %}
    
    {% if dhus_publication_annotations|length > 0 and "MISSING" != dhus_publication_status  %}
    {% set status = "OK" %}
    {% elif dhus_dissemination_annotations|length > 0 and "MISSING" != dhus_dissemination_status  %}
    {% set status = "MISSING DHUS PUBLICATION" %}
    {% elif dam_publication_annotations|length > 0 and "MISSING" != dam_publication_status %}
    {% set status = "MISSING DHUS DISSEMINATION" %}
    {% else %}
    {% set status = "MISSING DAM PUBLICATION" %}
    {% endif %}

    {% if status == "MISSING DHUS PUBLICATION" %}
    {% do missing_publication_tiles.append({"tile": tile, "dhus_product": dhus_product, "status": status, "footprint": footprint}) %}
    {% elif status == "MISSING DHUS DISSEMINATION" %}
    {% do missing_dissemination_tiles.append({"tile": tile, "dhus_product": dhus_product, "status": status, "footprint": footprint}) %}
    {% endif %}

    {% endfor %}

    {% set status = "COMPLETE" %}
    {% set stroke_color = "green" %}
    {% set status_class = "bold-green" %}
    {% set fill_color = "rgba(0,255,0,0.3)" %}
    {% if missing_publication_tiles|length == tile_infos|length %}
    {% set stroke_color = "yellow" %}
    {% set status = "MISSING PUBLICATION" %}
    {% set status_class = "bold-yellow" %}
    {% set fill_color = "rgba(245, 229, 27, 0.3)" %}
    {% elif missing_dissemination_tiles|length == tile_infos|length %}
    {% set stroke_color = "yellow" %}
    {% set status = "MISSING DISSEMINATION" %}
    {% set status_class = "bold-yellow" %}
    {% set fill_color = "rgba(245, 229, 27, 0.3)" %}
    {% elif missing_dissemination_tiles|length > 0 %}
    {% set status = "INCOMPLETE DISSEMINATION" %}
    {% set stroke_color = "orange" %}
    {% set status_class = "bold-orange" %}
    {% set fill_color = "rgba(255,165,0,0.3)" %}
    {% endif %}
     
    {
        "id": "{{ complete_processing_event.event_uuid }}",
        "tooltip": create_processing_tooltip_text("{{ satellite }}", "{{ sensing_orbit }}", "<a class='{{ status_class }}' href='/views/dhus-completeness-by-datatake/{{ corrected_planned_imaging_uuid }}'>{{ status }}</a>", "<a href='/eboa_nav/query-er-links/{{ complete_processing_event.explicitRef.explicit_ref_uuid }}'>{{ complete_processing_event.explicitRef.explicit_ref }}</a>", "{{ complete_processing_event.start.isoformat() }}", "{{ complete_processing_event.stop.isoformat() }}", "{{ planned_imaging.source.name }}", "{{ complete_processing_event.event_uuid }}", "/eboa_nav/query-event-links/{{ planned_imaging_uuid }}"),
        "geometries": [
            {% for geometry in complete_processing_event.eventGeometries %}
            {{ geometry.to_wkt() }},
            {% endfor %}
        ],
        "style": {
            "stroke_color": "{{ stroke_color }}",
            "fill_color": "{{ fill_color }}",
        }
    },

    {% if missing_dissemination_tiles|length < tile_infos|length %}
    {% for tile in missing_dissemination_tiles %}
    {% if tile["footprint"] != "N/A" %}
    {% set tile_name = tile["tile"] %}
    {% set status = tile["status"] %}
    {% set geometry = tile["footprint"] %}
    {
        "id": "{{ tile['tile'] }}",
        "tooltip": create_tile_tooltip_text("{{ satellite }}", "{{ sensing_orbit }}", "<span class='bold-red'>{{ status }}</span>", "<a href='/eboa_nav/query-er-by-name/{{ tile_name }}'>{{ tile_name }}</a>", "<a href='/eboa_nav/query-er/{{ complete_processing_event.explicitRef.explicit_ref_uuid }}'>{{ complete_processing_event.explicitRef.explicit_ref }}</a>", "{{ planned_imaging.source.name }}", "/eboa_nav/query-event-links/{{ planned_imaging_uuid }}"),
        "geometries": [
            {{ geometry.to_wkt() }},
        ],
        "style": {
            "stroke_color": "red",
            "fill_color": "rgba(255,0,0,0.3)",
        }
    },
    {% endif %}
    {% endfor %}
    {% endif %}
    
    {% endfor %}
]
