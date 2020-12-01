
var processing_timeliness_per_step_timeline = [
    {% for sensing_identifier, timeliness_group in events["timeliness"]|sort(attribute="explicitRef.explicit_ref")|group_by_substring("explicitRef.explicit_ref", "41", "57") %}    
    {% for timeliness in timeliness_group %}
    {% set datatake_annotations = timeliness.explicitRef.annotations|selectattr("annotationCnf.name", "equalto", "DATATAKE")|list %}
    {% if datatake_annotations|length > 0 %}
    {% set datatake = datatake_annotations|map(attribute="annotationTexts")|flatten|selectattr("name", "equalto", "datatake_identifier")|map(attribute="value")|first %}
    {% else %}
    {% set datatake = "N/A" %}
    {% endif %}

    {% set level = timeliness.explicitRef.explicit_ref[9:19] %}

    {% set step_info_group = events["step_info"]|selectattr("explicitRef.explicit_ref", "in", timeliness.explicitRef.explicit_ref) %}

    {% for step_info in step_info_group %}

    {% set identifier = step_info.eventTexts|selectattr("name", "equalto", "id")|map(attribute="value")|first %}

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
        "content": "{{ sensing_identifier }} / {{ identifier }}",
        "start": "{{ step_info.start.isoformat() }}",
        "stop": "{{ step_info.stop.isoformat() }}",
        "tooltip": "",
        "className": "{{ class_name }}"
    },
    {% endfor %}
    {% endfor %}
    {% endfor %}
]
