
var colors = {
    "S2A": {
        "stroke_color": "blue",
        "fill_color": "rgba(0,0,255,0.3)",
    },
    "S2B": {
        "stroke_color": "yellow",
        "fill_color": "rgba(255,255,0,0.3)",
    }
}
var datastrip_geometries = [
    {% set datastrips_by_satellite = events|events_group_by_text_value("satellite") %}
    {% for satellite in datastrips_by_satellite %}
    {% for datastrip in datastrips_by_satellite[satellite] %}
    
    {% set footprint_annotation = datastrip.explicitRef.annotations|selectattr("annotationCnf.name", "equalto", "FOOTPRINT")|first %}
    {% if footprint_annotation %}
    {% set geometry = footprint_annotation.annotationGeometries|selectattr("name", "equalto", "footprint")|first %}

    {% set datatake_annotation = datastrip.explicitRef.annotations|selectattr("annotationCnf.name", "equalto", "DATATAKE")|first %}
    {% set datatake = "N/A" %}
    {% if datatake_annotation %}
    {% set datatake = datatake_annotation.annotationTexts|selectattr("name", "equalto", "datatake_identifier")|map(attribute='value')|first %}
    {% endif %}
    {% set centres = datastrip.eventDoubles|selectattr("name", "equalto", "processing_centre")|map(attribute='value') %}
    {% set centre = "N/A" %}
    {% if centres|list|length > 0 %}
    {% set centre = centres|first|int %}
    {% endif %}

    {
        "id": "{{ datastrip.explicitRef.explicit_ref }}",
        "tooltip": create_tooltip("{{ datastrip.explicitRef.explicit_ref }}", "{{ satellite }}", "{{ datatake }}", "{{ centre }}", "{{ datastrip.start.isoformat() }}", "{{ datastrip.stop.isoformat() }}", "/eboa_nav/query-er/{{ datastrip.explicitRef.explicit_ref_uuid }}"),
        "style": {
            "stroke_color": colors["{{ satellite }}"]["stroke_color"],
            "fill_color": colors["{{ satellite }}"]["fill_color"],
            "text": "{{ satellite }}",
            "font_text": "bold"
        },
        "geometries": [
            {{ geometry.to_wkt() }},
        ]
    },
    {% endif %}
    {% endfor %}
    {% endfor %}
]
