
jQuery.urlParam = function(name){
    var results = new RegExp('[\\?&]' + name + '=([^&#]*)').exec(window.location.href);
    if (results) {
        return results[1];
        }
    };

var tm_urls = {
    eactive_key : '898cfa06a63e5ad7a427a30896cd95c2',
    // now pulled in from settings file...
    //tc_url : 'http://tc2.beardedmaps.com/tilecache.cgi/1.0.0/'
    //tc_url : 'http://tilecache.urbanforestmap.org/tiles/1.0.0/trees/',
    tc_url : 'http://sajara01:8080/tilecache/tilecache.cgi/1.0.0/',
    qs_tile_url : '/qs_tiles/1.0.0/foo/' // layername is pulled from request.GET, can remove 'foo' eventually
    };

var tm_icons = {
    //base folder for shadow and other icon specific stuff
    base_folder : '/static/images/map_icons/v3/',
    
    // v1 from earthsite
    //12x12
    //small_trees : "/static/images/map_icons/blue_3.png",
    // 23x23
    //focus_tree : "/static/images/map_icons/blue_tree.png",
    
    // v2 from earthsite

    //17x17
    small_trees : "/static/images/map_icons/v4/zoom5.png",
    small_trees_complete : "/static/images/map_icons/v4/zoom5.png",
    //62x62
    //focus_tree : "/static/images/map_icons/v3/UFM_Tree_Icon_zoom8a.png"
    //62x62
    focus_tree : '/static/images/map_icons/v4/zoom8.png'
    };

