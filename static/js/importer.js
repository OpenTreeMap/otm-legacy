/** Importer namespace **/
var I = {};

(function($,I,TM) {

    I.views = {};
    I.api = {};
    I.constants = {};

    I.constants.species_fields = ['genus', 'species', 'cultivar',
                                  'other part of scientific name'];

    var loadTemplateCache = {};
    function loadTemplate(t) {
        if (loadTemplateCache[t]) {
            return loadTemplateCache[t];
        } else {
            loadTemplateCache[t] = _.template($("#" + t).html());
            return loadTemplateCache[t];
        }
    };

    I.loadTemplate = loadTemplate;

    /** Dummy function (for now) **/
    I.signalError = function(error) {};

    /**
     * Species editing
     */

    /**
     * This needs to be refactored - not a great start
     *
     * Instead we should use the 'active' panel
     *
     * panelf is a function that is evaluated when the event handler
     * is called to get the current panel information
     */
    I.views.createMergeDialogHandler = function (panelf) {
        return function (evt) {
            var panel = panelf();
            var rowid = $(this).data('row');
            var matches = _.filter(panel.data.rows, function(row) { return row.row == rowid; });
            var data = matches[0];

            /** There must be a better way than empty()/append() **/
            I.rt.merge_dialog.find('.icontent').empty();
            I.rt.merge_dialog.find('.icontent').append(
                I.views.createMergeDialog(panel, data));
            I.rt.merge_dialog.dialog('open');
        };
    };


    /**
     * Wrap a checkbox click in the merge table
     * to provide more context.
     *
     * The given function f will be called
     * with a dictionary such as:
     * { value: <value>,
     *   row:   <row index>,
     *   field: <field to update>,
     *   midx: <index of the selected species>
     * }
     *
     */
    function wrapCheckboxEventWithInfo(f) {
        return function (evt) {
            var $t = $(this);
            var $td = $t.parent('td');
            var idx = _.indexOf($t.parents('tr').find('td'), $td[0]);
            var value = $td.text().trim();
            var field = $t.parents('tr').data('field');
            var row = $t.parents('table').data('row');
            f({ value: value,
                field: field,
                midx: idx - 1,
                row: row });
        };
    }

    /** Check and uncheck the right checkboxes */
    function updateCheckboxState(rowModel, $root) {
        _.each(rowModel.data, function(f) {
            var inputs = $root.find('tr[data-field="' + f.field + '"] input');
            _.map(inputs, function(inp, idx) {
                $(inp)
                    .prop('checked', idx == f.selected)
                    .prop('disabled', idx == f.selected);
            });
        });
    }

    I.views.createMergeDialog = function(panel, row) {
        var mergeModels = panel.mergeModel;

        if (!mergeModels) {
            mergeModels = I.createSpeciesMergeModel(panel);
            panel.mergeModel = mergeModels;
        }

        var rowModel = mergeModels.data[row.row];
        var rowData = {};
        for (var i=0;i<rowModel.data.length;i+=1) {
            rowData[rowModel.data[i].field] = rowModel.data[i];
        }
        rowModel.indexed_data = rowData;

        var $merge = $(
            _.template($("#merge-template").html(),
                       { 'fields': rowModel,
                         'field_order': panel.data.field_order }));

        // Select the correct checkboxes
        updateCheckboxState(rowModel, $merge);

        // Assign click handers for checkboxes
        $merge.find('input[type=checkbox]')
            .click(wrapCheckboxEventWithInfo(function(info) {
                // First handle outside data
                var fidx = _.indexOf(panel.data.fields, info.field);
                row.data[fidx] = info.value;

                // Now update the rowModel
                rowModel.data[fidx].selected = info.midx;

                // Update state of the checkbox for this merge window
                updateCheckboxState(rowModel, $merge);

                // Re-render the whole darn view
                replacePaneView(panel)(I.views.renderTable(panel));
            }));

        // Assign button handlers
        $merge.find('button').click(function() {
            var speciesid = $(this).data('matches');
            var rowidx = $(this).parents('table').data('row');

            I.api.resolveMergeConflict(
                I.importevent, rowidx, speciesid,
                _.zip(panel.data.fields, row.data))
                .done(function() {
                    // Update each pane since any data could've
                    // changed
                    _.map(I.rt.panels, I.updatePane);
                });

            // TODO: Poking out into global land....
            I.rt.merge_dialog.dialog('close');
        });

        return $merge;

    };


    /**
     * Given a panel create a model for merging species
     *
     * The model is a dict that looks something like:
     *
     * Note that if needsMerge is false, we don't need to
     * provide checkbox for that line
     *
     * {
     * data:
     *   [{'selected': <0-N>,
     *     'needsMerge': <boolean>
     *     'field': <field name>,
     *     'data': ['value 1', 'value 2', ...]}
     *     'header': ['Field', 'Orig', 'Match 1', 'Match ...', ...],
     *     'keys': [<species existing key1>, <species existing key 2>, ...]
     *   ...],
     *
     *  onRowChange: <function>,
     *  onMergeSpeciesButtonClick: <function>
     * }
     *
     */
    I.createSpeciesMergeModel = function(panel) {
        var data = panel.data;
        var rows = data.rows;

        // Generate model for each row
        var mergerows = _.map(rows, function(row) {
            // How many columns do we need to make?
            var diffs = row.diffs;
            var cols = diffs.length;

            // Generate column names
            var colNames = concat(
                ['Import Value'],
                _.range(1,cols+1).map(function(i) { return 'Match ' + i; }));

            var ids = _.pluck(
                _.pluck(diffs, 'id'), 0);

            var mergeData = _.zip(data.fields, row.data)
                    .map(function(fieldcelldata) {
                        var field = fieldcelldata[0];
                        var cellValue = fieldcelldata[1];

                        var mergefld = {};
                        mergefld.field = field;

                        // By default the import csv data is selected
                        mergefld.selected = 0;

                        // Check to see if we have any interesting diffs
                        var mergedata = [cellValue].concat(
                            _.chain(diffs)
                            .pluck(field)
                            .map(function(fld) { return fld? fld[0] : cellValue; })
                            .value());

                        // If all of the values are the same this field
                        // does not need to be merged
                        var foundDifferentValue =
                                _.some(mergedata, function(m)
                                       { return m != cellValue; });

                        mergefld.needsMerge = foundDifferentValue;
                        mergefld.data = mergedata;

                        return mergefld;
                    });

            return {
                'keys': ids,
                'header': colNames,
                'data': mergeData,
                'rowidx': row.row
            };
        });

        var mergedict = {};
        _.each(mergerows, function(mr) {
            mergedict[mr.rowidx] = mr;
        });

        return {
            data: mergedict,
            onRowChange: function(a) { return a; },
            onMergeSpeciesButtonClick: function(a) { return a; }
        };
    };

    I.views.updateListTableWithNewData = function(table, data) {
        _.map(data, function(counts, id) {
            var $tr = $(table).find("tr[data-id=" + id + "]");
            var $td = $(table).find("td[data-count]");

            var total = $td.data('count');

            // 3 => Number of pending records
            var pct = parseInt((1.0 - counts["3"] / total) * 1000.0) / 10.0;

            // Django can do the work
            $td.text((total - counts["3"]) + "/" + total + " (" + pct + "%)");
        });
    };

    /**
     * Get possible species matches
     */
    I.api.getSpeciesMatches = function(tgt) {
        return $.ajax(I.api_base + 'species/similar?target=' + tgt)
            .fail(I.signalError);
    };


    /**
     * Getting update counts
     *
     * Returns deferred obj
     */
    I.api.getUpdatedCounts = function () {
        return $.ajax(I.api_prefix + 'counts')
            .fail(I.signalError);
    };

    /**
     * Basic tree editing and shared code
     */

    /**
     * Commit the current edit
     *
     * @param importevent int the id of the import event
     */
    I.api.commitEdit = function(importevent) {
        return $.ajax(I.api_prefix + importevent + '/commit')
            .fail(I.signalError);
    };

    /**
     * Resolve a species merge conflict
     *
     * @param importevent
     * @param importrowidx
     * @param speciesid The species id or <new>
     * @param data updated data (array of key-value pairs)
     *
     * @return deferred ajax object
     */
    I.api.resolveMergeConflict = function(importevent, importrowidx, speciesid, data) {
        return $.ajax({
            url: I.api_prefix + importevent + '/' + importrowidx + '/solve',
            type: "POST",
            data: {
                data: JSON.stringify(data),
                species: speciesid
            }
        }).fail(I.signalError);
    };

    /**
     * Fetch a set of results from the server
     *
     * @param rslt_type { 'success', 'pending', 'error', 'watch' }
     * @param importevent int the id of the import event
     * @param page int the page of results to select
     *
     * @return deferred ajax object
     */
    I.api.fetchResults = function(rslt_type, importevent, page) {
        return $.ajax({
            url: I.api_prefix + importevent + '/results/' + rslt_type,
            data: {
                page: page || 0
            }});
    };

    /**
     * Fetch the next set of data for a given panel
     *
     * @param panel to fetch
     * @return deferred ajax object
     */
    I.api.fetchPanel = function(panel) {
        return I.api.fetchResults(panel.request_key, I.importevent, panel.page);
    };

    /**
     * Update a row and rerun verification
     *
     * @param row the row data to update
     */
    I.api.updateRow = function(row) {
        return $.ajax({
            url: I.api_prefix + I.importevent + '/update',
            data: {
                'row': JSON.stringify(row)
            }
        });
    };

    function concat(a,b) {
        return a.concat(b);
    }

    function extract_error_fields(row) {
        return _.chain(row.errors)
            .filter(function(r) { return r['fatal']; })
            .reduce(function(h,f) {
                return _.reduce(f.fields, function(hh, fld) {
                    hh[fld] = f; return hh;
                }, h);
            }, {})
            .value();
    }

    function extract_warning_fields(row) {
        return _.chain(row.errors)
            .filter(function(r) { return !r['fatal']; })
            .reduce(function(h,f) {
                return _.reduce(f.fields, function(hh, fld) {
                    hh[fld] = f; return hh;
                }, h);
            }, {})
            .value();
    }

    /**
     * Given the result of a fetch, render a new table and return
     * wrapped jquery object
     *
     * TODO: This is a bit burly... refactor to use regular templates
     *
     * @param rows panel to render
     */
    I.views.renderTable = function(panel) {
        var rows = panel.data;
        var header = '<th>Row #</th>';

        var datarow_tmpl = _.template(
            '<tr data-row="<%= row.row %>"><td><%= row.row + 1 %></td></tr>');

        var empty_table_row_tmpl = _.template(
            '<tr><td class="text-center" colspan="<%= rows.fields.length + 1 %>">' +
                'No Rows</td></tr>');

        if (panel.name == 'success' &&
           I.import_type == 'trees') {
            header += '<th>Plot</th>';
        }

        header = _.chain(panel.data.field_order)
            .map(function(f) { return '<th>' + f + '</th>'; })
            .reduce(concat, header)
            .value();

        var table = $('<table class="table table-condensed table-bordered">\n<tr>' + header + '</tr>\n');

        if (rows.count == 0) {
            table.append(empty_table_row_tmpl({rows:rows}));
        } else {
            table = _.reduce(
                rows.rows,
                function(table,row) {
                    // Select error fields
                    var errors = extract_error_fields(row);
                    var warnings = extract_warning_fields(row);

                    var $tr = $(datarow_tmpl({row: row}));

                    if (panel.name == 'success' &&
                       I.import_type == 'trees') {
                        //TODO: Need to use static field here
                        $tr.append('<td><a href="/plots/' + row.plot_id + '">' +
                                   'Plot #' + row.plot_id + '</a></td>');
                    }

                    // Key data by field name
                    var rowdata = {};
                    for (var i=0;i<row.data.length;i++) {
                        var key = rows.fields[i];
                        var fld = row.data[i];
                        rowdata[key] = fld;
                    }

                    for (var i=0;i<panel.data.field_order.length;i++) {
                        var key = panel.data.field_order[i];
                        var fld = rowdata[key];

                        var $td = $('<td></td>');
                        if (errors[key]) {
                            $td.addClass('error');
                            $td.click(I.createErrorClickHandler(
                                $td, rows.fields, row, errors[key], key, fld));

                        } else if (warnings[key]) {
                            $td.addClass('warning');

                            // Don't show errors on the merge panel
                            if (panel.name != "mergereq") {
                                $td.click(I.createWarningClickHandler(
                                    $td, row, warnings[key], fld));
                            }
                        }

                        $td.html('' + fld);
                        $tr.append($td);
                    }

                    if (panel.clickHandler) {
                        $tr.click(panel.clickHandler);
                    }

                    return table.append($tr);

                }, table);
        }

        var $html = $('<div></div>');
        return $html
            .append($('<div class="tablepanel"></div>').append(table))
            .append(I.views.createPager(panel));
    };

    // Modifies page state
    function closeErrorPopups() {
        // Remove old error popups
        $(".error-popup").remove();
    };


    I.createErrorClickHandler = function($td, flds, row, errors, fld, val) {
        return function() {
            // Remove old error popups
            closeErrorPopups();

            var popover = _.template($('#error-template').html(), {
                height: 200,
                header: errors['msg'],
                content: ''});

            var $popover = $(popover);
            if (_.contains(I.constants.species_fields, fld)) {
                var content = 'Looking for similar species...';
                $popover.find('.popover-content').html(content);

                getContentForSpeciesError(flds, row, fld, val, errors)
                    .done(function(content) {
                        $popover.find('.popover-content')
                                      .empty()
                                      .append(content);

                        resizePopovers();

                        // Don't trigger td click handlers
                        $popover.click(function(e) { e.stopPropagation(); });
                    });
            } else {
                var $content = getContentForGenericError(
                    flds, row, fld, val);

                $popover.find('.popover-content')
                    .empty()
                    .append($content);

                $popover.click(function(e) { e.stopPropagation(); });
            }

            $(this).parent().parent().parent().parent().parent().append($popover);
            var tdH = $(this).height(),
                tdW = $(this).width(),
                tdX = $(this).position().left + (tdW/2) - 100,
                tdY = $(this).position().top + tdH;
            resizePopovers(tdX, tdY);
        };
    };

    function getContentForGenericError(flds, row, fld, val) {
        var $content = $(loadTemplate('generic-error')({
            value: val,
            field: fld
        }));

        $content.find(".cancel").click(function(e) {
            closeErrorPopups();
            e.stopPropagation(); // Seems like a hack?
        });
        $content.find(".update").click(function(e) {
            var sln = {};
            sln.transform = function(row) {
                row[fld] = $content.find('input').val();

                return row;
            };

            commitRowWithSolution(flds, row, sln);

            closeErrorPopups();
            e.stopPropagation(); // Seems like a hack?
        });

        return $content;
    };

    // side-effecting function
    function resizePopovers(tdX, tdY) {
        var $popover = $('.error-popup');
        var titleHeight = $popover.find('.popover-title').height();
        var contentHeight = $popover.find('.popover-content').height();

        $popover.height(contentHeight + titleHeight + 38);
        $popover.css({
          'top': tdY + "px",
          'left': tdX + "px"
        });
    };

    function getContentForMoreSpeciesOptions(flds, row) {
        var source = _.map(TM.speciesData, function(d) {
            var sciname = d.genus + ' ' + d.species + ' ' + d.cultivar + ' ' + d.other_part;
            return d.cname + " [" + sciname + "]";
        });

        var $content = $(loadTemplate("species-error-more-content")({
            species: source
        }));

        function updateDropDown(event, ui) {
            $content.find(".specieslist")
                .val($content
                     .find(".speciesbyname")
                     .val());
        }

        $content.find(".speciesbyname")
            .autocomplete({
                source: source,
                change: updateDropDown
            });

        $content.find(".cancel").click(function(e) {
            closeErrorPopups();
            e.stopPropagation(); // Seems like a hack?
        });

        $content.find(".select").click(function(e) {
            var i =_.indexOf(source, $content.find(".specieslist").val());
            var d = TM.speciesData[i];

            var sln = {};
            sln.transform = function(row) {
                row.genus = d.genus;
                row.species = d.species;
                row.cultivar = d.cultivar;
                row['other part of scientific name'] = d.other_part;

                return row;
            };

            commitRowWithSolution(flds, row, sln);

            closeErrorPopups();
            e.stopPropagation(); // Seems like a hack?
        });

        return $content;
    };

    function getContentForSpeciesError(flds, row, fld, val, error) {
        return getSolutionsForSpeciesError(fld, val, error)
            .pipe(function (slns) {
                var best = slns[0];
                var $error = $(loadTemplate("species-error-content")({
                    possible: best['new_val']
                }));

                var $more = getContentForMoreSpeciesOptions(flds, row);

                // Wire up events
                $error.find(".cancel").click(function(e) {
                    closeErrorPopups();
                    e.stopPropagation(); // Seems like a hack?
                });
                $error.find(".moreoptions").click(function(e) {
                    $error.empty()
                        .append($more);

                    resizePopovers();

                    e.stopPropagation(); // Seems like a hack?
                });
                $error.find(".yes").click(function(e) {
                    commitRowWithSolution(flds, row, best);
                    closeErrorPopups();

                    e.stopPropagation(); // Seems like a hack?
                });
                return $error;
            });
    };

    /**
     * Update the given row with a particular solution
     */
    function commitRowWithSolution(flds, row, sln) {
        var r = sln['transform'](_.object(flds, row));
        r.id = row.row;
        I.api.updateRow(r).done(function() {
            _.map(I.rt.panels, I.updatePane);
        });
    };

    /**
     * Get a list of solutions for a species error. A single solution
     * is a dict of: 'old_val', 'new_val', 'transformer'.
     *
     * [old|new]_val is a string of the [old|new] value
     * transformer is a function that takes in the row data
     * and returns a new row data
     *
     * This method may make calls to the server and this returns
     * a deffered object
     */
    var species_memo;
    function getSolutionsForSpeciesError(fld, val, error) {
        // No need to make a bunch of extra round trips for
        // no reason
        species_memo = species_memo || {};

        if (species_memo[error.data]) {
            return $.when(species_memo[error.data]);
        }

        function createRowTransformer(keys, d) {
            return function(row) {
                var rslt = {};
                _.each(keys, function(key) {
                    rslt[key] = d[key];
                });
                return rslt;
            };
        }

        // Need to talk to the server to grab species
        // types
        return I.api.getSpeciesMatches(error.data)
            .pipe(function(data) { // Build solutions here
                return _.map(data, function(match) {
                    var newval = _.reduce(I.constants.species_fields,
                                          function(s,k) { return s + match[k] + ' '; },
                                          '');

                    return { 'old_val': val,
                             'new_val': newval,
                             'transform': createRowTransformer(
                                 I.constants.species_fields, match)
                           };
                });
            })
            .done(function(rslt) { // Memoize for future use
                species_memo[error.data] = rslt;
            });
    };

    I.createWarningClickHandler = function($td, row, warnings, fld) {
        return function() {
            // Remove old error popups
            $(".error-popup").remove();

            var $popover = $(_.template($('#error-template').html(), {
                height: 200,
                header: 'Warning',
                content: warnings['msg']}));

            $(this).append($popover);
            resizePopovers();
        };
    };

    I.views.createPager = function (panel) {
        var total_pages = panel.data.total_pages;
        var start_page = _.max([panel.page - 5, 0]);

        var $pager = $(_.template($('#pager-template').html(), {
            page: panel.page,
            start_page: start_page,
            end_page: _.min([total_pages,start_page + 10])
        }));

        $pager.find('a').click(function() {
            var current_page = panel.page;
            var txt = $(this).text().trim();

            if (txt == '<') {
                panel.page = current_page == 0? 0 : current_page - 1;
            } else if (txt == '<<') {
                panel.page = 0;
            } else if (txt == '>') {
                panel.page = (current_page + 1 >= total_pages)? current_page :
                    current_page + 1;
            } else if (txt == '>>') {
                panel.page = total_pages - 1;
            } else {
                panel.page = parseInt(txt) - 1;
            }

            // Only update if something changed
            if (current_page != panel.page) {
                I.updatePane(panel);
            }
        });

        return $pager;
    };


    /**
     * Create a function that binds to events that
     * update the tab headers' row counts
     */
    I.views.rowCountUpdater = function (pane) {
        return function(rows) {
            var count = "";
            if (rows.count >= 0) {
                count = ' (' + rows.count + ')';
                pane.count = rows.count;
            }

            pane.$tab.find('a').html(pane.display_name + count);

            return rows;
        };
    };

    /**
     * Get a function that can be used to replace
     * a given pane's view
     *
     * @param pane the panel to replace
     *
     * @returns function that takes in new content for 'pane'
     */
    function replacePaneView(pane) {
        return function(v) {
            pane.$content.empty().append(v);
        };
    };

    /**
     * Generate a setter function
     */
    function setter(obj, key) {
        return function (value) {
            obj[key] = value;
            return obj;
        };
    };

    I.updateIfPendingOrVerified = function (pane) {
        var pname = '';
        // this isn't great but works
        // shouldn't reference runtime variables here
        if (I.rt.mode === 'create') {
            pname = 'verified';
        } else {
            pname = 'pending';
        }

        if (pane.name === pname && pane.data.count > 0) {
            setTimeout(function() {
                _.map(I.rt.panels, I.updatePane);
            }, 10000);
        }

        return pane;
    };

    /**
     * Update a given panel
     */
    I.updatePane = function (pane) {
        I.api.fetchPanel(pane)
            .done(I.views.rowCountUpdater(pane))
            .pipe(setter(pane, 'data'))
            .pipe(I.updateIfPendingOrVerified)
            .pipe(I.views.renderTable)
            .pipe(replacePaneView(pane))
            .fail(I.signalError);
    };

    /**
     * Pick a particular pane to show
     *
     * @param pane panel to show
     * @param allpanes list of all of the panels (must include pane)
     */
    I.setVisiblePanel = function (pane, allpanes) {
        _.map(allpanes, function(p) {
            if (p === pane) {
                p.active = true;
                p.$tab.addClass('active');
                p.$content
                    .addClass('visible-pane')
                    .removeClass('invisible-pane');
            } else {
                p.active = false;
                p.$tab.removeClass('active');
                p.$content
                    .removeClass('visible-pane')
                    .addClass('invisible-pane');
            }
        });
    };

    function createTabPanel(parent, pane) {
        var tab = _.template('<li><a href="#" id="<%= pane.name %>-tab">' +
                             '<%= pane.display_name %></a></li>',
                             { pane: pane });

        var content = $('<div id="' + pane.name + '" class="tabpane"></div>');

        pane.$tab = $(tab);
        pane.$content = content;

        parent.find('.tabbar').append(pane.$tab);
        parent.find('.tabpanel').append(content);

        return parent;
    };

    function createTabContainer() {
        return $('<div>\n  ' +
                 '<ul class="nav nav-pills tabbar"></ul>\n  ' +
                 '<div class="tabpanel"></div>');
    };

    /**
     * Create basic tab structure
     */
    I.views.createTabs = function (panels) {
        return _.reduce(panels, createTabPanel, createTabContainer());
    };

}($,I,tm));

