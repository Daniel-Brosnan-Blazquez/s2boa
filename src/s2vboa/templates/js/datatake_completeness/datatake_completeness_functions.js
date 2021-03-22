/* Function to create the text for the tooltip of the datatake event information*/
function create_datatake_completeness_tooltip_text(uuid, satellite, level, orbit, status, datastrip, imaging_mode, start, stop, duration){
    
    return "<table border='1'>" +
            "<tr><td>UUID</td><td>" + uuid + "</td></tr>" +
            "<tr><td>Satellite</td><td>" + satellite + "</td></tr>" +
            "<tr><td>Level</td><td>" + level + "</td></tr>" +
            "<tr><td>Sensing orbit</td><td>" + orbit + "</td></tr>" +
            "<tr><td>Status</td><td>" + status + "</td></tr>" +
            '<tr><td>Datastrip</td><td>' + datastrip + '</td></tr>' +
            "<tr><td>Imaging mode</td><td>" + imaging_mode + "</td></tr>" +
            "<tr><td>Start</td><td>" + start + "</td></tr>" +
            "<tr><td>Stop</td><td>" + stop + "</td></tr>" +
            "<tr><td>Duration (m)</td><td>" + duration + "</td></tr>" +
            "</table>"
};