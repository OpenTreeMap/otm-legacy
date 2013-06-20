// Create new openlayer click control, because just registering a click event
// with the map doesn't work on mobile devices.
if (typeof OpenLayers != "undefined") {
    OpenLayers.Control.Click = OpenLayers.Class(OpenLayers.Control, {
        defaultHandlerOptions: {
            'single': true,
            'double': false,
            'pixelTolerance': 0,
            'stopSingle': false,
            'stopDouble': false
        },

        initialize: function(options) {
            this.handlerOptions = OpenLayers.Util.extend(
                {}, this.defaultHandlerOptions
            );
            OpenLayers.Control.prototype.initialize.apply(
                this, arguments
            );
            this.handler = new OpenLayers.Handler.Click(
                this, {
                    'click': this.onClick
                }, this.handlerOptions
            );
        },

        onClick: function(e) {
            var mapCoord = tm.map.getLonLatFromViewPortPx(e.xy);
            mapCoord.transform(tm.map.getProjectionObject(), new OpenLayers.Projection("EPSG:4326"));
            tm.clckTimeOut = window.setTimeout(function() {
                tm.singleClick(mapCoord)
            },300);
        }

    });
}

// If we're going to call this method from core, it should be in core
tm.display_polygon_details = function(ll) {
    return function (json) {
        var popupBody,
            popup;

        if (!_.isEmpty(json)) {
            var sfmt = function(s) {
                return _.chain(tm.speciesData)
                    .filter(function(v) { return v.id == s; })
                    .map(tm.formatTreeName)
                    .first()
                    .value();
            };

            var template = _.template(
            '<div id="max_polygon_infowindow">\
             <% _.each(json, function(counts, pid) { %>\
                <div>\
                <h3>Polygon #<%= pid %></h3>\
                <div class="polygon_infowindow_row">\
                    <div class="label">Species:</div>\
                    <div class="results"> \
                    <% if (counts.species.length > 0) { %>\
                      <%= _.chain(counts.species)\
                           .map(sfmt)\
                           .reduce(\
                              function (a,b) { return a + "," + b; })\
                            .value() %>\
                    <% } else { %>\
                       None Yet\
                    <% } %>\
                    </div>\
                </div>\
                <div class="polygon_infowindow_row">\
                    <div class="label">DBH Classes:</div>\
                    <div class="results"> \
                    <% if (counts.classes.length > 0) { %>\
                      <%= _(counts.classes)\
                           .reduce(\
                              function (a,b) { return a + ", " + b; }) %>\
                    <% } else { %>\
                       None Yet\
                    <% } %>\
                    </div>\
                </div>\
                <a target="_blank" href="<%= viewlink %>/<%= pid %>">View/Edit</a>\
             <% }) %>\
             </div>');

            popupBody = template({
                json: json,
                sfmt: sfmt,
                viewlink: tm_urls.site_root + "polygons"
            });

            popup = new OpenLayers.Popup.FramedCloud(
                "Polygon Info", ll, null,
                popupBody, null, true);

            popup.minSize = tm.popup_minSize;
            popup.maxSize = tm.popup_maxSize;
            popup.autoSize = true;
            popup.panMapIfOutOfView = true;
            tm.map.addPopup(popup, true);
        }
    };
};

