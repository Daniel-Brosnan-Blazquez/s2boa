
{% set data_volume = [0] %}
{% set datastrips = [] %}

var data_volume_evolution = [
    
    {% set datastrips_by_sensing_identifier = events | events_group_by_ref_annotation("sensing_identifier", "text", "SENSING_IDENTIFIER") %}
    {% for sensing_identifier in datastrips_by_sensing_identifier %}

    {% set datastrips = datastrips_by_sensing_identifier[sensing_identifier]|list %}

    {% set data_volume_sensing_identifier = [0] %}
    {% set datatakes = [] %}
    {% for datastrip in datastrips %}
    {% set size_annotation = datastrip.explicitRef.annotations|selectattr("annotationCnf.name", "equalto", "SIZE")|first %}
    {% if size_annotation %}
    {% set size = size_annotation.annotationDoubles|selectattr("name", "equalto", "aggregated_size")|map(attribute="value")|first|float %}
    {% set current_data_volume_sensing_identifier = data_volume_sensing_identifier.pop() %}
    {% do data_volume_sensing_identifier.append(current_data_volume_sensing_identifier + size) %}
    {% endif %}
    
    {% set datatake_annotation = datastrip.explicitRef.annotations|selectattr("annotationCnf.name", "equalto", "DATATAKE")|first %}
    {% if datatake_annotation %}
    {% do datatakes.append(datatake_annotation.annotationTexts|selectattr("name", "equalto", "datatake_identifier")|map(attribute="value")|first) %}
    {% endif %}
    {% endfor %}

    {% set current_data_volume = data_volume.pop() %}
    {% do data_volume.append(current_data_volume + data_volume_sensing_identifier[0]) %}

    {
        "id": "{{ sensing_identifier }}",
        "group": "",
        "x": "{{ datastrips[0].start }}",
        "y": "{{ (data_volume[0] / 1000 / 1000 / 1000) | round(3) }}",
        "tooltip": "<table border='1'>" +
            "<tr><td>Sensing identifier</td><td>{{ sensing_identifier }}</td></tr>" +
            '<tr><td>Datastrips</td><td>' +
            {% for datastrip in datastrips %}
        '<a href="/eboa_nav/query-er/{{ datastrip.explicitRef.explicit_ref_uuid }}">{{ datastrip.explicitRef.explicit_ref }}</a>  ' +
            {% endfor %}
        '</td></tr>' +
            "<tr><td>Size of datastrips</td><td>{{ (data_volume_sensing_identifier[0] / 1000 / 1000 / 1000) | round(3) }}</td></tr>" +
            "<tr><td>Accumulated size</td><td>{{ (data_volume[0] / 1000 / 1000 / 1000) | round(3) }}</td></tr>" +
            "<tr><td>Datatakes</td><td>" +
            {% for datatake in datatakes|unique %}
        "{{ datatake }}  " +
        {% endfor %}        
        "</td></tr>" +
            "<tr><td>Start</td><td>{{ datastrips[0].start.isoformat() }}</td></tr>" +
            "<tr><td>Stop</td><td>{{ datastrips[0].stop.isoformat() }}</td></tr>" +
            "<tr><td>Duration(m)</td><td>{{ (datastrips[0].get_duration() / 60)| round(3) }}</td></tr>" +
            "</table>",
    },
    {% endfor %}
]
