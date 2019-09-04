
/* Function to query and update the tracking map */
function query_and_update_map(start, stop, mission, sliding_window, dom_id){

    /* Update header table */
    const reporting_start = document.getElementById("header-content-date-start");
    reporting_start.innerHTML = start
    const reporting_stop = document.getElementById("header-content-date-stop");
    reporting_stop.innerHTML = stop

    vboa.request_info("/views/query-tracking?start=" + start + "&stop=" + stop + "&mission=" + mission, update_map, dom_id);

    if (sliding_window){
        var sliding_details_div = document.getElementById("header-content-sliding-details");
        if (sliding_details_div == undefined){
            sliding_details_div = document.createElement("div");
            sliding_details_div.id = "header-content-sliding-details"
            const header_container = document.getElementById("reporting-period-details");
            header_container.appendChild(sliding_details_div);
            sliding_details_text = '<br/><p style="text-indent: 1em"><b>Mission:</b> ' + mission + '</p>'
            sliding_details_text = sliding_details_text + '<p style="text-indent: 1em"><b>Window delay (days):</b> ' + sliding_window["window_delay"] + '</p>'
            sliding_details_text = sliding_details_text + '<p style="text-indent: 1em"><b>Window size (days):</b> ' + sliding_window["window_size"] + '</p>'
            sliding_details_text = sliding_details_text + '<p style="text-indent: 1em"><b>Repeat cycle (minutes):</b> ' + sliding_window["repeat_cycle"] + '</p>'
            sliding_details_text = sliding_details_text + '<p style="text-indent: 1em"><a href="/views/sliding_tracking_parameters?window_delay=' + sliding_window["window_delay"] + '&window_size=' + sliding_window["window_size"] + '&repeat_cycle=' + sliding_window["repeat_cycle"] + '&mission=' + sliding_window["mission"] + '"><b>Link for sharing</b></a></p><br/>'
            sliding_details_div.innerHTML = sliding_details_text
        }
        setTimeout(function(){
            const now = new Date();
            const stop_date = new Date(now - (sliding_window["window_delay"] * 24 * 60 * 60 * 1000));
            const stop = stop_date.toISOString().replace("Z", "000");
            const start_date = new Date(stop_date - (sliding_window["window_size"] * 24 * 60 * 60 * 1000));
            const start = start_date.toISOString().replace("Z", "000");
            const mission = sliding_window["mission"];
            query_and_update_map(start, stop, mission, sliding_window, dom_id)
        }, sliding_window["repeat_cycle"] * 60 * 1000);
    }
    else{
        var sliding_details_div = document.getElementById("header-content-sliding-details");
        if (sliding_details_div == undefined){
            sliding_details_div = document.createElement("div");
            sliding_details_div.id = "header-content-sliding-details"
            const header_container = document.getElementById("reporting-period-details");
            header_container.appendChild(sliding_details_div);
            sliding_details_text = '<br/><p style="text-indent: 1em"><b>Mission:</b> ' + mission + '</p>'
            sliding_details_div.innerHTML = sliding_details_text
        }
    }
};

/* Function to create the text for the tooltip of the playback event information*/
function update_map(dom_id, trackings){

    colors = [
        {
            "stroke_color": "blue",
            "fill_color": "rgba(0,0,255,0.3)",
        },
        {
            "stroke_color": "yellow",
            "fill_color": "rgba(255,255,0,0.3)",
        }
    ]
    
    const container = document.getElementById(dom_id);
    var polygons = []
    var j = 0
    for (const mission of Object.keys(trackings)){
        for (const tracking of trackings[mission]){
            if (tracking["id"] == "HEAD"){
                var style = {
                    "stroke_color": "green",
                    "fill_color": "rgba(0,255,0,0.3)",
                    "text": mission,
                    "font_text": "bold serif"
                }
            }
            else{
                stroke_color = "blue"
                fill_color = "rgba(0,0,255,0.3)"
                if (colors.length > j){
                    stroke_color = colors[j]["stroke_color"];
                    fill_color = colors[j]["fill_color"];
                }
                var style = {
                    "stroke_color": stroke_color,
                    "fill_color": fill_color,
                    "text": mission,
                    "font_text": "bold"
                }
            }
            if ("values" in tracking){
                tooltip = "<table border='1'>" +
                    "<tr><td>Mission</td><td>" + mission + "</td></tr>" +
                    "<tr><td>Start</td><td>" + tracking["start"] + "</td></tr>" +
                    "<tr><td>Stop</td><td>" + tracking["stop"] + "</td></tr>" +
                    "</table>";
                var i = 0
                for (const polygon of tracking["values"][0]["values"]){
                    polygons.push({"polygon": polygon["values"][0]["value"],
                                   "id": mission + "_" + tracking["start"] + "_" + tracking["stop"] + "_" + i,
                                   "style": style,
                                   "tooltip": tooltip})
                    i = i + 1;
                }
            }
        }
        j = j + 1;
    }
    if (polygons.length != 0){
        /* Display polygons on a map */
        vboa.display_map(dom_id, polygons);
    }
    else{
        container.innerHTML = "<br/><p id='" + dom_id + "-no-orbpre' style='text-indent: 1em'>There is not orbit prediction information during the requested period.</p>"
    }

};