tm.setup_polygon_edits = function() {

    function bind_remove_handlers() {
        $(".removespecies").click(function() {
            $(this).parents("tr").remove();
        });
    }

    bind_remove_handlers();

    $(".addspecies").click(function() {
        var sid = $(".specieslist").val();
        var species = _.filter(tm.speciesData, function(s) {
            return s.id == sid; })[0];

        var sname = species.sname;

        var polyid = $('.polygon-table').data('id');

        var speciesRow = '<td data-species-id="' + sid + '">' + sname + '</td>';
        var removeLink = '<td><a href="#" class="removespecies">Remove</a></td>';

        var $row = _.chain($("th[data-dbh-id]"))
            .map(function(cell) {
                return $(cell).data('dbh-id'); })
            .map(function(dbh_id) {
                return "pval_" + polyid + "_" + sid + "_" + dbh_id; })
            .map(function(id) {
                return "<td><input name=\"" + id + "\" value=\"0\"></td>"; })
            .reduce(function($row,cell) {
                return $row.append(cell); }, $("<tr>"))
            .value()
            .append(removeLink)
            .prepend(speciesRow);

        $('.polygon-table tbody').append($row);

        tm.setup_polygon_edit_species();
        bind_remove_handlers();
    });

    tm.setup_polygon_edit_species = function() {
        var existingSpecies = $("td[data-species-id]")
                .map(function(i,o) { return $(o).data('species-id'); });

        var sourceWithIds = _.chain(tm.speciesData)
                .filter(function (i) {
                    return !_.contains(existingSpecies, i.id); })
                .map(function(d) {
                    return [d.id, d.cname + " [" + d.sname + "]"];
                }).value();

        var source = _.map(sourceWithIds, function(sid) { return sid[1]; });
        var sourceIdMap = _.reduce(sourceWithIds, function(m, s) {
            m[s[1]] = s[0]; return m;
        }, {});

        function updateDropDown(event, ui) {
            $(".specieslist")
                .val(sourceIdMap[$(".speciesbyname").val()]);
        }

        $(".speciesbyname")
            .autocomplete({
                source: source,
                change: updateDropDown,
                select: updateDropDown,
                focus: updateDropDown
            })
            .change(updateDropDown)
            .val("");

        _.reduce(sourceWithIds, function($s, s) {
            return $s.append('<option value="' + s[0] + '">' + s[1] + "</option>");
        }, $(".specieslist").empty());
    };
};


// Search page map init
tm.init_map = function(div_id){
    tm.init_base_map(div_id);

     tm.singleClick = function(olLonLat) {
        var olProjXY = olLonLat.clone()
                .transform(new OpenLayers.Projection("EPSG:4326"),
                           tm.map.getProjectionObject()),
            jsonCallback = tm.showingPolygons ? tm.display_polygon_details(olProjXY) : tm.display_tree_details,
            urlSuffix = tm.showingPolygons ? 'polygons/search' : 'plots/location/';

        window.clearTimeout(tm.clckTimeOut);
        tm.clckTimeOut = null;
        var spp = $.urlParam('species');
        $.getJSON(tm_static + urlSuffix,
                      {'lat': olLonLat.lat, 'lon' : olLonLat.lon, 'format' : 'json', 'species':spp, 'query': tm.searchParams},
                      jsonCallback);
    };

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

    tm.click = new OpenLayers.Control.Click({handlerOptions:{"single":true}});
    tm.map.addControl(tm.click);
    tm.click.activate();

    tm.map.addLayers([tm.vector_layer, tm.tree_layer, tm.misc_markers]);
    tm.map.setCenter(
        new OpenLayers.LonLat(treemap_settings.mapCenterLon, treemap_settings.mapCenterLat).transform(new OpenLayers.Projection("EPSG:4326"), tm.map.getProjectionObject())
        , tm.start_zoom);

    //check to see if coming for a bookmarked tree
    var bookmark_id = $.urlParam('tree');
    if (bookmark_id){
        $.getJSON(tm_static + 'trees/' + bookmark_id  + '/',
                  {'format' : 'json'},
                  tm.display_tree_details);
    }


    tm.geocoder = new google.maps.Geocoder();

    $(".mapToggle").click(function(evt) {
        if ($(".mapToggle").html() == 'View Satellite') {
            tm.map.setBaseLayer(tm.aerial);
            $(".mapToggle").html('View Streets');
        }
        else if ($(".mapToggle").html() == 'View Streets') {
            if (tm.baseLayer.type == 'terrain' && tm.map.getZoom() >= 16)
            {
                $(".mapError").html('Terrain Layer is not available at this zoom level. Please zoom out to switch layers.').slideDown().delay(3500).slideUp();
            }
            else {
                tm.map.setBaseLayer(tm.baseLayer);
                $(".mapToggle").html('View Satellite');
            }
        }
        evt.preventDefault();
        evt.stopPropagation();
    });

};

tm.init_polygon_links = function() {
    $("#update-image").click(function(e) {
        e.preventDefault();
        $(".image-upload").toggle();
    });
};