var tm = {
    speciesData: null,
    speciesDataListeners: [],
    map : null, 
    tree_markers : [],
    geocoded_locations: {},
    tree_detail_marker : null,
    current_tile_overlay : null,
    current_select_tile_overlay : null,
    selected_tile_query : null,
    mgr : null,
    cur_polygon : null,
    geocoder : null,
    maxExtent : null,
    clckTimeOut : null,
    tree_columns_of_interest : {
        'address_street' : true,
        'id' : false,
        //'native' : true,
        'flowering' : true,
        'species' : true,
        //'orig_species' : true,
        'geocoded_address' : true,
        'site_type' : true
        },
    resultsTemplatePageLoad: function(min_year, current_year, min_updated, max_updated) {    
        tm.init_map('results_map');

        var spp = jQuery.urlParam('species');
        if (spp) {
            jQuery('#heading_location').html(spp);
            }
        
        $.address.externalChange(tm.pageLoadSearch);
        $(".characteristics input").change(function(evt) { 
            tm.searchParams[this.id] = this.checked ? 'true' : undefined; 
            tm.updateSearch(); 
        });
        $(".project_trees input").change(function(evt) { 
            tm.searchParams[this.id] = this.checked ? 'true' : undefined; 
            tm.updateSearch(); 
        });
        $(".outstanding input").change(function(evt) { 
            tm.searchParams[this.id] = this.checked ? 'true' : undefined; 
            tm.updateSearch(); 
        });
        $("#location_search_input").change(function(evt) {
            if (this.value) {
                tm.handleSearchLocation(this.value);
            } else {
                $("#location_search_input").val("Philadelphia, PA");
                delete tm.searchParams['location'];
                tm.updateSearch();

                if (tm.cur_polygon){
                    tm.map.removeOverlay(tm.cur_polygon);
                }
            }    
        });
        $("#species_search_input").change(function(evt) {
            if (this.value === "") {
                $("#species_search_id").val("");
                $(this).val("All species");
                delete tm.searchParams['species'];
                tm.updateSearch();
            }    
        });
        $("#species_search_id").change(function(evt) {
            if (this.value) {
                tm.searchParams['species'] = this.value;
                tm.updateSearch(); 
            }
        });
        $("#species_search_id_cultivar").change(function(evt) {
            if (this.value) {
                tm.searchParams['cultivar'] = this.value;
                tm.updateSearch();
            } else {
                delete tm.searchParams['cultivar'];
                tm.updateSearch();
            }
        });    
        $("#search_form").submit(function() { return false; });
        var curmin = 0;
        var curmax = 50;
        $("#diameter_slider").slider({'range': true, max: 50, min: 0, values: [curmin, curmax],
            slide: function() { 
                var min = $(this).slider('values', 0)
                var max = $(this).slider('values', 1)
                $('#min_diam').html(min);
                $('#max_diam').html(max);
            },    
            change: function() {
                var min = $(this).slider('values', 0)
                var max = $(this).slider('values', 1)
                $('#min_diam').html(min);
                $('#max_diam').html(max);
                tm.searchParams['diameter_range'] = min+'-'+max;
                tm.updateSearch(); 
            }
        });
        
        $("#planted_slider")[0].updateDisplay = function() {
            var min = $("#planted_slider").slider('values', 0)
            var max = $("#planted_slider").slider('values', 1)
            $('#min_planted').html(min);
            $('#max_planted').html(max);
        }        
        $("#planted_slider").slider({'range': true, min: min_year, max: current_year,
            values: [min_year, current_year],
            slide: function() { 
                $("#planted_slider")[0].updateDisplay();
            },    
            change: function() {
                $("#planted_slider")[0].updateDisplay();
                var min = $("#planted_slider").slider('values', 0)
                var max = $("#planted_slider").slider('values', 1)
                tm.searchParams['planted_range'] = min+'-'+max;
                tm.updateSearch(); 
            }
        });
        $("#planted_slider")[0].updateDisplay();
        
        $("#updated_slider")[0].updateDisplay = function() {
            var min = $("#updated_slider").slider('values', 0)
            var min_d = new Date(parseInt(min) * 1000);
            var max = $("#updated_slider").slider('values', 1)
            var max_d = new Date(parseInt(max) * 1000);
            $('#min_updated').html(tm.dateString(min_d));
            $('#max_updated').html(tm.dateString(max_d));
        }        

        $("#updated_slider").slider({'range': true, min: min_updated, max: max_updated,
            values: [min_updated, max_updated],
            slide: function() {
                $("#updated_slider")[0].updateDisplay();
            },    
            change: function() {
                $("#updated_slider")[0].updateDisplay();
                var min = $("#updated_slider").slider('values', 0)
                var max = $("#updated_slider").slider('values', 1)
                tm.searchParams['updated_range'] = min+'-'+max;
                tm.updateSearch(); 
            }
        });    
        $("#updated_slider")[0].updateDisplay();
    },    
    baseTemplatePageLoad:function() {
        jQuery.getJSON('/species/json/', function(species){
            tm.speciesData = species;
            tm.setupAutoComplete($('#species_search_input')).result(function(event, item) {
                $("#species_search_id").val(item.symbol).change(); 
                if (item.cultivar) {
                    $("#species_search_id_cultivar").val(item.cultivar).change(); 
                } else {
                    $("#species_search_id_cultivar").val("").change();
                }    
            });
            var spec = $.address.parameter("species");
            var cultivar = $.address.parameter("cultivar");
            tm.updateSpeciesFields("search_species",spec, cultivar);
            for (var i = 0; i < tm.speciesDataListeners.length; i++) {
                tm.speciesDataListeners[i]();
            }    
            //var loc = $.address.parameter("location");
            //tm.updateLocationFields(loc);
        });
        $("#species_search_form").submit(function() {
            if (location.href.substr(0,4) != "/map") {
                location.href="/map/#/?species=" + $("#species_search_id").val();
            }
            return false;
        });
        var adv_active = false;
        $('#advanced').click(function() {
                if (!adv_active) {
                    if (location.pathname == "/map/") {
                        $('.filter-box').slideDown('slow');
                    }
                    adv_active = true;
                    $('#arrow').attr('src','/static/images/v2/arrow2.gif');
                    $('#filter_name')[0].innerHTML = 'Hide advanced filters';
                }    
                else {
                    if (location.pathname == "/map/") {
                        $('.filter-box').slideUp('slow');
                    }
                    adv_active = false;
                    $('#arrow').attr('src','/static/images/v2/arrow1.gif');
                    $('#filter_name')[0].innerHTML = 'Show advanced filters';          
                }
                return false;
            });
        
        // todo - clean this logic up...
        if (jQuery.urlParam('diameter') || jQuery.urlParam('date') || jQuery.urlParam('characteristics') ||  jQuery.urlParam('advanced') )
        {
            jQuery('#advanced').click();
        }
        function triggerSearch() {
            var q = $.query.empty();
            if ($("#location_search_input").val() != "Philadelphia, PA") { 
                q = q.set("location", $("#location_search_input").val());
            }
            if ($("#species_search_id").val()) {
                q = q.set("species", $("#species_search_id").val());
            }
            if ($("#species_search_id_cultivar").val()) {
                q = q.set("cultivar", $("#species_search_id_cultivar").val());
            }
            if (tm.advancedClick) {
                q = q.set('advanced', 'open');
            }    
            window.location.href = "/map/#" + decodeURIComponent(q.toString());
            return false;
        }
        $("#search_form").submit(triggerSearch);    
        $("#advanced").click(function() {
            tm.advancedClick = true;
            triggerSearch();
            });    
    },    
    dateString: function(dateObj) {
        var d = (dateObj.getYear()+1900) + "-" +
            ((""+(dateObj.getMonth() + 1)).length > 1 ?  (dateObj.getMonth()+1) : "0"+(dateObj.getMonth()+1)) + "-" + 
            ((""+dateObj.getDate()).length > 1 ? dateObj.getDate() : "0" + dateObj.getDate());
        return d;    
    },
    // http://www.mredkj.com/javascript/numberFormat.html
    addCommas : function(nStr)
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
    },
    setup : function(){
        tm.geocoder = new GClientGeocoder();
        tm.map.setCenter(new GLatLng(39.99, -75.19), 11);
        // bounds based on new GLatLng(37.76, -122.45), 10);
        // we should consider making this a user-set database value
        tm.maxExtent = new GLatLngBounds(new GLatLng(39.75,-76), new GLatLng(40.5,-74.5));    
        tm.geocoder.setViewport(tm.maxExtent) //bias results for sf
        },
        
    load_nearby_trees : function(ll){
        //load in nearby trees as well
        var url = ['/trees/location/?lat=',ll.y,'&lon=',ll.x,'&format=json&max_trees=70'].join('');
        $.getJSON(url, function(geojson){
            $.each(geojson.features, function(i,f){
                coords = f.geometry.coordinates;
                var ll = new GLatLng(coords[1], coords[0]);
                marker = new MarkerLight(ll, {
                    image: tm_icons.small_trees,
                    width: 17, height:17})
                marker.tid = f.properties.id;
                if (tm.currentTreeId == 'undefined') {tm.currentTreeId = -1;}
                if (marker.tid != tm.currentTreeId){ //don't overlay same marker
                    tm.map.addOverlay(marker);
                    }
                });
            
            });
        },
                
    //custom dragging stuff for add tree map
    enable_add_tree_map_dragging : function(ll){
        tm.map.setCenter(ll,19);
        tm.load_nearby_trees(ll);
        tm.add_new_tree_marker(ll, true);
        tm.tree_marker.enableDragging();
        jQuery('#id_lat').val(ll.y);
        jQuery('#id_lon').val(ll.x);        
        //override 'default' (edit) drag listener
        GEvent.removeListener(tm.tree_drag_listener);
        tm.tree_drag_listener = GEvent.addListener(tm.tree_marker, 'dragend', function(ll){
            var wkt = 'POINT(' + ll.x + ' ' + ll.y + ')';
            tm.reverse_geocode(ll);
            jQuery('#id_lat').val(ll.y);
            jQuery('#id_lon').val(ll.x);           
        });
        
    },
        
        
    //initializes the map where a user places a new tree
    init_add_map : function(){
        tm.map = new GMap2(document.getElementById("add_tree_map"));
        tm.setup();
        tm.map.setMapType(G_HYBRID_MAP);
        tm.map.setUIToDefault();
        
        //listen for click and add marker if one doesn't exist
        tm.click_listener = GEvent.addListener(tm.map,"click", function(overlay, ll){
            if (tm.tree_marker)
            {
                return false;
            }
            tm.enable_add_tree_map_dragging(ll);
            });
    
        //listen for change to address field to update map location //todo always?
        
        jQuery('#id_edit_address_street').change(function(nearby_field){
            //console.log(nearby_field);
            var new_addy = nearby_field.target.value;
            //new_addy += ", ph";
            if (!tm.tree_marker && new_addy){ //only add marker if it doesn't yet exist
                
                tm.geocoder.getLatLng(new_addy, function(ll){
                    if (tm.validate_point(ll,new_addy)){ 
                        tm.enable_add_tree_map_dragging(ll);
                        }
                    });
                }
            });
        
        },
        
    //initializes map on the profile page; shows just favorited trees
    init_favorite_map : function(user){
        tm.map = new GMap2(document.getElementById("favorite_tree_map"));
        tm.setup();
        //tm.map.setCenter(ll, 19, G_HYBRID_MAP);
        tm.map.setUIToDefault();

        //load in favorite trees
        var url = ['/trees/favorites/' + user + '/geojson/']
        $.getJSON(url, function(json){
            var b = new GLatLngBounds()
            $.each(json, function(i,f){
                var coords = f.coords;
                var ll = new GLatLng(coords[1], coords[0]);
                b.extend(ll)
                marker = new MarkerLight(ll, {
                    image: tm_icons.small_trees,
                    width: 17, height:17})
                marker.tid = f.id;
                if (marker.tid != tm.currentTreeId){ //don't overlay same marker
                    tm.map.addOverlay(marker);
                    }
                });
                tm.map.setCenter(b.getCenter(),tm.map.getBoundsZoomLevel(b))
            
            });
        GEvent.addListener(tm.map,"click", function(overlay, ll){
            if (overlay && overlay.tid){
                var html = '<a href="/trees/' + overlay.tid + '">Tree #' + overlay.tid + '</a>';
                $('#alternate_tree_div').html(html);
                }
            });
        },
        
    //initializes the map on the detail/edit page, 
    // where a user just views, or moves, an existing tree
    // also it loads the streetview below the map
    init_tree_map : function(editable){
        tm.map = new GMap2(document.getElementById("add_tree_map"));
        tm.setup();
        var coords = tm.current_tree_geometry;
        var ll = new GLatLng(coords[1], coords[0]);
        tm.add_new_tree_marker(ll, editable);
        tm.map.setCenter(ll, 19, G_HYBRID_MAP);
        tm.map.setUIToDefault();
        
        tm.load_streetview(ll, 'tree_streetview');
        
        GEvent.addListener(tm.map,"click", function(overlay, ll){
            if (overlay && overlay.tid){
                var html = '<a href="/trees/' + overlay.tid + '">Tree #' + overlay.tid + '</a>';
                $('#alternate_tree_div').html(html);
                }
            });
            
        tm.load_nearby_trees(ll);
        if (!editable) {return;}
        
        //listen for change to address field to update map location //todo always?
        jQuery('#id_nearby_address').change(function(nearby_field){

            var new_addy = nearby_field.target.value;
            //new_addy += ', ph';
            tm.geocoder.getLatLng(new_addy, function(ll){
                if (tm.validate_point(ll,new_addy) && !tm.tree_marker){ //only add marker if it doesn't yet exist
                    tm.add_new_tree_marker(ll);
                    tm.map.setCenter(ll,16);
                    }
                
                });
            });
            
        
        },
            
    add_new_tree_marker : function(ll, editable){
        tm.tree_marker = new GMarker(ll, {
            icon:tm.get_tree_detail_icon(35), draggable: editable, bouncy : true});
        tm.tree_marker.disableDragging(); // only enabled explicitly now by enableEditTreeLocation
        tm.map.addOverlay(tm.tree_marker)
        tm.reverse_geocode(ll);
        
        //listen for dragend on marker to set the wkt of the geometry field
        tm.tree_drag_listener = GEvent.addListener(tm.tree_marker, 'dragend', function(ll){
            var coords = tm.current_tree_geometry;
            var start_pt = new GLatLng(coords[1], coords[0]);
            var dist = start_pt.distanceFrom(ll);
            
            if (dist > 30.5) {
                alert('You can only move the tree up to 100 feet.');
                tm.tree_marker.setLatLng(start_pt);
                tm.map.panTo(start_pt);
                return false;
                }
            
            //update the streetview
            tm.pano.setLocationAndPOV(ll);
            //todo:  should we update the address with reverse geocode info?
            if (jQuery('#id_geometry'))
            {
                jQuery('#id_geometry')[0].value = 'POINT(' + ll.x + ' ' + ll.y + ')';
            }
            tm.reverse_geocode(ll);
            });
        
        },
        

    get_tree_detail_icon : function(size){
        var icon = new GIcon(G_DEFAULT_ICON, tm_icons.focus_tree);
            
        icon.shadow = tm_icons.base_folder  + 'shadow.png'
        icon.printImage = tm_icons.base_folder  + 'printImage.png'
        icon.mozPrintImage = tm_icons.base_folder  + 'mozPrintImage.png'
        icon.iconSize = new GSize(size,size);
        icon.shadowSize = new GSize(size * 1.5, size);
        icon.iconAnchor = new GPoint(size / 2, size * 0.75);
        icon.infoWindowAnchor = new GPoint(size * 0.5, 0);
        icon.maxHeight = 10; //px height it rises when dragged
        return icon;
        },
        
        
    //pass in a GLatLng and get back closest address
    reverse_geocode : function(ll){
        tm.geocoder.getLocations(ll, function(locs){
            //console.log(locs);
            var loc = locs.Placemark[0];
            tm.loc = loc;
            var addy = loc.AddressDetails;
            var l = addy.Country.AdministrativeArea.SubAdministrativeArea.Locality;
            var city = l.LocalityName;
            var zip =  '';
            if (l.PostalCode){
                zip = l.PostalCode.PostalCodeNumber;
            }
            
            var street = l.Thoroughfare.ThoroughfareName;
            

            if ($('#edit_address_street')) {
                $('#edit_address_street').val(street);
                $('#edit_address_street').html(street);
            }
            if ($('#edit_address_city')) {
                $('#edit_address_city').val(city);
                $('#edit_address_city').html(city);
            }
            if ($('#edit_address_zip')) {
                $('#edit_address_zip').val(zip);
                $('#edit_address_zip').html(zip);
            }

            
            if ($('#id_edit_address_street') && street) {
                $('#id_edit_address_street').val(street);
                //$('#id_edit_address_street').html(street);
            }
            
            if ($('#id_edit_address_city')) {
                $('#id_edit_address_city').val(city);
                //$('#id_edit_address_city').html(city);
            }
            if ($('#id_edit_address_zip')) {
                $('#id_edit_address_zip').val(zip);
                //$('#id_edit_address_zip').html(zip);
            }
            

            //only update the database with new address and location on explicit Save
            });
        
        },
    
    init_map : function(div_id){
        if (!div_id) {
            div_id = "map";
        };
        tm.map = new GMap2(document.getElementById(div_id));
        tm.setup();
        tm.map.setUIToDefault();

        this.set_default_map_zoom_levels();
        //set map zoom levels
        //jQuery.each(tm.map.getMapTypes(), function(i,mt){
        //    mt.getMinimumResolution = function() {return 10;}
        //    mt.getMaximumResolution = function() {return 19;}
        //    if (mt.getName() == 'Terrain') {mt.getMaximumResolution = function() { return 15;}}
        //    //if (mt.getName() == 'Satellite') {tm.map.removeMapType(mt);}
        //    });
            
        //todo replace map layer with custom
        
        tm.mgr = new MarkerManager(tm.map);
        
        tm.set_tile_overlay();
        
        GEvent.addListener(tm.map,'maptypechanged',tm.set_tile_overlay);
        
        
        //check to see if coming for a bookmarked tree
        var bookmark_id = jQuery.urlParam('tree');
        if (bookmark_id){
            jQuery.getJSON('/trees/' + bookmark_id  + '/',
               {'format' : 'json'},
                tm.display_tree_details);
            }


        GEvent.addListener(tm.map,'click',mapClick); 
        
        function mapClick(ol,latlon,olLatlon) { 
                if (tm.clckTimeOut && !ol) { 
                        window.clearTimeout(tm.clckTimeOut); 
                        tm.clckTimeOut = null; 
                        doubleClick(ol,latlon);
                } 
                else { 
                    tm.clckTimeOut = window.setTimeout(function() {
                        singleClick(ol,latlon,olLatlon)
                        },500); 
                }
        }

        //listen for click and find closest tree
        function doubleClick(overlay,ll,olLatlon) { 
            // do nothing...
        } 
        
        function singleClick(overlay,ll,olLatlon) { 

            window.clearTimeout(tm.clckTimeOut); 
            tm.clckTimeOut = null; 
            // Process single click
            if (overlay && overlay.tid){
                jQuery.getJSON('/trees/' + overlay.tid + '/',
                   {'format' : 'json'},
                    tm.display_tree_details);
                }
            if (ll){
                //if (tm.map.getZoom() < 15){
                //    tm.map.setCenter(ll, tm.map.getZoom() + 0);
                //} else {
                var spp = jQuery.urlParam('species');
                jQuery.getJSON('/trees/location/',
                  {'lat': ll.y, 'lon' : ll.x, 'format' : 'json', 'species':spp},
                tm.display_tree_details);
                //}
            } 
        } 

    },
        
        
    /*
    load up streetview pointing at specified GLatLng, into specified div
    */
    load_streetview : function(ll, div){
          div = document.getElementById(div);
          tm.pano = new GStreetviewPanorama(div);
          GEvent.addListener(tm.pano, 'error', function(errorCode) {
            if (errorCode == 603) {
              div.innerHTML = 'StreetView requires flash plugin. Click <a href="http://get.adobe.com/flashplayer/" target="_blank"> here</a> to download';
            }
          });
          tm.pano.setLocationAndPOV(ll);
        },
        
        
    set_default_map_zoom_levels : function(){
        //set map zoom levels
        jQuery.each(tm.map.getMapTypes(), function(i,mt){
            mt.getMinimumResolution = function() {return 10;}
            mt.getMaximumResolution = function() {return 19;}
            if (mt.getName() == 'Terrain') {mt.getMaximumResolution = function() { return 15;}}
            //if (mt.getName() == 'Satellite') {tm.map.removeMapType(mt);}
            });
        },
        
    get_tile : function(a,b){
        // either "Map","Hybrid", or "Terrain"
        var layer_name = tm.map.getCurrentMapType().getName();
        var u = tm_urls.tc_url + layer_name + '/' + tm.map.getZoom() + '/' + a.x  + '/' + a.y + '.png';
        //var u = tm_urls.tc_url + 'trees/' + tm.map.getZoom() + '/' + a.x  + '/' + a.y + '.png';
        //console.log(u);
        return u;
        },
    
    set_tile_overlay : function(){
        if (tm.current_tile_overlay)
        {
            tm.map.removeOverlay(tm.current_tile_overlay);
        }
        
        var myCopyright = new GCopyrightCollection("(c) ");
        myCopyright.addCopyright(new GCopyright('Urban Forest Map',
          new GLatLngBounds(new GLatLng(-90,-180), new GLatLng(90,180)),
          0,'bar'));

        tm.tree_layer = new GTileLayer(myCopyright);
        tm.tree_layer.getTileUrl = tm.get_tile;
        tm.tree_layer.isPng = function() { return true;};
        if (navigator.appName != 'Microsoft Internet Explorer')
        {
            tm.tree_layer.getOpacity = function() { return .75; }
        }
    
        tm.current_tile_overlay = new GTileLayerOverlay(tm.tree_layer);
        tm.map.addOverlay(tm.current_tile_overlay);
    },
    
    
    get_tree_marker: function(lat, lng) {
        var ll = new GLatLng(lat,lng);
        
        var marker = new GMarker(ll, {
            icon: tm.get_tree_detail_icon(45)})
        //console.log(marker);
        return marker
        },
        
    highlight_geography : function(geometry, geog_type){
        tm.test = geometry;
        poly_color = {'zipcodes' : 'blue', 'neighborhoods' : 'red' };
        var verts = [];
        jQuery.each(geometry.coordinates[0], function(i, c){ //no multipoly support
            verts.push(new GLatLng(c[1],c[0]));
            });
        if (tm.cur_polygon){
            tm.map.removeOverlay(tm.cur_polygon);
            }
        tm.cur_polygon = new GPolyline(verts, poly_color[geog_type]);
        tm.map.addOverlay(tm.cur_polygon);
        // avoid zooming to bounds of geography
        // http://sftrees.securemaps.com/ticket/224
        /*var b = tm.cur_polygon.getBounds();
        var z = tm.map.getBoundsZoomLevel(b);
        tm.map.setCenter(b.getCenter(), z);
        */
        },
        
    display_tree_details : function(json){
        if (json) {
            if (json.features.length > 0) {
                var tree = json.features[0];
                var p = tree.properties;
                var coords = tree.geometry.coordinates;
                //console.log(coords);
                //remove old markers
                if (tm.tree_detail_marker){
                    tm.map.removeOverlay(tm.tree_detail_marker);
                    }
                //Add tree marker
                tm.tree_detail_marker = tm.get_tree_marker(coords[1], coords[0]);
                tm.tree_detail_marker.tree_id = p.id;
                tm.tree_detail_marker.nhbd_id = p.neighborhood_id;
                tm.tree_detail_marker.district_id = p.district_id;
                tm.map.addOverlay(tm.tree_detail_marker);
                
                //make infowindow tabs
          
                // var panoDiv = document.createElement('div');
                            // panoDiv.style.width = "400px"; // can be anything, will be auto resized
                            // panoDiv.style.height = "200px";
                // maxtitle = p.geocoded_address.split(',')[0];
                // if (p.common_name){maxtitle += ' (' + p.common_name + ')'}
        
                
                // var tabs = [new GInfoWindowTab('Information', '<div id="max_tree_infowindow">Loading ...</div>')
                            //new GInfoWindowTab('Street View', panoDiv)
                            // ];
                var ll = tm.tree_detail_marker.getLatLng();
                tm.map.panTo(ll);
                var html = '<div id="max_tree_infowindow">Loading ...</div>';
                tm.map.openInfoWindowHtml(ll, html, {
                    onOpenFn : function(){ 
                        jQuery('#max_tree_infowindow').load('/trees/' + tm.tree_detail_marker.tree_id + '/?format=base_infowindow');
                        }
                    });
                // if (!node.pano) {
                      // var pano = new GStreetviewPanorama(node);
                      // GEvent.addListener(pano, 'error', function(errorCode) {
                        // if (errorCode == 603) {
                          // node.innerHTML = 'StreetView requires flash plugin. Click <a href="http://get.adobe.com/flashplayer/" target="_blank"> here</a> to download';
                        // }
                      // });
                      // pano.setLocationAndPOV(latlng);
                      // node.pano = pano;
                    // }
        
                        // },
                    // 'maxTitle' : maxtitle
                    // });
            }
        }
    },
        
 
    display_benefits : function(benefits){
        //console.log(benefits);
        jQuery('#results_wrapper').show();
        jQuery.each(benefits, function(k,v){
            //console.log(k,v)
            jQuery('#benefits_' + k).html(tm.addCommas(parseInt(v)));
            });
        },
        
    display_summaries : function(summaries){
        //var callout = ['You selected ', summaries.total_trees, ' trees'].join('');
        //console.log(summaries);
        //jQuery('#callout').html(callout);
        jQuery(".tree_count").html(tm.addCommas(parseInt(summaries.total_trees)));
        if (summaries.total_trees == '0')
        {
            // todo.. http://sftrees.securemaps.com/ticket/148
            jQuery(".notrees").html("No results? Try changing the filters above.");
            //jQuery(".tree_count").css('font-size',20);
        } else {
            jQuery(".notrees").html("");
        }
        
        jQuery.each(summaries, function(k,v){
            var span = jQuery('#' + k);
            //console.log(span);
            if (span.length > 0){
                span.html(tm.addCommas(parseInt(v)));
            }
            /*else{
                console.log(k);
            }
            */
            });

        var benefits = summaries.benefits;
        tm.display_benefits(benefits);
   
        //set geog name or selected trees 
        },

    //UNUSED?    
    display_geography : function(geojson){
        if (geojson) {
            alert(1);
            if (geojson.features){
                feats = geojson.features;   
                geog = feats[0];
                if (geog) {
                    summaries = geog.properties.summaries;
                    benefits = geog.properties.benefits;
                    $('#summary_subset').html(geog.properties.name);
                    //$('#location').val(geog.properties.name);
                    tm.highlight_geography(geog, 'neighborhood')
        
                    if (summaries){tm.display_summaries(summaries)}
                    if (benefits){tm.display_benefits(benefits)}
                    var ew = $('#search_location_infowindow');
                    if (ew){
                        var addy = ew.html();
                        ew.html(addy + ' is in ' + geog.properties.name);
                        }
                    //todo - else display boundary, etc
                }
            }
        } 
    
        },
        
    get_selected_tile : function(a,b){
        // either "Map","Hybrid", or "Terrain"
        var layer_name = tm.map.getCurrentMapType().getName();
        //var u = tm_urls.tc_url + layer_name + '/' + tm.map.getZoom() + '/' + a.x  + '/' + a.y + '.png';
        var u = tm_urls.qs_tile_url + tm.map.getZoom() + '/' + a.x  + '/' + a.y + '.png?' + tm.selected_tile_query;
        //console.log(u);
        return u;
        },
    
    set_selected_tile_overlay : function(){
        if (tm.current_selected_tile_overlay)
        {
            tm.map.removeOverlay(tm.current_selected_tile_overlay);
        }
        
        var myCopyright = new GCopyrightCollection("(c) ");
        myCopyright.addCopyright(new GCopyright('Urban Forest Map',
          new GLatLngBounds(new GLatLng(-90,-180), new GLatLng(90,180)),
          0,'bar'));

        tm.selected_tree_layer = new GTileLayer(myCopyright);
        tm.selected_tree_layer.getTileUrl = tm.get_selected_tile;
        tm.selected_tree_layer.isPng = function() { return true;};
        /*
        if (navigator.appName != 'Microsoft Internet Explorer')
        {
            tm.tree_layer.getOpacity = function() { return .75; }
        }
        */
    
        tm.current_selected_tile_overlay = new GTileLayerOverlay(tm.selected_tree_layer);
        tm.map.addOverlay(tm.current_selected_tile_overlay);
    },
            
    display_search_results : function(results){
        jQuery('#displayResults').hide();
        if (tm.current_selected_tile_overlay)
        {
            tm.map.removeOverlay(tm.current_selected_tile_overlay);
        }
        if (results) {
            tm.display_summaries(results.summaries);
            if (results.geography) {
                var geog = results.geography;
                $('#summary_subset_val').html(geog.name);
                tm.highlight_geography(geog, 'neighborhood');
                var ew = $('#search_location_infowindow');
                if (ew){
                    var addy = ew.html();
                    //ew.html(addy + ' in ' + geog.name);
                    }
            } else {
                $('#summary_subset_val').html('Philadelphia');
            }
            if (results.tile_query){
                tm.selected_tile_query = results.tile_query;
                tm.set_selected_tile_overlay();
            }
            else 
            {
                if (results.trees.length){
                    tm.overlay_trees(results.trees);
                }
            }
        }
        
    },

    //returns a large or small markerLight
    get_marker_light : function(t, size){
        var ll = new GLatLng(t.lat, t.lon)
        if (size == 'small') {
            if (t.cmplt) { var img = tm_icons.small_trees_complete;}
            else { var img = tm_icons.small_trees; }
            var marker = new MarkerLight(ll, {
                image: img,
                width: 13, height:13})
          } else {
            var marker = new MarkerLight(ll, {
                image : tm_icons.focus_tree,
                width: 40, height:40})
          }

        marker.tid = t.id;
        return marker

        },        
        
    overlay_trees : function(trees){
        //could be lots of trees.  todo: cluster
        //if (trees.length > 600){
            //console.log('CLUSTER')
        //    }
        //remove old trees
        tm.tree_markers_small = []; //TODO mem leak
        tm.tree_markers_large = []; //TODO mem leak
        jQuery.each(trees, function(i,t){
            var smarker = tm.get_marker_light(t, 'small')
            tm.tree_markers_small.push(smarker);
            var lmarker = tm.get_marker_light(t, 'large')
            tm.tree_markers_large.push(lmarker);

            });
        tm.mgr.addMarkers(tm.tree_markers_small, 6, 17);
        tm.mgr.addMarkers(tm.tree_markers_large, 18, 19);
        tm.mgr.refresh();
        },
        
        // unused?
        select_species : function(species){
            tm.mgr.clearMarkers();
            jQuery.getJSON('/search/' + species + '/?simple=true', 
                tm.display_search_results);
        },

     
    enableEditTreeLocation : function(){
        tm.tree_marker.enableDragging();
        //TODO:  bounce marker a bit, or change its icon or something
        var save_html = '<a href="javascript:tm.saveTreeLocation()" class="buttomSm"><img src="/static/images/loading-indicator-trans.gif" width="12" /> Stop editing and save</a>'
        $('#edit_tree_location').html(save_html);
        return false;
        },
        
    saveTreeLocation : function(){
        tm.tree_marker.disableDragging();     
        var edit_html = '<a href="#" onclick="tm.enableEditTreeLocation(); return false;"class="buttomSm">Start editing tree location</a>'
        $('#edit_tree_location').html(edit_html);
        tm.updateEditableLocation();
        },


    validate_point : function(point,address) {
        if (!point) {
            alert(address + " not found");
            return false;
        } 
        var lat_lon = new GLatLng(point.lat(),point.lng(),0);

        if (tm.maxExtent && !tm.maxExtent.containsLatLng(lat_lon)){
            alert("Sorry, '" + address + "' appears to be too far away from our supported area.");
            return false;
        }
        return true;
    },
    
    geocode : function(address, display_local_summary, callback){
        if (!address){
            address = jQuery('#searchInput').text();
        }
        tm.geocoder.setViewport(tm.map.getBounds()); 
        var address = address + ", pa";
        tm.geocoder.getLatLng(address,function(point) {
            if (tm.validate_point(point,address)) {   
                if (tm.location_marker) {tm.map.removeOverlay(tm.location_marker)} 
                tm.map.setCenter(point, 15);
                tm.location_marker = new GMarker(point);
                address = address.replace('+',' '); 
                tm.location_marker.html = '<div id="search_location_infowindow">' + address + '</div>';
                GEvent.addListener(tm.location_marker, 'click', function (m){
                      tm.map.openInfoWindowHtml(m, tm.location_marker.html);
                });
                tm.map.addOverlay(tm.location_marker);

                if (callback) {
                    callback(point);
                }
            }
        });

    },
        
    setupEdit: function(field, model, id, options) {
        var editableOptions = {
            submit: 'Save',
            cancel: 'Cancel',
            cssclass:  'activeEdit',
            indicator: '<img src="/static/images/loading-indicator.gif" alt="" />',
            width: '80%',
            objectId: id,
            model: model,
            fieldName: field
        };
        if (options) {
            for (var key in options) {
                editableOptions[key] = options[key];
            }
        }
        $('#edit_'+field).editable(tm.updateEditableServerCall, editableOptions);
    },
    updateEditableServerCall: function(value, settings) {
        var data = {
            'model': settings.model,
            'update': {
            }
        };
        //console.log(value);
        // TODO - I think if '' then we should replace
        // with original value and if 'null' then
        // we should save None in database if its
        // a field that accepts nulls
        if (value === '') {
        //if (value == '' || value == 'null') {
           // do nothing
           this.innerHTML = 'Click to edit';
           return 'Click to edit';
        }
        else {
            if (settings.objectId) {
                data.id = settings.objectId;
            }    
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
            //if (!isNaN(Date.parse(value))) {
            //	//it's a javascript-parsable date, so we'll take it
            //	var dateVal = new Date(Date.parse(value));
            //	value = dateVal.getFullYear() + "-" + (dateVal.getMonth()+1) + "-" + dateVal.getDate()
            //}
            if (jQuery.inArray(settings.model, ["TreeAlert","TreeAction","TreeStatus", "TreeFlags"]) >=0) {
                data['update']['value'] = value;
                data['update']['key'] = settings.fieldName;
            } else {    
                data['update'][settings.fieldName] = value;
            }
            if (settings.extraData) {
                for (key in settings.extraData) {
                    data[key] = settings.extraData[key];
                }
            }    
            this.innerHTML = "Saving...";
            var jsonString = JSON.stringify(data);
            settings.obj = this;
            $.ajax({
                url: '/update/',
                type: 'POST',
                data: jsonString,
                complete: function(xhr, textStatus) {
                    var response =  JSON.parse(xhr.responseText);
                    if (response['success'] != true) {
                        settings.obj.className = "errorResponse";
                        settings.obj.innerHTML = "An error occurred in saving: "
                        $.each(response['errors'], function(i,err){
                             settings.obj.innerHTML += err;
                        });
                    } else {
                        var value = response['update'][settings.fieldName];
    
                        if (!value) {
                            value = response['update']['value'];
                        }
                        if (settings.fieldName == "species_id") {
                            for (var i = 0; i < tm.speciesData.length; i++) {
                                if (tm.speciesData[i].id == value) {
                                    value = tm.speciesData[i].sname;
                                    $("#edit_species").html(tm.speciesData[i].cname);
                                }
                            }    
                        }
                        settings.obj.innerHTML = value 
                    }
                }});
            return "Saving... " + '<img src="/static/images/loading-indicator.gif" />';
        } 
    },       
    updateEditableLocation: function() {
        var street = jQuery('#edit_address_street')[0].innerHTML;
        var city = jQuery('#edit_address_city')[0].innerHTML;
        var zip = ('#edit_address_zip')[0].innerHTML;
        
        var wkt = jQuery('#id_geometry').val();
        var data = {
            'model': 'Tree',
            'id': tm.currentTreeId,
            'update': {
                address_street: street,
                address_city: city,
                address_zip: zip,
                geometry: wkt
            }
        };
        var jsonString = JSON.stringify(data);
        $.ajax({
            url: '/update/',
            type: 'POST',
            data: jsonString,
            complete: function(xhr, textStatus) {
                var response =  JSON.parse(xhr.responseText);
            }});
    },
    setupAutoComplete: function(field) {
        //console.log(field);
        return field.autocomplete(tm.speciesData, {
            matchContains: true,
            minChars: 1,

            formatItem: function(row, i, max) {
                var text = row.cname;
                /*if (row.cultivar)
                {
                    text += ' /' + row.cultivar;
                }*/
                text += "  [" + row.sname;
                if (row.cultivar) {
                    text += " '" + row.cultivar + "'";
                }
                text += "]";
                return text;
                //return row.cname + "  [" + row.sname + "]";
            },
            formatMatch: function(row, i, max) {
                return row.symbol + " " + row.cname + " " + row.sname;
            },
            formatResult: function(row) {
                return row.cname + " / " + row.sname;
            }
        });

    },
    newAction: function() {
        var select = $("<select id='actionTypeSelection' />");
        for (var key in tm.actionTypes) {
            select.append($("<option value='"+key+"'>"+tm.actionTypes[key]+"</option>"));
        }    
        var tr = $("<tr />").append($(""), $("<td colspan='2' />").append(select));
        tr.append(
            $("<td />").append(
                $("<input type='submit' value='Submit' class='button' />").click(tm.handleNewAction)
            )
        );
        $("#actionTable").append(tr);
    },
    newLocal: function() {
            var select = $("<select id='localTypeSelection' />");
            for (var key in tm.localTypes) {
                select.append($("<option value='"+key+"'>"+tm.localTypes[key]+"</option>"));
            }    
            var tr = $("<tr />").append($(""), $("<td colspan='2' />").append(select));
            tr.append(
                $("<td />").append(
                    $("<input type='submit' value='Submit' class='button' />").click(tm.handleNewLocal)
                )
            );
            $("#localTable").append(tr);
    },
    newHazard: function() {
        var select = $("<select id='hazardTypeSelection' />");
        for (var key in tm.hazardTypes) {
            select.append($("<option value='"+key+"'>"+tm.hazardTypes[key]+"</option>"));
        }    
        var tr = $("<tr />").append($(""), $("<td colspan='2' />").append(select));
        tr.append(
            $("<td />").append(
                $("<input type='submit' value='Submit' class='button' />").click(tm.handleNewHazard)
            )
        );
        $("#hazardTable").append(tr);
    },
    handleNewHazard: function(evt) {
        var data = $("#hazardTypeSelection")[0].value;
        settings = {
            'extraData': {
                'parent': {
                    'model': 'Tree',
                    'id': tm.currentTreeId
                }
            },
            model: 'TreeAlert',
            fieldName: data,
            submit: 'Save',
            cancel: 'Cancel'
        };    
            
        $(this.parentNode.parentNode).remove();
        var d = new Date();
        var dateStr = (d.getYear()+1900)+"-"+(d.getMonth()+1)+"-"+d.getDate();
        tm.updateEditableServerCall(dateStr, settings)
        $("#hazardTable").append(
            $("<tr><td>"+tm.hazardTypes[data]+"</td><td>"+dateStr+"</td><td>False</td></tr>"));  
        $("#hazardCount").html(parseInt($("#hazardCount")[0].innerHTML) + 1);     
    },
    hazardTypes: {
        '1':'Needs watering',
        '2':'Needs pruning',
        '3':'Should be removed',
        '4':'Pest or disease present',
        '5':'Guard should be removed',
        '6':'Stakes and ties should be removed',
        '7':'Construction work in the vicinity',
        '8':'Touching wires',
        '9':'Blocking signs/traffic signals',
        '10':'Has been improperly pruned/topped'
   }, 
   deleteAction: function(key, value, elem) {
       $(elem.parentNode.parentNode).remove();
   
   },
   deleteHazard: function(key, value, elem) {
       $(elem.parentNode.parentNode).remove();
   
   },
   deleteLocal: function(key, value, elem) {
       $(elem.parentNode.parentNode).remove();
   
   },
   handleNewAction: function(evt) {
       var data = $("#actionTypeSelection")[0].value;
       settings = {
           'extraData': {
               'parent': {
                   'model': 'Tree',
                   'id': tm.currentTreeId
               }
           },
           model: 'TreeAction',
           fieldName: data,
           submit: 'Save',
           cancel: 'Cancel'
       };    
           
       $(this.parentNode.parentNode).remove();
       var d = new Date();
       var dateStr = (d.getYear()+1900)+"-"+(d.getMonth()+1)+"-"+d.getDate();
       tm.updateEditableServerCall(dateStr, settings)
       $("#actionTable").append(
           $("<tr><td>"+tm.actionTypes[data]+"</td><td>"+dateStr+"</td></tr>"));  
       $("#actionCount").html(parseInt($("#actionCount")[0].innerHTML) + 1);     
    },
    actionTypes: {
         //'planted':'Tree has been planted',
         '1':'Tree has been watered',
         '2':'Tree has been pruned',
         '3':'Fruit/nuts have been harvested from this tree',
         '4':'Tree has been removed',
         '5':'Tree has been inspected'
         // disabled till we have commenting ability
         //'other':'Other',
    },
   handleNewLocal: function(evt) {
       var data = $("#localTypeSelection")[0].value;
       settings = {
           'extraData': {
               'parent': {
                   'model': 'Tree',
                   'id': tm.currentTreeId
               }
           },
           model: 'TreeFlags',
           fieldName: data,
           submit: 'Save',
           cancel: 'Cancel'
       };    
           
       $(this.parentNode.parentNode).remove();
       var d = new Date();
       var dateStr = (d.getYear()+1900)+"-"+(d.getMonth()+1)+"-"+d.getDate();
       tm.updateEditableServerCall(dateStr, settings)
       $("#localTable").append(
           $("<tr><td>"+tm.localTypes[data]+"</td><td>"+dateStr+"</td></tr>"));  
       $("#localCount").html(parseInt($("#localCount")[0].innerHTML) + 1);     
    },
    localTypes: {
         '1': 'Landmark Tree',
	 '2': 'Local Carbon Fund',
	 '3': 'Fruit Gleaning Project',
    	 '4': 'Historically Significant Tree'
    },
    searchParams: {},
    pageLoadSearch: function () {
        tm.loadingSearch = true;
        tm.searchparams = {};
        var params = $.address.parameterNames();
        if (params.length) {
            for (var i = 0; i < params.length; i++) {
                var key = params[i];
                var val = $.address.parameter(key);
                tm.searchParams[key] = val;
                if (val == "true") {
                    $("#"+key).attr('checked', true);
                }
                if (key == "diameter_range") {
                    var dvals = $.address.parameter(key).split("-");
                    $("#diameter_slider").slider('values', 0, dvals[0]);
                    $("#diameter_slider").slider('values', 1, dvals[1]);
                }   
                if (key == "planted_range") {
                    var pvals = $.address.parameter(key).split("-");
                    $("#planted_slider").slider('values', 0, pvals[0]);
                    $("#planted_slider").slider('values', 1, pvals[1]);
                }   
                if (key == "updated_range") {
                    var uvals = $.address.parameter(key).split("-");
                    $("#updated_slider").slider('values', 0, uvals[0]);
                    $("#updated_slider").slider('values', 1, uvals[1]);
                }   
                if (key == "species") {
                    var cultivar = null;
                    if ($.address.parameter("cultivar")) {
                        cultivar = $.address.parameter("cultivar");
                    }    
                    tm.updateSpeciesFields('species_search',$.address.parameter(key), cultivar);
                } 
                if (key == "location") {
                    tm.updateLocationFields($.address.parameter(key));
                }    
            }    
        }
        tm.loadingSearch = false;
        tm.updateSearch();
    },
    serializeSearchParams: function() {
        var q = $.query.empty(); 
        for (var key in tm.searchParams) {
            if (!tm.searchParams[key]){
                continue;
            }
            var val = tm.searchParams[key];
            q = q.set(key, val);
        }
        var qstr = decodeURIComponent(q.toString()).replace(/\+/g, "%20")
        if (qstr != '?'+$.address.queryString()) {
            if (!tm.loadingSearch) { 
                $.address.value(qstr);
            }
        }
       
        if (tm.searchParams['location']) {
            var val = tm.searchParams['location'];
            var coords = tm.geocoded_locations[val];
            if (!coords)
            {
                return false;
            }
            q.SET('location', coords.join(','));
            qstr = decodeURIComponent(q.toString()).replace(/\+/g, "%20")
        }
        $("#kml_link").attr('href',"/search/kml/"+qstr);
        $("#csv_link").attr('href', "/search/csv/"+qstr);
        $("#shp_link").attr('href', "/search/shp/"+qstr);
        return qstr;
    },
    
    updateSearch: function() {
        if (tm.loadingSearch) { return; }
        tm.mgr.clearMarkers();
        var qs = tm.serializeSearchParams();
        if (!qs) { return; }
        jQuery('#displayResults').show();
        $.ajax({
            url: '/search/'+qs,
            dataType: 'json',
            success: tm.display_search_results,
            error: function(err) {
                jQuery('#displayResults').hide();
                alert("Error: " + err.status + "\nQuery: " + qs);
                }
        });    
    },
    
    
    widenEditMap : function(){
        return false;
                
        // #add_tree_map{
        // margin-left:-410px;
        // width:680px;
        // }


        // .activeEditTable{
        // margin-top:250px;
        // }
    
    },

    updateLocationFields: function(loc){
        if (loc){
            $("#location_search_input").val(loc);
            //var url = '/neighborhoods/?format=json&location=' + loc;
            tm.handleSearchLocation(loc);
            //tm.geocode(loc, true, tm.display_geography);
            //jQuery.getJSON(url, tm.display_geography);
        }
        
    },
    
    updateSpeciesFields: function(field_prefix,spec, cultivar){
        if (!tm.speciesData) { 
            var func = function() { 
                tm.updateSpeciesFields(field_prefix, spec, cultivar);
            }
            tm.speciesDataListeners.push(func);
            return;
        }
        if (spec) {
            $("#" + field_prefix + "_id").val(spec);
            if (cultivar) {
                $("#" + field_prefix + "_id_cultivar").val(cultivar);
            } else {
                $("#" + field_prefix + "_id_cultivar").val("");
            }    

            for (var i = 0; i < tm.speciesData.length; i++) {
                if (tm.speciesData[i].symbol == spec && (cultivar ? tm.speciesData[i].cultivar == cultivar : tm.speciesData[i].cultivar == '')) {
                    $("#" + field_prefix + "_input").val(tm.speciesData[i].cname + " / " + tm.speciesData[i].sname);
                }
            }
        }    
    },


    add_favorite_handlers : function(base_create, base_delete) {
        $('a.favorite.fave').live('click', function(e) {
            var pk = $(this).attr('id').replace('favorite_', '');
            var url = base_create + pk + '/';
            $.getJSON(url, function(data, textStatus) {
                $('#favorite_' + pk).removeClass('fave').addClass('unfave').text('Remove as favorite');
            });
            return false;
        });
        $('a.favorite.unfave').live('click', function(e) {
            var pk = $(this).attr('id').replace('favorite_', '');
            var url = base_delete + pk + '/';
            $.getJSON(url, function(data, textStatus) {
                $('#favorite_' + pk).removeClass('unfave').addClass('fave').text('Add as favorite');
            });
            return false;
        });
    },

    handleSearchLocation: function(search) {
       tm.geocode(search, true, function(point) {
           tm.geocoded_locations[search] = [point.x, point.y];
           tm.searchParams['location'] = search;
           tm.updateSearch();
       });
    },
    editDiameter: function(field, diams) {
        tm.editingDiameter = true;
        var diams = tm.currentTreeDiams || diams;
        var html = '';
        tm.currentDiameter = $(field).html();
        for (var i = 0; i < Math.max(diams.length, 1); i++) {
            var val = '';
            if (diams[i]) { val = parseFloat(diams[i].toFixed(3)); }
            html += "<input type='text' size='7' id='dbh"+i+"' name='dbh"+i+"' value='"+val+"' />";
            if (i == 0) {
                html += "<input type='checkbox' id='circum' name='circum' /> <small>Circumference?</small>"
            }
            html += "<br />";
        }
        tm.currentTreeDiams = diams.length ? diams : [0];
        html += "<span id='add_more_dbh'><a href='#' onclick='tm.addAnotherDiameter(); return false'>Another trunk?</a></span> <br />";
        html += "<span class='activeEdit'>";
        html += "<button type='submit' onclick='tm.saveDiameters(); return false;'>Save</button>";
        html += "<button type='submit' onclick='tm.cancelDiameters(); return false;'>Cancel</button>";
        html += "</span>";
        $(field).html(html);
    },
    cancelDiameters: function() {
        $("#edit_dbh").html(parseFloat(tm.currentDiameter).toFixed(1));
        tm.editingDiameter = false;
    },	
    addAnotherDiameter: function() {
        var dbh = $("#add_more_dbh")[0];
        var input = document.createElement("input");
        var count = tm.currentTreeDiams.length;
        input.name="dbh"+count;
        input.id="dbh"+count;
        input.size=7;
        tm.currentTreeDiams.push(null);
        dbh.parentNode.insertBefore(input, dbh);
        dbh.parentNode.insertBefore(document.createElement("br"), dbh);
    },
    saveDiameters: function() {
        var vals = [];
        var sum = 0;
        for (var i = 0; i < tm.currentTreeDiams.length; i++) {
            if ($("#dbh"+i).val()) {
			
                var val = parseFloat($("#dbh"+i).val());
                if ($("#circum").attr("checked") == true) {
                    val = val / Math.PI;
                }    
                vals.push(val);
                sum += Math.pow(val, 2);
            }
        }
        var total = Math.sqrt(sum);
        tm.currentTreeDiams = vals;
        var editableOptions = {
            submit: 'Save',
            cancel: 'Cancel',
            cssclass:  'activeEdit',
            indicator: '<img src="/static/images/loading-indicator.gif" alt="" />',
            width: '80%',
            model: 'TreeStatus',
            fieldName:  'dbh',
            extraData: {parent: {'model': 'Tree', 'id': tm.currentTreeId }}

        };
        tm.updateEditableServerCall(total, editableOptions);
        $("#edit_dbh").html(total.toFixed(1));
        tm.editingDiameter = false;
        
    },

     updateSpeciesFromKey: function(tree_code, tree_cultivar)  {
       alert(tree_code);
     },
    
    updateReputation: function(change_type, change_id, rep_dir) {
    	$.ajax({
	    url: '/verify/' + change_type + '/' + change_id + '/' + rep_dir,
	    dataType: 'json',
	    success: function(response) {
	    	$("#" + response.change_type + "_" + response.change_id).fadeOut();
	    },
	    error: function(err) {
		alert("Error: " + err.status + "\nQuery: " + change_type + " " + change_id + " " + rep_dir);
		}
        });
    },
    
}  
$.editable.addInputType("autocomplete_species", {
    element: function(settings, original) {
        var hiddenInput = $('<input type="hidden" class="hide">');
        var input = $("<input type='text' />");
        tm.setupAutoComplete(input).result(function(event, item) {
            hiddenInput[0].value = item.id; 
        });
        $(this).append(input);
        $(this).append(hiddenInput);
        return (hiddenInput);
    }
});    
