/* Function to create the text for the tooltip of the dissemination information*/
function create_hktm_workflow_tooltip_text(hktm_product, satellite, orbit, station, status, completeness_status, anx_time, pdmc_fos_time, delta_to_fos, product_size){
    
    return "<table border='1'>" +
            "<tr><td>HKTM Product</td><td>" + hktm_product + "</td></tr>" +
            "<tr><td>Satellite</td><td>" + satellite + "</td></tr>" +
            "<tr><td>Orbit</td><td>" + orbit + "</td></tr>" +
            "<tr><td>Station</td><td>" + station + "</td></tr>" +
            "<tr><td>Status</td><td>" + status + "</td></tr>" +
            "<tr><td>Completeness status</td><td>" + completeness_status + "</td></tr>" +
            "<tr><td>ANX time</td><td>" + anx_time + "</td></tr>" +
            "<tr><td>PDMC-FOS time</td><td>" + pdmc_fos_time + "</td></tr>" +
            "<tr><td>Delta to FOS (m)</td><td>" + delta_to_fos + "</td></tr>" +
            "<tr><td>Product size (B)</td><td>" + product_size + "</td></tr>" +
            "</table>"
};