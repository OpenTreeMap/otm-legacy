/**
 * Update a comment (given by flag_id) with the active
 * where action should be either "hide" or "unflag"
 */
tm.updateCommentFlag = function(flag_id, action) {
    var data = {
        'flag_id': flag_id
    };
    var jsonString = JSON.stringify(data);      
    $.ajax({
        url: tm_static + 'comments/' + action + '/',
        dataType: 'json',
        data: jsonString,
        type: 'POST',
        success: function(response) {
            $("#" + flag_id).fadeOut();
        },
        error: function(err) {
            alert("Couldn't edit comment");
        }
    });
};

tm.hideComment = function(flag_id) {
    tm.updateCommentFlag(flag_id, "hide");
};

tm.removeFlag = function(flag_id) {
    tm.updateCommentFlag(flag_id,"unflag");
};
