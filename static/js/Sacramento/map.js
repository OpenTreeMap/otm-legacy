var tm_urls = {
    eactive_key : '898cfa06a63e5ad7a427a30896cd95c2',
    tc_url : 'http://207.245.89.246:8080/tilecache/tilecache.py/',
    geo_url: 'http://207.245.89.246:8081/geoserver/wms?transparent=true',
    //tc_url : 'http://sajara01:8080/cgi-bin/mapserv.exe?map=E:\\Projects\\UrbanForestMap\\mapserver\\trees.map',
    qs_tile_url : '/qs_tiles/1.0.0/foo/' // layername is pulled from request.GET, can remove 'foo' eventually
};

tm.map_center_lon = -121.607666;
tm.map_center_lat = 38.6276;
tm.start_zoom = 1;
tm.add_start_zoom = 1;
tm.add_zoom = 9;
tm.edit_zoom = 9;
tm.initial_location_string = "Greenprint Region";
tm.initial_species_string = "All trees";
tm.popup_minSize = new OpenLayers.Size(450,200);
tm.popup_maxSize = new OpenLayers.Size(450,450);

tm.google_bounds = new google.maps.LatLngBounds(new google.maps.LatLng(38.2,-122.0), new google.maps.LatLng(39.2,-120.8));
tm.geo_layer = "sac:greenprint_treemap_tree"
tm.geo_layer_style = "greenprint_tree_highlight"
tm.panoAddressControl = false;

tm.init_base_map = function(div_id, controls){
    if (!div_id) {
        div_id = "map";
    };
    if (!controls) {
        tm.map = new OpenLayers.Map(div_id, {
            maxExtent: new OpenLayers.Bounds(-20037508.34, -20037508.34, 20037508.34, 20037508.34),
            restrictedExtent: new OpenLayers.Bounds(-13718917.834174, 4517428.3708463, -13338567.181496, 4810946.5594087), 
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
            restrictedExtent: new OpenLayers.Bounds(-13718917.834174, 4517428.3708463, -13338567.181496, 4810946.5594087), 
            units: 'm',
            projection: new OpenLayers.Projection("EPSG:102100"),
            displayProjection: new OpenLayers.Projection("EPSG:4326"),
            controls: controls
        });
    }

    tm.baseLayer = new OpenLayers.Layer.Google("Google Streets", {
        sphericalMercator: true,
        //numZoomLevels: 18
        minZoomLevel: 8,
        maxZoomLevel: 17
    });
  
    tm.aerial = new OpenLayers.Layer.Google("Hybrid", {
        type: google.maps.MapTypeId.HYBRID,            
        sphericalMercator: true,
        minZoomLevel: 8,
        maxZoomLevel: 17
        //numZoomLevels: 19
    });
    
    tm.tms = new OpenLayers.Layer.TMS('TreeLayer', 
        tm_urls.tc_url,
        {
            layername: 'Map',
            type: 'png',
            isBaseLayer: false,
            wrapDateLine: true,
            attribution: "(c) UrbanForestMap.org",
            zoomOffset: 8
        }
    );
    tm.tms.buffer = 0;
    tm.baseLayer.buffer = 0;
    tm.aerial.buffer = 0;
    tm.map.addLayers([tm.aerial, tm.baseLayer, tm.tms]);
    tm.map.setBaseLayer(tm.baseLayer);
};
