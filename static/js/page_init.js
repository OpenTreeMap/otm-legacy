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

        if (tm.setup_polygon_edit_species) {
            tm.setup_polygon_edit_species();
        }
    });
};

tm.buildLocationList = function() {
    $.getJSON(tm_static + 'neighborhoods/list/', {}, function(nbhoods){
        tm.generateLocationDropdown(nbhoods);
    });
};

tm.getChoicesList = function() {
    $.getJSON(tm_static + 'choices/', function(choices) {
        tm.choices = choices;
    });
}

tm.getHomeFeeds = function(callback) {
    $.getJSON(tm_static + "home/feeds/json/", function(feeds) {
        tm.homeFeeds = feeds;
        if (callback) {callback();}
    });
}

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
        if (this.value != "") {
            tm.searchParams[this.id] = this.value;
        } else {
            delete tm.searchParams[this.id];
        }

    });
    var curmin = 0;
    var curmax = 50;
    $("#diameter_slider").slider({'range': true, max: 75, min: 0, values: [0, 75],
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
    if ($("#planted_slider").length) {
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
    }

    if ($("#updated_slider").length) {
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
    }
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
        $("#diameter_slider").slider('option', 'values', [0, 75]);
        $('#min_diam').html(0);
        $('#max_diam').html(75);
        $("#planted_slider").slider('option', 'values', [min_year, current_year]);
        $("#updated_slider").slider('option', 'values', [min_updated, max_updated]);
        if ($("#planted_slider").length) {
            $("#planted_slider")[0].updateDisplay();
        }
        if ($("#updated_slider").length) {
            $("#updated_slider")[0].updateDisplay();
        }
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
        tm.searchParams = {}

        $("#options_form input:checked").attr('checked', false)
        tm.trackEvent('Search', 'Reset Advanced');
    });

};


tm.generateLocationDropdown = function(locations) {
    var ul = $("<ul id='n_list' style='max-height:180px; overflow:auto;'></ul>");
    $("#searchNBList").append(ul).hide();
    var states = {}
    for(var i=0; i<locations.length;i++) {
        var feature = locations[i];
        var st_co = feature.state + "-" + feature.county;
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
            var name = entries[i].name;
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
                var name = entries[i].name;
                var id = entries[i].id;
                select_nh.append("<option value='" + id + "' >" + name + "</li>")
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
        ul.append("<li id='" + speciesData[i].id + "' class='" + c + "'>" + tm.formatTreeName(speciesData[i]) + "</li>")
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
    tm.getChoicesList();

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

    $('a.search-suggestion').live('click', function(event) {
        $("#location_search_input").val($(this).text()).change();
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
                delete tm.searchParams['lat'];
                delete tm.searchParams['lon'];
                if (tm.misc_markers) {tm.misc_markers.clearMarkers();}
                if (tm.map) {
                    tm.map.setCenter(
                        new OpenLayers.LonLat(treemap_settings.mapCenterLon, treemap_settings.mapCenterLat).transform(new OpenLayers.Projection("EPSG:4326"), tm.map.getProjectionObject())
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

    if (tm.init_stewardship) {
        tm.init_stewardship();
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
        if (tm.advancedClick) {
            q = q.set('advanced', 'open');
        }
        if (tm.handleStewardship) {
            q = tm.handleStewardship(q);
        }
        window.location.href = tm_static + "map/#" + decodeURIComponent(q.toString());
        return false;
    }
    $("#advanced").click(function() {
        tm.advancedClick = true;
        if ($("#results").length == 0) {triggerSearch();}
    });


    //tm.add_favorite_handlers('/trees/favorites/create/', '/trees/favorites/delete/');
};
