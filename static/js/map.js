tm.start_zoom = 10;
tm.add_start_zoom = 11;
tm.add_zoom = 18;
tm.edit_zoom = 18;
tm.initial_location_string = "Philadelphia, PA";
tm.initial_species_string = "All trees";
tm.popup_minSize = new OpenLayers.Size(450,200);
tm.popup_maxSize = new OpenLayers.Size(450,450);

tm.google_bounds = new google.maps.LatLngBounds(
    new google.maps.LatLng(treemap_settings.boundingBox.bottom,treemap_settings.boundingBox.left),
    new google.maps.LatLng(treemap_settings.boundingBox.top, treemap_settings.boundingBox.right)
);

tm.panoAddressControl = false;

tm.benefitFactors = {
    'annual_air_quality_improvement': 0.453592, // kg per lb
    'annual_stormwater_management': 3.78541, // liters per gal
    'annual_energy_conserved': 1.0, // kWh
    'annual_co2_reduced': 0.453592, // kg per lb
};

tm.benefitUnitTransformer = function(k,v) { 
    if (tm.benefitFactors[k]) {
        return parseInt(tm.benefitFactors[k] * v)
    } else {
        console.log("* UNIT NOT CONVERTED *");
        return v;
    }
};

tm.init_base_map = function(div_id, controls){
    if (!div_id) {
        div_id = "map";
    };
    var restr = new OpenLayers.Bounds(-777364.0417177721, 6422865.926792589, 196913.04726422162, 7983783.306282676);

    if (!controls) {
        tm.map = new OpenLayers.Map(div_id, {
            maxExtent: new OpenLayers.Bounds(-20037508.34, -20037508.34, 20037508.34, 20037508.34),
            restrictedExtent: restr,
            units: 'm',
            projection: new OpenLayers.Projection("EPSG:900913"),
            displayProjection: new OpenLayers.Projection("EPSG:4326"),
            controls: [new OpenLayers.Control.Attribution(),
                       new OpenLayers.Control.Navigation(),
                       new OpenLayers.Control.ArgParser(),
                       new OpenLayers.Control.PanPanel(),
                       new OpenLayers.Control.ZoomPanel()]
        });
    }
    else {
        tm.map = new OpenLayers.Map(div_id, {
            maxExtent: new OpenLayers.Bounds(-20037508.34, -20037508.34, 20037508.34, 20037508.34),
            restrictedExtent: restr,
            units: 'm',
            projection: new OpenLayers.Projection("EPSG:900913"),
            displayProjection: new OpenLayers.Projection("EPSG:4326"),
            controls: controls
        });
    }
    
    tm.baseLayer = new OpenLayers.Layer.Google("Google Streets", {
        type: google.maps.MapTypeId.STREETS,
		sphericalMercator: true,
        numZoomLevels: 21
    });
  
    tm.aerial = new OpenLayers.Layer.Google("Hybrid", {
        type: google.maps.MapTypeId.HYBRID,            
        sphericalMercator: true,
        numZoomLevels: 21
    });
    
    tm.tms = new OpenLayers.Layer.TMS('TreeLayer', 
        tm_urls.tc_url,
        {
            layername: tm_urls.tc_layer_name,
            type: 'png',
            isBaseLayer: false,
            wrapDateLine: true,
            attribution: "&copy; Your Organization"
        }
    );
    tm.tms.buffer = 0;
    tm.baseLayer.buffer = 0;
    tm.aerial.buffer = 0;
    tm.map.addLayers([tm.aerial, tm.baseLayer, tm.tms]);
    tm.map.setBaseLayer(tm.baseLayer);
};
