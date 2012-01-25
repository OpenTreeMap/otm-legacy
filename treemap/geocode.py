from geopy import geocoders
from geopy.geocoders.base import Geocoder, GeocoderResultError

#todo: move to settings once this is all done.
GEOCODER_ORDER = ["DC", "Google"]

class DCGeocoder(Geocoder):

    def geocode(self, string):
        return None, None, None

    def reverse(self, point):
        return None, None, None



def parse_geocoder(name):
    if name == "DC":
        return DCGeocoder()
    elif name == "Google":
        return geocoders.Google()
    else:
        raise ValueError("Requested geocoder '%s' is not available" % name)
    
def geocode(address):
    for gname in GEOCODER_ORDER:
        try:
            g = parse_geocoder(gname)
            place, (lat, lng) = g.geocode(address)
            return place, lat, lng
        except:
            pass
    raise GeocoderResultError("No results found for address %s" % address)

def reverse_geocode(point):
    raise NotImplementedError()



