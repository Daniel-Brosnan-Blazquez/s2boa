
/* Function to create the text for the tooltip of the processing event information*/
function create_processing_tooltip_text(satellite, orbit, status, datastrip, start, stop, plan_file, processing_uuid, link_to_planned_imaging_details){
    const start_date = new Date(start);
    const stop_date = new Date(stop);
    const duration = ((stop_date.getTime() - start_date.getTime()) / (1000 * 60)).toFixed(3);

    return "<table border='1'>" +
        "<tr><td>UUID</td><td>" + processing_uuid + "</td></tr>" +
        "<tr><td>Satellite</td><td>" + satellite + "</td></tr>" +
        "<tr><td>Orbit</td><td>" + orbit + "</td></tr>" +
        "<tr><td>Datastrip</td><td>" + datastrip + "</td></tr>" +
        "<tr><td>Status</td><td>" + status + "</td></tr>" +
        "<tr><td>Start</td><td>" + start + "</td></tr>" +
        "<tr><td>Stop</td><td>" + stop + "</td></tr>" +
        "<tr><td>Duration(m)</td><td>" + duration + "</td></tr>" +
        "<tr><td>Plan file</td><td>" + plan_file + "</td></tr>" +
        '<tr><td>Planned imaging</td><td><a href="' + link_to_planned_imaging_details + '"><i class="fa fa-link"></i></a></td></tr>' +
        "</table>"
};

/* Function to create the text for the tooltip of the tile information*/
function create_tile_tooltip_text(satellite, orbit, status, tile, datastrip, plan_file, link_to_planned_imaging_details){

    return "<table border='1'>" +
        "<tr><td>Tile</td><td>" + tile + "</td></tr>" +
        "<tr><td>Satellite</td><td>" + satellite + "</td></tr>" +
        "<tr><td>Orbit</td><td>" + orbit + "</td></tr>" +
        "<tr><td>Datastrip</td><td>" + datastrip + "</td></tr>" +
        "<tr><td>Status</td><td>" + status + "</td></tr>" +
        "<tr><td>Plan file</td><td>" + plan_file + "</td></tr>" +
        '<tr><td>Planned imaging</td><td><a href="' + link_to_planned_imaging_details + '"><i class="fa fa-link"></i></a></td></tr>' +
        "</table>"
};

/* Function to create the text for the tooltip of the tile e2e timeliness*/
function create_tile_e2e_timeliness_tooltip_text(satellite, orbit, tile, delta_to_dhus_publication, datastrip, plan_file, link_to_planned_imaging_details){

    return "<table border='1'>" +
        "<tr><td>Tile</td><td>" + tile + "</td></tr>" +
        "<tr><td>Satellite</td><td>" + satellite + "</td></tr>" +
        "<tr><td>Orbit</td><td>" + orbit + "</td></tr>" +
        "<tr><td>Datastrip</td><td>" + datastrip + "</td></tr>" +
        "<tr><td>Sensing stop - publication in DHUS (m)</td><td>" + delta_to_dhus_publication + "</td></tr>" +
        "<tr><td>Plan file</td><td>" + plan_file + "</td></tr>" +
        '<tr><td>Planned imaging</td><td><a href="' + link_to_planned_imaging_details + '"><i class="fa fa-link"></i></a></td></tr>' +
        "</table>"
};

/* Function to create the text for the tooltip of the datastrip e2e timeliness*/
function create_datastrip_e2e_timeliness_tooltip_text(satellite, orbit, datatake, datastrip, mean_sensing_to_dhus_publication, plan_file, link_to_planned_imaging_details){

    return "<table border='1'>" +
        "<tr><td>Datatake</td><td>" + datatake + "</td></tr>" +
        "<tr><td>Datastrip</td><td>" + datastrip + "</td></tr>" +
        "<tr><td>Satellite</td><td>" + satellite + "</td></tr>" +
        "<tr><td>Orbit</td><td>" + orbit + "</td></tr>" +
        "<tr><td>Mean (sensing stop - publication in DHUS) of related tiles (m)</td><td>" + mean_sensing_to_dhus_publication + "</td></tr>" +
        "<tr><td>Plan file</td><td>" + plan_file + "</td></tr>" +
        '<tr><td>Planned imaging</td><td><a href="' + link_to_planned_imaging_details + '"><i class="fa fa-link"></i></a></td></tr>' +
        "</table>"
};
