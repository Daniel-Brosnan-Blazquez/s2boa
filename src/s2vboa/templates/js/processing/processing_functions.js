/* Function to create the text for the tooltip of the datastrip event information*/
function create_processing_tooltip_text(uuid, satellite, downlink_orbit, station, level, sensing_orbit, status, datastrip, start, stop, duration, sad_data){
    
    return "<table border='1'>" +
            "<tr><td>UUID</td><td>" + uuid + "</td></tr>" +
            "<tr><td>Satellite</td><td>" + satellite + "</td></tr>" +
            "<tr><td>Downlink orbit</td><td>" + downlink_orbit + "</td></tr>" +
            "<tr><td>Station</td><td>" + station + "</td></tr>" +
            "<tr><td>Level</td><td>" + level + "</td></tr>" +
            "<tr><td>Sensing orbit</td><td>" + sensing_orbit + "</td></tr>" +
            "<tr><td>Status</td><td>" + status + "</td></tr>" +
            '<tr><td>Datastrip</td><td>' + datastrip + '</td></tr>' +
            "<tr><td>Start</td><td>" + start + "</td></tr>" +
            "<tr><td>Stop</td><td>" + stop + "</td></tr>" +
            "<tr><td>Duration (m)</td><td>" + duration + "</td></tr>" +
            '<tr><td>SAD coverage</td><td>' + sad_data + '</td></tr>' +
            "</table>"
};