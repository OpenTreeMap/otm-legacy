from django.conf import settings
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse

from treemap.models import Plot, Species

from functools import wraps

import simplejson 

def api_call(content_type="application/json"):
    def decorate(req_function):
        @wraps(req_function)
        def newreq(request):
            outp = req_function(request)
            
            response = HttpResponse()
            response.write('%s' % simplejson.dumps(outp))
            response['Content-length'] = str(len(response.content))
            response['Content-Type'] = content_type
            return response
            
        return newreq
    return decorate


@require_http_methods(["GET"])
@api_call()
def version(request):
    """ API Request
    
    Get version information for OTM and the API. Generally, the API is unstable for
    any API version < 1 and minor changes (i.e. 1.4,1.5,1.6) represent no break in
    existing functionality

    URL: /version
    Verb: GET
    Params: None
    Output:
      { 
        otm_version, string -> Open Tree Map Version (i.e. 1.0.2)
        api_version, string -> API version (i.e. 1.6) 
      }

    """
    return { "otm_version": settings.OTM_VERSION,
             "api_version": settings.API_VERSION }

@require_http_methods(["GET"])
@api_call()
def get_plot_list(request):
    """ API Request

    Get a list of all plots in the database. This is meant to be a lightweight
    listing service. To get more details about a plot use the ^plot/{id}$ service
    
    URL: /plots
    Verb: GET
    Params: 
      offset, integer, default = 0  -> offset to start results from
      size, integer, default = 100 -> Maximum 10000, number of results to get

    Output:
      [{
          width, integer, opt -> Width of tree bed
          length, integer, opt -> Length of bed
          type, string, opt -> Plot type
          geometry, Point -> Lat/lng pt
          readonly, boolean -> True if this is a readonly tree
          tree, {
             id, integer -> tree id
             species, integer, opt -> Species id
             dbh, real, opt -> Diameter of the tree
          }             
       }]

      """
    start = int(request.REQUEST.get("offset","0"))
    size = min(int(request.REQUEST.get("size", "100")), 10000)
    end = size + start

    plotObjs = Plot.objects.filter(present=True)[start:end]
    plots = []

    for plot in plotObjs:
        current_tree = plot.current_tree()
        if current_tree:
            tree = { "id" : current_tree.pk }

            if current_tree.species:
                tree["species"] = current_tree.species.pk
        
            if current_tree.dbh:
                tree["dbh"] = current_tree.dbh

        else:
            tree = None
            
        plots.append({
                "id": plot.pk,
                "width": plot.width,
                "length": plot.length,
                "type": plot.type,
                "readonly": plot.readonly,
                "tree": tree,
                "geometry": {
                    "srid": plot.geometry.srid,
                    "lat": plot.geometry.y,
                    "lng": plot.geometry.x
                    }})

    return plots
