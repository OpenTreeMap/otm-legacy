tm.buildSpeciesList = function() {
    $.getJSON(tm_static + 'species/json/', function(species){
        tm.speciesData = species;
        tm.setupAutoComplete($('#species_search_input'));

        if ($('#id_species_name')) {
            tm.setupAutoComplete($('#id_species_name'));
        }

        tm.generateSpeciesDropdown(tm.speciesData);
        var spec = $.query.GET("species");
        if (spec) {
            tm.updateSpeciesFields("species_search",spec, '');
        }
    });        
};

tm.buildLocationList = function() {
    $.getJSON(tm_static + 'neighborhoods/', {format:'json', list: 'list'}, function(nbhoods){
        tm.locations = nbhoods;
        tm.generateLocationDropdown(tm.locations);
    });
};

tm.resultsTemplatePageLoad = function(min_year, current_year, min_updated, max_updated, min_plot, max_plot) {    
    tm.init_map('results_map');

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
        //tm.updateSearch();
        tm.trackEvent('Search', 'Reset Advanced');
    });        
    
};


tm.generateLocationDropdown = function(locations) {
    var ul = $("<ul id='n_list' style='max-height:180px; overflow:auto;'></ul>");
    $("#searchNBList").append(ul).hide();
    var states = {}
    for(var i=0; i<locations.features.length;i++) {
        var feature = locations.features[i];
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
};

tm.generateSpeciesDropdown = function(speciesData) {
    //TODO - use css for striping
    var ul = $("<ul id='s_list' style='max-height:180px; overflow:auto;'></ul>");
    $("#searchSpeciesList").append(ul).hide();
    for(var i=0; i<speciesData.length;i++) {
        if (speciesData[i].count == 0) {continue;}
        var c = "ac_odd";
        if (i%2 == 0) {c = 'ac-even';}
        ul.append("<li id='" + speciesData[i].id + "' class='" + c + "'>" + speciesData[i].cname + " [" + speciesData[i].sname + "]</li>")
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
};

tm.baseTemplatePageLoad = function() {
    tm.buildSpeciesList();
    tm.buildLocationList();

    var adv_active = false;
    $('#advanced').click(function() {
        if (!adv_active) {
            if ($('#results').length > 0) {
                $('.filter-box').slideDown('slow');
                if (tm.open_advanced_label) { $("#close-filters").html(tm.open_advanced_label); }  
                $('#arrow').attr('src',tm_static + 'static/images/v2/arrow2.gif');
            }
            adv_active = true; 
        }    
        else {
            if ($('#results').length > 0) {
                $('.filter-box').slideUp('slow');
                if (tm.closed_advanced_label) { $("#close-filters").html(tm.closed_advanced_label); }   
                $('#arrow').attr('src',tm_static + 'static/images/v2/arrow1.gif');  
            }
            adv_active = false;       
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

    if ($("#steward-box")) {

        function openMenu(e) {
            var button = $(this).addClass('active');
            var menu = $('#' + button.attr('name'));
            var offset = button.offset();
            var h = (button.outerHeight) ? button.outerHeight() : button.height();
            menu.addClass('active').css({
                'top': offset.top + h, 'left': offset.left
            }).click(function(e) { e.stopPropagation(); }).show(200, function() {
                $(document).one('click', {button: button, menu: menu}, closeMenu);
            });
        }
        function closeMenu(e) {
            e.data.menu.removeClass('active').hide(100, function() {
                e.data.button.removeClass('active');
            });
            e.data.button.one('click', openMenu);
        }
        $('button.menu').one('click', openMenu);

        $("#steward-date-1").datepicker({maxDate: "+0D"});
        $("#steward-date-2").datepicker({maxDate: "+0D"});

        //default values
        $("#steward-action-list").empty();
        $("#steward-action-list").append("<input type='checkbox' class='steward-action' name='steward-action' value='1' /> Watered <br>");
        $("#steward-action-list").append("<input type='checkbox' class='steward-action' name='steward-action' value='2' /> Pruned <br>");
        $("#steward-action-list").append("<input type='checkbox' class='steward-action' name='steward-action' value='3' /> Mulched <br>");
        $("#steward-action-list").append("<input type='checkbox' class='steward-action' name='steward-action' value='4' /> Cleared of Debris");


        $(".steward-type").change(function() {
            if ($(".steward-type:checked").val() == "tree") {
                $("#steward-action-list").empty();
                $("#steward-action-list").append("<input type='checkbox' class='steward-action' name='steward-action' value='1' /> Watered <br>");
                $("#steward-action-list").append("<input type='checkbox' class='steward-action' name='steward-action' value='2' /> Pruned <br>");
                $("#steward-action-list").append("<input type='checkbox' class='steward-action' name='steward-action' value='3' /> Mulched <br>");
                $("#steward-action-list").append("<input type='checkbox' class='steward-action' name='steward-action' value='4' /> Cleared of Debris");
                $("#ss_2").text("trees ");
                $("#ss_5").text("... ");
            }
            else {
                $("#steward-action-list").empty();
                $("#steward-action-list").append("<input type='checkbox' class='steward-action' name='steward-action' value='1' /> Enlarged <br>");
                $("#steward-action-list").append("<input type='checkbox' class='steward-action' name='steward-action' value='2' /> Added a Guard <br>");
                $("#steward-action-list").append("<input type='checkbox' class='steward-action' name='steward-action' value='3' /> Removed a Guard <br>");
                $("#steward-action-list").append("<input type='checkbox' class='steward-action' name='steward-action' value='4' /> Herbaceous Plants");    
                $("#ss_2").text("planting sites ");
                $("#ss_5").text("... ");
            }
        });

        $(".steward-reverse").change(function() {
            if ($(".steward-reverse:checked").val() == "true") {$("#ss_4").text("have been ");}
            else {$("#ss_4").text("have not been ");}
        });
        $(".steward-action").live('change', function() {
            var actions = $(".steward-action:checked");
            var action_string = [];
            for (i=0;i<actions.length;i++) {
                var dom = actions[i];
                switch (dom.value) {
                    case "1": 
                        if ($(".steward-type:checked").val() == "tree") {action_string.push("watered");} else {action_string.push("enlarged");} break;
                    case "2": 
                        if ($(".steward-type:checked").val() == "tree") {action_string.push("pruned");} else {action_string.push("guard added");} break;
                    case "3": 
                        if ($(".steward-type:checked").val() == "tree") {action_string.push("mulched");} else {action_string.push("guard removed");} break;
                    case "4": 
                        if ($(".steward-type:checked").val() == "tree") {action_string.push("cleared");} else {action_string.push("planted");} break;
                }
            }
            if (action_string.length == 0) {$("#ss_5").text("... ")}
            else {$("#ss_5").text(action_string.join(', '))}
            
        });

        $("#steward-date-1").change(function() {
            if ($("#steward-date-1").val()) {
                $("#ss_7").text($("#steward-date-1").val());
                if (!$("#steward-date-2").val()) {
                    $("#ss_9").text("now");
                }
            } 
            else {
                $("#ss_7").text("then");
            }
            if (!$("#steward-date-1").val() && ! $("#steward-date-2").val()) {
                $("#ss_7").text("then");
                $("#ss_9").text("now");
            }
        });
        $("#steward-date-2").change(function() {            
            if ($("#steward-date-2").val()) {
                if (!$("#steward-date-1").val()) {
                    $("#ss_7").text("then");
                }
                $("#ss_9").text($("#steward-date-2").val());
            } 
            else {
                $("#ss_9").text("now");
            }
            if (!$("#steward-date-1").val() && ! $("#steward-date-2").val()) {
                $("#ss_7").text("then");
                $("#ss_9").text("now");
            }
        });
        

    }

    // todo - clean this logic up...
    if ($.urlParam('diameter') || $.urlParam('date') || $.urlParam('characteristics') ||  $.urlParam('advanced') )
    {
        //TODO: might be causing duplicate search
        $('#advanced').click();
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
        q = tm.handleStewardship(q);
        window.location.href = tm_static + "map/#" + decodeURIComponent(q.toString());
        return false;
    }  
    $("#advanced").click(function() {
        tm.advancedClick = true;
        if ($("#results").length == 0) {triggerSearch();}
    });   
    
    
    tm.add_favorite_handlers('/trees/favorites/create/', '/trees/favorites/delete/');
};    

tm.handleStewardship = function(query) {
    if ($("#steward-box")) {
        var target =  $(".steward-type:checked");
        var reverse =  $(".steward-reverse:checked");
        var actions = $(".steward-action:checked");  //could be array
        var date1 = $("#steward-date-1").datepicker("getDate");
        var date2 = $("#steward-date-2").datepicker("getDate");

        query = query.remove('tree_stewardship');
        query = query.remove('plot_stewardship');
        query = query.remove('stewardship_reverse');
        query = query.remove('stewardship_range');
        
        if (actions.length == 0) {
            return query;
        }

        var action_string = [];
        for (i=0;i<actions.length;i++) {
            action_string.push(actions[i].value);
        }

        if (target.val() == "tree") {
            query = query.set('tree_stewardship', action_string.toString());
        }
        else {
            query = query.set('plot_stewardship', action_string.toString());
        }
        if (reverse.val() == "true") {
            query = query.set('stewardship_reverse', 'NOT');
        }
        // if no dates, don't bother sending range info
        if (!date1 && !date2) {
            return query;
        }        
        if (!date1) {date1 = new Date(1970,1,1)}
        if (!date2) {date2 = new Date()}
        query = query.set('stewardship_range', (date1.getTime()/1000).toString() + "-" + (date2.getTime()/1000).toString())
    }
    return query;
}

