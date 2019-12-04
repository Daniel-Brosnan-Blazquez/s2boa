
/* Function to create the text for the tooltip of the playback event information*/
function create_playback_tooltip_text(satellite, orbit, station, start, stop, playback_type, playback_mean, plan_file, uuid, link_to_details){
    const start_date = new Date(start);
    const stop_date = new Date(stop);
    const duration = ((stop_date.getTime() - start_date.getTime()) / (1000 * 60)).toFixed(3);

    return "<table border='1'>" +
            "<tr><td>UUID</td><td>" + uuid + "</td></tr>" +
            "<tr><td>Satellite</td><td>" + satellite + "</td></tr>" +
            "<tr><td>Orbit</td><td>" + orbit + "</td></tr>" +
            "<tr><td>Station</td><td>" + station + "</td></tr>" +
            "<tr><td>Start</td><td>" + start + "</td></tr>" +
            "<tr><td>Stop</td><td>" + stop + "</td></tr>" +
            "<tr><td>Duration(m)</td><td>" + duration + "</td></tr>" +
            "<tr><td>Playback type</td><td>" + playback_type + "</td></tr>" +
            "<tr><td>Playback mean</td><td>" + playback_mean + "</td></tr>" +
            "<tr><td>Plan file</td><td>" + plan_file + "</td></tr>" +
            '<tr><td>Details</td><td><a href="' + link_to_details + '"><i class="fa fa-link"></i></a></td></tr>' +
            "</table>"
};

/* Function to create the text for the tooltip of the imaging event information */
function create_imaging_tooltip_text(satellite, orbit, start, stop, imaging_mode, record_type, plan_file, uuid, link_to_details){
    const start_date = new Date(start);
    const stop_date = new Date(stop);
    const duration = ((stop_date.getTime() - start_date.getTime()) / (1000 * 60)).toFixed(3);

    return "<table border='1'>" +
            "<tr><td>UUID</td><td>" + uuid + "</td></tr>" +
            "<tr><td>Satellite</td><td>" + satellite + "</td></tr>" +
            "<tr><td>Orbit</td><td>" + orbit + "</td></tr>" +
            "<tr><td>Start</td><td>" + start + "</td></tr>" +
            "<tr><td>Stop</td><td>" + stop + "</td></tr>" +
            "<tr><td>Duration(m)</td><td>" + duration + "</td></tr>" +
            "<tr><td>Imaging mode</td><td>" + imaging_mode + "</td></tr>" +
            "<tr><td>Record type</td><td>" + record_type + "</td></tr>" +
            "<tr><td>Plan file</td><td>" + plan_file + "</td></tr>" +
            '<tr><td>Details</td><td><a href="' + link_to_details + '"><i class="fa fa-link"></i></a></td></tr>' +
            "</table>"
};
