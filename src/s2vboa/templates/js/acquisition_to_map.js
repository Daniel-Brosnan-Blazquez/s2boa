
var acquisition_geometries_missing = []
var acquisition_geometries_received = []
{% for event in events %}
  {% set original_playback_uuid = event.eventLinks|selectattr("name", "equalto", "PLANNED_PLAYBACK")|map(attribute='event_uuid_link')|first %}
  {% set original_playback = acquisition_events["playback"]["prime_events"]|selectattr("event_uuid", "equalto", original_playback_uuid)|first %}
  {% set satellite = original_playback.eventTexts|selectattr("name", "equalto", "satellite")|map(attribute='value')|first|string %}
  {% set orbit = original_playback.eventDoubles|selectattr("name", "equalto", "start_orbit")|map(attribute='value')|first|int %}
  {% set station = original_playback.eventTexts|selectattr("name", "equalto", "station")|map(attribute='value')|first|string %}
  {% set playback_type = original_playback.eventTexts|selectattr("name", "equalto", "playback_type")|map(attribute='value')|first|string %}
  {% set playback_mean = original_playback.eventTexts|selectattr("name", "equalto", "playback_mean")|map(attribute='value')|first|string %}
  {% set status = event.eventTexts|selectattr("name", "equalto", "status")|map(attribute='value')|first|string %}
  {% if status == "MISSING" %}
    acquisition_geometries_missing.push({
          "id": "{{ original_playback.event_uuid }}",
          "tooltip": create_acquisition_tooltip_text("{{ satellite }}", "{{ orbit }}", "{{ station }}", "{{ original_playback.start.isoformat() }}", "{{ original_playback.stop.isoformat() }}", "{{ playback_type }}", "{{ playback_mean }}", "{{ original_playback.source.name }}", "{{ original_playback.event_uuid }}", "/eboa_nav/query-event-links/{{ original_playback.event_uuid }}"),
          "geometries": [
              {% for geometry in event.eventGeometries %}
              {{ geometry.to_wkt() }},
              {% endfor %}
          ]
      });
  {% else %}
    acquisition_geometries_received.push({
          "id": "{{ original_playback.event_uuid }}",
          "tooltip": create_acquisition_tooltip_text("{{ satellite }}", "{{ orbit }}", "{{ station }}", "{{ original_playback.start.isoformat() }}", "{{ original_playback.stop.isoformat() }}", "{{ playback_type }}", "{{ playback_mean }}", "{{ original_playback.source.name }}", "{{ original_playback.event_uuid }}", "/eboa_nav/query-event-links/{{ original_playback.event_uuid }}"),
          "geometries": [
              {% for geometry in event.eventGeometries %}
              {{ geometry.to_wkt() }},
              {% endfor %}
          ]
      });
  {% endif %}
{% endfor %}
