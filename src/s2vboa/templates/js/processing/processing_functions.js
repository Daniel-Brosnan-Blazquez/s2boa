/* Function to create the text for the tooltip of the datastrip event information*/
function create_processing_tooltip_text(uuid, satellite, downlink_orbit, station, level, sensing_orbit, status, sad_data, link_to_details){
    
    return "<table border='1'>" +
            "<tr><td>UUID</td><td>" + uuid + "</td></tr>" +
            "<tr><td>Satellite</td><td>" + satellite + "</td></tr>" +
            "<tr><td>Downlink orbit</td><td>" + downlink_orbit + "</td></tr>" +
            "<tr><td>Station</td><td>" + station + "</td></tr>" +
            "<tr><td>Level</td><td>" + level + "</td></tr>" +
            "<tr><td>Sensing orbit</td><td>" + sensing_orbit + "</td></tr>" +
            "<tr><td>Status</td><td>" + status + "</td></tr>" +
            '<tr><td>SAD data</td><td><a href="' + sad_data + '"><i class="fa fa-link"></i></a></td></tr>' +
            '<tr><td>Details</td><td><a href="' + link_to_details + '"><i class="fa fa-link"></i></a></td></tr>' +
            "</table>"
};