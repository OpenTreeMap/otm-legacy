tm.dateString = function(dateObj) {
    var d = (dateObj.getYear()+1900) + "-" +
        ((""+(dateObj.getMonth() + 1)).length > 1 ?  (dateObj.getMonth()+1) : "0"+(dateObj.getMonth()+1)) + "-" + 
        ((""+dateObj.getDate()).length > 1 ? dateObj.getDate() : "0" + dateObj.getDate());
    return d;    
};

tm.getFeatureFromCoords = function (coords) {
    var verts = [];
    $.each(coords, function(i, c){ //no multipoly support
        verts.push(new OpenLayers.Geometry.Point(c[0],c[1]).transform(new OpenLayers.Projection("EPSG:4326"), tm.map.getProjectionObject()));
    });
    var poly = new OpenLayers.Geometry.LineString(verts);
    var feature = new OpenLayers.Feature.Vector(poly, null, {
        strokeColor: "#289255",
        strokeWidth: 4,
        strokeOpacity: 0.7
    });
    return feature;
};

tm.isNumber = function (o) {
    return ! isNaN (o-0);
};

tm.trackEvent = function(category, action, label, value) {
    _gaq.push(['_trackEvent', category, action, label, value]);        
};

tm.trackPageview = function(url) {        
    _gaq.push(['_trackPageview', url]);        
};

tm.genericErrorAlert = function() {
    e = "There was an issue processing your request"
    alert(e);
};

tm.coerceFromString = function(value) {
    if (Number(value) == value) {
        value = Number(value);
    }
    if (value == "true") {
        value = true;
    } 
    if (value == "false") {
        value = false;
    }    
    if (value == "null") {
        value = null;
    }            

    return value;
};


// http://www.mredkj.com/javascript/numberFormat.html
tm.addCommas = function(nStr)
{
    nStr += '';
    x = nStr.split('.');
    x1 = x[0];
    x2 = x.length > 1 ? '.' + x[1] : '';
    var rgx = /(\d+)(\d{3})/;
    while (rgx.test(x1)) {
        x1 = x1.replace(rgx, '$1' + ',' + '$2');
        }
    return x1 + x2;
};
