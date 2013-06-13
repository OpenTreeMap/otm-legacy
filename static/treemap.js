tm_icons = {
    //base folder for shadow and other icon specific stuff
    base_folder : tm_static + 'static/images/map_icons/v3/',
    small_trees : tm_static + "static/images/map_icons/v3/UFM_Tree_Icon_zoom7b.png",
    small_plots : tm_static + "static/images/map_icons/v3/UFM_Tree_Icon_zoom7_plot.png",
    small_trees_complete : tm_static + "static/images/map_icons/v3/UFM_Tree_Icon_zoom7b.png",
    focus_tree : tm_static + 'static/images/map_icons/v4/marker-selected.png',
    pending_tree : tm_static + 'static/images/map_icons/v4/marker-pending.png',
    marker : tm_static + 'static/openlayers/img/marker.png'
    };

tm = {
    speciesData: null,
    map : null,
    tree_markers : [],
    geocoded_locations: {},
    plot_detail_market : null,
    current_tile_overlay : null,
    current_select_tile_overlay : null,
    selected_tile_query : null,
    mgr : null,
    cur_polygon : null,
    geocoder : null,
    maxExtent : null,
    clckTimeOut : null,
    locations: null,

    start_zoom: null,
    add_start_zoom: null,
    add_zoom: null,

    google_bounds: null,
    panoAddressControl: true,

    searchParams: {},

    benefitUnitTransformer: function(k,v) { return v; },

    //initializes the map where a user places a new tree
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

    get_tree_marker: function(lat, lng) {
        var ll = new OpenLayers.LonLat(lng, lat).transform(new OpenLayers.Projection("EPSG:4326"), tm.map.getProjectionObject());
        var marker = new OpenLayers.Marker(ll, tm.get_icon(tm_icons.focus_tree, 19));

        return marker
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

    display_benefits : function(benefits){
        $('#results_wrapper').show();
        $("#no_results").hide();
        $.each(benefits, function(k,v){
            $('#benefits_' + k).html(tm.addCommas(parseInt(v)));
        });
        if (benefits['total'] == 0.0)
        {
            $("#no_results").show();
        }
    },

    display_summaries : function(summaries){
        $(".tree_count").html(tm.addCommas(parseInt(summaries.total_trees)));
        $(".plot_count").html(tm.addCommas(parseInt(summaries.total_plots)));
        if (summaries.total_trees == '0' && summaries.total_plots == '0')
        {
            $(".moretrees").html("");
            $(".notrees").html("No results? Try changing the filters above.");
        }  else {
            $(".moretrees").html("");
            $(".notrees").html("");
        }
        $.each(summaries, function(k,v){
            var span = $('#' + k);
            if (span.length > 0){
                span.html(tm.addCommas(
                    tm.benefitUnitTransformer(k,parseInt(v))));
            }
        });

    },

    display_search_results : function(results){
        if (tm.vector_layer) {tm.vector_layer.destroyFeatures();}
        $('#displayResults').hide();
        if (results) {
            tm.display_summaries(results.summaries);
            tm.display_benefits(results.benefits);

            tm.tree_layer.setVisibility(false);

            if (results.initial_tree_count != results.full_tree_count && !(results.summaries.total_trees == 0 && results.summaries.total_plots == 0)) {
                if (results.featureids) {
                    var cql = results.featureids;
                    delete tm.tree_layer.params.CQL_FILTER;
                    tm.tree_layer.mergeNewParams({'FEATUREID':cql});
                    tm.tree_layer.setVisibility(true);
                }
                else if (results.tile_query) {
                    var cql = results.tile_query;
                    delete tm.tree_layer.params.FEATUREID;
                    if (tm.set_style) {
                        var style = tm.set_style(results.tile_query);
                        tm.tree_layer.mergeNewParams({'CQL_FILTER':cql, 'styles':style});
                    }
                    else {
                        tm.tree_layer.mergeNewParams({'CQL_FILTER':cql, 'styles': tm_urls.geo_style});
                    }
                    tm.tree_layer.setVisibility(true);
                }
            }

            if (results.geography) {
                var geog = results.geography;
                $('#summary_subset_val').html(geog.name);
                tm.highlight_geography(geog, 'neighborhood');
            } else {
                $('#summary_subset_val').html('the region');
            }
        }

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

    enableEditTreeLocation : function(){
        tm.trackEvent('Edit', 'Location', 'Start');

        tm.drag_control.activate();
        //TODO:  bounce marker a bit, or change its icon or something
        var save_html = '<a href="javascript:tm.saveTreeLocation()" class="buttonSmall"><img src="' + tm_static + 'static/images/loading-indicator-trans.gif" width="12" /> Stop Editing and Save</a>'
        $('#edit_tree_location').html(save_html);
        return false;
    },

    saveTreeLocation : function(){
        tm.trackEvent('Edit', 'Location', 'Save');

        tm.drag_control.activate();
        var edit_html = '<a href="#" onclick="tm.enableEditTreeLocation(); return false;"class="buttonSmall">Start Editing Location</a>'
        $('#edit_tree_location').html(edit_html);
        tm.updateEditableLocation(tm.currentPlotId);
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

        if (model == "Plot") {
            $('#edit_'+field).editable(tm.updatePlotServerCall, editableOptions);
        } else if (model == "TreeStewardship"){
            $('#edit_'+field).editable(tm.addTreeStewardship, editableOptions);
        } else if (model == "PlotStewardship"){
            $('#edit_'+field).editable(tm.addPlotStewardship, editableOptions);
        } else {
            $('#edit_'+field).editable(tm.updateEditableServerCall, editableOptions);
        }
    },

    updatePlotServerCall: function(value, settings) {
        var data = {};
        var plotId = settings.objectId;
        var field = settings.fieldName;

        data[field] = tm.coerceFromString(value)

        this.innerHTML = "Saving..."; //TODO- is this needed?
        var jsonString = JSON.stringify(data);
        settings.obj = this;
        $.ajax({
            url: tm_static + 'plots/' + plotId + '/update/',
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

                    if (settings.fieldName == "width" || settings.fieldName == "length") {
                        if (value == 99.0) {value = "15+"}
                    }

                    settings.obj.innerHTML = value
                    tm.trackEvent("Edit", settings.fieldName)
                }
            }});

        return "Saving... " + '<img src="' + tm_static + 'static/images/loading-indicator.gif" />';
    },

    addTreeStewardship: function(value, date, settings) {
        var data = {};
        var treeId = settings.objectId;

        data['activity'] = tm.coerceFromString(value)
        data['performed_date'] = tm.coerceFromString(date)

        var jsonString = JSON.stringify(data);
        settings.obj = this;
        $.ajax({
            url: tm_static + 'trees/' + treeId + '/stewardship/',
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
                    var value = response['update']['activity'];

                    settings.obj.innerHTML = value
                    tm.trackEvent("Edit", settings.fieldName)
                    tm.newTreeActivity();
                }
            }});

        return "Saving... " + '<img src="' + tm_static + 'static/images/loading-indicator.gif" />';

    },

    addPlotStewardship: function(value, date, settings) {
        var data = {};
        var plotId = settings.objectId;

        data['activity'] = tm.coerceFromString(value)
        data['performed_date'] = tm.coerceFromString(date)

        var jsonString = JSON.stringify(data);
        settings.obj = this;
        $.ajax({
            url: tm_static + 'plots/' + plotId + '/stewardship/',
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
                    var value = response['update']['activity'];

                    settings.obj.innerHTML = value
                    tm.trackEvent("Edit", settings.fieldName)
                    tm.newPlotActivity();
                }
            }});

        return "Saving... " + '<img src="' + tm_static + 'static/images/loading-indicator.gif" />';
    },

    updateEditableServerCall: function(value, settings) {
        var data = {
            'model': settings.model,
            'update': {
            }
        };

        if (settings.objectId) {
            data.id = settings.objectId;
        }

        value = tm.coerceFromString(value);

        $(this).removeClass("error");

        if (settings.fieldName == 'species_id') {
            if (value == 0) {
                $(this).addClass("error");
                return "Please select a species from the provided list.";
            }
            data['update']['species_other1'] = $('#other_species1')[0].value;
            data['update']['species_other2'] = $('#other_species2')[0].value;
        }

        //do some validation for height and canopy height
        if ((settings.fieldName == 'height' || settings.fieldName == 'canopy_height') && value > 300) {
            $(this).addClass("error");
            return "Height is too large.";
        }

        if (settings.fieldName == 'height' && isNaN(value)) {
            $(this).addClass("error");
            return "Height must be a number.";
        }


        if ($.inArray(settings.model, ["TreeAlert","TreeAction","TreeFlags"]) >=0) {
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

        this.innerHTML = "Saving..."; //TODO: Is this needed?

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
                                value = tm.formatSpeciesName(tm.speciesData[i]);
                                $("#edit_species").html(tm.speciesData[i].cname);
                            }
                        }
                        var other1 = response['update']['species_other1'];
                        var other2 = response['update']['species_other2'];
                        if ($('#edit_species_other').length > 0) {
                            $('#edit_species_other')[0].innerHTML = other1 + " " + other2;
                        } else {
                            $("#edit_species").append('<br>' + other1 + " " + other2);
                        }

                    }
                    if (settings.fieldName == "plot_width" || settings.fieldName == "plot_length") {
                        if (value == 99.0) {value = "15+"}
                    }
                    settings.obj.innerHTML = value;
                    tm.trackEvent("Edit", settings.fieldName)
                }
            }});
        return "Saving... " + '<img src="' + tm_static + 'static/images/loading-indicator.gif" />';
    },

    updateEditableLocation: function(currentPlotId) {
        $("#edit_map_errors")[0].innerHTML = "Saving..."
        var wkt = $('#id_geometry').val();
        var geoaddy = $("#id_geocode_address").val();
        var data = {
            'model': 'Plot',
            'id': currentPlotId,
            'update': {
                geometry: wkt,
                geocoded_address: geoaddy
            }
        };

        if (tm.update_address_on_location_update) {
            data['update']['address_street'] = geoaddy;
        };

        var jsonString = JSON.stringify(data);
        $.ajax({
            url: tm_static + 'update/',
            type: 'POST',
            data: jsonString,
            complete: function(xhr, textStatus) {
                var response =  JSON.parse(xhr.responseText);
                $("#edit_map_errors")[0].innerHTML = ""
                $("#edit_map_errors")[0].className = "";
                if (response['success'] != true) {
                    $("#edit_map_errors")[0].className = "errorResponse";
                    $("#edit_map_errors")[0].innerHTML = "An error occurred in saving: ";
                    var newError = ""
                    $.each(response['errors'], function(i,err){
                         newError += err;
                    });

                    if (newError.indexOf("exclusion zone") >= 0 &&
                        newError.indexOf("Geometry") >= 0) {
                        $("#edit_map_errors")[0].innerHTML = "An error occurred in saving the location. Trees may not be placed within the white areas.";
                    } else {
                        $("#edit_map_errors")[0].innerHTML = newError;
                    }
                } else {
                    $("#edit_map_errors")[0].innerHTML = "New location saved."
                    if (tm.update_address_on_location_update) {
                        $("#edit_address_street")[0].innerHTML = geoaddy;
                    };
                }
            }});
    },

    formatTreeName: function(item) {
        var cultivar_portion = item.cultivar ? " '" + item.cultivar + "'" : " ";
        return item.cname + " [ " + item.sname + " " + cultivar_portion +
            " " + item.family + " " + item.other_part + "]";
    },

    formatSpeciesName: function(item) {
        var cultivar_portion = item.cultivar ? " '" + item.cultivar + "'" : " ";
        return item.sname + cultivar_portion + item.family +
            " " + item.other_part;
    },

    setupAutoComplete: function(field) {
        return field.autocomplete({
            source:function(request, response){
                response( $.map( tm.speciesData, function( item ) {
                    if (item.cname.toLowerCase().indexOf(request.term.toLowerCase()) != -1 ||
                        item.sname.toLowerCase().indexOf(request.term.toLowerCase()) != -1)
                    {
                                            return {
                                                    label: tm.formatTreeName(item),
                                                    value: item.id
                                            }
                    }
                                }));
            },
            minLength: 1,
            select: function(event, ui) {
                field.val(ui.item.label);
                $("#species_search_id").val(ui.item.value).change();
                if ($("#id_species_id").length > 0) {
                    $("#id_species_id").val(ui.item.value).change();
                }
                return false;
            }
        });

    },

    newTreeActivity: function() {
        return tm.createAttributeDateRow("treeActivityTypeSelection", tm.choices['tree_stewardship'], "treeActivityTable",
                                     tm.handleNewTreeStewardship("treeActivityTypeSelection",
                                                           "TreeStewardship",
                                                           "treeActivityTable",
                                                           "treeActivityCount"));
    },
    newPlotActivity: function() {
        return tm.createAttributeDateRow("plotActivityTypeSelection", tm.choices['plot_stewardship'], "plotActivityTable",
                                     tm.handleNewPlotStewardship("plotActivityTypeSelection",
                                                           "PlotStewardship",
                                                           "plotActivityTable",
                                                           "plotActivityCount"));
    },
    newAction: function() {
        return tm.createAttributeRow("actionTypeSelection", tm.choices['actions'], "actionTable",
                                     tm.handleNewAttribute("actionTypeSelection",
                                                           "TreeAction",
                                                           "actionTable",
                                                           "actionCount", tm.choices['actions']));
    },

    newLocal: function() {
        return tm.createAttributeRow("localTypeSelection", tm.choices['projects'], "localTable",
                                     tm.handleNewAttribute("localTypeSelection",
                                                           "TreeFlags",
                                                           "localTable",
                                                           "localCount", tm.choices['projects']));
    },

    newHazard: function() {
        return tm.createAttributeRow("hazardTypeSelection", tm.choices['alerts'], "hazardTable",
                                     tm.handleNewAttribute("hazardTypeSelection",
                                                           "TreeAlert",
                                                           "hazardTable",
                                                           "hazardCount", tm.choices['alerts']));
    },

    createAttributeRow: function(selectId, typesArray, tableName, submitEvent) {
        var select = $("<select id='" + selectId + "' />");
        for (var i=0; i < typesArray.length;i++) {
            select.append($("<option value='"+typesArray[i][0]+"'>"+ typesArray[i][1]+"</option>"));
        }
        var row = $("<tr />");

        row.append($(""), $("<td colspan='2' />").append(select)).append(
            $("<td />").append(
                $("<input type='submit' value='Submit' class='buttonSmall' />").click(submitEvent),
                $("<input type='submit' value='Cancel' class='buttonSmall' />").click(function() {
                    row.remove();
                })
            )
        );

        $("#" + tableName).append(row);
    },
    createAttributeDateRow: function(selectId, typesArray, tableName, submitEvent) {
        var select = $("<select id='" + selectId + "' />");
        for (var i=0; i < typesArray.length;i++) {
            select.append($("<option value='"+typesArray[i][0]+"'>"+ typesArray[i][1]+"</option>"));
        }
        var row = $("<tr id='data-row' />");

        row.append(
            $(""),
            $("<td />").append(select),
            $("<td />").append($("<input id='" + selectId + "-datepicker' type='text'>").datepicker({ maxDate: "+0d" })),
            $("<td />").append(
                $("<input type='submit' value='Submit' class='buttonSmall' />").click(submitEvent),
                $("<input type='submit' value='Cancel' class='buttonSmall' />").click(function() {
                    row.remove();
                })
            )
        );

        $("#" + tableName).append(row);

    },

    handleNewTreeStewardship: function(select, model, table, count) {
        return function() {
            var data = $("#" + select)[0].value;
            var data_date = $("#" + select + "-datepicker")[0].value;

            if (data == "" || data_date == "") {
                alert("You must enter a date for the tree activity.");
                return;
            }

            settings = {
                model: model,
                objectId: tm.currentTreeId,
                activity: data,
                submit: 'Save',
                cancel: 'Cancel'
            };

            $(this.parentNode.parentNode).remove();
            tm.addTreeStewardship(data, data_date, settings);
            var choices = tm.choices['tree_stewardship'];
            for (var i=0;i<choices.length; i++) {
                if (choices[i][0] == data) {
                    $("#" + table).append(
                        $("<tr><td>"+choices[i][1]+"</td><td>"+data_date+"</td><td></td></tr>"));
                    $("#" + count).html(parseInt($("#" + count)[0].innerHTML) + 1);
                    break;
                }
            }
        };
    },

    handleNewPlotStewardship: function(select, model, table, count) {
        return function() {
            var data = $("#" + select)[0].value;
            var data_date = $("#" + select + "-datepicker")[0].value;

            if (data == "" || data_date == "") {
                alert("You must enter a date for the planting site activity.");
                return;
            }

            settings = {
                model: model,
                objectId: tm.currentPlotId,
                activity: data,
                performed_date: data_date,
                submit: 'Save',
                cancel: 'Cancel'
            };

            $(this.parentNode.parentNode).remove();
            tm.addPlotStewardship(data, data_date, settings);
            var choices = tm.choices['plot_stewardship'];
            for (var i=0;i<choices.length; i++) {
                if (choices[i][0] == data) {
                    $("#" + table).append(
                        $("<tr><td>"+choices[i][1]+"</td><td>"+data_date+"</td><td></td></tr>"));
                    $("#" + count).html(parseInt($("#" + count)[0].innerHTML) + 1);
                    break;
                }
            }
        };
    },

    handleNewAttribute: function(select, model, table, count, data_array) {
        return function() {
            var data = $("#" + select)[0].value;
            settings = {
                'extraData': {
                    'parent': {
                        'model': 'Tree',
                        'id': tm.currentTreeId
                    }
                },
                model: model,
                fieldName: data,
                submit: 'Save',
                cancel: 'Cancel'
            };

            $(this.parentNode.parentNode).remove();
            var d = new Date();
            var dateStr = (d.getYear()+1900)+"-"+(d.getMonth()+1)+"-"+d.getDate();
            tm.updateEditableServerCall(dateStr, settings)
            for (var i=0;i<data_array.length; i++) {
                if (data_array[i][0] == data) {
                    $("#" + table).append(
                        $("<tr><td>"+data_array[i][1]+"</td><td>"+dateStr+"</td><td></td></tr>"));
                    $("#" + count).html(parseInt($("#" + count)[0].innerHTML) + 1);
                    break;
                }
            }
        };
    },

    //TODO: These don't delete from the database
    deleteAction: function(key, value, elem) {
        $(elem.parentNode.parentNode).remove();
    },
    deleteHazard: function(key, value, elem) {
        $(elem.parentNode.parentNode).remove();
    },
    deleteLocal: function(key, value, elem) {
       $(elem.parentNode.parentNode).remove();
    },

    deleteTreeActivity: function(id, elem) {
        $.ajax({
            url: tm_static + 'trees/' + tm.currentTreeId + "/stewardship/" + id + "/delete/",
            complete: function(xhr, textStatus) {
                $(elem.parentNode.parentNode).remove();
                $("#treeActivityCount").html(parseInt($("#treeActivityCount")[0].innerHTML) - 1);
            }
        });
    },

    deletePlotActivity: function(id, elem) {
        $.ajax({
            url: tm_static + 'plots/' + tm.currentPlotId + "/stewardship/" + id + "/delete/",
            complete: function(xhr, textStatus) {
                $(elem.parentNode.parentNode).remove();
                $("#plotActivityCount").html(parseInt($("#plotActivityCount")[0].innerHTML) - 1);
            }
        });
    },

    pageLoadSearch: function () {
        tm.loadingSearch = true;
        tm.searchParams = {};
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
                    tm.updateSpeciesFields('species_search',$.address.parameter(key), '');
                }
                if (key == "location") {
                    tm.updateLocationFields($.address.parameter(key).replace(/\+/g, " "));
                }
                if (key == "tree_stewardship") {
                    $("#steward-tree").click();
                    var actions = val.split(',');
                    for (j=0;j<actions.length;j++) {
                        $(".steward-action[value=" + actions[j] + "]").click();
                    }
                }
                if (key == "plot_stewardship") {
                    $("#steward-plot").click();
                    var actions = val.split(',');
                    for (k=0;k<actions.length;k++) {
                        $(".steward-action[value=" + actions[k] + "]").click();
                    }
                }
                if (key == "stewardship_reverse") {
                    $(".steward-reverse[value=" + val + "]").click();
                }
                if (key == "stewardship_range") {
                    var svals = $.address.parameter(key).split("-");
                    var date1 = new Date(parseInt(svals[0] * 1000));
                    var date2 = new Date(parseInt(svals[1] * 1000));

                    $("#steward-date-1").datepicker("setDate", date1).change();
                    $("#steward-date-2").datepicker("setDate", date2).change();
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
        if (tm.handleStewardship) {
            q = tm.handleStewardship(q);
        }

        var qstr = decodeURIComponent(q.toString()).replace(/\+/g, "%20")
        if (qstr != '?'+$.query.toString()) {
            if (!tm.loadingSearch) {
                $.query.load(qstr);
            }
        }


        return qstr;
    },

    updateSearch: function() {
        if (tm.loadingSearch) { return; }

        var qs = tm.serializeSearchParams();

        $("#kml_link").attr('href', tm_static + "search/kml/"+qs);
        $("#csv_link").attr('href', tm_static + "search/csv/"+qs);
        $("#shp_link").attr('href', tm_static + "search/shp/"+qs);

        if (qs === false) { return; }

        tm.trackPageview('/search/' + qs);

        $('#displayResults').show();
        $.ajax({
            url: tm_static + 'search/'+qs,
            dataType: 'json',
            success: tm.display_search_results,
            error: function(err) {
                $('#displayResults').hide();
                alert("There was an error while executing your search");
            }
        });
    },

    updateLocationFields: function(loc){
        if (loc){
            $("#location_search_input").val(loc);
            tm.handleSearchLocation(loc);
        }
    },

    updateSpeciesFields: function(field_prefix, spec){
        if (!tm.speciesData) {
            return;
        }

        if (spec) {
            $("#" + field_prefix + "_id").val(spec);

            for (var i = 0; i < tm.speciesData.length; i++) {
                if (tm.speciesData[i].id == spec) {
                    $("#" + field_prefix + "_input").val(tm.speciesData[i].cname + " [ " + tm.speciesData[i].sname + " ]");
                    break;
                }
            }
        }
    },


    add_favorite_handlers : function(base_create, base_delete) {
        $('.favorite.fave').live('click', function(e) {
            var pk = $(this).attr('id').replace('favorite_', '');
            var url = base_create + pk + '/';
            $.getJSON(tm_static + url, function(data, textStatus) {
                $('#favorite_' + pk).removeClass('fave').addClass('unfave');
                $('#favorite_' + pk).html('Remove as favorite');
            });
            tm.trackEvent('Favorite', 'Add Favorite', 'Tree', pk);
            return false;
        });
        $('.favorite.unfave').live('click', function(e) {
            var pk = $(this).attr('id').replace('favorite_', '');
            var url = base_delete + pk + '/';
            $.getJSON(tm_static + url, function(data, textStatus) {
                $('#favorite_' + pk).removeClass('unfave').addClass('fave');
                $('#favorite_' + pk).html('Add as favorite');
            });
            tm.trackEvent('Favorite', 'Remove Favorite', 'Tree', pk);
            return false;
        });
    },

    /**
     * Determine if "search" is a zipcode, neighborhood, or address
     * and then <do more search stuff>
     */
    handleSearchLocation: function(search) {
        if (tm.misc_markers) {tm.misc_markers.clearMarkers();}
        if (tm.vector_layer) {tm.vector_layer.destroyFeatures();}

        tm.geocode_address = search;
        // clean up any previous location search params
        delete tm.searchParams.location;
        delete tm.searchParams.geoName;
        delete tm.searchParams.lat;
        delete tm.searchParams.lon;

        function continueSearchWithFeature(nbhoods) {
            var bbox = OpenLayers.Bounds.fromArray(nbhoods.bbox).transform(new OpenLayers.Projection("EPSG:4326"), tm.map.getProjectionObject());
            tm.map.zoomToExtent(bbox, true);

            tm.add_location_marker(bbox.getCenterLonLat());
            var featureName = nbhoods.features[0].properties.name;
            if (featureName) {
                tm.searchParams['geoName'] = featureName;
            }
            else {
                featureName = nbhoods.features[0].properties.zip;
                tm.searchParams['location'] = featureName;
                tm.geocoded_locations[search] = featureName;
            }

            tm.updateSearch();
        }

        // Search order:
        // -> If the string is a number, assume it is a zipcode and search by zipcode
        // -> Otherwise:
        //    -> Check the string aginst the neighborhoods table
        //    -> Otherwise assume it's an address
        if (tm.isNumber(search)) {
            $.getJSON(tm_static + 'zipcodes/', {format:'json', name: search}, function(zips){
                if (tm.location_marker) {tm.misc_markers.removeMarker(tm.location_marker)}

                if (zips.features.length > 0) {
                    continueSearchWithFeature(zips);
                }
            });
        }
        else
        {
            $.getJSON(tm_static + 'neighborhoods/', {format:'json', name: search}, function(nbhoods){
                if (tm.location_marker) {tm.misc_markers.removeMarker(tm.location_marker)}

                if (nbhoods.features.length > 0) {
                    continueSearchWithFeature(nbhoods);
                } else {
                    tm.geocode(search, function(lat, lng, place) {
                        var olPoint = new OpenLayers.LonLat(lng, lat);
                        var llpoint = new OpenLayers.LonLat(lng, lat).transform(new OpenLayers.Projection("EPSG:4326"), tm.map.getProjectionObject());
                        tm.map.setCenter(llpoint, tm.add_zoom);

                        tm.add_location_marker(llpoint);

                        tm.geocoded_locations[search] = [olPoint.lon, olPoint.lat];
                        tm.searchParams['lat'] = olPoint.lat;
                        tm.searchParams['lon'] = olPoint.lon;
                        tm.updateSearch();
                   });
               }
            });
        }
    },

    editDiameter: function(field, diams) {
        // no value: show box
        // one value: show box w/ value
        // many values: show boxes w/ split values
        if (!$.isArray(diams)) {diams=[0];}

        //diams is either [0] or an array of what's there by this point
        diams = tm.currentTreeDiams || diams;
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
                if ($("#circum").attr("checked")) {
                    val = val / Math.PI;
                }
                vals.push(val);
                sum += Math.pow(val, 2);
            }
        }
        var total = Math.sqrt(sum);

        if (total > 100) {
            $("#edit_dbh").append("<br/><span class='smError'>Total diameter too large.</span>")
            return;
        }

        if (isNaN(total)) {
            $("#edit_dbh").append("<br/><span class='smError'>Diameter must be a number.</span>")
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

    }
};
