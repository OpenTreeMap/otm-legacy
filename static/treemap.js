
jQuery.urlParam = function(name){
    var results = new RegExp('[\\?&]' + name + '=([^&#]*)').exec(window.location.href);
    if (results) {
        return results[1];
        }
    };
    
jQuery('html').ajaxSend(function(event, xhr, settings) {
    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
        // Only send the token to relative URLs i.e. locally.
        xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
    }
});



var tm_icons = {
    //base folder for shadow and other icon specific stuff
    base_folder : tm_static + 'static/images/map_icons/v3/', 
    small_trees : tm_static + "static/images/map_icons/v3/UFM_Tree_Icon_zoom7b.png",
    small_trees_complete : tm_static + "static/images/map_icons/v3/UFM_Tree_Icon_zoom7b.png",
    focus_tree : tm_static + 'static/images/map_icons/v4/marker-selected.png',
    pending_tree : tm_static + 'static/images/map_icons/v4/marker-pending.png', 
    marker : tm_static + 'static/openlayers/img/marker.png'
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

    map_center_lon: null,
    map_center_lat: null,
    start_zoom: null,
    add_start_zoom: null,
    add_zoom: null,

    google_bounds: null,
    panoAddressControl: true,

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
    trackEvent: function(category, action, label, value) {
       
        _gaq.push(['_trackEvent', category, action, label, value]);
        
    },
    trackPageview: function(url) {        
        _gaq.push(['_trackPageview', url]);        
    },
    baseTemplatePageLoad:function() {
        //document.namespaces;
        $("#logo").click(function() {
        //    location.href="/home";
        });        
        jQuery.getJSON(tm_static + 'species/json/', function(species){
            tm.speciesData = species;
            tm.setupAutoComplete($('#species_search_input')).result(function(event, item) {
                $("#species_search_id").val(item.id).change(); 
                if (item.cultivar) {
                    $("#species_search_id_cultivar").val(item.cultivar).change(); 
                } else {
                    $("#species_search_id_cultivar").val("").change();
                } 
            });
            if ($('#id_species_name')) {
                tm.setupAutoComplete($('#id_species_name')).result(function(event, item) {
                    $("#id_species_id").val(item.symbol).change();
                });
            }
            tm.setupSpeciesList();
            var spec = $.address.parameter("species");
            var cultivar = $.address.parameter("cultivar");
            tm.updateSpeciesFields("search_species",spec, cultivar);
            for (var i = 0; i < tm.speciesDataListeners.length; i++) {
                tm.speciesDataListeners[i]();
            }    
        });
        jQuery.getJSON(tm_static + 'neighborhoods/', {format:'json', list: 'list'}, function(nbhoods){
            tm.locations = nbhoods;
            tm.setupLocationList();
        });
        var adv_active = false;
        $('#advanced').click(function() {
            if (!adv_active) {
                $('.filter-box').slideDown('slow');
                adv_active = true;
                $('#arrow').attr('src',tm_static + 'static/images/v2/arrow2.gif');
            }    
            else {
                $('.filter-box').slideUp('slow');
                adv_active = false;
                $('#arrow').attr('src',tm_static + 'static/images/v2/arrow1.gif');
            }
            return false;
        });
        
        $("#location_search_input").blur(function(evt) {
            if (!this.value) {
                $("#location_search_input").val("");
                $(this).val(tm.initial_location_string);
            }    
        }).keydown(function(evt) {
            if (evt.keyCode == 13) {
                $("#location_go").click();
            }
        });
        
        $("#species_search_input").blur(function(evt) {
            if (!this.value) {
                $("#species_search_id").val("");
                $(this).val(tm.initial_species_string);
            }    
        }).keydown(function(evt) {
            if (evt.keyCode == 13) {
                $("#species_go").click();
            }
        });
        $("#species_search_id").change(function(evt) {
            if (this.value) {
                tm.searchParams['species'] = this.value;
            }
        });
        $("#location_go").click(function(evt) {
            if ($('body')[0].id == "results") {
                if ($("#location_search_input")[0].value && $("#location_search_input").val() != tm.initial_location_string) {
                //if ($("#location_search_input")[0].value ) {
                    tm.handleSearchLocation($("#location_search_input")[0].value);
                } else {
                    $("#location_search_input").val(tm.initial_location_string);
                    delete tm.searchParams['location'];
                    delete tm.searchParams['geoName'];
                    if (tm.misc_markers) {tm.misc_markers.clearMarkers();}
                    if (tm.map) {
                        tm.map.setCenter(
                            new OpenLayers.LonLat(tm.map_center_lon, tm.map_center_lat).transform(new OpenLayers.Projection("EPSG:4326"), tm.map.getProjectionObject())
                            , tm.start_zoom);
                    }
                    tm.updateSearch();
                } 
            } else {
                triggerSearch();
            }
        });
        
        $("#species_go").click(function(evt) {
            $("#location_go").click();
        });
        $("#searchSpeciesBrowse").click(function(evt) {
            $("#searchSpeciesList").slideToggle();
            tm.trackEvent('Search', 'List Species');
        });
        $("#searchLocationBrowse").click(function(evt) {
            $("#searchNBList").slideToggle();
            tm.trackEvent('Search', 'List Location');
        });

        // todo - clean this logic up...
        if (jQuery.urlParam('diameter') || jQuery.urlParam('date') || jQuery.urlParam('characteristics') ||  jQuery.urlParam('advanced') )
        {
            //TODO: might be causing duplicate search
            jQuery('#advanced').click();
        }
        function triggerSearch() {
            var q = $.query.empty();
            if ($("#location_search_input").val() != tm.initial_location_string) { 
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
            window.location.href = tm_static + "map/#" + decodeURIComponent(q.toString());
            return false;
        }
        //$("#search_form").submit(triggerSearch);    
        $("#advanced").click(function() {
            tm.advancedClick = true;
            triggerSearch();
            });   
            
            
        tm.add_favorite_handlers('/trees/favorites/create/', '/trees/favorites/delete/');
    },    
    resultsTemplatePageLoad: function(min_year, current_year, min_updated, max_updated, min_plot, max_plot) {    
        tm.init_map('results_map');

        var spp = jQuery.urlParam('species');
        if (spp) {
            jQuery('#heading_location').html(spp);
            }
        
        $.address.externalChange(tm.pageLoadSearch);
        $(".characteristics input").change(function(evt) { 
            tm.searchParams[this.id] = this.checked ? 'true' : undefined; 
        });
        $(".project_trees input").change(function(evt) { 
            tm.searchParams[this.id] = this.checked ? 'true' : undefined; 
        });
        $(".outstanding input").change(function(evt) { 
            tm.searchParams[this.id] = this.checked ? 'true' : undefined; 
        });
        $(".plot_type input").change(function(evt) { 
            tm.searchParams[this.id] = this.checked ? 'true' : undefined; 
        });
        
        $(".input-box input").change(function(evt) { 
            tm.searchParams[this.id] = this.value; 
        });
        var curmin = 0;
        var curmax = 50;
        $("#diameter_slider").slider({'range': true, max: 50, min: 0, values: [0, 50],
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
            }
        });
        $("#height_slider").slider({'range': true, max: 200, min: 0, values: [0, 200],
            slide: function() { 
                var min = $(this).slider('values', 0)
                var max = $(this).slider('values', 1)
                $('#min_height').html(min);
                $('#max_height').html(max);
            },    
            change: function() {
                var min = $(this).slider('values', 0)
                var max = $(this).slider('values', 1)
                $('#min_height').html(min);
                $('#max_height').html(max);
                tm.searchParams['height_range'] = min+'-'+max;
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
            }
        });    
        $("#updated_slider")[0].updateDisplay();
        
        if (!tm.isNumber(max_plot) && max_plot.indexOf('+') != -1) {
            max_p = parseInt(max_plot.split('+')[0]) + 1;
            m_text = max_p - 1 + "+"
            $("#plot_slider").slider({'range': true, max: max_p, min: min_plot, values: [min_plot, max_p],
                slide: function() { 
                    var min = $(this).slider('values', 0)
                    var max = $(this).slider('values', 1)
                    $('#min_plot').html(min);
                    if (max == max_p) {max = m_text;}
                    else {$('#max_plot').html(max);}
                },    
                change: function() {
                    var min = $(this).slider('values', 0)
                    var max = $(this).slider('values', 1)
                    $('#min_plot').html(min);
                    if (max == max_p) {$('#max_plot').html(m_text);tm.searchParams['plot_range'] = min+'-100';}
                    else {$('#max_plot').html(max);tm.searchParams['plot_range'] = min+'-'+max;}
                    
                }
            });
        }
        else {
            $("#plot_slider").slider({'range': true, max: max_plot, min: min_plot, values: [min_plot, max_plot],
                slide: function() { 
                    var min = $(this).slider('values', 0)
                    var max = $(this).slider('values', 1)
                    $('#min_plot').html(min);
                    $('#max_plot').html(max);
                },    
                change: function() {
                    var min = $(this).slider('values', 0)
                    var max = $(this).slider('values', 1)
                    $('#min_plot').html(min);
                    $('#max_plot').html(max);
                    tm.searchParams['plot_range'] = min+'-'+max;
                }
            });
        }
       
        
        $("#species_search_input").change(function(evt) {
            if (this.value === "") {
                $("#species_search_id").val("");
                $(this).val(tm.initial_species_string);
                delete tm.searchParams['species'];
            }    
        });

        $("#close-filters").click(function(evt) {
            $("#diameter_slider").slider('option', 'values', [0, 50]);
                $('#min_diam').html(0);
                $('#max_diam').html(50);
            $("#planted_slider").slider('option', 'values', [min_year, current_year]);
                $("#planted_slider")[0].updateDisplay();
            $("#updated_slider").slider('option', 'values', [min_updated, max_updated]);
                $("#updated_slider")[0].updateDisplay();
            $("#height_slider").slider('option', 'values', [0, 200]);
                $('#min_height').html(0);
                $('#max_height').html(200);
            if (!tm.isNumber(max_plot) && max_plot.indexOf('+') != -1) {
                max_p = parseInt(max_plot.split('+')[0]) + 1;
                m_text = max_p - 1 + "+"
                $("#plot_slider").slider('option', 'values', [min_plot, max_p]);
                $('#min_plot').html(min_plot);
                $('#max_plot').html(m_text);
            }
            else {
                $("#plot_slider").slider('option', 'values', [min_plot, max_plot]);
                $('#min_plot').html(min_plot);
                $('#max_plot').html(max_plot);
            }
            
            $("#steward").val('');
            $("#owner").val('');
            $("#updated_by").val('');
            $("#funding").val('');
            delete tm.searchParams['diameter_range'];
            delete tm.searchParams['planted_range'];
            delete tm.searchParams['updated_range'];
            delete tm.searchParams['height_range'];
            delete tm.searchParams['plot_range'];
            delete tm.searchParams['advanced'];
            delete tm.searchParams['steward'];
            delete tm.searchParams['owner'];
            delete tm.searchParams['updated_by'];
            delete tm.searchParams['funding'];

            var checks = $("#options_form input:checked");
            for(var i=0;i<checks.length;i++) {
                delete tm.searchParams[checks[i].id];
            }
            $("#options_form input:checked").attr('checked', false)  
            tm.updateSearch();
            tm.trackEvent('Search', 'Reset Advanced');
        });        
    },    
    
    setupSpeciesList: function() {
        var ul = $("<ul id='s_list' style='max-height:180px; overflow:auto;'></ul>");
        $("#searchSpeciesList").append(ul).hide();
        for(var i=0; i<tm.speciesData.length;i++) {
            if (tm.speciesData[i].count == 0) {continue;}
            var c = "ac_odd";
            if (i%2 == 0) {c = 'ac-even';}
            ul.append("<li id='" + tm.speciesData[i].id + "' class='" + c + "'>" + tm.speciesData[i].cname + " [" + tm.speciesData[i].sname + "]</li>")
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
        var states = {}
        for(var i=0; i<tm.locations.features.length;i++) {
            var feature = tm.locations.features[i];
            var st_co = feature.properties.state + "-" + feature.properties.county;
            if (!states[st_co])
            {
                states[st_co] = []
            }
            states[st_co].push(feature);
        }

        for(var state in states) {
            ul.append("<li class='header'>" + state + " County</li>")
            var entries = states[state];
            for(i=0;i<entries.length;i++) {
                var c = "ac_odd";
                if (i%2 == 0) {c = 'ac-even';}
                var name = entries[i].properties.name;
                ul.append("<li id='" + name + "' class='" + c + "'>" + name + "</li>")
            }
        }

        $("#n_list > li").hover(function(evt) {
            $(this).addClass("ac_over")
        }, function(evt) {
            $(this).removeClass("ac_over")
        }).click(function(evt) {
            if ($(this).hasClass("header")) {return;}
            $('#location_search_input').val(this.innerHTML);
            $("#searchNBList").toggle();
        });
        
        if ($("#s_nhood")) {
            select_nh = $("#s_nhood");
            for(var state in states) {
                select_nh.append("<option class='header' disabled='disabled'>" + state + " County</li>")
                var entries = states[state];
                for(i=0;i<entries.length;i++) {
                    var name = entries[i].properties.name;
                    select_nh.append("<option value='" + name + "' >" + name + "</li>")
                }
            }
        }    
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
    
    // Search page map init
    init_map : function(div_id){
        tm.init_base_map(div_id);

        tm.misc_markers = new OpenLayers.Layer.Markers('MarkerLayer2');
        tm.vector_layer = new OpenLayers.Layer.Vector('Vectors');

        tm.tree_layer = new OpenLayers.Layer.WMS(
                    "treemap_tree - Tiled", tm_urls['geo_url'],
                    {
                        transparent: 'true',
                        width: '256',
                        srs: 'EPSG:4326',
                        layers: tm_urls.geo_layer,
                        height: '256',
                        styles: tm_urls.geo_style,
                        format: 'image/png',
                        tiled: 'true',
                        tilesOrigin : tm.map.maxExtent.left + ',' + tm.map.maxExtent.bottom
                    },
                    {
                        buffer: 0,
                        displayOutsideMaxExtent: true,
                        visibility: false,
                        tileOptions: {maxGetUrlLength: 2048}
                    } 
                );

        
        tm.map.addLayers([tm.vector_layer, tm.tree_layer, tm.misc_markers]);
        tm.map.setCenter(
            new OpenLayers.LonLat(tm.map_center_lon, tm.map_center_lat).transform(new OpenLayers.Projection("EPSG:4326"), tm.map.getProjectionObject())
            , tm.start_zoom);
            
        //check to see if coming for a bookmarked tree
        var bookmark_id = jQuery.urlParam('tree');
        if (bookmark_id){
            jQuery.getJSON(tm_static + 'trees/' + bookmark_id  + '/',
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
            jQuery.getJSON(tm_static + 'trees/location/',
              {'lat': olLonlat.lat, 'lon' : olLonlat.lon, 'format' : 'json', 'species':spp},
            tm.display_tree_details);
        } 

        tm.geocoder = new google.maps.Geocoder();

        $(".mapToggle").click(function(evt) {
            if ($(".mapToggle").html() == 'View Satellite') {
                tm.map.setBaseLayer(tm.aerial);
                $(".mapToggle").html('View Streets')
            }
            else if ($(".mapToggle").html() == 'View Streets') {
                tm.map.setBaseLayer(tm.baseLayer);
                $(".mapToggle").html('View Satellite')
            }
            evt.preventDefault();
            evt.stopPropagation();
        });

    },
            
    //initializes the map where a user places a new tree
    init_add_map : function(){
        tm.init_base_map('add_tree_map');
        
        
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

        tm.map.addLayers([tm.add_vector_layer, tm.tree_layer]);
        tm.map.setBaseLayer(tm.aerial);
        tm.map.addControl(tm.drag_control);
        tm.map.setCenter(
            new OpenLayers.LonLat(tm.map_center_lon, tm.map_center_lat).transform(new OpenLayers.Projection("EPSG:4326"), tm.map.getProjectionObject())
            , tm.add_start_zoom);
            
        //jQuery("#mapHolder").hide();
        //jQuery("#calloutContainer").hide();
        
        tm.geocoder = new google.maps.Geocoder();
        
        jQuery('#id_edit_address_street').keydown(function(evt){
            if (evt.keyCode == 13) {                
                evt.preventDefault();
                evt.stopPropagation();
                if (jQuery('#id_edit_address_street').val() != "") {
                    jQuery('#update_map').click();
                }
            }
        });
        jQuery('#id_edit_address_city').keydown(function(evt){
            if (evt.keyCode == 13) {                
                evt.preventDefault();
                evt.stopPropagation();
                jQuery('#update_map').click();
            }
        });
        
        jQuery('#update_map').click(function(evt) {
            var address = jQuery('#id_edit_address_street').val();
            var city = jQuery('#id_edit_address_city').val();
            if (city == "Enter a City") {
               city = ""
            }
            if (!address || address == "Enter an Address or Intersection") {return;}
            tm.geocoder.geocode({
                address: address + " " + city,
                bounds: tm.google_bounds    
            }, function(results, status){
                if (status == google.maps.GeocoderStatus.OK) {
                    var olPoint = new OpenLayers.LonLat(results[0].geometry.location.lng(), results[0].geometry.location.lat());
                    var zoom = tm.add_zoom;
                    if (tm.map.getZoom() > tm.add_zoom) {zoom = tm.map.getZoom();}
                    tm.map.setCenter(new OpenLayers.LonLat(results[0].geometry.location.lng(), results[0].geometry.location.lat()).transform(new OpenLayers.Projection("EPSG:4326"), tm.map.getProjectionObject()), zoom);
                    
                    if (tm.add_vector_layer) {tm.add_vector_layer.destroyFeatures();}
                    if (tm.tree_layer) {tm.tree_layer.clearMarkers();}
                    
                    tm.load_nearby_trees(olPoint);
                    tm.add_new_tree_marker(olPoint, true);
                    
                    tm.drag_control.activate();
                    
                    jQuery('#id_lat').val(olPoint.lat);
                    jQuery('#id_lon').val(olPoint.lon);
                    jQuery('#id_geocode_address').val(results[0].formatted_address)
                    jQuery('#id_initial_map_location').val(olPoint.lat + "," + olPoint.lon);                   

                    jQuery('#update_map').html("Update Map");
                    jQuery("#mapHolder").show();
                    jQuery("#calloutContainer").show();
                    tm.trackEvent('Add', 'View Map');
                }
            });
            
        });
    },
        
    //initializes map on the profile page; shows just favorited trees
    init_favorite_map : function(user){
        tm.init_base_map('favorite_tree_map');
        
        tm.tree_layer = new OpenLayers.Layer.Markers('MarkerLayer')
        tm.map.addLayers([tm.tree_layer]);
        
        //load in favorite trees
        var url = ['trees/favorites/' + user + '/geojson/']
        $.getJSON(tm_static + url, function(json){
            $.each(json, function(i,f){
                var coords = f.coords;
                var ll = new OpenLayers.LonLat(coords[0], coords[1]);
                marker = tm.get_marker_light(ll, 17);
                marker.tid = f.id;
                tm.tree_layer.addMarker(marker);
            });
            var bounds = tm.tree_layer.getDataExtent();
            if (bounds) {
                tm.map.zoomToExtent(bounds, true);
            }
        });
    },
    //initializes map on the recently added page; shows just recently added trees
    init_new_map : function(user){
        tm.init_base_map('add_tree_map');
        
        tm.tree_layer = new OpenLayers.Layer.Markers('MarkerLayer')
        tm.map.addLayers([tm.tree_layer]);
        var url = []
        //load in new trees
        if (user) {url = ['trees/new/' + user + '/geojson/']}
        else {url = ['trees/new/geojson/']}
        $.getJSON(tm_static + url, function(json){
            $.each(json, function(i,f){
                var coords = f.coords;
                var ll = new OpenLayers.LonLat(coords[0], coords[1]);
                marker = tm.get_marker_light(ll, 17);
                marker.tid = f.id;
                tm.tree_layer.addMarker(marker);
            });
            var bounds = tm.tree_layer.getDataExtent();
            tm.map.zoomToExtent(bounds, true);
            tm.map.zoomOut();
        });
    },
        
    //initializes the map on the detail/edit page, 
    // where a user just views, or moves, an existing tree
    // also it loads the streetview below the map
    init_tree_map : function(editable){
        var controls = [new OpenLayers.Control.Attribution(),
               new OpenLayers.Control.Navigation(),
               new OpenLayers.Control.ArgParser(),
               new OpenLayers.Control.ZoomPanel()];
        tm.init_base_map('edit_tree_map', controls);
        
        tm.add_vector_layer = new OpenLayers.Layer.Vector('AddTreeVectors')
        tm.tree_layer = new OpenLayers.Layer.Markers('MarkerLayer')
        
        tm.drag_control = new OpenLayers.Control.DragFeature(tm.add_vector_layer);
        tm.drag_control.onComplete = function(feature, mousepix) {
            var mapCoord = tm.map.getLonLatFromViewPortPx(mousepix);
            mapCoord.transform(tm.map.getProjectionObject(), new OpenLayers.Projection("EPSG:4326"));
            jQuery('#id_geometry').val('POINT (' + mapCoord.lon + ' ' + mapCoord.lat + ')')
            tm.reverse_geocode(mapCoord);
            //tm.updateEditableLocation();
            
        }
        
        tm.map.addLayers([tm.tree_layer, tm.add_vector_layer]);
        tm.map.addControl(tm.drag_control);
        tm.map.setBaseLayer(tm.aerial);
        
        var currentPoint = new OpenLayers.LonLat(tm.current_tree_geometry[0], tm.current_tree_geometry[1]);        
        var olPoint = new OpenLayers.LonLat(tm.current_tree_geometry[0], tm.current_tree_geometry[1]).transform(new OpenLayers.Projection("EPSG:4326"), tm.map.getProjectionObject());
        
        tm.map.setCenter(olPoint, tm.edit_zoom);
        
        tm.geocoder = new google.maps.Geocoder();
        tm.add_new_tree_marker(currentPoint, false);
        //TODO: get this working
        tm.load_nearby_trees(currentPoint);
        
        if (tm.current_tree_geometry_pends && tm.current_tree_geometry_pends.length > 0) {
            tm.add_pending_markers(tm.current_tree_geometry_pends);
            jQuery('#edit_tree_map_legend').show();
        }
        //if (editable) { tm.drag_control.activate(); }
        
        tm.load_streetview(currentPoint, 'tree_streetview');
                
        tm.map.events.register('click', tm.map, function(e){
            var mapCoord = tm.map.getLonLatFromViewPortPx(e.xy);
            mapCoord.transform(tm.map.getProjectionObject(), new OpenLayers.Projection("EPSG:4326"));
            jQuery.getJSON(tm_static + 'trees/location/',
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
        
    load_nearby_trees : function(ll){
        //load in nearby trees as well
        var url = ['trees/location/?lat=',ll.lat,'&lon=',ll.lon,'&format=json&max_trees=70'].join('');
        $.getJSON(tm_static + url, function(geojson){
            $.each(geojson.features, function(i,f){
                coords = f.geometry.coordinates;
                var ll = new OpenLayers.LonLat(coords[0], coords[1]).transform(new OpenLayers.Projection("EPSG:4326"), tm.map.getProjectionObject());
                if (f.properties.id == tm.currentTreeId) {return;}
                var icon = tm.get_icon(tm_icons.small_trees, 19);
                var marker = new OpenLayers.Marker(ll, icon);
                marker.tid = f.properties.id;
                
                tm.tree_layer.addMarker(marker);
                                
            });
        });
    },
    
    get_tree_marker: function(lat, lng) {
        var ll = new OpenLayers.LonLat(lng, lat).transform(new OpenLayers.Projection("EPSG:4326"), tm.map.getProjectionObject());
        var marker = new OpenLayers.Marker(ll, tm.get_icon(tm_icons.focus_tree, 19));

        return marker
        },
    add_pending_markers: function(pends) {
        for (var i=0; i<pends.length; i++) {
            var ll = new OpenLayers.LonLat(pends[i].x, pends[i].y).transform(new OpenLayers.Projection("EPSG:4326"), tm.map.getProjectionObject());
            var icon = tm.get_icon(tm_icons.pending_tree, 19);
            var marker = new OpenLayers.Marker(ll, icon);
            
            tm.tree_layer.addMarker(marker);

            var popupPixel = tm.map.getViewPortPxFromLonLat(ll);
            popupPixel.y += marker.icon.offset.y - 15;
            tm.smallPopup = new OpenLayers.Popup("popup_id",
                       tm.map.getLonLatFromPixel(popupPixel),
                       null,
                       "<span class='pendPopup'>" + pends[i].id + "</span>",
                       false);
            tm.smallPopup.minSize = new OpenLayers.Size(25,25);
            tm.smallPopup.maxSize = new OpenLayers.Size(150,25);
            tm.map.addPopup(tm.smallPopup);
            tm.smallPopup.updateSize();
            tm.smallPopup.setBackgroundColor('transparent');
        }
    },
    add_new_tree_marker : function(ll, do_reverse_geocode){
        if (tm.add_vector_layer) {
            tm.add_vector_layer.destroyFeatures();
        }
        var tree_marker = new OpenLayers.Geometry.Point(ll.lon, ll.lat).transform(new OpenLayers.Projection("EPSG:4326"), tm.map.getProjectionObject());
        var tree_vector = new OpenLayers.Feature.Vector(tree_marker)
        
        tm.add_vector_layer.addFeatures([tree_vector])
        if (do_reverse_geocode) {
            tm.reverse_geocode(ll);
        }
        
        },
        
    add_location_marker: function (ll) {
        var icon = tm.get_icon(tm_icons.marker,0);
        tm.location_marker = new OpenLayers.Marker(ll, icon);
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
    },
    

    geocode : function(address, display_local_summary, callback){
        if (!address){
            address = jQuery('#searchInput').text();
        }

        tm.geocode_address = address;

        tm.geocoder.geocode({
            address: tm.geocode_address,
            bounds: tm.google_bounds  
        }, function(results, status){
            if (status == google.maps.GeocoderStatus.OK) {
                var olPoint = new OpenLayers.LonLat(results[0].geometry.location.lng(), results[0].geometry.location.lat());
                var llpoint = new OpenLayers.LonLat(results[0].geometry.location.lng(), results[0].geometry.location.lat()).transform(new OpenLayers.Projection("EPSG:4326"), tm.map.getProjectionObject());
                tm.map.setCenter(llpoint, 15);

                tm.add_location_marker(llpoint);

                if (callback) {
                    callback(olPoint);
                }

            } else {
                alert("Geocode was not successful for the following reason: " + status);
            }

        });
                 
    },
        
        
    //pass in a GLatLng and get back closest address
    reverse_geocode : function(ll){
        latlng = new google.maps.LatLng(ll.lat, ll.lon)
        tm.geocoder.geocode({
                latLng: latlng
            }, function(results, status){
            if (status == google.maps.GeocoderStatus.OK) {
                var addy = results[0].address_components;
                
                if ($("#geocode_address")) {
                    $("#geocode_address").html("<b>Address Found: </b><br>" + results[0].formatted_address);
                }
                if ($("#id_geocode_address")) {
                    $('#id_geocode_address').val(results[0].formatted_address);
                }
                if ($('#nearby_trees')) {
                    $('#nearby_trees').html("Loading...")
                    var url = ['trees/location/?lat=',ll.lat,'&lon=',ll.lon,'&format=json&max_trees=10&distance=.0001'].join('');
                    $.getJSON(tm_static + url, function(geojson){
                        if (geojson.features.length == 0) {
                            $('#nearby_trees').html("No other trees nearby.")
                        }
                        else {
                            $('#nearby_trees').html("Found " + geojson.features.length + " tree(s) that may be too close to the tree you want to add. Please double-check that you are not adding a tree that is already on our map:")
                            $.each(geojson.features, function(i,f){
                                var tree = $('#nearby_trees');
                                if (f.properties.common_name){
                                    tree.append("<div class='nearby_tree_info'><a href='/trees/" + f.properties.id + "' target='_blank'>" + f.properties.common_name + " (#" + f.properties.id + ")</a><br><span class='nearby_tree_scientific'>" + f.properties.scientific_name + "</span></div>");
                                }
                                else {
                                    tree.append("<div class='nearby_tree_info'><a href='/trees/" + f.properties.id + "' target='_blank'>No species information (#" + f.properties.id + ")</a></div>")
                                }
                                if (f.properties.current_dbh){
                                    tree.append("<div class='nearby_tree_diameter'>Diameter: " + f.properties.current_dbh + " inches</div>");
                                }
                                
                            });
                        }
                    });
                }
                
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
                

            } else {
                if ($("#geocode_address")) {
                    $("#geocode_address").html("<b>Address Found: </b><br>" + results[0].formatted_address);
                    var url = ['trees/location/?lat=',ll.lat,'&lon=',ll.lon,'&format=json&distance=20'].join('');
                    $.getJSON(tm_static + url, function(geojson){
                        $.each(geojson.features, function(i,f){
                            alert("trees");
                            //TODO: add each tree to list
                        });
                    });
                }
                else {
                    alert("Reverse Geocode was not successful.");
                }
            }        
        });        
    },    
        
    /*
    load up streetview pointing at specified GLatLng, into specified div
    */
    load_streetview : function(ll, div){
          div = document.getElementById(div);
          panoPosition = new google.maps.LatLng(ll.lat, ll.lon);
          new google.maps.StreetViewService().getPanoramaByLocation(panoPosition, 50, function(data, status) {
              if (status == google.maps.StreetViewStatus.OK) {
                  tm.pano = new google.maps.StreetViewPanorama(div, {position:panoPosition, addressControl:tm.panoAddressControl});
                  
              }
              else {
                  $(div).hide()
              }
          });       
          
    },
        
                
    highlight_geography : function(geometry, geog_type){        
        if (tm.vector_layer){
            tm.vector_layer.destroyFeatures();
        }
        if (geometry.coordinates.length == 1) {            
            var feature = tm.getFeatureFromCoords(geometry.coordinates[0]);
            tm.vector_layer.addFeatures(feature);
        }
        for (var i=0; i<geometry.coordinates.length;i++) {
            var feature = tm.getFeatureFromCoords(geometry.coordinates[i][0])
            tm.vector_layer.addFeatures(feature);
        }
    },

    getFeatureFromCoords : function (coords) {
        var verts = [];
        jQuery.each(coords, function(i, c){ //no multipoly support
            verts.push(new OpenLayers.Geometry.Point(c[0],c[1]).transform(new OpenLayers.Projection("EPSG:4326"), tm.map.getProjectionObject()));
            });
        var poly = new OpenLayers.Geometry.LineString(verts);
        var feature = new OpenLayers.Feature.Vector(poly, null, {
            strokeColor: "#289255",
            strokeWidth: 4,
            strokeOpacity: 0.7
        });
        return feature;
    },
        
    display_tree_details : function(json){
        if (json) {
            if (json.features.length > 0) {
                var tree = json.features[0];
                var p = tree.properties;
                var coords = tree.geometry.coordinates;
                
                //remove old markers
                if (tm.tree_detail_marker) {tm.misc_markers.removeMarker(tm.tree_detail_marker);}
                
                var AutoSizeFramedCloud = OpenLayers.Class(OpenLayers.Popup.FramedCloud, {
                    'autoSize': true
                });
                                
                //Add tree marker
                tm.tree_detail_marker = tm.get_tree_marker(coords[1], coords[0]);
                tm.tree_detail_marker.tree_id = p.id;
                tm.tree_detail_marker.nhbd_id = p.neighborhood_id;
                tm.tree_detail_marker.district_id = p.district_id;
                tm.misc_markers.addMarker(tm.tree_detail_marker);
                
                
                var ll = tm.tree_detail_marker.lonlat;
                
                popup = new OpenLayers.Popup.FramedCloud("Tree Info",
                   ll,
                   null,
                   '<div id="max_tree_infowindow">Loading ...</div>',
                   tm.tree_detail_marker.icon,
                   true);
                popup.minSize = tm.popup_minSize;
                popup.maxSize = tm.popup_maxSize;
                popup.autoSize = true;
                popup.panMapIfOutOfView = true;
                tm.map.addPopup(popup, true);
                
                tm.trackEvent('Search', 'Map Detail', 'Tree', p.id);
                
                if (!p.address_street) {
                    latlng = new google.maps.LatLng(coords[1], coords[0])
                    tm.geocoder.geocode({
                        latLng: latlng
                    }, function(results, status){
                        if (status == google.maps.GeocoderStatus.OK) {
                            //TODO: add jsonString here for post
                            var data = {
                                'tree_id': p.id,
                                'address': results[0].formatted_address.split(", ")[0],
                                'city': results[0].formatted_address.split(", ")[1]
                            };
                            var jsonString = JSON.stringify(data);

                            $.ajax({
                                url: tm_static + 'trees/location/update/',
                                type: 'POST',
                                data: jsonString,
                                complete: function(xhr, textStatus) {
                                    jQuery('#max_tree_infowindow').load(tm_static + 'trees/' + tm.tree_detail_marker.tree_id + '/?format=base_infowindow');
                                }
                            });
                        } else {
                            jQuery('#max_tree_infowindow').load(tm_static + 'trees/' + tm.tree_detail_marker.tree_id + '/?format=base_infowindow');
                        }
                    });
                }
                else {
                    jQuery('#max_tree_infowindow').load(tm_static + 'trees/' + tm.tree_detail_marker.tree_id + '/?format=base_infowindow');
                }
            }
        }
    },
        
 
    display_benefits : function(benefits){
        jQuery('#results_wrapper').show();
        jQuery("#no_results").hide();
        jQuery.each(benefits, function(k,v){
            jQuery('#benefits_' + k).html(tm.addCommas(parseInt(v)));
        });
        if (benefits['total'] == 0.0)
        {
            jQuery("#no_results").show();
            //alert("here");
        }   
    },
        
    display_summaries : function(summaries){
        //var callout = ['You selected ', summaries.total_trees, ' trees'].join('');
        //jQuery('#callout').html(callout);
        jQuery(".tree_count").html(tm.addCommas(parseInt(summaries.total_trees)));
        if (summaries.total_trees == '0')
        {
            // todo.. http://sftrees.securemaps.com/ticket/148
            jQuery(".moretrees").html("");
            jQuery(".notrees").html("No results? Try changing the filters above.");
            //jQuery(".tree_count").css('font-size',20);
        }  else {
            jQuery(".moretrees").html("");
            jQuery(".notrees").html("");
        }
        
        jQuery.each(summaries, function(k,v){
            var span = jQuery('#' + k);
            if (span.length > 0){
                span.html(tm.addCommas(parseInt(v)));
            }
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
        if (tm.vector_layer) {tm.vector_layer.destroyFeatures();}
        //if (tm.misc_markers) {tm.misc_markers.clearMarkers();}
        jQuery('#displayResults').hide();
        //if (tm.current_selected_tile_overlay)
        //{
        //    tm.map.removeOverlay(tm.current_selected_tile_overlay);
        //}
        if (results) {
            tm.display_summaries(results.summaries);
            
            if (results.initial_tree_count != results.full_tree_count && results.initial_tree_count != 0) {
                if (results.featureids) {
                    var cql = results.featureids;
                    delete tm.tree_layer.params.CQL_FILTER;
                    tm.tree_layer.mergeNewParams({'FEATUREID':cql});
                    tm.tree_layer.setVisibility(true);     
                }
                else if (results.tile_query) {
                    var cql = results.tile_query;
                    delete tm.tree_layer.params.FEATUREID;
                    tm.tree_layer.mergeNewParams({'CQL_FILTER':cql});
                    tm.tree_layer.setVisibility(true);     
                }    
                else {
                    tm.tree_layer.setVisibility(false);
                }                
            }            
            else {
                tm.tree_layer.setVisibility(false);
            }

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
                $('#summary_subset_val').html('the region');
            }
        }
        
    },

    // unused?
    select_species : function(species){
        tm.mgr.clearMarkers();
        jQuery.getJSON(tm_static + 'search/' + species + '/?simple=true', 
            tm.display_search_results);
    },

     
    enableEditTreeLocation : function(){
        //tm.tree_marker.enableDragging();
        tm.drag_control.activate();
        //TODO:  bounce marker a bit, or change its icon or something
        tm.trackEvent('Edit', 'Location', 'Start');
        var save_html = '<a href="javascript:tm.saveTreeLocation()" class="buttonSmall"><img src="' + tm_static + 'static/images/loading-indicator-trans.gif" width="12" /> Stop Editing and Save</a>'

        $('#edit_tree_location').html(save_html);
        return false;
        },
        
    saveTreeLocation : function(){
        //tm.tree_marker.disableDragging();     
        tm.drag_control.activate();
        tm.trackEvent('Edit', 'Location', 'Save');
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
    
    setupEdit: function(field, model, id, options) {
        var editableOptions = {
            submit: 'Save',
            cancel: 'Cancel',
            cssclass:  'activeEdit',
            indicator: '<img src="' + tm_static + 'static/images/loading-indicator.gif" alt="" />',
            width: '80%',
            objectId: id,
            model: model,
            fieldName: field
        };
        if (options) {
            for (var key in options) {
                if (key == "loadurl") {
                    editableOptions[key] =  options[key];
                } else {
                    editableOptions[key] = options[key];
                }
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
        // TODO - I think if '' then we should replace
        // with original value and if 'null' then
        // we should save None in database if its
        // a field that accepts nulls
        //if (value === '') {
        //if (value == '' || value == 'null') {
           // do nothing
           //this.innerHTML = 'Click to edit';
           //return 'Click to edit';
        //}
        //else {
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
            
                
            if (settings.fieldName == 'species_id' && value == 0) {
                $(this).addClass("error");
                return "Please select a species from the provided list.";
            }
            //do some validation for height and canopy height
            if (settings.fieldName == 'height' || settings.fieldName == 'canopy_height') {
                if (value > 300) {
                    $(this).addClass("error");
                    return "Height is too large.";
                }
                else {
                    $(this).removeClass("error");
                }
            }
            
            if (jQuery.inArray(settings.model, ["TreeAlert","TreeAction","TreeFlags"]) >=0) {
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
                url: tm_static + 'update/',
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
                        if (settings.fieldName == "plot_width" || settings.fieldName == "plot_length") {
                            if (value == 99.0) {value = "15+"}
                        }
                        settings.obj.innerHTML = value 
                        tm.trackEvent("Edit", settings.fieldName)
                    }
                }});
            return "Saving... " + '<img src="' + tm_static + 'static/images/loading-indicator.gif" />';
        //} 
    },       
    updateEditableLocation: function() {
        
        var wkt = jQuery('#id_geometry').val();
        var geoaddy = jQuery("#id_geocode_address").val();
        var data = {
            'model': 'Tree',
            'id': tm.currentTreeId,
            'update': {
                geometry: wkt,
                geocoded_address: geoaddy
            }
        };
        var jsonString = JSON.stringify(data);
        $.ajax({
            url: tm_static + 'update/',
            type: 'POST',
            data: jsonString,
            complete: function(xhr, textStatus) {
                var response =  JSON.parse(xhr.responseText);
            }});
    },
    setupAutoComplete: function(field) {
        return field.autocomplete(tm.speciesData, {
            matchContains: true,
            minChars: 1,
            max:50,

            formatItem: function(row, i, max) {
                var text = row.cname;
                text += "  [" + row.sname;
                if (row.cultivar) {
                    text += " '" + row.cultivar + "'";
                }
                text += "]";
                return text;
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
                $("<input type='submit' value='Submit' class='button' />").click(tm.handleNewAction),
                $("<input type='submit' value='Cancel' class='button' />").click(tm.cancelNew)
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
                    $("<input type='submit' value='Submit' class='button' />").click(tm.handleNewLocal),
                    $("<input type='submit' value='Cancel' class='button' />").click(tm.cancelNew)
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
            $("<td style='white-space:nowrap;' />").append(
                $("<input type='submit' value='Submit' class='button' />").click(tm.handleNewHazard),
                $("<input type='submit' value='Cancel' class='button' />").click(tm.cancelNew)
            )
        );
        $("#hazardTable").append(tr);
    },
    cancelNew: function(evt) {
        $(this.parentNode.parentNode).remove();
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
        '4': 'Just One Tree'
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
                if (key == "height_range") {
                    var hvals = $.address.parameter(key).split("-");
                    $("#height_slider").slider('values', 0, hvals[0]);
                    $("#height_slider").slider('values', 1, hvals[1]);
                }   
                if (key == "plot_range") {
                    var plvals = $.address.parameter(key).split("-");
                    $("#plot_slider").slider('values', 0, plvals[0]);
                    $("#plot_slider").slider('values', 1, plvals[1]);
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
            if (!coords) {return false;}
            if (coords.join) {
                q.SET('location', coords.join(','));
            }
            else {
                q.SET('location', coords);
            }
            qstr = decodeURIComponent(q.toString()).replace(/\+/g, "%20")
        }
        $("#kml_link").attr('href', tm_static + "search/kml/"+qstr);
        $("#csv_link").attr('href', tm_static + "search/csv/"+qstr);
        $("#shp_link").attr('href', tm_static + "search/shp/"+qstr);
        return qstr;
    },
    

    updateSearch: function() {
        
        if (tm.loadingSearch) { return; }
        var qs = tm.serializeSearchParams();
        if (qs === false) { return; }
        tm.trackPageview('/search/' + qs);
        jQuery('#displayResults').show();
        //TODO: send a geoserver CQL request also
        $.ajax({
            url: tm_static + 'search/'+qs,
            dataType: 'json',
            success: function(results) {
                tm.display_search_results(results)
            },
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
            $.getJSON(tm_static + url, function(data, textStatus) {
                $('#favorite_' + pk).removeClass('fave').addClass('unfave').text('Remove as favorite');
            });
            tm.trackEvent('Favorite', 'Add Favorite', 'Tree', pk);
            return false;
        });
        $('a.favorite.unfave').live('click', function(e) {
            var pk = $(this).attr('id').replace('favorite_', '');
            var url = base_delete + pk + '/';
            $.getJSON(tm_static + url, function(data, textStatus) {
                $('#favorite_' + pk).removeClass('unfave').addClass('fave').text('Add as favorite');
            });
            tm.trackEvent('Favorite', 'Remove Favorite', 'Tree', pk);
            return false;
        });
    },
    
    handleSearchLocation: function(search) {
        if (tm.misc_markers) {tm.misc_markers.clearMarkers();}
        if (tm.vector_layer) {tm.vector_layer.destroyFeatures();}
        //possible zipcode 
        tm.geocode_address = search;
        if (tm.isNumber(search)) {
            jQuery.getJSON(tm_static + 'zipcodes/', {format:'json', name: tm.geocode_address}, function(zips){
                if (tm.location_marker) {tm.misc_markers.removeMarker(tm.location_marker)} 
                            
                if (zips.features.length > 0) {
                    var olPoint = OpenLayers.Bounds.fromArray(zips.bbox).getCenterLonLat();
                    var bbox = OpenLayers.Bounds.fromArray(zips.bbox).transform(new OpenLayers.Projection("EPSG:4326"), tm.map.getProjectionObject());
                    tm.map.zoomToExtent(bbox, true);

                   // if (zips.features[0].properties.name == 'Philadelphia'){                    
                   //     delete tm.searchParams.location;
                   //     delete tm.searchParams.geoName;
                    //}else {  
                        tm.add_location_marker(bbox.getCenterLonLat());
                        tm.geocoded_locations[tm.geocode_address] = tm.geocode_address;
                        tm.searchParams['location'] = tm.geocode_address;  
                        tm.searchParams['geoName'] = zips.features[0].properties.name;
                    //}
                    tm.updateSearch();
                }
                
            });
        }
        else
        {
            jQuery.getJSON(tm_static + 'neighborhoods/', {format:'json', name: tm.geocode_address}, function(nbhoods){
                if (tm.location_marker) {tm.misc_markers.removeMarker(tm.location_marker)} 

                if (nbhoods.features.length > 0) {
                    var olPoint = OpenLayers.Bounds.fromArray(nbhoods.bbox).getCenterLonLat();
                    var bbox = OpenLayers.Bounds.fromArray(nbhoods.bbox).transform(new OpenLayers.Projection("EPSG:4326"), tm.map.getProjectionObject());
                    tm.map.zoomToExtent(bbox, true);

                    //if (nbhoods.features[0].properties.name == 'Philadelphia'){                    
                    //    delete tm.searchParams.location; 
                    //    delete tm.searchParams.geoName;
                    //} else {  
                        tm.add_location_marker(bbox.getCenterLonLat());
                        tm.geocoded_locations[tm.geocode_address] = [olPoint.lon, olPoint.lat];
                        tm.searchParams['location'] = tm.geocode_address;
                        tm.searchParams['geoName'] = nbhoods.features[0].properties.name;
                    //}
                    tm.updateSearch();
                } else {                 
                    delete tm.searchParams.geoName;        
                    tm.geocode(search, true, function(point) {
                        if (point) {
                            tm.geocoded_locations[search] = [point.lon, point.lat];
                            tm.searchParams['location'] = search;       
                        } else {
                            delete tm.searchParams.location;
                        }
                        tm.updateSearch();
                    });
                }
            });
        }
    },
    editDiameter: function(field, diams) {
        tm.editingDiameter = true;
        if (diams == "None") {diams=[];}        
        var diams = tm.currentTreeDiams || diams;
        var html = '';
        tm.currentDiameter = $(field).html();
	if ($.isArray(diams)){
            for (var i = 0; i < Math.max(diams.length, 1); i++) {
                var val = '';
                if (diams[i]) { val = parseFloat(diams[i].toFixed(3)); }
                html += "<input type='text' size='7' id='dbh"+i+"' name='dbh"+i+"' value='"+val+"' />";
                if (i == 0) {
                    html += "<br /><input type='radio' id='diam' checked name='circum' /><label for='diam'><small>Diameter</small></label><input type='radio' id='circum' name='circum' /><label for='circum'><small>Circumference</small></label>"
                }
                html += "<br />";
            }
	} else {
	    html += "<input type='text' size='7' id='dbh0' name='dbh0' value='"+ parseFloat(diams).toFixed(3) + "' />";
	    html += "<br /><input type='radio' id='diam' checked name='circum' /><label for='diam'><small>Diameter</small></label><input type='radio' id='circum' name='circum' /><label for='circum'><small>Circumference</small></label>"
	    html += "<br />";
        }

        if ($.isArray(diams)) {
            if (diams.length == 0) {
                tm.currentTreeDiams = [0];
            } else {
                tm.currentTreeDiams = diams;
            }
        } else {
            tm.currentTreeDiams = [diams];
        }

        html += "<span id='add_more_dbh'><a href='#' onclick='tm.addAnotherDiameter(); return false'>Add another trunk?</a></span> <br />";
        html += "<span class='activeEdit'>";
        html += "<button type='submit' onclick='tm.saveDiameters(); return false;'>Save</button>";
        html += "<button type='submit' onclick='tm.cancelDiameters(); return false;'>Cancel</button>";
        html += "</span>";
        $(field).html(html);
    },
    cancelDiameters: function() {
        if (isNaN(parseFloat(tm.currentDiameter))) {
            $("#edit_dbh").html("Click icon to edit");
        } else {
            $("#edit_dbh").html(parseFloat(tm.currentDiameter).toFixed(1));
        }            
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
        
        if (total > 100) {
            $("#edit_dbh").append("<br/><span class='error'>Total diameter too large.</span>")
            tm.editingDiameter = false;
            return;
        }
        
        tm.currentTreeDiams = vals;
        var editableOptions = {
            submit: 'Save',
            cancel: 'Cancel',
            cssclass:  'activeEdit',
            indicator: '<img src="' + tm_static + 'static/images/loading-indicator.gif" alt="" />',
            width: '80%',
            model: 'Tree',
            fieldName:  'dbh',
            objectId: tm.currentTreeId

        };
        tm.updateEditableServerCall(total, editableOptions);
        $("#edit_dbh").html(total.toFixed(1));
        tm.editingDiameter = false;
        
    },
    approvePend: function(pend_id) {
        $.ajax({
            url: tm_static + 'trees/pending/' + pend_id + '/approve/',
            dataType: 'json',
            type: 'POST',
            success: function(response) {
                tm.trackEvent('Pend', 'Approve', 'id', pend_id);
                location.reload();
            },
            error: function(err) {
                alert("Error: " + err.status + "\nQuery: " + pend_id);
            }
        });
    },
    rejectPend: function(pend_id) {
        $.ajax({
            url: tm_static + 'trees/pending/' + pend_id + '/reject/',
            dataType: 'json',
            type: 'POST',
            success: function(response) {
                tm.trackEvent('Pend', 'Reject', 'id', pend_id);
                location.reload();
            },
            error: function(err) {
                alert("Error: " + err.status + "\nQuery: " + pend_id);
            }
        });
    },
    deleteTree: function(tree_id) {
        if (window.confirm("Are you sure you want to delete this tree permanently from the system?"))
        {
            $.ajax({
                url: tm_static + 'trees/' + tree_id + '/delete/',
                dataType: 'json',
                type: 'POST',
                success: function(response) {
                    tm.trackEvent('Edit', 'Delete');
                    window.location = tm_static + "map/";
                },
                error: function(err) {
                alert("Error: " + err.status + "\nQuery: " + tree_id);
                }
            });
        }
    },

    deletePhoto: function(tree_id, photo_id) {
        if (window.confirm("Are you sure you want to delete this photo permanently from the system?"))
        {
            $.ajax({
                url: tm_static + 'trees/' + tree_id + '/deletephoto/' +  photo_id,
                dataType: 'json',
                type: 'POST',
                success: function(response) {
                    window.location.reload(true);
                },
                error: function(err) {
                alert("Error: " + err.status + "\nQuery: " + user_id + " " + rep_total);
                }
            });
        }
    },
    
    deleteUserPhoto: function(username) {
        if (window.confirm("Are you sure you want to delete this photo permanently from the system?"))
        {
            $.ajax({
                url: tm_static + 'profiles/' + username + '/deletephoto/',
                dataType: 'json',
                type: 'POST',
                success: function(response) {
                    window.location.reload(true);
                },
                error: function(err) {
                alert("Error: " + err.status + "\nQuery: " + user_id + " " + rep_total);
                }
            });
        }
    },
    
     updateSpeciesFromKey: function(tree_code, tree_cultivar)  {
       alert(tree_code);
     },
    
    updateReputation: function(change_type, change_id, rep_dir) {
        $.ajax({
        url: tm_static + 'verify/' + change_type + '/' + change_id + '/' + rep_dir,
        dataType: 'json',
        success: function(response) {
            $("#" + response.change_type + "_" + response.change_id).fadeOut();
            tm.trackEvent("Reputation", rep_dir)
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
        url: tm_static + 'users/update/',
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
            url: tm_static + 'users/update/',
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
    
    banUser: function(user_id) {
        var data = {
            'user_id': user_id
        };
        var jsonString = JSON.stringify(data);

        $.ajax({
            url: tm_static + 'users/ban/',
            dataType: 'json',
            data: jsonString,
            type: 'POST',
            success: function(response) {
                $('#' + response.user_id).children("#rep").children("#ban").toggle();
                $('#' + response.user_id).children("#rep").children("#activate").toggle();
                $('#' + response.user_id).children("#active").html('Inactive');
            },
            error: function(err) {
            alert("Error: " + err.status + "\nQuery: " + user_id);
            }
        });
    },
    activateUser: function(user_id) {
        var data = {
            'user_id': user_id
        };
        var jsonString = JSON.stringify(data);

        $.ajax({
            url: tm_static + 'users/activate/',
            dataType: 'json',
            data: jsonString,
            type: 'POST',
            success: function(response) {
                $('#' + response.user_id).children("#rep").children("#ban").toggle();
                $('#' + response.user_id).children("#rep").children("#activate").toggle();
                $('#' + response.user_id).children("#active").html('Active');
            },
            error: function(err) {
            alert("Error: " + err.status + "\nQuery: " + user_id);
            }
        });
    },

    updatePend: function(pend_id, pend_dir) {
        $.ajax({
        url: tm_static + 'trees/pending/' + pend_id + '/' + pend_dir,
        dataType: 'json',
        success: function(response) {
            $("#" + response.pend_id).hide();
            tm.trackEvent("Pending", pend_dir)
        },
        error: function(err) {
        alert("Error: " + err.status + "\nQuery: " + pend_id + " " + pend_dir);
        }
        });
    },

    validate_watch: function(watch_id){
        var data = {
            'watch_id': watch_id
        };
        var jsonString = JSON.stringify(data);      
        $.ajax({
            url: tm_static + 'watch/validate/',
            dataType: 'json',
            data: jsonString,
            type: 'POST',
            success: function(response) {
                $("#" + watch_id).fadeOut();
            },
            error: function(err) {
                alert("Error: " + err.status + "\nQuery: " + watch_id );
            }
        });
    },
    
    hideComment: function(flag_id) {
        var data = {
            'flag_id': flag_id
        };
        var jsonString = JSON.stringify(data);      
        $.ajax({
            url: tm_static + 'comments/hide/',
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
            url: tm_static + 'comments/unflag/',
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
    isNumber: function (o) {
      return ! isNaN (o-0);
    }
};  
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
$.editable.addInputType('date', {
    element : function(settings, original) {       
        var monthselect = $('<select id="month_">');
        var dayselect  = $('<select id="day_">');
        var yearselect  = $('<select id="year_">');
    
        /* Month loop */
        for (var month=1; month <= 12; month++) {
            if (month < 10) {
                month = '0' + month;
            }
            var option = $('<option>').val(month).append(month);
            monthselect.append(option);
        }
        $(this).append(monthselect);

        /* Day loop */
        for (var day=1; day <= 31; day++) {
            if (day < 10) {
                day = '0' + day;
            }
            var option = $('<option>').val(day).append(day);
            dayselect.append(option);
        }
        $(this).append(dayselect);
            
        /* Year loop */
        thisyear = new Date().getFullYear()
        for (var year=thisyear; year >= 1800; year--) {
            var option = $('<option>').val(year).append(year);
            yearselect.append(option);
        }
        $(this).append(yearselect);
        
        $(this).append("<br><span>MM</span><span style='padding-left:30px;'>DD</span><span style='padding-left:36px;'>YYYY</span><br><div style='color:red;' id='dateplanted_error'/>")
        
        /* Hidden input to store value which is submitted to server. */
        var hidden = $('<input type="hidden">');
        $(this).append(hidden);
        return(hidden);
    },
    submit: function (settings, original) {
        var vdate = new Date($("#year_").val(), $("#month_").val()-1, $('#day_').val());
        if (vdate.getTime() > new Date().getTime()) {
            $("#dateplanted_error").html("Enter a past date")
            return false;
        }
        
        var value = $("#year_").val() + "-" + $("#month_").val() + "-" + $('#day_').val();
        $("input", this).val(value);
    },
    content : function(string, settings, original) {
        var pieces = string.split('-');
        var year = pieces[0];
        var month  = pieces[1];
        var day  = pieces[2];
        

        $("#year_", this).children().each(function() {
            if (year == $(this).val()) {
                $(this).attr('selected', 'selected');
            }
        });
        $("#month_", this).children().each(function() {
            if (month == $(this).val()) {
                $(this).attr('selected', 'selected');
            }
        });
        $("#day_", this).children().each(function() {
            if (day == $(this).val()) {
                $(this).attr('selected', 'selected');
            }
        });
    }
});
$.editable.addInputType('feetinches', {
    element : function(settings, original) {       
        var footselect = $('<select id="feet_">');
        var inchselect  = $('<select id="inches_">');
    
        /* Month loop */
        for (var foot=1; foot <= 15; foot++) {
            var option = $('<option>').val(foot).append(foot);
            footselect.append(option);
        }
        var option = $('<option>').val(99).append('15+');
        footselect.append(option);
        $(this).append(footselect);

        /* Day loop */
        for (var inch=0; inch <= 11; inch++) {
            var option = $('<option>').val(inch).append(inch);
            inchselect.append(option);
        }
        $(this).append(inchselect);
            
        
        $(this).append("<br><span>Feet</span><span style='padding-left:30px;'>Inches</span><br><div style='color:red;' id='dateplanted_error'/>")
        
        /* Hidden input to store value which is submitted to server. */
        var hidden = $('<input type="hidden">');
        $(this).append(hidden);
        return(hidden);
    },
    submit: function (settings, original) {
        var vfeet = parseFloat($("#feet_").val());
        var vinch = parseFloat($("#inches_").val());
        var value = vfeet + (vinch / 12)
        if (vfeet == 99) {
            $("input", this).val(vfeet);
        }
        else {
            $("input", this).val(Math.round(value*100)/100);
        }
    },
    content : function(string, settings, original) {
        var pieces = parseFloat(string);
        var ft = Math.floor(pieces);
        var inch = Math.round((pieces - ft) * 12);
        

        $("#feet_", this).children().each(function() {
            if (ft == $(this).val()) {
                $(this).attr('selected', 'selected');
            }
        });
        $("#inches_", this).children().each(function() {
            if (inch == $(this).val()) {
                $(this).attr('selected', 'selected');
            }
        });
    }
});
