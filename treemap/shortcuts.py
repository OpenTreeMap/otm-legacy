from django.contrib.gis.db.models.fields import GeometryField
from django.contrib.gis.geos import Point
from django.utils import simplejson
from django.core.serializers import json 
from django.http import HttpResponse
from django.core.exceptions import ValidationError
from django.forms.forms import NON_FIELD_ERRORS

from django.conf import settings

def validate_form(form, request):
    if form.is_valid():
        try:
            new_stuff = form.save(request)
            form.result = new_stuff
            return True
        except ValidationError, e:
            form._errors[NON_FIELD_ERRORS] = form.error_class(e.messages)
            return False
    else:
        return False


import re

def get_pt_or_bbox(rg):
    """
    parse out lat/lon or bbox from request.get and return geos geom
    """
    dec_num_re = "(\d+?(\.\d+))"
    bbox_re = '%s,%s.*?%s,%s' % (dec_num_re,dec_num_re,dec_num_re,dec_num_re)

    lat = rg.get('lat','')
    lon = rg.get('lon','')
    if lat and lon: 
        return Point(float(lon), float(lat), srid=4326)
    bbox = rg.get('bbox','')
    if bbox:
        b = re.search(rg.get('bbox',''), bbox_re).groups()
        p1 = Point((b[2],b[0]))
        p2 = Point((b[6],b[4]))
        return p1.union(p2).envelope
    return None

ADD_INITIAL_DEFAULTS = {
    'address': "Enter an Address or Intersection", 
    'city': "Enter a City", 
    'species_full': "Enter a Species Name", 
    'genus': "", 
    'species': "", 
    'dbh': "", 
    'height': "", 
    'canopy': "", 
    'owner': ""
}
def get_add_initial(setting_name):
    if settings.ADD_INITIAL_DEFAULTS and set([setting_name]).issubset(settings.ADD_INITIAL_DEFAULTS):
        return settings.ADD_INITIAL_DEFAULTS[setting_name]
    else:
        return ADD_INITIAL_DEFAULTS[setting_name]

def render_to_geojson(query_set, geom_field=None, mimetype='text/plain', pretty_print=True, excluded_fields=[], simplify='', additional_data=None, model=None, extent=None):
    '''
    
    Shortcut to render a GeoJson FeatureCollection from a Django QuerySet.
    Currently computes a bbox and adds a crs member as a sr.org link
    
    '''
    collection = {}

    if not model:
        model = query_set.model

    if not extent and query_set:
        extent = query_set.extent()

    fields = model._meta.fields
    geo_fields = [f for f in fields if isinstance(f, GeometryField)]
    
    #attempt to assign geom_field that was passed in
    if geom_field:
        geo_fieldnames = [x.name for x in geo_fields]
        try:
            geo_field = geo_fields[geo_fieldnames.index(geom_field)]
        except:
            raise Exception('%s is not a valid geometry on this model' % geom_field)
    else:
        geo_field = geo_fields[0] # no support yet for multiple geometry fields
        
        
    #remove other geom fields from showing up in attributes    
    if len(geo_fields) > 1:
        for gf in geo_fields:
            if gf.name not in excluded_fields: excluded_fields.append(gf.name)
        excluded_fields.remove(geo_field.name)    
    # Gather the projection information
    crs = {}
    crs['type'] = "link"
    crs_properties = {}
    crs_properties['href'] = 'http://spatialreference.org/ref/epsg/%s/' % geo_field.srid
    crs_properties['type'] = 'proj4'
    crs['properties'] = crs_properties 
    collection['crs'] = crs
    
    
    # Build list of features
    features = []
    if query_set:
      for item in query_set:
        feat = {}
        feat['type'] = 'Feature'
        d = {}
        
        #special attribs for trees:
        if  model.__name__ == 'Tree':
            if item.species:
                d['scientific_name'] = item.species.scientific_name
                d['common_name'] = item.species.common_name
                d['flowering'] = item.species.flower_conspicuous
                d['native'] = item.species.native_status
        elif model.__name__ == 'Plot':
            tree = item.current_tree()
            if tree:
                if tree.species:
                    d['scientific_name'] = tree.species.scientific_name
                    d['common_name'] = tree.species.common_name
                d['dbh'] = tree.dbh
                d['height'] = tree.height
                d['tree'] = True
            else:
                d['tree'] = False
                
        if hasattr(item, 'distance'):
            d['distance'] = getattr(item,'distance').ft
                
        g = getattr(item,geo_field.name)
        if simplify:
            g = g.simplify(simplify)
        for field in item._meta.fields:
            if field.name not in excluded_fields:
                d[field.name] = str(getattr(item, field.name))

        feat['geometry'] = simplejson.loads(g.geojson)
        feat['properties'] = d
        features.append(feat)
    else:
        pass #features.append({'type':'Feature','geometry': {},'properties':{}})

    # Label as FeatureCollection and add Features
    collection['type'] = "FeatureCollection"    
    collection['features'] = features
    
    # Attach extent of all features
    if query_set:
        collection['bbox'] = [x for x in extent]
    
    if additional_data:
        collection.update(additional_data)
    # Return response
    response = HttpResponse()
    if pretty_print:
        response.write('%s' % simplejson.dumps(collection, indent=1, cls=json.DateTimeAwareJSONEncoder))

    else:
        response.write('%s' % simplejson.dumps(collection, cls=json.DateTimeAwareJSONEncoder))    
    response['Content-length'] = str(len(response.content))
    response['Content-Type'] = mimetype
    return response
