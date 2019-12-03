
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
    {% set datastrips_by_satellite = datastrips|events_group_by_text_value("satellite") %}
    {% for satellite in datastrips_by_satellite %}
    {% for datastrip in datastrips_by_satellite[satellite] %}
    
    {% set footprint_annotation = datastrip.explicitRef.annotations|selectattr("annotationCnf.name", "equalto", "FOOTPRINT")|first %}
    {% if footprint_annotation %}
    {% set geometry = footprint_annotation.annotationGeometries|selectattr("name", "equalto", "footprint")|first %}

    {% set sensing_orbits = datastrip.eventDoubles|selectattr("name", "equalto", "sensing_orbit")|map(attribute='value') %}
    {% set sensing_orbit = "N/A" %}
    {% if sensing_orbits|list|length > 0 %}
    {% set sensing_orbit = sensing_orbits|first|int %}
    {% endif %}
    {% set centres = datastrip.eventDoubles|selectattr("name", "equalto", "processing_centre")|map(attribute='value') %}
    {% set centre = "N/A" %}
    {% if centres|list|length > 0 %}
    {% set centre = centres|first|int %}
    {% endif %}

    {
        "id": "{{ datastrip.explicitRef }}",
        "tooltip": "<table border='1'>" +
            "<tr><td>Satellite</td><td>{{ satellite }}</td>" +
            "<tr><td>Sensing orbit</td><td>{{ sensing_orbit }}</td>" +
            "<tr><td>StationProcessing centre</td><td>{{ centre }}</td>" +
            "<tr><td>Start</td><td>{{ datastrip.start.isoformat() }}</td>" +
            "<tr><td>Stop</td><td>{{ datastrip.stop.isoformat() }}</td>" +
            "<tr><td>Duration(m)</td><td>{{ (datastrip.get_duration() / 60)| round(3) }}</td>" +
            '<tr><td>Details</td><td><a href="/eboa_nav/query-er/{{ datastrip.explicitRef.explicit_ref_uuid }}"><i class="fa fa-link"></i></a></td>' +
            "</tr></table>",
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
