
var processing_timeliness_per_step_timeline = [
    {% for sensing_identifier, timeliness_group in events["timeliness"]|sort(attribute="explicitRef.explicit_ref")|group_by_substring("explicitRef.explicit_ref", "41", "57") %}    
    {% for timeliness in timeliness_group %}
    {% set processing_validity = events["processing_validity"]|selectattr("explicitRef.explicit_ref", "in", timeliness.explicitRef.explicit_ref)|first %}
    
    {% set datatake_annotations = timeliness.explicitRef.annotations|selectattr("annotationCnf.name", "equalto", "DATATAKE")|list %}
    {% if datatake_annotations|length > 0 %}
    {% set datatake = datatake_annotations|map(attribute="annotationTexts")|flatten|selectattr("name", "equalto", "datatake_identifier")|map(attribute="value")|first %}
    {% else %}
    {% set datatake = "N/A" %}
    {% endif %}

    {% set level = timeliness.explicitRef.explicit_ref[9:19] %}

    {% set step_info_group = events["step_info"]|selectattr("explicitRef.explicit_ref", "in", timeliness.explicitRef.explicit_ref) %}

    {% for step_info in step_info_group %}

    {% set step_identifier = step_info.eventTexts|selectattr("name", "equalto", "id")|map(attribute="value")|first %}

    {% if level == "MSI_L1A_DS" %}
    {% set class_name = "background-light-yellow" %}
    {% elif level == "MSI_L1B_DS" %}
    {% set class_name = "background-light-blue" %}
    {% elif level == "MSI_L1C_DS" %}
    {% set class_name = "background-light-green" %}
    {% elif level == "MSI_L2A_DS" %}
    {% set class_name = "background-light-brown" %}
    {% else %}
    /* MSI_LO__DS */
    {% set class_name = "background-light-pink" %}
    {% endif %}
    {
        "id": "{{ step_info.event_uuid }}",
        "group": "",
        "timeline": "",
        "content": "{{ step_identifier }} / {{ sensing_identifier }}",
        "start": "{{ step_info.start.isoformat() }}",
        "stop": "{{ step_info.stop.isoformat() }}",
        "tooltip": "<table border='1'>" +
            "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-er/{{ timeliness.explicitRef.explicit_ref_uuid }}'>{{ timeliness.explicitRef.explicit_ref }}</a></td></tr>" +
            "<tr><td>Sensing start</td><td>{{ processing_validity.start.isoformat() }}</td></tr>" +
            "<tr><td>Sensing stop</td><td>{{ processing_validity.stop.isoformat() }}</td></tr>" +
            "<tr><td>Sensing duration (m)</td><td>{{ ((processing_validity.get_duration()) / 60)|round(3) }}</td></tr>" +
            "<tr><td>Processing start</td><td>{{ timeliness.start.isoformat() }}</td></tr>" +
            "<tr><td>Processing stop</td><td>{{ timeliness.stop.isoformat() }}</td></tr>" +
            "<tr><td>Processing duration (m)</td><td>{{ ((timeliness.get_duration()) / 60)|round(3) }}</td></tr>" +
            "<tr><td>Step start</td><td>{{ step_info.start.isoformat() }}</td></tr>" +
            "<tr><td>Step stop</td><td>{{ step_info.stop.isoformat() }}</td></tr>" +
            "<tr><td>Step duration (m)</td><td>{{ ((step_info.get_duration()) / 60)|round(3) }}</td></tr>" +
            "<tr><td>Step identifier</td><td>{{ step_identifier }}</td></tr>" +
            "<tr><td>Datatake</td><td>{{ datatake }}</td></tr>" +
            "</table>",
        "className": "{{ class_name }}"
    },
    {% endfor %}
    {% endfor %}
    {% endfor %}
]
