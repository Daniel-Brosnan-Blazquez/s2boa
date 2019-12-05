
/* Function to create the text for the tooltip of the playback event information*/
function create_tooltip(datastrip, satellite, datatake, centre, start, stop, details_link){
    const start_date = new Date(start);
    const stop_date = new Date(stop);
    const duration = ((stop_date.getTime() - start_date.getTime()) / (1000 * 60)).toFixed(3);

    return "<table border='1'>" +
            '<tr><td>Datastrip</td><td><a href="' + details_link + '">' + datastrip + '</a></td></tr>' +        
            "<tr><td>Satellite</td><td>" + satellite + "</td></tr>" +
            "<tr><td>Datatake</td><td>" + datatake + "</td></tr>" +
            "<tr><td>Processing centre</td><td>" + centre + "</td></tr>" +
            "<tr><td>Start</td><td>" + start + "</td></tr>" +
            "<tr><td>Stop</td><td>" + stop + "</td></tr>" +
            "<tr><td>Duration(m)</td><td>" + duration + "</td></tr>" +
            "</table>"
};
