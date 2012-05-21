tm.map_center_lon = -75.19;
tm.map_center_lat = 39.99;
tm.start_zoom = 11;
tm.add_start_zoom = 13;
tm.add_zoom = 18;
tm.edit_zoom = 18;
tm.initial_location_string = "Address, City, State";
tm.initial_species_string = "All trees";
tm.popup_minSize = new OpenLayers.Size(450,200);
tm.popup_maxSize = new OpenLayers.Size(450,450);
tm.google_bounds = new google.maps.LatLngBounds(new google.maps.LatLng(39.8,-75.4), new google.maps.LatLng(40.2,-74.9));

tm.geo_layer = "philly:ph_treemap_tree"
tm.geo_layer_style = "phillytreemap_tree_highlight"

tm.init_base_map = function(div_id, controls){
    if (!div_id) {
        div_id = "map";
    };
    if (!controls) {
        tm.map = new OpenLayers.Map(div_id, {
            maxExtent: new OpenLayers.Bounds(-20037508.34, -20037508.34, 20037508.34, 20037508.34),
            restrictedExtent: new OpenLayers.Bounds(-8552949.884372,4608577.702163,-8187275.141121,5011248.307428), 
            units: 'm',
            projection: new OpenLayers.Projection("EPSG:900913"),
            displayProjection: new OpenLayers.Projection("EPSG:4326"),
            controls: [new OpenLayers.Control.Attribution(),
                       new OpenLayers.Control.Navigation(),
                       new OpenLayers.Control.ArgParser(),
                       new OpenLayers.Control.PanPanel(),
                       new OpenLayers.Control.ZoomPanel(),
                       new OpenLayers.Control.TouchNavigation({
                          dragPanOptions: {
                               enableKinetic: true
                           }
                       })
                       ]
        });
    }
    else {
        tm.map = new OpenLayers.Map(div_id, {
            maxExtent: new OpenLayers.Bounds(-20037508.34, -20037508.34, 20037508.34, 20037508.34),
            restrictedExtent: new OpenLayers.Bounds(-8552949.884372,4608577.702163,-8187275.141121,5011248.307428), 
            units: 'm',
            projection: new OpenLayers.Projection("EPSG:900913"),
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
        numZoomLevels: 20,
        MAX_ZOOM_LEVEL: 20,
        MIN_ZOOM_LEVEL: 0
    });
  
    tm.aerial = new OpenLayers.Layer.VirtualEarth("Hybrid", {
        type: VEMapStyle.Hybrid,            
        sphericalMercator: true,
        numZoomLevels: 20,
        MAX_ZOOM_LEVEL: 20,
        MIN_ZOOM_LEVEL: 0
    });
    
    tm.tms = new OpenLayers.Layer.TMS('TreeLayer', 
        tm_urls.tc_url,
        {
            layername:  tm_urls.tc_layer_name,
            type: 'png',
            isBaseLayer: false,
            //opacity:0.7, causes issues with IE and bing layer. 
            wrapDateLine: true,
            attribution: "(c) PhillyTreeMap.org"
        }
    );
    tm.tms.buffer = 0;
    tm.baseLayer.buffer = 0;
    tm.aerial.buffer = 0;
    tm.map.addLayers([tm.aerial, tm.baseLayer, tm.tms]);
    tm.map.setBaseLayer(tm.baseLayer);
};
