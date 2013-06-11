from django.http import HttpResponse
from models import TreeRegionPolygon, TreeRegionEntry
from django.contrib.gis.geos import Point
from django.utils import simplejson

def polygon_search(request):
    lat = float(request.GET['lat'])
    lon = float(request.GET['lon'])

    point = Point(lon, lat, srid=4326)
    mercator_point = point.transform(3785, clone=True)

    id = request.GET.get('id', None)

    if id:
        entries = TreeRegionEntry.objects.filter(polygon_id=id)
    else:
        entries = TreeRegionEntry.objects.filter(polygon__geometry__contains=point)

    data = {}
    if entries:
        for entry in entries:
            if data.has_key(entry.species.id):
                data[entry.species.id][entry.dbhclass.label] = entry.count
            else:
                data[entry.species.id] = { entry.dbhclass.label: entry.count }

    response = {
        "lat": lat,
        "lon": lon,
        "x": mercator_point.x,
        "y": mercator_point.y,
        "status": "SUCCESS",
        "hasResults": (True if entries else False),
        "data": data,
    }
    return HttpResponse(simplejson.dumps(response),
                        content_type='application/json')
