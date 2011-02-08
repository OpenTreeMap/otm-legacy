
jQuery.urlParam = function(name){
    var results = new RegExp('[\\?&]' + name + '=([^&#]*)').exec(window.location.href);
    if (results) {
        return results[1];
        }
    };

var tm_urls = {
    eactive_key : '898cfa06a63e5ad7a427a30896cd95c2',
    tc_url : 'http://sajara01:8080/tilecache/tilecache.cgi/',
    //tc_url : 'http://sajara01:8080/cgi-bin/mapserv.exe?map=E:\\Projects\\UrbanForestMap\\mapserver\\trees.map',
    qs_tile_url : '/qs_tiles/1.0.0/foo/' // layername is pulled from request.GET, can remove 'foo' eventually
    };

var tm_icons = {
    //base folder for shadow and other icon specific stuff
    base_folder : '/static/images/map_icons/v3/', 
    small_trees : "/static/images/map_icons/v4/zoom5.png",
    small_trees_complete : "/static/images/map_icons/v4/zoom5.png",
    focus_tree : '/static/images/map_icons/v4/marker-selected.png',
    marker : '/static/openlayers/img/marker.png'
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
    locations: null,
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
        //$("#search_form").submit(function() { return false; });
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
        $("#location_go").unbind('click');
        $("#location_go").click(function(evt) {
            if ($("#location_search_input")[0].value && $("#location_search_input").val() != "Philadelphia, PA") {
                tm.handleSearchLocation($("#location_search_input")[0].value);
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
                $(this).val("All trees");
                delete tm.searchParams['species'];
                tm.updateSearch();
            }    
        });
        $("#species_go").unbind('click');
        $("#species_go").click(function(evt) {
            if ($("#species_search_input")[0].value) {
                tm.updateSearch();
            }    
        });

        $("#close-filters").click(function(evt) {
            $("#diameter_slider").slider('option', 'values', [curmin, curmax]);
            $("#planted_slider").slider('option', 'values', [min_year, current_year]);
            $("#updated_slider").slider('option', 'values', [min_updated, max_updated]);
            delete tm.searchParams['diameter_range'];
            delete tm.searchParams['planted_range'];
            delete tm.searchParams['updated_range'];

            var checks = $("#options_form input:checked");
            for(var i=0;i<checks.length;i++) {
                delete tm.searchParams[checks[i].id];
            }
            $("#options_form input:checked").attr('checked', false)
            tm.updateSearch()

        });
        
        //tm.updateSearch();
    },    
    
    setupSpeciesList: function() {
        var ul = $("<ul id='s_list' style='max-height:180px; overflow:auto;'></ul>");
        $("#searchSpeciesList").append(ul).hide();
        for(var i=0; i<tm.speciesData.length;i++) {
            if (tm.speciesData[i].count == 0) {continue;}
            var c = "ac_odd";
            if (i%2 == 0) {c = 'ac-even';}
            ul.append("<li id='" + tm.speciesData[i].symbol + "' class='" + c + "'>" + tm.speciesData[i].cname + " [" + tm.speciesData[i].sname + "]</li>")
        }
        
        $("#s_list > li").hover(function(evt) {
            $(this).addClass("ac_over")
        }, function(evt) {
            $(this).removeClass("ac_over")
        }).click(function(evt) {
            $('#species_search_input').val(this.innerHTML)
            $("#species_search_id").val(this.id).change();
            $("#searchSpeciesList").toggle();
        });
        
    },
    
    setupLocationList: function() {
        var ul = $("<ul id='n_list' style='max-height:180px; overflow:auto;'></ul>");
        $("#searchNBList").append(ul).hide();
        for(var i=0; i<tm.locations.features.length;i++) {
            var c = "ac_odd";
            if (i%2 == 0) {c = 'ac-even';}
            var feature = tm.locations.features[i];
            var name = feature.properties.name;
            ul.append("<li id='" + feature.properties.name + "' class='" + c + "'>" + name + "</li>")
        }

        $("#n_list > li").hover(function(evt) {
            $(this).addClass("ac_over")
        }, function(evt) {
            $(this).removeClass("ac_over")
        }).click(function(evt) {
            $('#location_search_input').val(this.innerHTML).change();
            $("#searchNBList").toggle();
        });
            
    },
    baseTemplatePageLoad:function() {
        $("#logo").click(function() {
            location.href="http://207.245.89.214/";
        });        
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
            tm.setupSpeciesList();
            var spec = $.address.parameter("species");
            var cultivar = $.address.parameter("cultivar");
            tm.updateSpeciesFields("search_species",spec, cultivar);
            for (var i = 0; i < tm.speciesDataListeners.length; i++) {
                tm.speciesDataListeners[i]();
            }    
            //var loc = $.address.parameter("location");
            //tm.updateLocationFields(loc);
        });
        jQuery.getJSON('/neighborhoods/', {format:'json', list: 'list'}, function(nbhoods){
            tm.locations = nbhoods;
            tm.setupLocationList();
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
                //$('#filter_name')[0].innerHTML = 'Hide advanced filters';
            }    
            else {
                if (location.pathname == "/map/") {
                    $('.filter-box').slideUp('slow');
                }
                adv_active = false;
                $('#arrow').attr('src','/static/images/v2/arrow1.gif');
                //$('#filter_name')[0].innerHTML = 'Show advanced filters';          
            }
            return false;
        });
        
        $("#location_search_input").blur(function(evt) {
            if (!this.value) {
                $("#location_search_input").val("Philadelphia, PA");
            }    
        });
        $("#species_search_input").blur(function(evt) {
            if (!this.value) {
                $("#species_search_id").val("");
                $(this).val("All trees");
            }    
        });
        $("#location_go").click(function(evt) {
                triggerSearch();
        });
        $("#species_go").click(function(evt) {            
                triggerSearch();
        });
        $("#searchSpeciesBrowse").click(function(evt) {
            $("#searchSpeciesList").toggle();
        });
        $("#searchLocationBrowse").click(function(evt) {
            $("#searchNBList").toggle();
        });

        // todo - clean this logic up...
        if (jQuery.urlParam('diameter') || jQuery.urlParam('date') || jQuery.urlParam('characteristics') ||  jQuery.urlParam('advanced') )
        {
            //TODO: might be causing duplicate search
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
            
            
        tm.add_favorite_handlers('/trees/favorites/create/', '/trees/favorites/delete/');
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
    
    load_nearby_trees : function(ll){
        //load in nearby trees as well
        var url = ['/trees/location/?lat=',ll.lat,'&lon=',ll.lon,'&format=json&max_trees=70'].join('');
        $.getJSON(url, function(geojson){
            $.each(geojson.features, function(i,f){
                coords = f.geometry.coordinates;
                var ll = new OpenLayers.LonLat(coords[0], coords[1]).transform(new OpenLayers.Projection("EPSG:4326"), tm.map.getProjectionObject());
                if (f.properties.id == tm.currentTreeId) {return;}
                var icon = tm.get_icon(tm_icons.small_trees, 17);
                var marker = new OpenLayers.Marker(ll, icon);
                marker.tid = f.properties.id;
                
                tm.tree_layer.addMarker(marker);
                                
            });
        });
    },
    
    init_base_map: function(div_id){
        if (!div_id) {
            div_id = "map";
        };
        tm.map = new OpenLayers.Map(div_id, {
                maxExtent: new OpenLayers.Bounds(-20037508.34, -20037508.34, 20037508.34, 20037508.34),
                restrictedExtent: new OpenLayers.Bounds(-8552949.884372,4717730.118866,-8187275.141121,5011248.307428), 
                units: 'm',
                projection: new OpenLayers.Projection("EPSG:102100"),
                displayProjection: new OpenLayers.Projection("EPSG:4326"),
                controls: [new OpenLayers.Control.Attribution(),
                           new OpenLayers.Control.Navigation(),
                           new OpenLayers.Control.ArgParser(),
                           new OpenLayers.Control.PanPanel(),
                           new OpenLayers.Control.ZoomPanel()]
            }
        );
        
        var baseLayer = new OpenLayers.Layer.XYZ("ArcOnline", 
            "http://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/${z}/${y}/${x}.jpg", 
            {
                sphericalMercator: true
            }
        );
        tms = new OpenLayers.Layer.TMS('TreeLayer', 
            tm_urls.tc_url,
            {
                layername: 'Map',
                type: 'png',
                isBaseLayer: false,
                opacity:0.7,
                wrapDateLine: true,
                attribution: "(c) PhillyTreeMap.org"
            }
        );
        baseLayer.buffer = 0;
        tm.map.addLayers([baseLayer, tms]);
    },
        
    init_map : function(div_id){
        tm.init_base_map(div_id);
        
        tm.tree_layer = new OpenLayers.Layer.Markers('MarkerLayer')
        tm.misc_markers = new OpenLayers.Layer.Markers('MarkerLayer2')
        tm.vector_layer = new OpenLayers.Layer.Vector('Vectors')
        
        tm.map.addLayers([tm.vector_layer, tm.tree_layer, tm.misc_markers]);
        tm.map.setCenter(
            new OpenLayers.LonLat(-75.19, 39.99).transform(new OpenLayers.Projection("EPSG:4326"), tm.map.getProjectionObject())
            , 11);
            
        //check to see if coming for a bookmarked tree
        var bookmark_id = jQuery.urlParam('tree');
        if (bookmark_id){
            jQuery.getJSON('/trees/' + bookmark_id  + '/',
               {'format' : 'json'},
                tm.display_tree_details);
            }
        
        tm.map.events.register("click", tm.map, function (e) {
            var mapCoord = tm.map.getLonLatFromViewPortPx(e.xy);
            mapCoord.transform(tm.map.getProjectionObject(), new OpenLayers.Projection("EPSG:4326"));           
            tm.clckTimeOut = window.setTimeout(function() {
                singleClick(mapCoord)
                },500); 
        });
                
        function singleClick(olLonlat) { 
            window.clearTimeout(tm.clckTimeOut); 
            tm.clckTimeOut = null; 
            var spp = jQuery.urlParam('species');
            jQuery.getJSON('/trees/location/',
              {'lat': olLonlat.lat, 'lon' : olLonlat.lon, 'format' : 'json', 'species':spp},
            tm.display_tree_details);
        } 

        tm.geocoder = new google.maps.Geocoder();

    },
            
    //initializes the map where a user places a new tree
    init_add_map : function(){
        tm.init_base_map('add_tree_map');
        
        var arial = new OpenLayers.Layer.XYZ("ArcOnlineArial", 
            "http://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/${z}/${y}/${x}.jpg", 
            {
                sphericalMercator: true
            }
        );
        var roads = new OpenLayers.Layer.XYZ("ArcOnlineRoads", 
            "http://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Transportation/MapServer/tile/${z}/${y}/${x}.jpg", 
            {
                sphericalMercator: true, isBaseLayer:false
            }
        );
        
        tm.add_vector_layer = new OpenLayers.Layer.Vector('AddTreeVectors')
        tm.tree_layer = new OpenLayers.Layer.Markers('MarkerLayer')

        tm.drag_control = new OpenLayers.Control.DragFeature(tm.add_vector_layer);
        tm.drag_control.onComplete = function(feature, mousepix) {
            var mapCoord = tm.map.getLonLatFromViewPortPx(mousepix);
            mapCoord.transform(tm.map.getProjectionObject(), new OpenLayers.Projection("EPSG:4326"));
            tm.reverse_geocode(mapCoord);
            jQuery('#id_lat').val(mapCoord.lat);
            jQuery('#id_lon').val(mapCoord.lon);
        }

        tm.map.addLayers([arial, roads, tm.add_vector_layer, tm.tree_layer]);
        tm.map.setBaseLayer(arial);
        tm.map.addControl(tm.drag_control);
        tm.map.setCenter(
            new OpenLayers.LonLat(-75.19, 39.99).transform(new OpenLayers.Projection("EPSG:4326"), tm.map.getProjectionObject())
            , 13);
            
        tm.map.events.register("click", tm.map, function (e) {
            if (tm.add_vector_layer.features.length > 0) {
                return false;
            }
            var mapCoord = tm.map.getLonLatFromViewPortPx(e.xy);
            var zoom = 15;
            if (tm.map.getZoom() > 15) {zoom = tm.map.getZoom();}
            tm.map.setCenter(mapCoord, zoom);
            
            mapCoord.transform(tm.map.getProjectionObject(), new OpenLayers.Projection("EPSG:4326"));
            
            tm.load_nearby_trees(mapCoord);
            tm.add_new_tree_marker(mapCoord);
            
            tm.drag_control.activate();
            
            jQuery('#id_lat').val(mapCoord.lat);
            jQuery('#id_lon').val(mapCoord.lon);
        });
                
        tm.geocoder = new google.maps.Geocoder();
    
        //listen for change to address field to update map location //todo always?
        
        jQuery('#id_edit_address_street').change(function(nearby_field){
            //console.log(nearby_field);
            var new_addy = nearby_field.target.value;
            //new_addy += ", ph";
            if (!tm.tree_marker && new_addy){ //only add marker if it doesn't yet exist                
                tm.geocoder.geocode({
                        address: new_addy,
                        bounds: new google.maps.LatLngBounds(new google.maps.LatLng(39.75,-76), new google.maps.LatLng(40.5,-74.5))    
                    }, 
                    function(results, status) {
                        if (status == google.maps.GeocoderStatus.OK) {
                            var olPoint = new OpenLayers.LonLat(results[0].geometry.location.lng(), results[0].geometry.location.lat());
                            tm.map.setCenter(new OpenLayers.LonLat(results[0].geometry.location.lng(), results[0].geometry.location.lat()).transform(new OpenLayers.Projection("EPSG:4326"), tm.map.getProjectionObject()), 15);
         
                            tm.load_nearby_trees(olPoint);
                            tm.add_new_tree_marker(olPoint);

                            tm.drag_control.activate();

                            jQuery('#id_lat').val(olPoint.lat);
                            jQuery('#id_lon').val(olPoint.lon);

                        } else {
                            alert("Geocode was not successful for the following reason: " + status);
                        }

                    }
                );  
            }        
        });
    },
        
    //initializes map on the profile page; shows just favorited trees
    init_favorite_map : function(user){
        tm.init_base_map('favorite_tree_map');
        
        tm.tree_layer = new OpenLayers.Layer.Markers('MarkerLayer')
        tm.map.addLayers([tm.tree_layer]);
        
        //load in favorite trees
        var url = ['/trees/favorites/' + user + '/geojson/']
        $.getJSON(url, function(json){
            $.each(json, function(i,f){
                var coords = f.coords;
                var ll = new OpenLayers.LonLat(coords[0], coords[1]);
                marker = tm.get_marker_light(ll, 17);
                marker.tid = f.id;
                tm.tree_layer.addMarker(marker);
            });
            var bounds = tm.tree_layer.getDataExtent();
            tm.map.zoomToExtent(bounds, true);
        });
            
        //TODO: get this working
        //GEvent.addListener(tm.map,"click", function(overlay, ll){
        //    if (overlay && overlay.tid){
        //        var html = '<a href="/trees/' + overlay.tid + '">Tree #' + overlay.tid + '</a>';
        //        $('#alternate_tree_div').html(html);
        //        }
        //    });
        },
        
    //initializes the map on the detail/edit page, 
    // where a user just views, or moves, an existing tree
    // also it loads the streetview below the map
    init_tree_map : function(editable){
        tm.init_base_map('add_tree_map');
        
        tm.add_vector_layer = new OpenLayers.Layer.Vector('AddTreeVectors')
        tm.tree_layer = new OpenLayers.Layer.Markers('MarkerLayer')
        
        tm.drag_control = new OpenLayers.Control.DragFeature(tm.add_vector_layer);
        tm.drag_control.onComplete = function(feature, mousepix) {
            var mapCoord = tm.map.getLonLatFromViewPortPx(mousepix);
            mapCoord.transform(tm.map.getProjectionObject(), new OpenLayers.Projection("EPSG:4326"));
            jQuery('#id_geometry').val('POINT (' + mapCoord.lon + ' ' + mapCoord.lat + ')')
            //tm.updateEditableLocation();
            
        }
        
        tm.map.addLayers([tm.tree_layer, tm.add_vector_layer]);
        tm.map.addControl(tm.drag_control);
        
        var currentPoint = new OpenLayers.LonLat(tm.current_tree_geometry[0], tm.current_tree_geometry[1]);        
        var olPoint = new OpenLayers.LonLat(tm.current_tree_geometry[0], tm.current_tree_geometry[1]).transform(new OpenLayers.Projection("EPSG:4326"), tm.map.getProjectionObject());
        
        tm.map.setCenter(olPoint, 17);
        
        tm.geocoder = new google.maps.Geocoder();
        tm.add_new_tree_marker(currentPoint);
        tm.load_nearby_trees(currentPoint);
        
        //if (editable) { tm.drag_control.activate(); }
        
        tm.load_streetview(currentPoint, 'tree_streetview');
                
        tm.map.events.register('click', tm.map, function(e){
            var mapCoord = tm.map.getLonLatFromViewPortPx(e.xy);
            mapCoord.transform(tm.map.getProjectionObject(), new OpenLayers.Projection("EPSG:4326"));
            jQuery.getJSON('/trees/location/',
                {'lat': mapCoord.lat, 'lon' : mapCoord.lon, 'format' : 'json', 'max_trees' : 1},
                function(json) {
                    var html = '<a href="/trees/' + json.features[0].properties.id + '">Tree #' + json.features[0].properties.id + '</a>';
                    $('#alternate_tree_div').html(html);
                }
            );
        });
        
        if (!editable) {return;}
        
        //listen for change to address field to update map location //todo always?
        jQuery('#id_nearby_address').change(function(nearby_field){

            var new_addy = nearby_field.target.value;
            //new_addy += ', ph';
            tm.geocoder.getLatLng(new_addy, function(ll){
                if (tm.validate_point(ll,new_addy) && !tm.tree_marker){ //only add marker if it doesn't yet exist
                    tm.add_new_tree_marker(ll);
                    tm.map.setCenter(ll,15);
                    }
                
                });
            });
        },
    
    get_icon: function(type, size) {
        var size = new OpenLayers.Size(size, size);
        var offset = new OpenLayers.Pixel(-(size.w/2), -(size.h/2));
        if (type == tm_icons.marker) {
            size = new OpenLayers.Size(33, 32);
            offset = new OpenLayers.Pixel(-(size.w/2), -(size.h)); 
        }
        
        var icon = new OpenLayers.Icon(type, size, offset);
        return icon
    },
        
    //returns a large or small markerLight
    get_marker_light : function(t, size){
        var ll = new OpenLayers.LonLat(t.lon, t.lat).transform(new OpenLayers.Projection("EPSG:4326"), tm.map.getProjectionObject());       

        if (size == 'small') {        
            if (t.cmplt) { var icon = tm.get_icon(tm_icons.small_trees_complete, 13);}
            else { var icon = tm.get_icon(tm_icons.small_trees, 13);}
            var marker = new OpenLayers.Marker(ll, icon);
          } else {
            var icon = tm.get_icon(tm_icons.focus_tree, 19);
            var marker = new OpenLayers.Marker(ll, icon);
                        
          }
          
        return marker
    },        
        
    get_tree_marker: function(lat, lng) {
        var ll = new OpenLayers.LonLat(lng, lat).transform(new OpenLayers.Projection("EPSG:4326"), tm.map.getProjectionObject());
        var marker = new OpenLayers.Marker(ll, tm.get_icon(tm_icons.focus_tree, 19));

        return marker
        },
        
    add_new_tree_marker : function(ll){
        if (tm.add_vector_layer) {
            tm.add_vector_layer.destroyFeatures();
        }
        var tree_marker = new OpenLayers.Geometry.Point(ll.lon, ll.lat).transform(new OpenLayers.Projection("EPSG:4326"), tm.map.getProjectionObject());
        var tree_vector = new OpenLayers.Feature.Vector(tree_marker)
        
        tm.add_vector_layer.addFeatures([tree_vector])
        tm.reverse_geocode(ll);
        
        },
        
        
    //pass in a GLatLng and get back closest address
    reverse_geocode : function(ll){
        latlng = new google.maps.LatLng(ll.lat, ll.lon)
        tm.geocoder.geocode({
                latLng: latlng
            }, function(results, status){
            if (status == google.maps.GeocoderStatus.OK) {
                var addy = results[0].address_components;
                
                $.each(addy, function(index, value){
                    if ($.inArray('locality', value.types) > -1) {
                         if ($('#edit_address_city')) {
                            $('#edit_address_city').val(value.long_name);
                            $('#edit_address_city').html(value.long_name);
                        }
                        if ($('#id_edit_address_city')) {
                            $('#id_edit_address_city').val(value.long_name);
                        }
                    }
                    else if ($.inArray('postal_code', value.types) > -1) {
                        if ($('#edit_address_zip')) {
                            $('#edit_address_zip').val(value.long_name);
                            $('#edit_address_zip').html(value.long_name);
                        }
                        if ($('#id_edit_address_zip')) {
                            $('#id_edit_address_zip').val(value.long_name);
                        }
                    }
                    
                });
                
                var street = results[0].formatted_address.split(',')[0];
                
                if ($('#edit_address_street')) {
                    $('#edit_address_street').val(street);
                    $('#edit_address_street').html(street);
                }
                
                if ($('#id_edit_address_street') && street) {
                    $('#id_edit_address_street').val(street);
                }

            } else {
                alert("Geocode was not successful for the following reason: " + status);
            }
        
        });
    
        
        },
    
        
    /*
    load up streetview pointing at specified GLatLng, into specified div
    */
    load_streetview : function(ll, div){
          div = document.getElementById(div);
          panoPosition = new google.maps.LatLng(ll.lat, ll.lon);
          tm.pano = new google.maps.StreetViewPanorama(div, {position:panoPosition});
          
        },
        
                
    highlight_geography : function(geometry, geog_type){
        poly_color = {'zipcodes' : 'blue', 'neighborhoods' : 'red' };
        var verts = [];
        jQuery.each(geometry.coordinates[0], function(i, c){ //no multipoly support
            verts.push(new OpenLayers.Geometry.Point(c[0],c[1]).transform(new OpenLayers.Projection("EPSG:4326"), tm.map.getProjectionObject()));
            });
        if (tm.vector_layer){
            tm.vector_layer.destroyFeatures();
            }
        var poly = new OpenLayers.Geometry.LineString(verts);
        var feature = new OpenLayers.Feature.Vector(poly, null, {
            strokeColor: "#289255",
            strokeWidth: 4,
            strokeOpacity: 0.7
        });
        tm.vector_layer.addFeatures(feature);
        },
        
    display_tree_details : function(json){
        if (json) {
            if (json.features.length > 0) {
                var tree = json.features[0];
                var p = tree.properties;
                var coords = tree.geometry.coordinates;
                
                //remove old markers
                if (tm.tree_detail_marker) {tm.tree_layer.removeMarker(tm.tree_detail_marker);}
                
                var AutoSizeFramedCloud = OpenLayers.Class(OpenLayers.Popup.FramedCloud, {
                    'autoSize': true
                });
                                
                //Add tree marker
                tm.tree_detail_marker = tm.get_tree_marker(coords[1], coords[0]);
                tm.tree_detail_marker.tree_id = p.id;
                tm.tree_detail_marker.nhbd_id = p.neighborhood_id;
                tm.tree_detail_marker.district_id = p.district_id;
                tm.tree_layer.addMarker(tm.tree_detail_marker);
                
                
                var ll = tm.tree_detail_marker.lonlat;
                
                popup = new OpenLayers.Popup.FramedCloud("Tree Info",
                   ll,
                   null,
                   '<div id="max_tree_infowindow">Loading ...</div>',
                   tm.tree_detail_marker.icon,
                   true);
                popup.minSize = new OpenLayers.Size(400,200);
                popup.maxSize = new OpenLayers.Size(500,500);
                popup.autoSize = true;
                popup.panMapIfOutOfView = true;
                tm.map.addPopup(popup, true);
                jQuery('#max_tree_infowindow').load('/trees/' + tm.tree_detail_marker.tree_id + '/?format=base_infowindow');
                
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
        //var layer_name = tm.map.getCurrentMapType().getName();
        //var u = tm_urls.tc_url + layer_name + '/' + tm.map.getZoom() + '/' + a.x  + '/' + a.y + '.png';
        //var u = tm_urls.qs_tile_url + tm.map.getZoom() + '/' + a.x  + '/' + a.y + '.png?' + tm.selected_tile_query;
        //console.log(u);
        //return u;
        },
    
    set_selected_tile_overlay : function(){
        //if (tm.current_selected_tile_overlay)
        //{
        //    tm.map.removeOverlay(tm.current_selected_tile_overlay);
        //}
        //if (tm.cur_polygon){
        //    tm.map.removeOverlay(tm.cur_polygon);
        //}
        //if (tm.tree_detail_marker){
        //tm.map.removeOverlay(tm.tree_detail_marker);
        //}

        //var myCopyright = new GCopyrightCollection("(c) ");
        //myCopyright.addCopyright(new GCopyright('Urban Forest Map',
        //  new GLatLngBounds(new GLatLng(-90,-180), new GLatLng(90,180)),
        //  0,'bar'));

        //tm.selected_tree_layer = new GTileLayer(myCopyright);
        //tm.selected_tree_layer.getTileUrl = tm.get_selected_tile;
        //tm.selected_tree_layer.isPng = function() { return true;};
        /*
        if (navigator.appName != 'Microsoft Internet Explorer')
        {
            tm.tree_layer.getOpacity = function() { return .75; }
        }
        */
    
        //tm.current_selected_tile_overlay = new GTileLayerOverlay(tm.selected_tree_layer);
        //tm.map.addOverlay(tm.current_selected_tile_overlay);
    },
            
    display_search_results : function(results){
        
        if (tm.tree_layer) {tm.tree_layer.clearMarkers();}
        if (tm.tree_layer) {tm.vector_layer.destroyFeatures();}
        jQuery('#displayResults').hide();
        //if (tm.current_selected_tile_overlay)
        //{
        //    tm.map.removeOverlay(tm.current_selected_tile_overlay);
        //}
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
    
    overlay_trees : function(trees){
        //remove old trees
        jQuery.each(trees, function(i,t){
            var smarker = tm.get_marker_light(t, 'small')
            tm.tree_layer.addMarker(smarker);
            });
        },
        
        // unused?
        select_species : function(species){
            tm.mgr.clearMarkers();
            jQuery.getJSON('/search/' + species + '/?simple=true', 
                tm.display_search_results);
        },

     
    enableEditTreeLocation : function(){
        //tm.tree_marker.enableDragging();
        tm.drag_control.activate();
        //TODO:  bounce marker a bit, or change its icon or something
        var save_html = '<a href="javascript:tm.saveTreeLocation()" class="buttonSmall"><img src="/static/images/loading-indicator-trans.gif" width="12" /> Stop editing and save</a>'
        $('#edit_tree_location').html(save_html);
        return false;
        },
        
    saveTreeLocation : function(){
        //tm.tree_marker.disableDragging();     
        tm.drag_control.activate();
        var edit_html = '<a href="#" onclick="tm.enableEditTreeLocation(); return false;"class="buttonSmall">Start editing tree location</a>'
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
        
        tm.geocode_address = address;
                
        jQuery.getJSON('/neighborhoods/', {format:'json', name: tm.geocode_address}, function(nbhoods){
            if (tm.location_marker) {tm.tree_layer.removeMarker(tm.location_marker)} 
                
            if (nbhoods.features.length > 0) {
                var olPoint = OpenLayers.Bounds.fromArray(nbhoods.bbox).getCenterLonLat();
                var bbox = OpenLayers.Bounds.fromArray(nbhoods.bbox).transform(new OpenLayers.Projection("EPSG:4326"), tm.map.getProjectionObject());
                tm.map.zoomToExtent(bbox, true);
                
                if (nbhoods.features[0].properties.name == 'Philadelphia'){                    
                    if (callback) {
                        callback(null);
                    }   
                }else {  
                    var icon = tm.get_icon(tm_icons.marker,0);
                    tm.location_marker = new OpenLayers.Marker(bbox.getCenterLonLat(), icon);
                    tm.misc_markers.addMarker(tm.location_marker);
                    tm.location_marker.events.register("mouseover", tm.location_marker, function(e){
                        var popupPixel = tm.map.getViewPortPxFromLonLat(this.lonlat);
                        popupPixel.y += this.icon.offset.y - 25;
                        tm.smallPopup = new OpenLayers.Popup("popup_address",
                                   tm.map.getLonLatFromPixel(popupPixel),
                                   null,
                                   $("#location_search_input").val(),
                                   false);
                        tm.smallPopup.minSize = new OpenLayers.Size(20,25);
                        tm.smallPopup.maxSize = new OpenLayers.Size(150,25);
                        tm.smallPopup.border = "1px solid Black";
                        tm.map.addPopup(tm.smallPopup);
                        tm.smallPopup.updateSize();
                    });
                    tm.location_marker.events.register("mouseout", tm.location_marker, function(e){
                        tm.map.removePopup(tm.smallPopup);
                    });
                                  
                    if (callback) {
                        callback(olPoint);
                    }
                }

            }
            else {
                var address = tm.geocode_address + ", pa";
                        
                tm.geocoder.geocode({
                    address: address,
                    bounds: new google.maps.LatLngBounds(new google.maps.LatLng(39.75,-76), new google.maps.LatLng(40.5,-74.5))    
                }, function(results, status){
                    if (status == google.maps.GeocoderStatus.OK) {
                        var olPoint = new OpenLayers.LonLat(results[0].geometry.location.lng(), results[0].geometry.location.lat());
                        tm.map.setCenter(new OpenLayers.LonLat(results[0].geometry.location.lng(), results[0].geometry.location.lat()).transform(new OpenLayers.Projection("EPSG:4326"), tm.map.getProjectionObject()), 15);

                        var icon = tm.get_icon(tm_icons.marker,0);
                        tm.location_marker = new OpenLayers.Marker(new OpenLayers.LonLat(results[0].geometry.location.lng(), results[0].geometry.location.lat()).transform(new OpenLayers.Projection("EPSG:4326"), tm.map.getProjectionObject()), icon);

                        tm.misc_markers.addMarker(tm.location_marker);

                        tm.location_marker.events.register("mouseover", tm.location_marker, function(e){
                            var popupPixel = tm.map.getViewPortPxFromLonLat(this.lonlat);
                            popupPixel.y += this.icon.offset.y - 25;
                            tm.smallPopup = new OpenLayers.Popup("popup_address",
                                       tm.map.getLonLatFromPixel(popupPixel),
                                       null,
                                       $("#location_search_input").val(),
                                       false);
                            tm.smallPopup.minSize = new OpenLayers.Size(20,25);
                            tm.smallPopup.maxSize = new OpenLayers.Size(150,25);
                            tm.smallPopup.border = "1px solid Black";
                            tm.map.addPopup(tm.smallPopup);
                            tm.smallPopup.updateSize();
                        });

                        tm.location_marker.events.register("mouseout", tm.location_marker, function(e){
                            tm.map.removePopup(tm.smallPopup);
                        });


                        if (callback) {
                            callback(olPoint);
                        }

                    } else {
                        alert("Geocode was not successful for the following reason: " + status);
                    }
                
                });
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
            //  //it's a javascript-parsable date, so we'll take it
            //  var dateVal = new Date(Date.parse(value));
            //  value = dateVal.getFullYear() + "-" + (dateVal.getMonth()+1) + "-" + dateVal.getDate()
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
            max:50,

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
                    tm.updateLocationFields($.address.parameter(key).replace(/\+/g, " "));
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
        //tm.tree_layer.clearMarkers();
        var qs = tm.serializeSearchParams();
        if (qs === false) { return; }
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
        if (tm.misc_markers) {tm.misc_markers.clearMarkers();}
        if (tm.vector_layer) {tm.vector_layer.destroyFeatures();}
        tm.geocode(search, true, function(point) {
            if (point) {
                tm.geocoded_locations[search] = [point.lon, point.lat];
                tm.searchParams['location'] = search;                
            } else {
                delete tm.searchParams.location;
            }
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
    
    updateReputation_Admin: function(user_id, rep_total) {
        var data = {
        'user_id': user_id,
        'rep_total': rep_total
    };
        var jsonString = JSON.stringify(data);
        
        $.ajax({
        url: '/users/update/',
        dataType: 'json',
        data: jsonString,
        type: 'POST',
        success: function(response) {
        },
        error: function(err) {
        alert("Error: " + err.status + "\nQuery: " + user_id + " " + rep_total);
        }
        });
    },
    
    updateGroup_Admin: function(user_id, group_id) {
        var data = {
            'user_id': user_id,
            'group_id': group_id
        };
            var jsonString = JSON.stringify(data);
            
        $.ajax({
            url: '/users/update/',
            dataType: 'json',
            data: jsonString,
            type: 'POST',
            success: function(response) {
                if (response.new_rep)
                {$("#reputation_" + response.user_id).val(response.new_rep);}
            },
            error: function(err) {
            alert("Error: " + err.status + "\nQuery: " + user_id + " " + group_id);
            }
        });
    },
    
    hideComment: function(flag_id) {
    var data = {
            'flag_id': flag_id
        };
        var jsonString = JSON.stringify(data);      
        $.ajax({
        url: '/comments/hide/',
        dataType: 'json',
        data: jsonString,
        type: 'POST',
        success: function(response) {
        $("#" + flag_id).fadeOut();
        },
        error: function(err) {
        alert("Error: " + err.status + "\nQuery: " + flag_id );
        }
        });
    },
    removeFlag: function(flag_id) {
        var data = {
        'flag_id': flag_id
    };
    var jsonString = JSON.stringify(data);      
    $.ajax({
        url: '/comments/unflag/',
        dataType: 'json',
        data: jsonString,
        type: 'POST',
        success: function(response) {
        $("#" + flag_id).fadeOut();
        },
        error: function(err) {
        alert("Error: " + err.status + "\nQuery: " + flag_id );
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
