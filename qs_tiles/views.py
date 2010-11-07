# Django 
from django.conf import settings
from django.http import HttpResponse

# TileCache 
#import TileCache.Layer as Layer
from TileCache.Service import Service
from TileCache.Caches.Disk import Disk
from TileCache.Caches.Memcached import Memcached
from TileCache.Layer import Tile
from TileCache.Layers.Mapnik import Mapnik as MapnikLayer

from treemap.views import _build_tree_search_result

# http://bitbucket.org/springmeyer/djmapnik/
from djmapnik.adapter import qs_to_map

try:
    import mapnik2 as mapnik
except:
    import mapnik

# todo - remove <layername>, and remove 'foo' from url in static/treemap.js
tile_request_pat = r'/(?P<version>\d{1,2}\.\d{1,3}\.\d{1,3})/(?P<layername>[a-z]{1,64})/(?P<z>\d{1,10})/(?P<x>\d{1,10})/(?P<y>\d{1,10})\.(?P<extension>(?:png|jpg|gif))'

# hackish way to grab style obj and avoid parsing XML each request...
m = mapnik.Map(1,1)
mapnik.load_map(m,settings.MAPNIK_STYLESHEET)
style = m.find_style('style')
del m

srv = None

if settings.CACHE_SEARCH_METHOD == 'mem':
    srv = Service(
      Memcached(),
      {}, # layers are dynamic
    )
else:
    srv = Service(
      Disk(settings.CACHE_SEARCH_DISK_PATH),
      {}, # layers are dynamic
    )

query_hash = {}

class TileResponse(object):
    def __init__(self, tile_bytes):
        self.tile_bytes = tile_bytes

    def __call__(self, extension='png'):
        if self.tile_bytes:
            # mod_python handler in django borkes unless mimetype is string
            return HttpResponse(self.tile_bytes, mimetype=str('image/%s' % extension))
        else:
            raise Http404

def strip_name(name):
    if '&advanced=open' in name:
        return name.replace('&advanced=open','')
    elif 'advanced=open' in name:
        return name.replace('advanced=open','')
    return name

def get_tile(request, version, layername, z, x, y, extension='png'):
    global style
    image = None
    name = request.META['QUERY_STRING'] or 'all'
    name = strip_name(name)
    mapnik_layer = MapnikLayer(
                 name,
                 'foo',# mapfile skipped as we dynamically assign map object
                 spherical_mercator = 'true',
                 extension = "png",
                 tms_type = 'google',
                 paletted = 'true',
                 debug=False
                 )
    srv.layers[name] = mapnik_layer
    z, x, y = int(z), int(x), int(y)
    if mapnik_layer.tms_type == "google":
        res = mapnik_layer.resolutions[z]
        maxY = int(
          round(
            (mapnik_layer.bbox[3] - mapnik_layer.bbox[1]) / 
            (res * mapnik_layer.size[1])
           )
        ) - 1
        tile  = Tile(mapnik_layer, x, maxY - y, z)
    else:
        tile = Tile(mapnik_layer, x, y, z)
    if settings.CACHE_SEARCH_TILES:
        image = srv.cache.get(tile)
    if not image:
        # cached map - must be run multiprocess to avoid potential race condition
        m = query_hash.get(name)
        if not m:
            trees, geog_obj = _build_tree_search_result(request)
            trees = trees.only('geometry')
            styles=[{'name':'style','obj':style}]
            m = qs_to_map(trees,styles=styles)
            query_hash[name] = m
        # push the actual mapnik map into the TC MapnikLayer
        mapnik_layer.mapnik = m
        if settings.CACHE_SEARCH_TILES:
            # render and cache
            image = srv.renderTile(tile)[1]
        else:
            # render directly from layer, not service, therefore bypassing saving to cache
            image = mapnik_layer.renderTile(tile)
    response = TileResponse(image)    
    return response(extension)