tm.init_polygon_map = function(div, pgonjson) {
    var lon = 5;
    var lat = 40;
    var zoom = 5;
    var map, layer;

    map = new OpenLayers.Map(div, {
            maxExtent: new OpenLayers.Bounds(-20037508.34, -20037508.34, 20037508.34, 20037508.34),
            units: 'm',
            projection: new OpenLayers.Projection("EPSG:900913"),
            displayProjection: new OpenLayers.Projection("EPSG:4326"),
            controls: [new OpenLayers.Control.Attribution(),
                       new OpenLayers.Control.Navigation(),
                       new OpenLayers.Control.ArgParser(),
                       new OpenLayers.Control.PanPanel(),
                       new OpenLayers.Control.ZoomPanel()]
        });

    var rings = _.map(pgonjson.coordinates, function (ring) {
        return new OpenLayers.Geometry.LinearRing(
            _.map(ring, function(j) {
                return new OpenLayers.Geometry.Point(j[0], j[1]);
            }));
    });


    var proj900913 = new OpenLayers.Projection("EPSG:900913");
    var proj4326 = new OpenLayers.Projection("EPSG:4326");

    var polygon = new OpenLayers.Geometry.Polygon(rings);
    polygon.transform(proj4326, proj900913);

    var ft = new OpenLayers.Feature.Vector(polygon, {});

    var vectors = new OpenLayers.Layer.Vector("Woodland Polygon");

    vectors.addFeatures([ft]);

    var aerial = new OpenLayers.Layer.Google("Hybrid", {
        type: google.maps.MapTypeId.HYBRID,
        sphericalMercator: true,
        numZoomLevels: 21
    });

    map.addLayers([aerial, vectors]);
    map.setBaseLayer(aerial);

    var bounds = vectors.getDataExtent();

    map.zoomToExtent(bounds, false);
};

tm.init_add_map = function(){
    tm.init_base_map('add_tree_map');

    var vector_style = OpenLayers.Util.extend({}, OpenLayers.Feature.Vector.style['default']);
    vector_style.fillColor = "yellow";
    vector_style.fillOpacity = 0.8;
    vector_style.strokeWidth = 3;
    vector_style.pointRadius = 8;

    tm.add_vector_layer = new OpenLayers.Layer.Vector('AddTreeVectors', { style: vector_style });
    tm.tree_layer = new OpenLayers.Layer.Markers('MarkerLayer');

    tm.drag_control = new OpenLayers.Control.DragFeature(tm.add_vector_layer);
    tm.drag_control.onComplete = function(feature, mousepix) {
        var mapCoord = tm.map.getLonLatFromViewPortPx(mousepix);
        mapCoord.transform(tm.map.getProjectionObject(), new OpenLayers.Projection("EPSG:4326"));
        $('#id_lat').val(mapCoord.lat);
        $('#id_lon').val(mapCoord.lon);
        tm.reverse_geocode(mapCoord, function(ll, full_address, city, zip) {
            tm.update_add_address(ll, full_address, city, zip);

        }, function (ll) {
            if ($("#geocode_address")) {
                $("#geocode_address").html("<b>Address Found: </b><br>" + $('#id_geocode_address').val);
                tm.update_nearby_trees_list(ll, 10, .0001);
            }
            else {
                alert("Reverse Geocode was not successful.");
            }
        });
    }


    if (tm.mask) {tm.map.addLayer(tm.mask);}
    if (tm.parcels) {tm.map.addLayer(tm.parcels);}
    if (tm.parcel_highlight) {tm.map.addLayer(tm.parcel_highlight);}

    tm.map.addLayers([tm.add_vector_layer, tm.tree_layer]);

    tm.map.setBaseLayer(tm.aerial);
    tm.map.addControl(tm.drag_control);
    tm.map.setCenter(
        new OpenLayers.LonLat(treemap_settings.mapCenterLon, treemap_settings.mapCenterLat).transform(new OpenLayers.Projection("EPSG:4326"), tm.map.getProjectionObject())
        , tm.add_start_zoom);

    tm.geocoder = new google.maps.Geocoder();

    $('#id_edit_address_street').keydown(function(evt){
        if (evt.keyCode == 13) {
            evt.preventDefault();
            evt.stopPropagation();
            if ($('#id_edit_address_street').val() != "") {
                $('#update_map').click();
            }
        }
    });
    $('#id_edit_address_city').keydown(function(evt){
        if (evt.keyCode == 13) {
            evt.preventDefault();
            evt.stopPropagation();
            $('#update_map').click();
        }
    });

    $('#update_map').click(function(evt) {
        var address = $('#id_edit_address_street').val();
        var city = $('#id_edit_address_city').val();
        if (city == "Enter a City") {
            city = ""
        }
        if (!address || address == "Enter an Address or Intersection") {return;}
        geo_address = address + " " + city
        tm.geocode(geo_address, function (lat, lng, place) {
            var olPoint = new OpenLayers.LonLat(lng, lat);
            var zoom = tm.add_zoom;
            if (tm.map.getZoom() > tm.add_zoom) {zoom = tm.map.getZoom();}
            tm.map.setCenter(new OpenLayers.LonLat(lng, lat).transform(new OpenLayers.Projection("EPSG:4326"), tm.map.getProjectionObject()), zoom);

            if (tm.add_vector_layer) {tm.add_vector_layer.destroyFeatures();}
            if (tm.tree_layer) {tm.tree_layer.clearMarkers();}

            tm.load_nearby_trees(olPoint);
            tm.add_new_tree_marker(olPoint, true);

            if (tm.parcel_highlight) {
                tm.parcel_highlight.mergeNewParams({'CQL_FILTER':' CONTAINS(the_geom, POINT(' + lng + ' ' + lat + ')) '});
                tm.parcel_highlight.setVisibility(true);
            }

            tm.drag_control.activate();

            $('#id_lat').val(olPoint.lat);
            $('#id_lon').val(olPoint.lon);
            $('#id_geocode_address').val(place)
            $('#id_initial_map_location').val(olPoint.lat + "," + olPoint.lon);
            $('#update_map').html("Update Map");
            $("#mapHolder").show();
            $("#calloutContainer").show();
            tm.trackEvent('Add', 'View Map');
        }, function() {
            if (tm.parcel_highlight) {

                tm.parcel_highlight.setVisibility(false);
            }
        });

    });
};

