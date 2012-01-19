var threaded = {

    show_reply_form: function (csrf, comment_id, url, person_name) {
        var csrf_field = '<input type="hidden" name="csrfmiddlewaretoken" value="' + csrf + '">';
        var form = "<li>" +
            '<label for="id_comment"="">' + 
            'comment:<textarea id="id_comment" rows="10" cols="40" name="comment"></textarea>' +
            '<li><label for="id_markup">Markup:</label>' +
            '<select name="markup" id="id_markup"><option value="">---------</option><option value="1">markdown</option><option value="2">textile</option><option value="3">restructuredtext</option><option value="5" selected="selected">plaintext</option></select></li>';

        var comment_reply = $('#' + comment_id);
        var to_add = $( new Array(
            '<div class="response"><p>Reply to ' + person_name + ':</p>',
            '<form method="POST" action="' + url + '">', csrf_field,
            '<ul>',  form, 
            '<li><input type="submit" value="Submit Comment" /></li>',
            '</ul>', '</form>', '</div>').join(''));
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