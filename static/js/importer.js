
/** Importer namespace **/
var I = {
    importevent: window.location.pathname.match('/([0-9]+)')[1]
};

(function($,I) {

    /** Dummy function (for now) **/
    I.signalError = function(error) {};

    /**
     * Commit the current edit
     *
     * @param importevent int the id of the import event
     */
    I.commitEdit = function(importevent) {
        return $.ajax('/importer/api/' + importevent + '/commit');
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
    I.fetchResults = function(rslt_type, importevent, page) {
        return $.ajax({
            url: '/importer/api/' + importevent + '/results/' + rslt_type,
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
    I.fetchPanel = function(panel) {
        return I.fetchResults(panel.request_key, I.importevent, panel.page);
    };

    I.views = {};

    function concat(a,b) {
        return a.concat(b);
    }

    /**
     * Given the result of a fetch, render a new table and return
     * wrapped jquery object
     *
     * @param rows panel to render
     */
    I.views.renderTable = function(panel) {
        var rows = panel.data;
        var header = '<th>Row #</th>';

        if (panel.name == 'success') {
            header += '<th>Plot</th>';
        }

        header = _(rows.fields)
            .map(function(f) { return '<th>' + f + '</th>'; })
            .reduce(function(a,b) { return a + b; }, header);

        var html = $('<table class="table table-condensed table-bordered">\n<tr>' + header + '</tr>\n');

        if (rows.count == 0) {
            html.append('<tr><td class="text-center" colspan="' +
                        (rows.fields.length + 1) +
                        '">No Rows</td></tr>');
        } else {
            html = _.reduce(
                rows.rows,
                function(html,row) {
                    // Select error fields
                    var errors = _(row.errors)
                            .filter(function(r) { return r['fatal']; })
                            .map(function(r) { return r['fields']; })
                            .reduce(concat, [])
                            .reduce(function(h,f) { h[f] = 1; return h; }, {});

                    var warnings = _(row.errors)
                            .filter(function(r) { return !r['fatal']; })
                            .map(function(r) { return r['fields']; })
                            .reduce(concat, [])
                            .reduce(function(h,f) { h[f] = 1; return h; }, {});

                    var $tr = $('<tr><td>' + (row.row + 1) + '</td></tr>');

                    if (panel.name == 'success') {
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
                        $td.html(fld);
                        $tr.append($td);
                    }

                    return html.append($tr);

                }, html);
        }

        return html;
    };

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

    /**
     * Update a given panel
     */
    I.updatePane = function (pane) {
        I.fetchPanel(pane)
            .done(I.views.rowCountUpdater(pane))
            .pipe(setter(pane, 'data'))
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
                p.$tab.addClass('active');
                p.$content
                    .addClass('visible-pane')
                    .removeClass('invisible-pane');
            } else {
                p.$tab.removeClass('active');
                p.$content
                    .removeClass('visible-pane')
                    .addClass('invisible-pane');
            }
        });
    };

    function createTabPanel(parent, pane) {
        var tab = $('<li>' +
                    '<a href="#" id="' + pane.name + '-tab">' +
                    pane.display_name +
                    '</a>' +
                    '</li>');

        var content = $('<div id="' + pane.name + '" class="tabpane"></div>');

        pane.$tab = tab;
        pane.$content = content;

        parent.find('.tabbar').append(tab);
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
        panels: {
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
        }
    };

    $("#tabs").append(I.views.createTabs(I.rt.panels));

    // Wire up 'create' button
    $("#createtrees").click(function() {
        I.commitEdit(I.importevent)
            .done(function () { _.map(I.rt.panels, I.updatePane); });
    });

    // Initially show 'verified' panels
    I.setVisiblePanel(I.rt.panels.verified, I.rt.panels);

    // Wire up click listeners
    _.map(I.rt.panels, function(panel) {
        panel.$tab.click(function() {
            I.setVisiblePanel(panel, I.rt.panels);
        });
    });

    // Update each pane to grab initial data
    _.map(I.rt.panels, I.updatePane);



});