I.init = {};
I.init.status = function() {

    I.importevent = window.location.pathname.match('/([a-z]+)/([0-9]+)$')[2];
    I.import_type = window.location.pathname.match('/([a-z]+)/([0-9]+)$')[1];
    I.api_base = tm_urls.site_root + 'importer/api/';
    I.api_prefix = tm_urls.site_root + 'importer/api/' + I.import_type + '/';

    /**
     * Runtime layout and information
     */
    I.rt = {
        tree_panels: {
            verified: {
                request_key: 'verified',
                name: 'verified',
                display_name: 'Ready to Add',
                page: 0
            },
            errors: {
                request_key: 'error',
                name: 'errors',
                display_name: 'Errors',
                page: 0
            },
            treewatch: {
                request_key: 'watch',
                name: 'treewatch',
                display_name: 'Tree Watch',
                page: 0
            },
            success: {
                request_key: 'success',
                name: 'success',
                display_name: 'Successfully Added',
                page: 0
            },
            pending: {
                request_key: 'waiting',
                name: 'pending',
                display_name: 'Pending',
                page: 0
            }
        },
        species_panels: {
            newspecies: {
                request_key: 'verified',
                name: 'verified',
                display_name: 'Ready to Add',
                page: 0
            },
            merge_req: {
                request_key: 'mergereq',
                name: 'mergereq',
                display_name: 'Merge Required',
                page: 0
            },
            errors: {
                request_key: 'error',
                name: 'errors',
                display_name: 'Errors',
                page: 0
            },
            success: {
                request_key: 'success',
                name: 'success',
                display_name: 'Successfully Added',
                page: 0
            }
        }

    };

    I.rt.species_panels.merge_req.clickHandler =
        I.views.createMergeDialogHandler(function() { return I.rt.panels.merge_req; });

    if (I.import_type == 'species') {
        I.rt.panels = I.rt.species_panels;
    } else {
        I.rt.panels = I.rt.tree_panels;
    }

    /** Create Dialog **/
    I.rt.merge_dialog = $('<div id="merge-dialog"><div class="icontent"></div></div>');
    $("body").append(I.rt.merge_dialog);
    I.rt.merge_dialog.dialog({
        autoOpen: false,
        width: 600
    });

    /** Init tabs **/
    $("#tabs").append(I.views.createTabs(I.rt.panels));

    // Wire up 'create' button
    $("#createtrees").click(function() {
        I.rt.mode = 'create';
        I.api.commitEdit(I.importevent)

        window.location =
            window.location.pathname.match('(.*/importer/).*$')[1];
    });

    // Initially show first panel
    I.setVisiblePanel(I.rt.panels.verified || I.rt.panels.merge_req, I.rt.panels);

    // Wire up click listeners
    _.map(I.rt.panels, function(panel) {
        panel.$tab.click(function() {
            I.setVisiblePanel(panel, I.rt.panels);
        });
    });

    // Update each pane to grab initial data
    _.map(I.rt.panels, I.updatePane);

};

