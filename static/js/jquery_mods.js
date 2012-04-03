Date.prototype.getMonthName = function(lang) {
    lang = lang && (lang in Date.locale) ? lang : 'en';
    return Date.locale[lang].month_names[this.getMonth()];
};

Date.prototype.getMonthNameShort = function(lang) {
    lang = lang && (lang in Date.locale) ? lang : 'en';
    return Date.locale[lang].month_names_short[this.getMonth()];
};

Date.locale = {
    en: {
       month_names: ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'],
       month_names_short: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    }
};


$.urlParam = function(name){
    var results = new RegExp('[\\?&]' + name + '=([^&#]*)').exec(window.location.href);
    if (results) {
        return results[1];
        }
    };
    
$('html').ajaxSend(function(event, xhr, settings) {
    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = $.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
        // Only send the token to relative URLs i.e. locally.
        xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
    }
});

$.editable.addInputType("autocomplete_species", {
    element: function(settings, original) {
        var hiddenInput = $('<input type="hidden" class="hide">');
        var input = $("<input type='text' />");
        var other = $("<input type='text' id='other_species1' /><input type='text' id='other_species2' /><br><span>Genus and species</span>")
        tm.setupAutoComplete(input).bind("autocompleteselect", function(event, item) {
            hiddenInput[0].value = item.item.value; 
            if (input[0].value.indexOf('Other') > -1) {
                other.show();
            } else {
                other.hide();
                $('#other_species1').empty();
                $('#other_species2').empty();
            }
        });
        var target = $(this);
        target.append(input);
        target.append(other);
        other.hide();
        target.append(hiddenInput);

        return (hiddenInput);
    }
});

$.editable.addInputType('date', {
    element : function(settings, original) {       
        var monthselect = $('<select id="month_">');
        var dayselect  = $('<select id="day_">');
        var yearselect  = $('<select id="year_">');
    
        /* Month loop */
        for (var month=1; month <= 12; month++) {
            if (month < 10) {
                month = '0' + month;
            }
            var option = $('<option>').val(month).append(month);
            monthselect.append(option);
        }
        $(this).append(monthselect);

        /* Day loop */
        for (var day=1; day <= 31; day++) {
            if (day < 10) {
                day = '0' + day;
            }
            var option = $('<option>').val(day).append(day);
            dayselect.append(option);
        }
        $(this).append(dayselect);
            
        /* Year loop */
        thisyear = new Date().getFullYear()
        for (var year=thisyear; year >= 1800; year--) {
            var option = $('<option>').val(year).append(year);
            yearselect.append(option);
        }
        $(this).append(yearselect);
        
        $(this).append("<br><span>MM</span><span style='padding-left:30px;'>DD</span><span style='padding-left:36px;'>YYYY</span><br><div style='color:red;' id='dateplanted_error'/>")
        
        /* Hidden input to store value which is submitted to server. */
        var hidden = $('<input type="hidden">');
        $(this).append(hidden);
        return(hidden);
    },
    submit: function (settings, original) {
        var vdate = new Date($("#year_").val(), $("#month_").val()-1, $('#day_').val());
        if (vdate.getTime() > new Date().getTime()) {
            $("#dateplanted_error").html("Enter a past date")
            return false;
        }
        
        var value = $("#year_").val() + "-" + $("#month_").val() + "-" + $('#day_').val();
        $("input", this).val(value);
    },
    content : function(string, settings, original) {
        var pieces = string.split('-');
        var year = pieces[0];
        var month  = pieces[1];
        var day  = pieces[2];
        

        $("#year_", this).children().each(function() {
            if (year == $(this).val()) {
                $(this).attr('selected', 'selected');
            }
        });
        $("#month_", this).children().each(function() {
            if (month == $(this).val()) {
                $(this).attr('selected', 'selected');
            }
        });
        $("#day_", this).children().each(function() {
            if (day == $(this).val()) {
                $(this).attr('selected', 'selected');
            }
        });
    }
});
$.editable.addInputType('feetinches', {
    element : function(settings, original) {       
        var footselect = $('<select id="feet_">');
        var inchselect  = $('<select id="inches_">');
    
        /* Month loop */
        for (var foot=1; foot <= 15; foot++) {
            var option = $('<option>').val(foot).append(foot);
            footselect.append(option);
        }
        var option = $('<option>').val(99).append('15+');
        footselect.append(option);
        $(this).append(footselect);

        /* Day loop */
        for (var inch=0; inch <= 11; inch++) {
            var option = $('<option>').val(inch).append(inch);
            inchselect.append(option);
        }
        $(this).append(inchselect);
            
        
        $(this).append("<br><span>Feet</span><span style='padding-left:30px;'>Inches</span><br><div style='color:red;' id='dateplanted_error'/>")
        
        /* Hidden input to store value which is submitted to server. */
        var hidden = $('<input type="hidden">');
        $(this).append(hidden);
        return(hidden);
    },
    submit: function (settings, original) {
        var vfeet = parseFloat($("#feet_").val());
        var vinch = parseFloat($("#inches_").val());
        var value = vfeet + (vinch / 12)
        if (vfeet == 99) {
            $("input", this).val(vfeet);
        }
        else {
            $("input", this).val(Math.round(value*100)/100);
        }
    },
    content : function(string, settings, original) {
        var pieces = parseFloat(string);
        var ft = Math.floor(pieces);
        var inch = Math.round((pieces - ft) * 12);
        

        $("#feet_", this).children().each(function() {
            if (ft == $(this).val()) {
                $(this).attr('selected', 'selected');
            }
        });
        $("#inches_", this).children().each(function() {
            if (inch == $(this).val()) {
                $(this).attr('selected', 'selected');
            }
        });
    }
});
