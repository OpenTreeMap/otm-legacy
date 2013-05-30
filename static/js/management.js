tm.approvePend = function(pend_id) {
    $.ajax({
        url: tm_static + 'trees/pending/' + pend_id + '/approve/',
        dataType: 'json',
        type: 'POST',
        success: function(response) {
            tm.trackEvent('Pend', 'Approve', 'id', pend_id);
            location.reload();
        },
        error: tm.genericErrorAlert
    });
};

tm.rejectPend = function(pend_id) {
    $.ajax({
        url: tm_static + 'trees/pending/' + pend_id + '/reject/',
        dataType: 'json',
        type: 'POST',
        success: function(response) {
            tm.trackEvent('Pend', 'Reject', 'id', pend_id);
            location.reload();
        },
        error: tm.genericErrorAlert
    });
};

tm.addTreeToPlot = function(plot_id) {
    $.ajax({
        url: tm_static + 'plots/' + plot_id + '/addtree/',
        dataType: 'json',
        type: 'POST',
        success: function(response) {
            tm.trackEvent('Add', 'New Tree');
            location = tm_static + "plots/" + plot_id + "/";
        },
        error: tm.genericErrorAlert
    });
};

tm.deleteTree = function(tree_id) {
    if (window.confirm("Are you sure you want to remove this tree permanently from the system?"))
    {
        $.ajax({
            url: tm_static + 'trees/' + tree_id + '/delete/',
            dataType: 'json',
            type: 'POST',
            success: function(response) {
                tm.trackEvent('Edit', 'Delete');
                location = tm_static + "plots/" + tm.currentPlotId + "/";
            },
            error: tm.genericErrorAlert
        });
    }
};

tm.deletePlot = function(plot_id) {
    if (window.confirm("Are you sure you want to remove this planting site and it's current tree permanently from the system?"))
    {
        $.ajax({
            url: tm_static + 'plots/' + plot_id + '/delete/',
            dataType: 'json',
            type: 'POST',
            success: function(response) {
                tm.trackEvent('Edit', 'Delete');
                window.location = tm_static + "map/";
            },
            error: tm.genericErrorAlert
        });
    }
};

tm.deletePhoto = function(tree_id, photo_id) {
    if (window.confirm("Are you sure you want to delete this photo permanently from the system?"))
    {
        $.ajax({
            url: tm_static + 'trees/' + tree_id + '/deletephoto/' +  photo_id,
            dataType: 'json',
            type: 'POST',
            success: function(response) {
                window.location.reload(true);
            },
            error: tm.genericErrorAlert
        });
    }
};

tm.deleteUserPhoto = function(username) {
    if (window.confirm("Are you sure you want to delete this photo permanently from the system?"))
    {
        $.ajax({
            url: tm_static + 'profiles/' + username + '/deletephoto/',
            dataType: 'json',
            type: 'POST',
            success: function(response) {
                window.location.reload(true);
            },
            error: tm.genericErrorAlert
        });
    }
};

tm.updateReputation = function(change_type, change_id, rep_dir) {
    $.ajax({
        url: tm_static + 'verify/' + change_type + '/' + change_id + '/' + rep_dir,
        dataType: 'json',
        success: function(response) {
            $("#" + response.change_type + "_" + response.change_id).fadeOut();
            tm.trackEvent("Reputation", rep_dir)
        },
        error: tm.genericErrorAlert
    });
};

tm.updateReputation_Admin = function(user_id, rep_total) {
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
        error: tm.genericErrorAlert
    });
};

tm.updateGroup_Admin = function(user_id, group_id) {
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
            if (response.new_rep) {
                $("#reputation_" + response.user_id).val(response.new_rep);
            }
        },
        error: tm.genericErrorAlert
    });
};

tm._banOrActivate = function(user_id, url, show_selector, hide_selector, status_text) {
    var data = {
        'user_id': user_id
    };

    var jsonString = JSON.stringify(data);

    $.ajax({
        url: url,
        dataType: 'json',
        data: jsonString,
        type: 'POST',
        success: function(response) {
            var $userEditRow = $('.user_edit_row[data-id=' + user_id + ']');

            $userEditRow.children("#rep").children(hide_selector).hide();
            $userEditRow.children("#rep").children(show_selector).show();
            $userEditRow.children("#active").html(status_text);
        },
        error: tm.genericErrorAlert
    });
}

tm.banUser = function (user_id) {
    tm._banOrActivate(user_id, tm_static + 'users/ban/', "#activate", "#ban", "Inactive");
}

tm.activateUser = function (user_id) {
    tm._banOrActivate(user_id, tm_static + 'users/activate/', "#ban", "#activate", "Active");
}

tm.updatePend = function(pend_id, pend_dir) {
    $.ajax({
        url: tm_static + 'trees/pending/' + pend_id + '/' + pend_dir,
        dataType: 'json',
        success: function(response) {
            $("#" + response.pend_id).hide();
            tm.trackEvent("Pending", pend_dir)
        },
        error: tm.genericErrorAlert
    });
};

tm.validate_watch = function(watch_id){
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
        error: tm.genericErrorAlert
    });
};
