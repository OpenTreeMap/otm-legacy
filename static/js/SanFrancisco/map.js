tm.map_center_lon = -122.437821;
tm.map_center_lat = 37.752809;
tm.start_zoom = 12;
tm.add_start_zoom = 11;
tm.add_zoom = 18;
tm.edit_zoom = 18;
tm.initial_location_string = "San Francisco, CA";
tm.initial_species_string = "All trees";
tm.popup_minSize = new OpenLayers.Size(450,200);
tm.popup_maxSize = new OpenLayers.Size(450,450);

tm.google_bounds = new google.maps.LatLngBounds(new google.maps.LatLng(37.62,-122.62), new google.maps.LatLng(37.88,-122.19));
tm.panoAddressControl = false;

tm.init_base_map = function(div_id, controls){
    if (!div_id) {
        div_id = "map";
    };
    if (!controls) {
        tm.map = new OpenLayers.Map(div_id, {
            maxExtent: new OpenLayers.Bounds(-20037508.34, -20037508.34, 20037508.34, 20037508.34),
            restrictedExtent: new OpenLayers.Bounds(-13669424.883684, 4502981.7575163, -13574337.220514, 4576361.3046569), 
            units: 'm',
            projection: new OpenLayers.Projection("EPSG:102100"),
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
            restrictedExtent: new OpenLayers.Bounds(-13669424.883684, 4502981.7575163, -13574337.220514, 4576361.3046569), 
            units: 'm',
            projection: new OpenLayers.Projection("EPSG:102100"),
            displayProjection: new OpenLayers.Projection("EPSG:4326"),
            controls: controls
        });
    }
    

   tm.baseLayer = new OpenLayers.Layer.Google("Google Streets", {
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
            attribution: "(c) UrbanForestMap.org"
        }
    );
    tm.tms.buffer = 0;
    tm.baseLayer.buffer = 0;
    tm.aerial.buffer = 0;
    tm.map.addLayers([tm.aerial, tm.baseLayer, tm.tms]);
    tm.map.setBaseLayer(tm.baseLayer);
};
