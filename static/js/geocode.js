tm.geocode = function(address, callback, error_callback){
    if (!address){
        address = $('#searchInput').text();
    }

    tm.geocode_address = address;

    if (tm.local_geocoder) {
        $.getJSON(tm_static + "geocode/", {address: address, geocoder_name: tm.local_geocoder}, function(json) {
            if (json.success == true) {
                if (callback) {
                    callback(json.lat, json.lng, json.place)
                }
            }
            else {
                tm.geocoder.geocode({
                    address: address,
                    bounds: tm.google_bounds  
                }, function(results, status){
                    if (status == google.maps.GeocoderStatus.OK) {
                        
                        if (callback) {
                            callback(results[0].geometry.location.lat(), results[0].geometry.location.lng(), results[0].formatted_address);
                        }

                    } else {
                        if (error_callback) {
                            error_callback(status)
                        }
                    }

                });
            }
        });
    }
    else {
        tm.geocoder.geocode({
            address: address,
            bounds: tm.google_bounds  
        }, function(results, status){
            if (status == google.maps.GeocoderStatus.OK) {
                
                if (callback) {
                    callback(results[0].geometry.location.lat(), results[0].geometry.location.lng(), results[0].formatted_address);
                }

            } else {
                if (error_callback) {
                    error_callback(status)
                }
            }

        });
    }

},


//pass in a GLatLng and get back closest address
tm.reverse_geocode = function(ll, callback, error_callback){
    if (tm.local_geocoder) {
        $.getJSON(tm_static + "geocode/reverse/", {lat: ll.lat, lng: ll.lon, geocoder_name: tm.local_geocoder}, function(json) {
            if (json.success == true) {
                if (callback) {
                    var city = json.place.split(", ")[1] + " " + json.place.split(", ")[2];
                    var zip = json.place.split(", ")[3];
                    callback(ll, json.place, city, zip)
                }
            }
            else {
                latlng = new google.maps.LatLng(ll.lat, ll.lon)
                tm.geocoder.geocode({
                    latLng: latlng
                }, function(results, status){
                    if (status == google.maps.GeocoderStatus.OK) {
                        if (callback) {
                            var full_address = results[0].formatted_address
                            var addy = results[0].address_components;
                            var city = "";
                            var zip = "";
                            
                            for (var i=0; i<addy.length; i++) {
                                if ($.inArray('locality', addy[i].types) > -1) {
                                    city = addy[i].long_name;
                                }
                                else if ($.inArray('postal_code', addy[i].types) > -1) {    
                                    zip = addy[i].long_name;
                                }
                                else if ($.inArray('administrative_area_level_1', addy[i].types) > -1) {
                                    city += " " + addy[i].short_name;
                                }
                            }

                            callback(ll, full_address, city, zip);
                        }

                    } else {
                        if (error_callback) {error_callback(ll);}               
                    }        
                });   
            }
        });
    }
    else {
        latlng = new google.maps.LatLng(ll.lat, ll.lon)
        tm.geocoder.geocode({
            latLng: latlng
        }, function(results, status){
            if (status == google.maps.GeocoderStatus.OK) {
                if (callback) {
                    var full_address = results[0].formatted_address
                    var addy = results[0].address_components;
                    var city = "";
                    var zip = "";
                    
                    for (var i=0; i<addy.length; i++) {
                        if ($.inArray('locality', addy[i].types) > -1) {
                            city = addy[i].long_name;
                        }
                        else if ($.inArray('postal_code', addy[i].types) > -1) {    
                            zip = addy[i].long_name;
                        }
                    }

                    callback(ll, full_address, city, zip);
                }

            } else {
                if (error_callback) {error_callback(ll);}               
            }        
        });   
    }     
};            