//initializes map on the profile page; shows just favorited trees
tm.init_favorite_map = function(user){
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
};

//initializes map on the recently added page; shows just recently added trees
tm.init_new_map = function(user){
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
};

//returns a large or small markerLight
tm.get_marker_light = function(t, size) {
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
};


/**
 * initializes the map on the detail/edit page,
 * where a user just views, or moves, an existing tree
 * also it loads the streetview below the map
 */
tm.init_tree_map = function(editable){
    var controls = [new OpenLayers.Control.Attribution(),
                    new OpenLayers.Control.Navigation(),
                    new OpenLayers.Control.ArgParser(),
                    new OpenLayers.Control.ZoomPanel(),
                    new OpenLayers.Control.TouchNavigation({
                        dragPanOptions: {
                            enableKinetic: true
                        }
            })];

    var vector_style = OpenLayers.Util.extend({}, OpenLayers.Feature.Vector.style['default']);
    vector_style.fillColor = "yellow";
    vector_style.fillOpacity = 0.8;
    vector_style.strokeWidth = 3;
    vector_style.pointRadius = 8;

    tm.init_base_map('edit_tree_map', controls);

    tm.singleClick = function(olLonlat) {
        $.getJSON(tm_static + 'plots/location/',
              {'lat': olLonlat.lat, 'lon' : olLonlat.lon, 'format' : 'json', 'max_plots' : 1},
              function(json) {
                  var html = '<a href="' + tm_static  + 'plots/' + json.features[0].properties.id + '">Planting Site #' + json.features[0].properties.id + '</a>';
                  $('#alternate_tree_div').html(html);
              }
        );
    };


    tm.add_vector_layer = new OpenLayers.Layer.Vector('AddTreeVectors', { style: vector_style })
    tm.tree_layer = new OpenLayers.Layer.Markers('MarkerLayer')

    if (tm.mask) {tm.map.addLayer(tm.mask);}
    if (tm.parcels) {tm.map.addLayer(tm.parcels);}

    tm.drag_control = new OpenLayers.Control.DragFeature(tm.add_vector_layer);
    tm.drag_control.onComplete = function(feature, mousepix) {
        var mapCoord = tm.map.getLonLatFromViewPortPx(mousepix);
        mapCoord.transform(tm.map.getProjectionObject(), new OpenLayers.Projection("EPSG:4326"));
        $('#id_geometry').val('POINT (' + mapCoord.lon + ' ' + mapCoord.lat + ')')
        tm.reverse_geocode(mapCoord, function(ll, full_address, city, zip) {
            if ($('#edit_address_city')) {
                $('#edit_address_city').val(city);
                $('#edit_address_city').html(city);
            }
            if ($('#id_geocode_address')) {
                var geocode_address = full_address.split(city)[0].split(',')[0]
                $('#id_geocode_address').val(geocode_address);
                $('#id_geocode_address').html(geocode_address);
            }
            if ($('#edit_address_zip')) {
                $('#edit_address_zip').val(zip);
                $('#edit_address_zip').html(zip);
            }
        });
    }

    tm.click = new OpenLayers.Control.Click({handlerOptions:{"single":true}});
    tm.map.addControl(tm.click);
    tm.click.activate();

    tm.map.addLayers([tm.tree_layer, tm.add_vector_layer]);
    tm.map.addControl(tm.drag_control);
    tm.map.setBaseLayer(tm.aerial);

    var currentPoint = new OpenLayers.LonLat(tm.current_tree_geometry[0], tm.current_tree_geometry[1]);
    var olPoint = new OpenLayers.LonLat(tm.current_tree_geometry[0], tm.current_tree_geometry[1]).transform(new OpenLayers.Projection("EPSG:4326"), tm.map.getProjectionObject());

    tm.map.setCenter(olPoint, tm.edit_zoom);

    tm.geocoder = new google.maps.Geocoder();
    tm.add_new_tree_marker(currentPoint, false);

    tm.load_nearby_trees(currentPoint);

    if (tm.current_tree_geometry_pends && tm.current_tree_geometry_pends.length > 0) {
        tm.add_pending_markers(tm.current_tree_geometry_pends);
        $('#edit_tree_map_legend').show();
    }
    //if (editable) { tm.drag_control.activate(); }

    tm.load_streetview(currentPoint, 'tree_streetview');


    if (!editable) {return;}

    //listen for change to address field to update map location
    //TODO: Disallow editing of nearby address
    $('#id_nearby_address').change(function(nearby_field){
        var new_addy = nearby_field.target.value;
        tm.geocode(new_addy, function(lat,lng){
            var ll = new OpenLayers.LonLat(lng,lat);
            if (tm.validate_point(ll,new_addy) && !tm.tree_marker){ //only add marker if it doesn't yet exist
                tm.add_new_tree_marker(ll, false);
                tm.map.setCenter(ll,15);
            }
        });
    });
};

