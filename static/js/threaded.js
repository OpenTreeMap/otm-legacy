var threaded = {

    show_reply_form: function (csrf, comment_id, url, person_name) {
        var csrf_field = '<input type="hidden" name="csrfmiddlewaretoken" value="' + csrf + '">';
        var form = '<textarea id="id_comment" rows="10" cols="40" name="comment"></textarea>';

        var comment_reply = $('#' + comment_id);
        var to_add = $( new Array(
            '<div class="response"><p>Reply to ' + person_name + ':</p>',
            '<form method="POST" id="comment_post"  action="' + url + '">', csrf_field,
            form, 
            '<div><input type="submit"class="submit-post buttonSmall" value="Post"/></div>',
            '</div>', '</form>', '</div>').join(''));
        to_add.css("display", "none");
        comment_reply.after(to_add);
        to_add.slideDown(function() {
            comment_reply.replaceWith(new Array('<a id="',
                                                comment_id,'" href="javascript:threaded.hide_reply_form(\'',
                                                comment_id, '\',\'', url, '\',\'', person_name,
                                                '\')">Stop Replying</a>').join(''));
        });
    },

    hide_reply_form: function (comment_id, url, person_name) {
        var comment_reply = $('#' + comment_id);
        comment_reply.next().slideUp(function (){
            comment_reply.next('.response').remove();
            comment_reply.replaceWith(new Array('<a id="',
                                                comment_id,'" href="javascript:threaded.show_reply_form(\'',
                                                comment_id, '\',\'', url, '\',\'', person_name,
                                                '\')">Reply</a>').join(''));
        });
    }
}
