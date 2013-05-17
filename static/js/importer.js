/** Importer namespace **/
var I = {
    importevent: window.location.pathname.match('/([a-z]+)/([0-9]+)')[2],
    import_type: window.location.pathname.match('/([a-z]+)/([0-9]+)')[1]
};

I.api_prefix = '/importer/api/' + I.import_type + '/';

(function($,I) {

    I.views = {};
    I.api = {};

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

        var $merge = $(
            _.template($("#merge-template").html(),
                       { 'fields': rowModel}));

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

    function concat(a,b) {
        return a.concat(b);
    }

    function extract_error_fields(row) {
        return _(row.errors)
            .filter(function(r) { return r['fatal']; })
            .map(function(r) { return r['fields']; })
            .reduce(concat, [])
            .reduce(function(h,f) { h[f] = 1; return h; }, {});
    }

    function extract_warning_fields(row) {
        return _(row.errors)
            .filter(function(r) { return !r['fatal']; })
            .map(function(r) { return r['fields']; })
            .reduce(concat, [])
            .reduce(function(h,f) { h[f] = 1; return h; }, {});
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

        header = _(rows.fields)
            .map(function(f) { return '<th>' + f + '</th>'; })
            .reduce(concat, header);

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

                    for (var i=0;i<row.data.length;i++) {
                        var key = rows.fields[i];
                        var fld = row.data[i];

                        var $td = $('<td></td>');
                        if (errors[key]) {
                            $td.addClass('error');
                        } else if (warnings[key]) {
                            $td.addClass('warning');
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

}($,I));


$(function() {
    /**
     * Runtime layout and information
     */
    I.rt = {
        tree_panels: {
            success: {
                request_key: 'success',
                name: 'success',
                display_name: 'Success',
                page: 0
            },
            pending: {
                request_key: 'waiting',
                name: 'pending',
                display_name: 'Pending',
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
            verified: {
                request_key: 'verified',
                name: 'verified',
                display_name: 'Verified',
                page: 0
            }
        },
        species_panels: {
            success: {
                request_key: 'success',
                name: 'success',
                display_name: 'Success',
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
            newspecies: {
                request_key: 'verified',
                name: 'verified',
                display_name: 'Ready to Create',
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
            .done(function () { _.map(I.rt.panels, I.updatePane); });

        // Start the update engine
        _.map(I.rt.panels, I.updatePane);
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

});
