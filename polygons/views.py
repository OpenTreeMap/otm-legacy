from django.http import HttpResponse
from models import TreeRegionPolygon, TreeRegionEntry
from django.contrib.gis.geos import Point
import json

def polygon_search(request):
    id = request.GET.get('id', None)

    if id:
        polygons = TreeRegionPolygon.objects.filter(pk=id)
    else:
        lat = float(request.GET['lat'])
        lon = float(request.GET['lon'])

        point = Point(lon, lat, srid=4326)

        polygons = TreeRegionPolygon.objects.filter(geometry__contains=point)

    polys = {}
    for polygon in polygons:
        entries = TreeRegionEntry.objects.filter(polygon=polygon)

        data = {e.species.pk: {} for e in entries}
        for entry in entries:
            species = data[entry.species.pk]
            species[entry.dbhclass.label] = entry.count

        polys[polygon.pk] = data

    return HttpResponse(json.dumps(polys),
                        content_type='application/json')

def polygon_view(request):
    pass
