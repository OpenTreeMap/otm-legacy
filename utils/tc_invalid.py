import math
import sys
import os
import time
import urllib
import memcache
if len(sys.argv) < 3:
    print "Usage: %s <path to settings module> <settings module name>" % sys.argv[0]
    sys.exit()    
class KeyboardException: pass
sys.path = [sys.argv[1]] + sys.path
os.environ['DJANGO_SETTINGS_MODULE'] = sys.argv[2] 
from profiles.models import *
from treemap.models import PointUpdate, TreePhoto

#tilecache_base = "http://tilecache.urbanforestmap.org/tiles/trees/1.0.0/"
tilecache_base = "http://tilecache.urbanforestmap.org/tiles/1.0.0/trees"

def lon_lat_to_xy(lon, lat):
    x = lon * 20037508.34 / 180
    y = math.log(math.tan((90 + lat) * math.pi / 360)) / (math.pi / 180)
    y = y * 20037508.34 / 180
    return [x, y]

def tile_ids(xy, min_zoom=7, max_zoom=20):
    input = xy 
    max_res = 156543.0339
    max_extent = [-20037508.34,-20037508.34,20037508.34,20037508.34]
    levels = range(min_zoom,max_zoom)
    # regen highest zooms first
    levels.reverse()
    for zoom in levels:
        x_diff = input[0] - max_extent[0]
        x = int(math.floor(x_diff/(max_res/(2**zoom))/256))
        y_diff = max_extent[3] - input[1] 
        y = int(math.floor(y_diff/(max_res/(2**zoom))/256))
        yield zoom, x, y

def refresh_tile(z,x,y):
    global tilecache_base
    # was hitting:
    # http://tilecache.urbanforestmap.org/tiles/trees/1.0.0//1.0.0/18/41930/101350.jpg?FORCE=true
    # now should hit:
    # http://tilecache.urbanforestmap.org/tiles/1.0.0/trees/Map/12/656/1585.png
    # todo - pull these dynamically
    layers = ['Map','Terrain','Satellite','Hybrid']
    for l in layers:
        url = "%s/%s/%s/%s/%s.png?FORCE=true" % (tilecache_base, l, z, x, y)
        print url
        urllib.urlopen(url)    


def run():
    mc = memcache.Client(['127.0.0.1:11211'])
    while True:
        points = PointUpdate.objects.all()
        if points.count():
            try:
                point = points[0]
                for i in tile_ids(lon_lat_to_xy(point.lon, point.lat)):
                    refresh_tile(*i)
                mc.flush_all()
                print "Finished with %s" % point.id
                point.delete()  
            except Exception, E:
                print "Error occurred (%s)" % E
        time.sleep(1)     

if __name__ == "__main__":  
    run() 
