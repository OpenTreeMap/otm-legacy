var tm_urls = {
    eactive_key : '898cfa06a63e5ad7a427a30896cd95c2',
    tc_url : 'http://tilecache.urbanforestmap.org/tilecache.cgi/',
    //tc_url : 'http://sajara01:8080/cgi-bin/mapserv.exe?map=E:\\Projects\\UrbanForestMap\\mapserver\\trees.map',
    qs_tile_url : '/qs_tiles/1.0.0/foo/' // layername is pulled from request.GET, can remove 'foo' eventually
};

tm.map_center_lon = -122.437821;
tm.map_center_lat = 37.752809;
tm.start_zoom = 12;
tm.add_zoom = 14;

tm.google_bounds = new google.maps.LatLngBounds(new google.maps.LatLng(37.5,-122.6), new google.maps.LatLng(40.0,-122.0));

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
    
//        tm.baseLayer = new OpenLayers.Layer.XYZ("ArcOnline", 
//            "http://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/${z}/${y}/${x}.jpg", 
//           {
//              sphericalMercator: true
//            }
//        );

      tm.baseLayer = new OpenLayers.Layer.VirtualEarth("Streets", {
        type: VEMapStyle.Shaded,
        sphericalMercator: true,
        animationEnabled: false,
        numZoomLevels: 18,
        MAX_ZOOM_LEVEL: 18,
        MIN_ZOOM_LEVEL: 0
    });
  
    tm.aerial = new OpenLayers.Layer.VirtualEarth("Hybrid", {
        type: VEMapStyle.Hybrid,            
        sphericalMercator: true,
        animationEnabled: false, 
        numZoomLevels: 19,
        MAX_ZOOM_LEVEL: 19,
        MIN_ZOOM_LEVEL: 0
    });
    
    tm.tms = new OpenLayers.Layer.TMS('TreeLayer', 
        tm_urls.tc_url,
        {
            layername: 'Map',
            type: 'png',
            isBaseLayer: false,
            opacity:0.7,
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
