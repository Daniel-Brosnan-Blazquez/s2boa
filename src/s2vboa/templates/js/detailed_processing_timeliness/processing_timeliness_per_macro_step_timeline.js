
{% set macro_micro_step_relation = {
    "MSI_L0__DS": {},
    "MSI_L1B_DS": {
        "step_Init_Workflow": {"workflow": "L1AB Workflow", "macro_step": "L1A/B Radiometric Processing"},
        "step_GSE": {"workflow": "L1AB Workflow", "macro_step": "L1A/B Radiometric Processing"},
        "step_Unformat_Ds": {"workflow": "L1AB Workflow", "macro_step": "L1A/B Radiometric Processing"},
        "step_Unformat_Gr": {"workflow": "L1AB Workflow", "macro_step": "L1A/B Radiometric Processing"},
        "step_QL_Decomp": {"workflow": "L1AB Workflow", "macro_step": "L1A/B Radiometric Processing"},
        "step_Update_Loc": {"workflow": "L1AB Workflow", "macro_step": "L1A/B Radiometric Processing"},
        "step_QL_Cloud_Mask": {"workflow": "L1AB Workflow", "macro_step": "L1A/B Radiometric Processing"},
        "step_On_Board_Decompression": {"workflow": "L1AB Workflow", "macro_step": "L1A/B Radiometric Processing"},
        "step_Init_Loc_L1": {"workflow": "L1AB Workflow", "macro_step": "L1A/B Radiometric Processing"},
        "step_RADIO_AB": {"workflow": "L1AB Workflow", "macro_step": "L1A/B Radiometric Processing"},
        "step_RADIO_AB_Refining": {"workflow": "L1AB Workflow", "macro_step": "L1A/B Radiometric Processing"},
        "step_Radio_Finalise": {"workflow": "L1AB Workflow", "macro_step": "L1A/B Radiometric Processing"},
        "step_Dispatch_Metadata": {"workflow": "L1AB Workflow", "macro_step": "L1A/B Radiometric Processing"},
        "step_Get_GRI": {"workflow": "L1AB Workflow", "macro_step": "L1A/B Radiometric Processing"},
        "step_GRI_Decomp_Mask_Aggregation": {"workflow": "L1AB Workflow", "macro_step": "L1A/B Radiometric Processing"},
        "step_Init_VS_Geo_Refining": {"workflow": "L1AB Workflow", "macro_step": "L1B Geo Refining"},
        "step_Resample_VS_Refining_Gri": {"workflow": "L1AB Workflow", "macro_step": "L1B Geo Refining"},
        "step_Resample_VS_Refining_Product": {"workflow": "L1AB Workflow", "macro_step": "L1B Geo Refining"},
        "step_TP_Collect_Refining": {"workflow": "L1AB Workflow", "macro_step": "L1B Geo Refining"},
        "step_TP_Filter_Refining": {"workflow": "L1AB Workflow", "macro_step": "L1B Geo Refining"},
        "step_Spatio_Refining": {"workflow": "L1AB Workflow", "macro_step": "L1B Geo Refining"},
        "step_GEO1B_Finalise": {"workflow": "L1AB Workflow", "macro_step": "L1A/B image compression and PDI generation"},
        "step_Format_Image_L1A": {"workflow": "L1AB Workflow", "macro_step": "L1A/B image compression and PDI generation"},
        "step_Format_Metadata_OLQC_L1A_Gr": {"workflow": "L1AB Workflow", "macro_step": "L1A/B image compression and PDI generation"},
        "step_Format_Metadata_L1A_Ds": {"workflow": "L1AB Workflow", "macro_step": "L1A/B image compression and PDI generation"},
        "step_Format_Image_L1B": {"workflow": "L1AB Workflow", "macro_step": "L1A/B image compression and PDI generation"},
        "step_Format_Metadata_OLQC_L1B_Gr": {"workflow": "L1AB Workflow", "macro_step": "L1A/B image compression and PDI generation"},
        "step_Inv_Metadata_L1B_Gr": {"workflow": "L1AB Workflow", "macro_step": "L1A/B image compression and PDI generation"},
        "step_Format_Metadata_L1B_Ds": {"workflow": "L1AB Workflow", "macro_step": "L1A/B image compression and PDI generation"},
        "step_OLQC_L1B_Ds": {"workflow": "L1AB Workflow", "macro_step": "L1A/B image compression and PDI generation"},
        "step_Archive_L1B_Request": {"workflow": "L1AB Workflow", "macro_step": "L1A/B image compression and PDI generation"},
        "step_Workflow_Cancel": {"workflow": "L1AB Workflow", "macro_step": "L1A/B image compression and PDI generation"},
        "step_Get_List_Tile": {"workflow": "L1AB Workflow", "macro_step": "L1C Request"},
        "step_Get_List_Tile_Request_L1C": {"workflow": "L1AB Workflow", "macro_step": "L1C Request"}
    },
    "MSI_L1C_DS": {
        "Init_Workflow": {"workflow": "L1C Workflow", "macro_step": "L1C Initialization"},
        "Tile_Init": {"workflow": "L1C Workflow", "macro_step": "L1C processing and PDI generation"},
        "Gen_Ortho_Toa": {"workflow": "L1C Workflow", "macro_step": "L1C processing and PDI generation"},
        "Tile_Finalize_MS2": {"workflow": "L1C Workflow", "macro_step": "L1C processing and PDI generation"},
        "Format_Image_L1C": {"workflow": "L1C Workflow", "macro_step": "L1C processing and PDI generation"},
        "Format_Image_TCI": {"workflow": "L1C Workflow", "macro_step": "L1C processing and PDI generation"},
        "Format_Metadata_Tile_OLQC_Inv_Metadata_L1C": {"workflow": "L1C Workflow", "macro_step": "L1C processing and PDI generation"},
        "Format_Metadata_L1C_Ds": {"workflow": "L1C Workflow", "macro_step": "L1C processing and PDI generation"},
        "OLQC_L1C_Ds": {"workflow": "L1C Workflow", "macro_step": "L1C processing and PDI generation"},
        "Inv_Metadata_L1C_Ds": {"workflow": "L1C Workflow", "macro_step": "L1C processing and PDI generation"},
        "Archive_TILE": {"workflow": "L1C Workflow", "macro_step": "L1C processing and PDI generation"},
        "Archive_TCI": {"workflow": "L1C Workflow", "macro_step": "L1C processing and PDI generation"},
        "Workflow_Cancel": {"workflow": "L1C Workflow", "macro_step": "L1C processing and PDI generation"},
        "Request_L2A": {"workflow": "L1C Workflow", "macro_step": "L2A Request"},
    },
    "MSI_L2A_DS": {
        "Init_Workflow": {"workflow": "L2A Workflow", "macro_step": "L2A Initialization"},
        "sen2Cor_DS": {"workflow": "L2A Workflow", "macro_step": "L2A processing and PDI generation"},
        "sen2Cor_TL_20": {"workflow": "L2A Workflow", "macro_step": "L2A processing and PDI generation"},
        "sen2Cor_TL_10": {"workflow": "L2A Workflow", "macro_step": "L2A processing and PDI generation"},
        "Format_Tiles": {"workflow": "L2A Workflow", "macro_step": "L2A processing and PDI generation"},
        "L2A_OLQC_TL": {"workflow": "L2A Workflow", "macro_step": "L2A processing and PDI generation"},
        "Inv_Metadata_L2A_TL": {"workflow": "L2A Workflow", "macro_step": "L2A processing and PDI generation"},
        "L2A_OLQC_DS": {"workflow": "L2A Workflow", "macro_step": "L2A processing and PDI generation"},
        "Inv_Metadata_L2A_Ds": {"workflow": "L2A Workflow", "macro_step": "L2A processing and PDI generation"},
        "Archive_TILE_L2A": {"workflow": "L2A Workflow", "macro_step": "L2A processing and PDI generation"},
        "workflow_Clean": {"workflow": "L2A Workflow", "macro_step": "L2A processing and PDI generation"}
    }
} %}