tm.load_nearby_trees = function(ll){
    //load in nearby trees as well
    var url = ['plots/location/?lat=',ll.lat,'&lon=',ll.lon,'&format=json&max_plots=70'].join('');
    $.getJSON(tm_static + url, function(geojson){
        $.each(geojson.features, function(i,f){
            coords = f.geometry.coordinates;
            var ll = new OpenLayers.LonLat(coords[0], coords[1]).transform(new OpenLayers.Projection("EPSG:4326"), tm.map.getProjectionObject());
            if (f.properties.id == tm.currentTreeId) {return;}
            var icon = tm.get_icon(tm_icons.small_trees, 19);
            if (f.properties.tree == false) {icon = tm.get_icon(tm_icons.small_plots, 19);}
            var marker = new OpenLayers.Marker(ll, icon);
            marker.tid = f.properties.id;

            tm.tree_layer.addMarker(marker);

        });
    });
};

tm.add_new_tree_marker = function(ll, do_reverse_geocode) {
    if (tm.add_vector_layer) {
        tm.add_vector_layer.destroyFeatures();
    }
    var tree_marker = new OpenLayers.Geometry.Point(ll.lon, ll.lat).transform(new OpenLayers.Projection("EPSG:4326"), tm.map.getProjectionObject());
    var tree_vector = new OpenLayers.Feature.Vector(tree_marker)

    tm.add_vector_layer.addFeatures([tree_vector])
    if (do_reverse_geocode) {
        tm.reverse_geocode(ll, function(ll, full_address, city, zip) {
            tm.update_add_address(ll, full_address, city, zip);
        });
    }

};

tm.add_pending_markers = function(pends) {
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
};

tm.update_add_address = function(ll, full_address, city, zip) {
    if ($("#geocode_address")) {
        $("#geocode_address").html("<b>Address Found: </b><br>" + full_address);
    }
    if ($("#id_geocode_address")) {
        $('#id_geocode_address').val(full_address);
    }
    if ($('#edit_address_city')) {
        $('#edit_address_city').val(city);
        $('#edit_address_city').html(city);
    }
    if ($('#id_edit_address_city')) {
        $('#id_edit_address_city').val(city);
    }
    if ($('#edit_address_zip')) {
        $('#edit_address_zip').val(zip);
        $('#edit_address_zip').html(zip);
    }
    if ($('#id_edit_address_zip')) {
        $('#id_edit_address_zip').val(zip);
    }

    tm.update_nearby_trees_list(ll, 10, .0001);
};