I.init.list = function() {
    I.api_prefix = tm_urls.site_root + 'importer/api/';

    // Auto-updater
    var numPrevSpeciesCounts = -1;
    var numPrevTreeCounts = -1;

    function update_counts() {
        if ($("tr[data-running=true]").length > 0) {
            I.api.getUpdatedCounts()
                .done(function(c) {
                    if ((numPrevSpeciesCounts > 0 &&
                         _.keys(c.species).length != numPrevSpeciesCounts) ||
                        (numPrevTreeCounts > 0 &&
                         _.keys(c.trees).length != numPrevTreeCounts)) {
                        document.location.reload(true);
                    }


                    I.views.updateListTableWithNewData($("#activetree"), c['trees']);
                    I.views.updateListTableWithNewData($("#activespecies"), c['species']);

                    numPrevSpeciesCounts = _.keys(c.species).length;
                    numPrevTreeCounts = _.keys(c.trees).length;

                    if (numPrevSpeciesCounts + numPrevTreeCounts > 0) {
                        setTimeout(update_counts, 5000);
                    }
                });
        }
    }

    // Create unit types dialog
    var conversions =
        { "Inches" : 1.0,
          "Meters": 39.3701,
          "Centimeters": 0.393701 };

    function setupUnitsDialog($unitsDialog, $submit, $form) {

        var $select = _.reduce(conversions, function ($sel,factor,label) {
            return $sel.append($("<option>")
                               .attr("value",factor)
                               .text(label));
        }, $("<select>"));

        $unitsDialog.find("tr").each(function (i,row) {
            if (i > 0) {
                $(row).append($("<td>").append($select.clone()));
            }
        });

        $("body").append($unitsDialog);

        $unitsDialog.dialog({
            autoOpen: false,
            width: 350,
            modal: true
        });

        $submit.click(function() {
            $unitsDialog.dialog('open');
        });

        $unitsDialog.find(".cancel").click(function() {
            $unitsDialog.dialog('close');
        });

        $unitsDialog.find(".create").click(function() {
            var fields = {};
            // Extract field values
            $unitsDialog.find("tr").each(function (i,row) {
                if (i > 0) {
                    var tds = $(row).find("td");
                    fields["unit_" + tds.first().html().replace(" ","_").toLowerCase()] =
                        tds.last().find("select").val();
                }
            });

            // Update hidden format fields
            _.each(fields, function(val,label) {
                $form.find("input[name=" + label  + "]")
                    .attr("value", val);
            });

            $form.submit();
        });
    }


    setupUnitsDialog($("#treeunitsdialog"),
                    $("#submittree"),
                    $("#treeform"));

    setupUnitsDialog($("#speciesunitsdialog"),
                    $("#submitspecies"),
                    $("#speciesform"));


    // Start the updater
    update_counts();

};

$(function() { I.init[_.last(window.location.pathname.match('/importer/([a-z]+)')) || "list"](); });