var processing_timeliness_per_macro_step_timeline = [
    {% set macro_steps_segments = {} %}
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

    {% set macro_step_timestamps = {} %}
    {% do macro_steps_segments.update({timeliness.explicitRef.explicit_ref: {"id": timeliness.explicitRef.explicit_ref_uuid,
                                                                             "sensing_identifier": sensing_identifier,
                                                                             "sensing_start": processing_validity.start.isoformat(),
                                                                             "sensing_stop": processing_validity.stop.isoformat(),
                                                                             "sensing_duration": ((processing_validity.get_duration()) / 60)|round(3),
                                                                             "processing_start": timeliness.start.isoformat(),
                                                                             "processing_stop": timeliness.stop.isoformat(),
                                                                             "processing_duration": ((timeliness.get_duration()) / 60)|round(3),
                                                                             "datatake": datatake,
                                                                             "macro_step_timestamps": macro_step_timestamps}}) %}

    {% set step_info_group = events["step_info"]|selectattr("explicitRef.explicit_ref", "in", timeliness.explicitRef.explicit_ref) %}
    {% for step_info in step_info_group %}

    {% set step_identifier = step_info.eventTexts|selectattr("name", "equalto", "id")|map(attribute="value")|first %}

    {% set micro_step_group_list = ["N/A"] %}
    {% for micro_step_group_definition in macro_micro_step_relation[level].keys() %}
    {% if step_identifier.startswith(micro_step_group_definition) %}
    {% do micro_step_group_list.pop() %}
    {% do micro_step_group_list.append(micro_step_group_definition) %}
    {% endif %}
    {% endfor %}

    {% set micro_step_group = micro_step_group_list[0] %}
    {% if micro_step_group == "N/A" %}
    {% set macro_step = "N/A" %}
    {% else %}
    {% set macro_step = macro_micro_step_relation[level][micro_step_group]["macro_step"] %}
    {% endif %}

    {% if not macro_step in macro_steps_segments[timeliness.explicitRef.explicit_ref]["macro_step_timestamps"] %}
    {% do macro_step_timestamps.update({macro_step: []}) %}
    {% endif %}
    {% do macro_step_timestamps.update({macro_step: macro_step_timestamps[macro_step] + [step_info.start]}) %}
    {% do macro_step_timestamps.update({macro_step: macro_step_timestamps[macro_step] + [step_info.stop]}) %}
    
    {% endfor %}
    {% endfor %}
    {% endfor %}

    {% for datastrip in macro_steps_segments.keys() %}

    {% for macro_step in macro_steps_segments[datastrip]["macro_step_timestamps"].keys() %}

    {% set start = macro_steps_segments[datastrip]["macro_step_timestamps"][macro_step]|sort|first %}
    {% set stop = macro_steps_segments[datastrip]["macro_step_timestamps"][macro_step]|sort|last %}

    {% set level = datastrip[9:19] %}

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

    {% if macro_step == "N/A" %}
    {% set class_name = "background-red" %}
    {% endif %}
    
    {
        "id": "{{ macro_step }} / {{ macro_steps_segments[datastrip]['id'] }}",
        "group": "",
        "timeline": "",
        "content": "{{ macro_step }} / {{ macro_steps_segments[datastrip]['sensing_identifier'] }}",
        "start": "{{ start.isoformat() }}",
        "stop": "{{ stop.isoformat() }}",
        "tooltip": "<table border='1'>" +
            "<tr><td>Datastrip</td><td><a href='/eboa_nav/query-er/{{ macro_steps_segments[datastrip]['id'] }}'>{{ datastrip }}</a></td></tr>" +
            "<tr><td>Sensing start</td><td>{{ macro_steps_segments[datastrip]['sensing_start'] }}</td></tr>" +
            "<tr><td>Sensing stop</td><td>{{ macro_steps_segments[datastrip]['sensing_stop'] }}</td></tr>" +
            "<tr><td>Sensing duration (m)</td><td>{{ macro_steps_segments[datastrip]['sensing_duration'] }}</td></tr>" +
            "<tr><td>Processing start</td><td>{{ macro_steps_segments[datastrip]['processing_start'] }}</td></tr>" +
            "<tr><td>Processing stop</td><td>{{ macro_steps_segments[datastrip]['processing_stop'] }}</td></tr>" +
            "<tr><td>Processing duration (m)</td><td>{{ macro_steps_segments[datastrip]['processing_duration'] }}</td></tr>" +
            "<tr><td>Macro step</td><td>{{ macro_step }}</td></tr>" +
            "<tr><td>Macro step start</td><td>{{ start.isoformat() }}</td></tr>" +
            "<tr><td>Macro step stop</td><td>{{ stop.isoformat() }}</td></tr>" +
            "<tr><td>Macro step duration (m)</td><td>{{ ((stop - start).total_seconds() / 60)|round(3) }}</td></tr>" +
            "<tr><td>Datatake</td><td>{{ macro_steps_segments[datastrip]['datatake'] }}</td></tr>" +
            "</table>",
        "className": "{{ class_name }}"
    },
    {% endfor %}
    {% endfor %}
]

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
    
{% set micro_step_group_list = ["N/A"] %}
{% for micro_step_group_definition in macro_micro_step_relation[level].keys() %}
{% if step_identifier.startswith(micro_step_group_definition) %}
{% do micro_step_group_list.pop() %}
{% do micro_step_group_list.append(micro_step_group_definition) %}
{% endif %}
{% endfor %}

{% set micro_step_group = micro_step_group_list[0] %}
{% if micro_step_group == "N/A" %}
{% set macro_step = "N/A" %}
{% else %}
{% set macro_step = macro_micro_step_relation[level][micro_step_group]["macro_step"] %}
{% endif %}
console.log("LEVEL: {{ level }}, MICRO STEP: {{ step_identifier }}, MICRO STEP GROUP: {{ micro_step_group }}, MACRO STEP: {{ macro_step }}")
{% if not step_identifier.startswith(macro_micro_step_relation[level].keys()|convert_to_tuple) %}
console.log("MISSING STEP: {{ step_identifier }}, level: {{ level }}")
{% set class_name = "background-red" %}
{% endif %}

{% endfor %}
{% endfor %}
{% endfor %}