tm.update_nearby_trees_list = function (ll, plots, distance) {
    if ($('#nearby_trees')) {
        $('#nearby_trees').html("Loading...")
        var url = ['plots/location/?lat=',ll.lat,'&lon=',ll.lon,'&format=json&max_plots=' + plots + '&distance=' + distance].join('');
        $.getJSON(tm_static + url, function(geojson){
            if (geojson.features.length == 0) {
                $('#nearby_trees').html("No other trees nearby.")
            }
            else {
                $('#nearby_trees').html("Found " + geojson.features.length + " planting site(s) that may be too close to the tree you want to add. Please double-check that you are not adding a tree that is already on our map:")
                $.each(geojson.features, function(i,f){
                    var tree = $('#nearby_trees');
                    if (f.properties.common_name){
                        tree.append("<div class='nearby_tree_info'><a href='" + tm_static + "plots/" + f.properties.id + "' target='_blank'>" + f.properties.common_name + " (#" + f.properties.id + ")</a><br><span class='nearby_tree_scientific'>" + f.properties.scientific_name + "</span></div>");
                    }
                    else {
                        tree.append("<div class='nearby_tree_info'><a href='" + tm_static + "plots/" + f.properties.id + "' target='_blank'>No species information (#" + f.properties.id + ")</a></div>")
                    }
                    if (f.properties.current_dbh){
                        tree.append("<div class='nearby_tree_diameter'>Diameter: " + f.properties.current_dbh + " inches</div>");
                    }

                });
            }
        });
    }
};

/*
  load up streetview pointing at specified GLatLng, into specified div
*/
tm.load_streetview = function(ll, div){
    div = document.getElementById(div);
    panoPosition = new google.maps.LatLng(ll.lat, ll.lon);
    new google.maps.StreetViewService().getPanoramaByLocation(panoPosition, 50, function(data, status) {
        if (status == google.maps.StreetViewStatus.OK) {
            tm.pano = new google.maps.StreetViewPanorama(div, {position:panoPosition, addressControl:tm.panoAddressControl});

        }
        else {
            $(div).html("<div class='no_streetview'>Street View is not available for this location.</div>");
        }
    });

};

tm.display_tree_details = function(json){
    if (json) {
        if (json.features.length > 0) {
            var tree = json.features[0];
            var p = tree.properties;
            var coords = tree.geometry.coordinates;

            //remove old markers
            if (tm.plot_detail_market) {tm.misc_markers.removeMarker(tm.plot_detail_market);}

            var AutoSizeFramedCloud = OpenLayers.Class(OpenLayers.Popup.FramedCloud, {
                'autoSize': true
            });

            //Add tree marker
            tm.plot_detail_market = tm.get_tree_marker(coords[1], coords[0]);
            tm.plot_detail_market.plot_id = p.id;
            tm.plot_detail_market.nhbd_id = p.neighborhood_id;
            tm.plot_detail_market.district_id = p.district_id;
            tm.misc_markers.addMarker(tm.plot_detail_market);


            var ll = tm.plot_detail_market.lonlat;

            popup = new OpenLayers.Popup.FramedCloud("Tree Info",
                                                     ll,
                                                     null,
                                                     '<div id="max_tree_infowindow">Loading ...</div>',
                                                     tm.plot_detail_market.icon,
                                                     true);
            popup.minSize = tm.popup_minSize;
            popup.maxSize = tm.popup_maxSize;
            popup.autoSize = true;
            popup.panMapIfOutOfView = true;
            tm.map.addPopup(popup, true);

            tm.trackEvent('Search', 'Map Detail', 'Tree', p.id);

            function displayDetailPopup() {
                $('#max_tree_infowindow').load(
                    tm_static + 'plots/' + tm.plot_detail_market.plot_id + '/?format=popup');
            }

            if (!p.address_street) {
                tm.reverse_geocode(new OpenLayers.LonLat(coords[0], coords[1]),
                                   function(ll, place, city, zip) {
                                       var data = {
                                           'plot_id': p.id,
                                           'address': place,
                                           'city': city
                                       };

                                       var jsonString = JSON.stringify(data);

                                       $.ajax({
                                           url: tm_static + 'plots/location/update/',
                                           type: 'POST',
                                           data: jsonString,
                                           complete: displayDetailPopup
                                       });
                                   },
                                   displayDetailPopup
                                  );
            } else {
                displayDetailPopup();
            }
        }
    }
};
