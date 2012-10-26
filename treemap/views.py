import os
import time
import sys
from time import mktime, strptime
from datetime import timedelta
import tempfile
import zipfile
from contextlib import closing
import subprocess
from operator import itemgetter, attrgetter
from itertools import chain
import simplejson 
from functools import wraps

from django.conf import settings
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden, Http404, HttpResponseBadRequest, HttpResponseNotAllowed
from django.core.paginator import Paginator
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.gis.feeds import Feed
from django.contrib.gis.geos import Point, GEOSGeometry
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_view_exempt
from django.views.decorators.http import require_http_methods
from django.db.models import Count, Sum, Q, Min, Max
from django.contrib.gis.shortcuts import render_to_kml
from django.utils.datastructures import SortedDict
from django.utils.decorators import available_attrs
from django.core.exceptions import PermissionDenied
# formsets
from django.forms.formsets import formset_factory
from django.forms.models import inlineformset_factory, modelformset_factory

from threadedcomments.models import ThreadedComment

from models import *
from forms import *
from profiles.models import UserProfile
from profiles.utils import change_reputation_for_user
from shortcuts import render_to_geojson, get_pt_or_bbox, validate_form

from registration.signals import user_activated
from django_reputation.models import Reputation, Permission, UserReputationAction, ReputationAction
from geopy_extensions.geocoders.CitizenAtlas import CitizenAtlas

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

def redirect(rel):
    # Trim off slash
    if rel[0] == "/":
        rel = rel[1:]

    return HttpResponseRedirect('%s%s' % (settings.SITE_ROOT, rel))

app_models = {'UserProfile':'profiles','User':'auth'}

#TODO: is this used anywhere?
def average(seq):
    return float(sum(l))/len(l)

#TODO: is this used anywhere?
def get_app(name):
    app = app_models.get(name)
    return app or 'treemap'
    
def render_to_json(j):
    response = HttpResponse()
    response.write('%s' % simplejson.dumps(j))
    response['Content-length'] = str(len(response.content))
    response['Content-Type'] = 'text/plain'
    return response

def user_activated_callback(sender, **kwargs):    
    rep = Reputation.objects.reputation_for_user(kwargs['user'])
    #print rep
user_activated.connect(user_activated_callback)

def list_neighborhoods(request):
    n = Neighborhood.objects.all().defer('geometry').order_by('state','county','name')
    ns = []
    for hood in n:
        ns.append({
            'name': hood.name,
            'region_id': hood.region_id,
            'city': hood.city,
            'county': hood.county,
            'state': hood.state })

    return render_to_json(ns)

#@cache_page(60*5)
# Static pages have user information in them, so caching them doesn't work.
def static(request, template, subdir="treemap"):
    if not template:
        template = "index.html"
    template = template.rstrip("/")
    if not template.endswith(".html") and not template.endswith(".css") \
            and not template.endswith(".js") and not template.endswith(".txt"):
        template += ".html"
    if subdir:
        template = os.path.join(subdir, template)
    return render_to_response(template, RequestContext(request,{}))

def permission_required_or_403_forbidden(perm):
    """
    Decorator for views that checks that the user has the specified permission
    and raises a PermissionDenied exception if they do not, which Django coverts
    to a 403 HTTP response.
    """

    def decorator(view_func):
        @wraps(view_func, assigned=available_attrs(view_func))
        def _wrapped_view(request, *args, **kwargs):
            if request.user.has_perm(perm):
                return view_func(request, *args, **kwargs)
            else:
                raise PermissionDenied('%s cannot access this view because they do not have the %s permission' % (request.user.username, perm))
        return _wrapped_view
    return decorator

def location_map(request):
    pass

def json_home_feeds(request):
    feeds = {}
    feeds['species'] = [(s.id, s.common_name) for s in Species.objects.order_by('-tree_count')[0:4]]
    feeds['active_nhoods'] = [(n.id, n.name, n.aggregates.total_trees) for n in Neighborhood.objects.order_by('-aggregates__total_trees')[0:6]]
    return render_to_json(feeds)

def home_feeds(request):
    feeds = {}
    recent_trees = Tree.history.filter(present=True).order_by("-last_updated")[0:3]
    
    feeds['recent_edits'] = unified_history(recent_trees)
    feeds['recent_photos'] = TreePhoto.objects.exclude(tree__present=False).order_by("-reported")[0:7]
    feeds['species'] = Species.objects.order_by('-tree_count')[0:4]
    
    #TODO: change from most populated neighborhood to most updates in neighborhood
    feeds['active_nhoods'] = Neighborhood.objects.order_by('-aggregates__total_trees')[0:6]
    
    return render_to_response('treemap/index.html', RequestContext(request,{'feeds': feeds}))

def get_all_csv(request):
    csv_f = open(os.path.join(os.path.dirname(__file__), '../All_Trees.csv'))
    response = HttpResponse(csv_f, mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename=All_Trees.csv'
    return response

def get_all_kmz(request):
    csv_f = open(os.path.join(os.path.dirname(__file__), '../All_Trees.kmz'))
    response = HttpResponse(csv_f, mimetype='application/vnd.google-earth.kmz')
    response['Content-Disposition'] = 'attachment; filename=All_Trees.kmz'
    return response

@require_http_methods(["GET", "HEAD"])
def get_geocode(request):
    address = request.GET.get("address")  
    geocoder_name = request.GET.get("geocoder_name") 
    js = {}
    if geocoder_name == "CitizenAtlas":
        g = CitizenAtlas(format_string="%s, Washington DC", threshold=80)
    else:
        js["success"] = False
        js["error"] = "No geocoder found for name: %s" % geocoder_name
        return render_to_json(js)
    if address:
        try:
            place, (lat, lng) = g.geocode(address)
            js["success"] = True
            js["place"] = place
            js["lat"] = lat
            js["lng"] = lng
        except Exception as error:
            js["success"] = False
            js["error"] = str(error)
    else:
        js["success"] = False
        js["error"] = "No address specified"
    return render_to_json(js)
       
@require_http_methods(["GET", "HEAD"])
def get_reverse_geocode(request):
    lat = request.GET.get("lat")
    lng = request.GET.get("lng")
    geocoder_name = request.GET.get("geocoder_name") 
    js = {}
    if geocoder_name == "CitizenAtlas":
        g = CitizenAtlas(format_string="%s, Washington DC", threshold=80)
    else:
        js["success"] = False
        js["error"] = "No geocoder found for name: %s" % geocoder_name
        return render_to_json(js)

    if lat and lng:
        try:
            point = (lat, lng)
            place, new_point = g.reverse(point)
            js["success"] = True
            js["place"] = place
            js["lat"] = new_point[0]
            js["lng"] = new_point[1]
        except Exception as error:
            js["success"] = False
            js["error"] = str(error)
    else:
        js["success"] = False
        js["error"] = "No point specified"
    return render_to_json(js)

def get_choices(request):
    choices_list = {}
    choices_obj = settings.CHOICES

    return render_to_json(choices_obj)

#@cache_page(60*1)
def result_map(request):
    # get enviro attributes for 'selected' trees
    min_year = 1970

    min_tree_year = Tree.objects.exclude(date_planted=None).exclude(present=False).aggregate(Min("date_planted"))

    if "date_planted__min" in min_tree_year and min_tree_year['date_planted__min']:
        min_year = min_tree_year['date_planted__min'].year

    current_year = datetime.now().year    

    # TODO: Fix this to include updates to treeflag objects
    min_updated = 0
    max_updated = 0 

    updated = Tree.objects.exclude(last_updated=None, present=False).aggregate(Max("last_updated"), Min("last_updated"))

    if "last_updated__min" in updated and updated["last_updated__min"]:
        min_updated = mktime(updated['last_updated__min'].timetuple())

    if "last_updated__max" in updated and updated["last_updated__max"]:
        max_updated = mktime(updated['last_updated__max'].timetuple())


    minmax_plot = Tree.objects.exclude(last_updated=None, present=False).filter(plot__width__isnull=False)
    minmax_plot = minmax_plot.aggregate(Max('plot__width'), Max('plot__length'), Min('plot__width'), Min('plot__length'))

    max_plot = 0
    min_plot = sys.maxint

    if "plot__length__max" in minmax_plot and minmax_plot["plot__length__max"]:
        max_plot = minmax_plot["plot__length__max"]
    if "plot__width__max" in minmax_plot and minmax_plot["plot__width__max"]:
        max_plot = max(max_plot, minmax_plot["plot__width__max"])

    if "plot__length__min" in minmax_plot and minmax_plot["plot__length__min"]:
        min_plot = minmax_plot["plot__length__min"]
    if "plot__width__min" in minmax_plot and minmax_plot["plot__width__min"]:
        min_plot = min(min_plot, minmax_plot["plot__width__min"])

    if min_plot == sys.maxint:
        min_plot = 0

    recent_trees = Tree.objects.filter(present=True).exclude(last_updated_by__is_superuser=True).order_by("-last_updated")[0:3]
    recent_plots = Plot.objects.filter(present=True).exclude(last_updated_by__is_superuser=True).order_by("-last_updated")[0:3]
    latest_photos = TreePhoto.objects.exclude(tree__present=False).order_by("-reported")[0:8]

    return render_to_response('treemap/results.html',RequestContext(request,{
                'latest_trees': recent_trees,
                'latest_plots' : recent_plots,
                'latest_photos': latest_photos,
                'min_year': min_year,
                'current_year': current_year,
                'min_updated': min_updated,
                'max_updated': max_updated,
                'min_plot': min_plot,
                'max_plot': max_plot,
                }))


def plot_location_search(request):
    geom = get_pt_or_bbox(request.GET)
    if not geom:
        return HttpResponseBadRequest()
    
    distance = request.GET.get('distance', settings.MAP_CLICK_RADIUS)
    max_plots = int(request.GET.get('max_plots', 1))

    if max_plots > 500: max_plots = 500

    orig_trees, orig_plots, geog_obj, agg_object, tile_query = _build_tree_search_result(request, False)
    
    if geom.geom_type == 'Point':
        orig_plots = orig_plots.filter(geometry__dwithin=(geom, float(distance))).distance(geom).order_by('distance')
        if orig_plots.count() > 0:
            plots = orig_plots
        else:
            plots = Plot.objects.filter(present=True).filter(geometry__dwithin=(geom, float(distance))).distance(geom).order_by('distance')
    else:
        orig_plots = orig_plots.filter(geometry__intersects=geom)
        if orig_plots.count() > 0:
            plots = orig_plots
        else:
            plots = Plot.objects.filter(present=True).filter(geometry__intersects=geom)

    if plots:
        extent = plots.extent()
    else:
        extent = []
    
    if len(plots) > 0:
        plots = plots[:max_plots]

    return render_to_geojson(plots,
                             geom_field='geometry', 
                             excluded_fields=['sidewalk_damage',
                             'address_city',
                             'address_street',
                             'address_zip',
                             'neighborhood',
                             'neighborhoods',
                             'length',
                             'distance',
                             'geometry',
                             'geocoded_address',
                             'last_updated_by',
                             'last_updated',
                             'present',
                             'powerline_conflict_potential',
                             'width',
                             'geocoded_lat',
                             'geocoded_lon',
                             'type',
                             'import_event',
                             'address_zip',
                             'owner_additional_properties',
                             'owner_additional_id',
                             'geocoded_accuracy',
                             'data_owner',
                             'owner_orig_id',
                             'owner_additional_id',
                             'owner_additional_properties',
                             'zipcode_id'
                             ],
                             model=Plot,
                             extent=extent)

#@cache_page(60*60*4)
def species(request, selection='all', format='html'):
    """
    return list of species
     - selection:  'in-use',  'page' or 'nearby'
     url params
     - page: # (only used with 'all' which is paginated)
     - format:  html or json (defaults to html) #todo add csv
     - nearby: return 5 closest species
    """
    page = 0
    
    species = Species.objects.all()
    if selection == 'in-use':
        species = species.filter(tree_count__gt=0).order_by('-tree_count')
        
    if selection == 'nearby':
        location = request.GET.get('location','')
        if not location:
            raise Http404
        coord = map(float,location.split(','))
        pt = Point(coord[0], coord[1])
        trees =  Tree.objects.filter(present=True).filter(plot__geometry__dwithin = (pt,.001))#.distance(pt).order_by('distance').count()
        species = Species.objects.filter(tree__in=trees)
    
    if selection == 'all':
        species = Species.objects.all().order_by('common_name')
    
    if format == 'json':
        res = [{"symbol":str(x.symbol or ''), 
                 "cname":str(x.common_name or ''),
                 "cultivar":str(x.cultivar_name or ''),
                 "sname":str(x.scientific_name or x.genus),
                 "id": int(x.id),
                 "count": int(x.tree_count)} for x in species]
        return render_to_response('treemap/basic.json',{'json':simplejson.dumps(res)})
        
    if format == 'csv':
        sql_object =  [{
            "name":"species", 
            "sql":str(species.query), 
            "srs":'EPSG:4326'
        }]
        return ogr_conversion('CSV', sql_object, "", name="species", geo=False)    

    #render to html    
    return render_to_response('treemap/species.html',RequestContext(request,{
        'species' : species,
        'page' : page #so template can do next page kind of stuff
        }))
        

#TODO: is this used anywhere? Does it even do anything?
@cache_page(60*5)    
def top_species(request):
    Species.objects.all().annotate(num_trees=Count('tree')).order_by('-num_trees')        
    return 

def favorites(request, username):
    faves = User.objects.get(username=username).treefavorite_set.filter(tree__present=True)
    js = [{
       'id':f.tree.id, 
       'coords':[f.tree.plot.geometry.x, f.tree.plot.geometry.y]} for f in faves]
    return render_to_json(js)
    
def trees(request, tree_id=''):
    # testing - to match what you get in /location query and in map tiles.
    favorite = False
    recent_edits = []
    trees = Tree.objects.all()
    if tree_id:
        trees = trees.filter(pk=tree_id)
        
        if trees.count() == 0:
            raise Http404
        
        plot = trees[0].plot
        if trees[0].present == False:
            if plot.present == False:
                raise Http404
            else:
                return redirect('plots/%s/' % plot.id)

        # get the last 5 edits to each tree piece
        history = trees[0].history.order_by('-last_updated')[:5]
        history = list(chain(history, plot.history.order_by('-last_updated')[:5]))
        
        recent_edits = unified_history(history)
    
        if request.user.is_authenticated():
            favorite = TreeFavorite.objects.filter(user=request.user,
                tree=trees[0], tree__present=True).count() > 0
    else:
	#TODO: do we ever call this w/o id???
        trees = Tree.objects.filter(present=True)
    
    if request.GET.get('format','') == 'json':
        return render_to_geojson(trees, geom_field='geometry')
    first = None
    if trees.exists():
        first = trees[0]
    else:
        raise Http404
    if request.GET.get('format','') == 'base_infowindow':
        raise Http404
    #TODO: is this used anymore now that the plot info window is called from the map page?
    if request.GET.get('format','') == 'eco_infowindow':
        return render_to_response('treemap/tree_detail_eco_infowindow.html',RequestContext(request,{'tree':first}))
    else:
        return render_to_response('treemap/tree_detail.html',RequestContext(request,{'favorite': favorite, 'tree':first, 'plot': first.plot, 'recent': recent_edits}))

def plot_detail(request, plot_id=''):
    plots = Plot.objects.filter(present=True)

    if not plot_id:
       raise HttpResponseBadRequest

    plots = plots.filter(pk=plot_id)

    if not plots.exists():
        raise Http404

    plot = plots[0]

    if request.GET.get('format','') == 'popup':
        return render_to_response('treemap/plot_detail_infowindow.html',RequestContext(request,{
            'plot': plot,
            'tree': plot.current_tree()
        }))
    else:
        current_tree = plot.current_tree()
        history = plot.history.order_by('-last_updated')[:5]
        if current_tree:
            history = list(chain(history, current_tree.history.order_by('-last_updated')[:5]))
        recent_edits = unified_history(history)
        if request.user.is_authenticated() and current_tree:
            favorite = TreeFavorite.objects.filter(user=request.user, tree=current_tree).count() > 0
        else:
            favorite = None
        return render_to_response('treemap/tree_detail.html',RequestContext(request,{'favorite': favorite, 'tree':current_tree, 'plot': plot, 'recent': recent_edits}))

@login_required
def plot_add_tree(request, plot_id): 
    user = request.user
    tree = Tree()
    plot = Plot.objects.get(pk=plot_id)
    tree.plot = plot
    import_event, created = ImportEvent.objects.get_or_create(file_name='site_add',)
    tree.import_event = import_event
    tree.last_updated_by = request.user
    tree.save()

    history = plot.history.order_by('-last_updated')[:5]
    if tree:
        history = list(chain(history, tree.history.order_by('-last_updated')[:5]))
    recent_edits = unified_history(history)

    change_reputation_for_user(user, 'add tree', tree)
    return render_to_json({'status':'success'})

def unified_history(trees, plots=[]):
    recent_edits = []
    for t in trees:
        if t._audit_change_type == "I":
            edit = "New Tree"
        else:
            if t._audit_diff:
                edit = clean_key_names(t._audit_diff)
            else:
                edit = ""
        recent_edits.append((t.last_updated_by.username, t.last_updated, edit))

    for p in plots:
        if p._audit_change_type == "I":
            edit = "New Plot"
        else:
            if p._audit_diff:
                edit = clean_key_names(p.audit_diff)
            else:
                edit = ""
        recent_edits.append((p.last_updated_by.username, p.last_updated, edit))


    # sort by the date descending
    return sorted(recent_edits, key=itemgetter(1), reverse=True)

   
def tree_edit_choices(request, tree_id, type_):
    tree = get_object_or_404(Tree, pk=tree_id)
    choices = settings.CHOICES[type_]
    data = SortedDict(choices)
    if hasattr(tree, type_):
        val = getattr(tree, type_)
        data['selected'] = val   
    else:
        #TODO: this code looks to be defunct after switch to choices.py archetecture
        if type_ == "condition":
            sidewalks = tree.treestatus_set.filter(key="condition").order_by("-reported")
            if sidewalks.count():
                data['selected'] = str(int(sidewalks[0].value))
        if type_ == "canopy_condition":
            sidewalks = tree.treestatus_set.filter(key="canopy_condition").order_by("-reported")
            if sidewalks.count():
                data['selected'] = str(int(sidewalks[0].value))
    return HttpResponse(simplejson.dumps(data))    

  
def plot_edit_choices(request, plot_id, type_):
    plot = get_object_or_404(Plot, pk=plot_id)
    choices = settings.CHOICES[type_]
    data = SortedDict(choices)
    if hasattr(plot, type_):
        val = getattr(plot, type_)
        data['selected'] = val   
    else:
        #TODO: this code looks to be defunct after switch to choices.py archetecture
        if type_ == "sidewalk_damage":
            sidewalks = plot.treestatus_set.filter(key="sidewalk_damage").order_by("-reported")
            if sidewalks.count():
                data['selected'] = str(int(sidewalks[0].value))
    return HttpResponse(simplejson.dumps(data))    

#http://docs.djangoproject.com/en/dev/topics/forms/modelforms/#model-formsets
# todo - convert into formsets, to allow adding many photos
# todo - allow editing/deleting existing photos
@login_required    
def tree_add_edit_photos(request, tree_id = ''):

    tree = get_object_or_404(Tree, pk=tree_id)
    # allowing non-owners to edit
    # http://sftrees.securemaps.com/ticket/140
    #if not request.user in (tree.data_owner, tree.tree_owner) and not request.user.is_superuser:
    #    return render_to_response("not_allowed.html", {'user' : request.user, "error_message":"You are not the owner of this tree."})
    if request.method == 'POST':
        form = TreeEditPhotoForm(request.POST,request.FILES)
        if form.is_valid():
            photo = form.save(commit=False)
            photo.reported_by = request.user
            # gets saved at the right time when calling add()
            #photo.save()
            tree.treephoto_set.add(photo)
            return redirect('trees/%s/edit/' % tree.id)
    else:
        form = TreeEditPhotoForm(instance=tree)

    return render_to_response('add_edit_photos.html',RequestContext(request,{ 'instance': tree, 'form': form }))        
         

@login_required
#TODO: possibly unused
def batch_edit(request):
    return render_to_response('treemap/batch_edit.html',RequestContext(request,{ }))

@login_required
def tree_edit(request, tree_id = ''):
    
    tree = get_object_or_404(Tree, pk=tree_id, present=True)
    #if not request.user in (tree.data_owner, tree.tree_owner) and not request.user.is_superuser:
    #    return render_to_response("not_allowed.html", {'user' : request.user, "error_message":"You are not the owner of this tree."})
    
    reputation = {        
        "base_edit": Permission.objects.get(name = 'can_edit_condition'),
        "user_rep": Reputation.objects.reputation_for_user(request.user)    
    }

    return render_to_response('treemap/tree_edit.html',RequestContext(request,{ 'tree': tree, 'plot': tree.plot, 'reputation': reputation, 'user': request.user}))           

@login_required
def plot_edit(request, plot_id = ''):
    plot = get_object_or_404(Plot, pk=plot_id, present=True)
    reputation = {        
        "base_edit": Permission.objects.get(name = 'can_edit_condition'),
        "user_rep": Reputation.objects.reputation_for_user(request.user)    
    }

    return render_to_response('treemap/tree_edit.html',RequestContext(request,{ 'tree': plot.current_tree(), 'plot': plot, 'reputation': reputation, 'user': request.user}))   

@transaction.commit_on_success
def tree_delete(request, tree_id):
    tree = Tree.objects.get(pk=tree_id)
    tree.remove()
    
    return HttpResponse(
        simplejson.dumps({'success':True}, sort_keys=True, indent=4),
        content_type = 'text/plain'
    )

@transaction.commit_on_success
def plot_delete(request, plot_id):
    plot = Plot.objects.get(pk=plot_id)
    plot.remove()
    
    return HttpResponse(
        simplejson.dumps({'success':True}, sort_keys=True, indent=4),
        content_type = 'text/plain'
    )

def photo_delete(request, tree_id, photo_id):    
    tree = Tree.objects.get(pk=tree_id)
    photo = TreePhoto.objects.get(pk=photo_id)
    photo.delete()
    
    return HttpResponse(
        simplejson.dumps({'success':True}, sort_keys=True, indent=4),
        content_type = 'text/plain'
    )
    
def userphoto_delete(request, username):
    profile = UserProfile.objects.get(user__username=username)
    profile.photo = ""
    profile.save()
    
    return HttpResponse(
        simplejson.dumps({'success':True}, sort_keys=True, indent=4),
        content_type = 'text/plain'
    )

from django.contrib.auth.decorators import permission_required

@login_required
@permission_required('auth.change_user')
def edit_users(request):        
    users = User.objects.all()
    if 'username' in request.GET:
        users = users.filter(username__icontains=request.GET['username'])
    if 'name' in request.GET:
        users = users.filter(Q(first_name__icontains=request.GET['name']) | Q(last_name__icontains=request.GET['name']) | Q(email__icontains=request.GET['name']))
    if 'group' in request.GET:
        g = Group.objects.filter(name__icontains=request.GET['group'])
        if g.count() == 1:
            users = users.filter(groups=g)
        else:
            users = users.filter(groups__in=g)
    
    groups = Group.objects.all()
    return render_to_response('treemap/user_edit.html',RequestContext(request, {'users': users, 'groups': groups}))

@permission_required('auth.change_user')
def update_users(request):
    response_dict = {}
    if request.method == 'POST':
        post = simplejson.loads(request.raw_post_data)
    
    if post.get('rep_total'):  
        id = post.get('user_id')
        user = User.objects.get(pk=id)
        user.reputation.reputation = int(post.get('rep_total'))
        user.reputation.save()
        response_dict['success'] = True
    elif post.get('group_id'):
        id = post.get('user_id')
        gid = post.get('group_id')
        user = User.objects.get(pk=id)
        try:
            group = Group.objects.get(pk=gid)
            user.groups.clear()
            user.groups.add(group)
            rep = Reputation.objects.reputation_for_user(user)
            #increase rep if now part of an 'admin' group and too low
            if user.has_perm('django_reputation.change_reputation') and rep.reputation < 1000:
                user.reputation.reputation = 1001
                user.reputation.save()
                response_dict['new_rep'] = user.reputation.reputation
                response_dict['user_id'] = user.id
        except Exception:
            user.groups.clear()
        
        response_dict['success'] = True
    else:
        raise Http404
    
    return HttpResponse(
        simplejson.dumps(response_dict, sort_keys=True, indent=4),
        content_type = 'text/plain'
    )

@permission_required('auth.change_user')
def user_opt_in_list(request):
    users = UserProfile.objects.filter(active=True)
    if 'username' in request.GET:
        users = users.filter(user__username__icontains=request.GET['username'])
    if 'email' in request.GET:
        users = users.filter(user__email__icontains=request.GET['email'])
    if 'status' in request.GET:
        update_bool = request.GET['status'].lower() == "true"
        users = users.filter(updates=update_bool)

    return render_to_response('treemap/admin_emails.html',RequestContext(request, {'users': users}))

@permission_required('auth.change_user')
def user_opt_export(request, format):
    users = UserProfile.objects.filter(active=True)
    where = []
    if 'username' in request.GET:
        users = users.filter(user__username__icontains=request.GET['username'])
        where.append(" a.username ilike '%" + request.GET['username'] + "%' ")
    if 'email' in request.GET:
        users = users.filter(user__email__icontains=request.GET['email'])
        where.append(" a.email ilike '%" + request.GET['email'] + "%' ")
    if 'status' in request.GET:
        update_bool = request.GET['status'].lower() == "true"
        users = users.filter(updates=update_bool)
        where.append(" b.updates is " + str(update_bool) + " ")

    sql = "select a.username, a.email, case when b.updates = 't' then 'True' when b.updates = 'f' then 'False' end as \"opt-in\" from auth_user as a, profiles_userprofile as b where b.user_id = a.id"
    if len(where) > 0:
        sql = sql + " and " + ' and '.join(where)
    
    return ogr_conversion('CSV', [{'name':'emails', 'sql':sql}], name="emails", geo=False)    

@permission_required('auth.change_user')
def ban_user(request):
    response_dict = {}
    if request.method == 'POST':
        post = simplejson.loads(request.raw_post_data)
        user = User.objects.get(pk=post.get('user_id'))
        user.is_active = False
        user.save()
        response_dict['user_id'] = user.id
        
    response_dict['success'] = True
     
    return HttpResponse(
        simplejson.dumps(response_dict, sort_keys=True, indent=4),
        content_type = 'text/plain'
    )
    
@permission_required('auth.change_user')
def unban_user(request):
    response_dict = {}
    if request.method == 'POST':
        post = simplejson.loads(request.raw_post_data)
        user = User.objects.get(pk=post.get('user_id'))
        user.is_active = True
        user.save()
        response_dict['user_id'] = user.id

    response_dict['success'] = True

    return HttpResponse(
        simplejson.dumps(response_dict, sort_keys=True, indent=4),
        content_type = 'text/plain'
    )
        

# http://docs.djangoproject.com/en/dev/topics/db/transactions/
# specific imports needed for the below view, keeping here in case
# this view gets moved elsewhere...
from django.db import transaction
from django.db.models.loading import get_model
from django.forms import ModelForm
from datetime import datetime
from django.core.exceptions import ValidationError
import sys
@login_required
@transaction.commit_manually
@csrf_view_exempt
#TODO: is this used?
def multi_status(request):
    if request.method == 'POST':
        if request.META['SERVER_NAME'] == 'testserver':
            post = request.POST        
        else:
            post = simplejson.loads(request.raw_post_data)
    id = post.get('id')
    tree = Tree.objects.get(pk=id)
    key = post.get('key')
    tree.treestatus_set.filter(key=key).delete()
    for val in post.get("values"):
        ts = TreeStatus(key=key, val=val, tree=tree)
        ts.save()
    return HttpResponse("OK")    

def get_tree_pend_or_plot_pend_by_id_or_404_not_found(pend_id):
    try:
        pend = TreePending.objects.get(pk=pend_id)
        model_name = 'Tree'
    except TreePending.DoesNotExist:
        pend = None
        model_name = None

    if not pend:
        try:
            pend = PlotPending.objects.get(pk=pend_id)
            model_name = 'Plot'
        except PlotPending.DoesNotExist:
            pend = None
            model_name = None

    if not pend:
        raise Http404

    return pend, model_name

@login_required
@permission_required_or_403_forbidden('treemap.change_pending')
def approve_pend(request, pend_id):
    pend, model = get_tree_pend_or_plot_pend_by_id_or_404_not_found(pend_id)

    pend.approve_and_reject_other_active_pends_for_the_same_field(request.user)

    if model == 'Tree':
        change_reputation_for_user(pend.submitted_by, 'edit tree', pend.tree, change_initiated_by_user=pend.updated_by)
    else: # model == 'Plot'
        change_reputation_for_user(pend.submitted_by, 'edit plot', pend.plot, change_initiated_by_user=pend.updated_by)

    return HttpResponse(
        simplejson.dumps({'success': True, 'pend_id': pend_id}, sort_keys=True, indent=4),
        content_type = 'text/plain'
    ) 

@login_required
@permission_required_or_403_forbidden('treemap.change_pending')
def reject_pend(request, pend_id):
    pend, model = get_tree_pend_or_plot_pend_by_id_or_404_not_found(pend_id)
    pend.reject(request.user)
    return HttpResponse(
        simplejson.dumps({'success': True, 'pend_id': pend_id}, sort_keys=True, indent=4),
        content_type = 'text/plain'
    ) 

@login_required
@permission_required('auth.change_user')
def view_pends(request):
    tree_pends = TreePending.objects.all()
    plot_pends = PlotPending.objects.all()
    if 'username' in request.GET:
        u = User.objects.filter(username__icontains=request.GET['username'])
        tree_pends = tree_pends.filter(submitted_by__in=u)
        plot_pends = plot_pends.filter(submitted_by__in=u)
    if 'address' in request.GET:
        tree_pends = tree_pends.filter(tree__plot__address_street__icontains=request.GET['address'])
        plot_pends = plot_pends.filter(address_street__icontains=request.GET['address'])
    if 'nhood' in request.GET:
        n = Neighborhood.objects.filter(name=request.GET['nhood'])
        tree_pends = tree_pends.filter(tree__plot__neighborhood=n)
        plot_pends = plot_pends.filter(neighborhood=n)
    if 'status' in request.GET:
        tree_pends = tree_pends.filter(status=request.GET['status'])
        plot_pends = plot_pends.filter(status=request.GET['status'])

    pends = list(chain(tree_pends, plot_pends)) # chain comes from itertools
    return render_to_response('treemap/admin_pending.html',RequestContext(request,{'pends': pends}))

@login_required
@permission_required('auth.change_user')
def view_stewardship(request):
    tree_activity = TreeStewardship.objects.all()
    plot_activity = PlotStewardship.objects.all()
    if 'username' in request.GET:
        u = User.objects.filter(username__icontains=request.GET['username'])
        tree_activity = tree_activity.filter(performed_by__in=u)
        plot_activity = plot_activity.filter(performed_by__in=u)
    if 'address' in request.GET:
        tree_activity = tree_activity.filter(tree__plot__address_street__icontains=request.GET['address'])
        plot_activity = plot_activity.filter(plot__address_street__icontains=request.GET['address'])
    if 'nhood' in request.GET:
        n = Neighborhood.objects.filter(name=request.GET['nhood'])
        tree_activity = tree_activity.filter(tree__plot__neighborhood=n)
        plot_activity = plot_activity.filter(plot__neighborhood=n)
    if 'status' in request.GET:
        tree_activity = tree_activity.filter(activity=request.GET['status'])
        plot_activity = plot_activity.filter(activity=request.GET['status'])
    if 'target' in request.GET:
        if request.GET['target'] == 'plot':
            tree_activity = TreeStewardship.objects.none()
        if request.GET['target'] == 'tree':
            plot_activity = PlotStewardship.objects.none()

    activities = list(chain(tree_activity, plot_activity)) # chain comes from itertools
    activities = sorted(activities, key=attrgetter('performed_date'))
    return render_to_response('treemap/admin_stewardship.html',RequestContext(request,{'activities': activities}))

@login_required
@transaction.commit_manually
@csrf_view_exempt
def object_update(request):
    """
    Generic record and row based update view.
    
    Accepts POST data only, consisting of:
    
      model: model name,
      id: record id,
      update: dict of fields to update with value,
      parent: model/id the posted data should be added to
    
    """ 
           
    response_dict = {'success': False, 'errors': []}
        
    parent_instance = None
    post = {}
    
    if request.method == 'POST':
        if request.META['SERVER_NAME'] == 'testserver':
            post = request.POST        
        else:
            post = simplejson.loads(request.raw_post_data)
    else:
        response_dict['errors'].append('Please POST data')
    
    if post.get('model'):
        mod_name = post['model']
        model_object = get_model(get_app(mod_name),mod_name)
        if not model_object:
            response_dict['errors'].append('Model %s not found' % post['model'])
        else:
            if post.get('id'):
                # assume if passed an 'id' we are
                # updating a model instance/record
                instance = model_object._default_manager.get(pk=int(post['id']))
                if not instance:
                    response_dict['errors'].append('Record id %s not found' % int(post['id']))
            else:
                # if not passed an 'id' assume we
                # are creating a new instance/record
                instance = model_object()
    
            update = post.get('update')
            delete = post.get('delete')
            parent = post.get('parent')
            
            if delete:
                response_dict['delete'] = {}
                parent_object = get_model('treemap',parent['model'])
                parent_instance = parent_object._default_manager.get(pk=int(parent['id']))
                all = model_object.objects.filter(tree=parent_instance)
                exc = []
                if request.user.is_superuser:
                    all = all.filter(reported_by=request.user)
                for k,v in delete.items():
                    all = all.filter(**{str(k):v})
                ids = [x.id for x in all]    
                if all.count():
                    all.delete()
                    response_dict['delete']['ids'] = ids
            
           

            if update:
                response_dict['update'] = {}
 
                #check pending feature status and user permisisons
                #{"model":"Tree","update":{"height":10},"id":6}
                #{"model":"Tree","update":{"species_id":397},"id":6}
                #{"model":"Tree","id":6,"update":{"address_street":"12th and L","address_city":"Sacramento","address_zip":"95814","geometry":"POINT (-121.49136539755177 38.5773014443589)"}}
                
                    # if the tree was added by the public, or the current user is not public, skip pending
                if settings.PENDING_ON and (post['model'] == "Tree" or post['model'] == "Plot"):
                    audit_insert_records = instance.history.filter(_audit_change_type='I')
                    if len(audit_insert_records) > 0:
                        insert_event_mgmt = audit_insert_records[0].last_updated_by.has_perm('auth.change_user')
                    else:
                        insert_event_mgmt = True # If the insert audit record is missing, assume it was created by a manager

                    mgmt_user = request.user.has_perm('auth.change_user')
                    if insert_event_mgmt and not mgmt_user:
                        for k,v in update.items():  
                            fld = instance._meta.get_field(k.replace('_id',''))
                            try:
                                cleaned = fld.clean(v,instance)
                                response_dict['pending'] = 'true'

                                response_dict['update']['old_' + k] = getattr(instance,k).__str__()
                                response_dict['update'][k] = 'Pending'

                                if post['model'] == "Tree":
                                    pend = TreePending(tree=instance)
                                else: # post['model'] == "Plot":
                                    pend = PlotPending(plot=instance)
                                    if k == 'geometry':
                                        pend.geometry = cleaned
                                    else:
                                        # Omit the geometry so that PlotPending.approve will use the text value
                                        pend.geometry = None

                                pend.field = k
                                pend.value = cleaned
                                pend.submitted_by = request.user
                                pend.status = 'pending'
                                pend.updated_by = request.user

                                if k == 'species_id':
                                    pend.text_value = Species.objects.get(id=v).scientific_name

                                for field in instance._meta.fields:
                                    if str(field.name) == str(fld.name):
                                        for choice in field.choices:
                                            if str(choice[0]) == str(cleaned):
                                                pend.text_value = choice[1]
                                                break
                                        break

                                pend.save()

                            except ValidationError,e:
                                response_dict['errors'].append(e.messages[0])
                            except Exception,e:
                                response_dict['errors'].append('Error editing %s: %s' % (k,str(e)))
                            if len(response_dict['errors']):
                                transaction.rollback()
                            else:
                                transaction.commit()    
                                response_dict['success'] = True

                        return HttpResponse(
                                simplejson.dumps(response_dict, sort_keys=True, indent=4),
                                #content_type = 'application/javascript; charset=utf8'
                                content_type = 'text/plain'
                                )
                # attempts to use forms...
                # not working as nicely as I'd want
                # will likely circle back to using the approach
                # once the basics are proven to be working
                # so that custom clean() methods can added to form
                # and therefore used here...

                #updates.update({'last_updated_by':request.user.id})
                #class MyForm(ModelForm):
                #    class Meta:
                #        model = model_object
                #        exclude = [f.name for f in model_object._meta.fields if True in (f.null,f.blank)]       
                #form = MyForm(updates,instance=instance)
                #import pdb;pdb.set_trace()
                #form.instance.last_updated_by = request.user
                #if not form.is_valid():
                #    response_dict.update({'success': False })
                #    response_dict['errors'].update(form.errors)
                                        
                # re-implement just the pieces of form validation
                # we need which is per field cleaning
                
                #if hasattr(instance,'key') and hasattr(instance,'value'):
                #    iterable = update.items()
                #else:
                    #iterable = []
                    #for k,v in update.items():
                #if update.get('key') == 'circ':
                #   update['key'] = 'dbh'
                #   circ = update.get('value')
                #   if circ:
                #       update['value'] = circ/math.pi 
                #   #response_dict['update']['']  
                for k,v in update.items():
                    if hasattr(instance,k):
                        #print k,v
                        fld = instance._meta.get_field(k.replace('_id',''))
                        try:
                            if k == 'species_id':
                                response_dict['update']['old_' + k] = instance.get_scientific_name()
                                instance.set_species(v,commit=False)
                            else:
                                # old value for non-status objects only, status objects return None
                                # and are handled after parent model is set
                                response_dict['update']['old_' + k] = getattr(instance,k).__str__()
                                cleaned = fld.clean(v,instance)
                                setattr(instance,k,cleaned)
                        except ValidationError,e:
                            response_dict['errors'].append(e.messages[0])
                        except Exception,e:
                            response_dict['errors'].append('Error editing %s: %s' % (k,str(e)))

                        if hasattr(instance,'display'):
                            value = getattr(instance,'display')
                        elif hasattr(instance,'get_%s_display' % k):
                            value = getattr(instance,'get_%s_display' % k)()
                        else:    
                            value = getattr(instance, k)

                        if isinstance(value,datetime): 
                            value = value.strftime('%b %d %Y')
                        elif not isinstance(value, basestring):
                            value = unicode(value)

                        if k == "key" and value == "None":
                            for s in status_choices:
                                if v == s[0]: value = s[1]
                        response_dict['update'][k] = value
                    else:
                        response_dict['errors'].append("%s does not have a '%s' attribute" % (instance,k))

            # todo - try to make this more generic...
            # needs to be set on Tree model
            if hasattr(instance,'last_updated_by_id'):
                instance.last_updated_by = request.user
            # needs to be set on models inheriting from TreeItem 
            if hasattr(instance,'reported_by_id'):
                instance.reported_by = request.user
            
            if parent and not delete:
                parent_object = get_model('treemap',parent['model'])
                if not parent_object:
                    response_dict['errors'].append('Parent model "%s" not found' % parent['model'])
                else:
                    # TODO - can't assume parent is Tree model...
                    parent_instance = parent_object._default_manager.get(pk=int(parent['id']))
                    if not parent_instance:
                        response_dict['errors'].append('Parent object #%s not found' % parent['id'])
                    else:
                        parent_instance.last_updated = datetime.now()
                        parent_instance.last_updated_by = request.user
                        try:
                            # get the foreignkey related manager of the parent to be able to 
                            # add the new instance back to the parent object
                            # eg. Tree.objects.all()[1].treestatus_set
                            set = getattr(parent_instance,post['model'].lower() + '_set')
                            set.add(instance)
                            #if response_dict['update'].has_key('old_value'):
                            #    history = model_object.history.filter(tree__id__exact=instance.tree.id).filter(key__exact=instance.key).filter(_audit_change_type__exact="U").order_by('-reported')
                            #    if history.count() == 0:
                            #        history = model_object.history.filter(tree__id__exact=instance.tree.id).filter(key__exact=instance.key).filter(_audit_change_type__exact="I").order_by('reported')
                            #    if history.count() > 0:
                            #        if isinstance(history[0].value, datetime):
                            #            response_dict['update']['old_value'] = history[0].value.strftime("%b %d %Y")
                            #        else:
                            #            response_dict['update']['old_value'] = history[0].value.__str__()
                        except Exception, e:
                            response_dict['errors'].append('Error setting related obj: %s: %s' % (sys.exc_type,str(e)))

            # finally save the instance...
            try:
                if not delete:
                    instance._audit_diff = simplejson.dumps(response_dict["update"])
                    instance.save()
                    if post['model'] in  ["Tree", "TreeFlags", "Plot"] :
                        if post['model'] == 'Plot':
                            action_name = 'edit plot'
                        else:
                            action_name = 'edit tree'
                        change_reputation_for_user(request.user, action_name, instance)
                    if hasattr(instance, 'validate_all'):
                        instance.validate_all()
                if parent_instance:
                    #pass
                    parent_instance._audit_diff = simplejson.dumps(response_dict["update"])
                    parent_instance.save()
                    #print "instance parent save"
                    #print parent_instance, instance
            except Exception, e:
                response_dict['errors'].append('Related - %s: %s' % (sys.exc_type,str(e)))

    if len(response_dict['errors']):
        transaction.rollback()
    else:
        transaction.commit()    
        response_dict['success'] = True

    return HttpResponse(
            simplejson.dumps(response_dict, sort_keys=True, indent=4),
            content_type = 'text/plain'
            )


def create_pending_records(plot_base, plot_new_flds, user):
    pends = []
    for fld, new_field_val in plot_new_flds.iteritems():
        if getattr(plot_base, fld) is not new_field_val:
            pend = PlotPending(plot=plot_base, field=fld, value=new_field_val, status='pending')
            pend.submitted_by = pend.updated_by = user
        
            if fld == 'geometry':
                pend.geometry = plot_new_flds

            for field in Plot._meta.fields:
                if str(field.name) == str(fld):
                    for choice in field.choices:
                        if str(choice[0]) == str(new_field_val):
                            pend.text_value = choice[1]
                            break
                    break

            pends.append(pend)

    return pends

def parse_post(request):
    if request.META['SERVER_NAME'] == 'testserver':
        post = request.POST        
    else:
        post = simplejson.loads(request.raw_post_data)

    return post

@login_required
@csrf_view_exempt
def add_tree_stewardship(request, tree_id):
    """ Add stewardship activity to a tree """
    response_dict = {'success': False, 'errors': []}

    post = {}
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    post = parse_post(request)
    tree = get_object_or_404(Tree, pk=tree_id)
    
    try:
        date = datetime.strptime(post['performed_date'],'%m/%d/%Y')
        activity = TreeStewardship(performed_by=request.user, tree=tree, activity=post['activity'], performed_date=date)
        activity.save()
        change_reputation_for_user(request.user, 'add stewardship', activity)
    except ValidationError, e:
        if hasattr(e, 'message_dict'):
            for (fld,msgs) in e.message_dict.items():
                msg = reduce(lambda (a,b): a + b, msgs)
                response_dict["errors"].append("%s: %s" % (fld, msg))
        else:
            response_dict["errors"] += e.messages    
    
    if len(response_dict["errors"]) == 0:
        response_dict['success'] = True
        response_dict['update'] = {}        
        response_dict['update']['activity'] = activity.activity  
        response_dict['update']['performed_date'] = activity.performed_date.strftime("%m/%d/%Y")   

    return HttpResponse(
            simplejson.dumps(response_dict),
            content_type = 'application/json')

@login_required
@csrf_view_exempt
def add_plot_stewardship(request, plot_id):
    """ Add stewardship activity to a plot """
    response_dict = {'success': False, 'errors': []}

    post = {}
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    post = parse_post(request)
    plot = get_object_or_404(Plot, pk=plot_id)
    
    try:
        date = datetime.strptime(post['performed_date'],'%m/%d/%Y')
        activity = PlotStewardship(performed_by=request.user, plot=plot, activity=post['activity'], performed_date=date)
        activity.save()
        change_reputation_for_user(request.user, 'add stewardship', activity)
    except ValidationError, e:
        if hasattr(e, 'message_dict'):
            for (fld,msgs) in e.message_dict.items():
                msg = reduce(lambda (a,b): a + b, msgs)
                response_dict["errors"].append("%s: %s" % (fld, msg))
        else:
            response_dict["errors"] += e.messages    
    
    if len(response_dict["errors"]) == 0:
        response_dict['success'] = True
        response_dict['update'] = {}        
        response_dict['update']['activity'] = activity.activity    
        response_dict['update']['performed_date'] = activity.performed_date.strftime("%m/%d/%Y")

    return HttpResponse(
            simplejson.dumps(response_dict),
            content_type = 'application/json')

@login_required
@csrf_view_exempt
def delete_tree_stewardship(request, tree_id, activity_id):
    activity = get_object_or_404(TreeStewardship, pk=activity_id)
    activity.delete()
    change_reputation_for_user(request.user, 'remove stewardship', activity)
    return HttpResponse(
            simplejson.dumps({'success': True}),
            content_type = 'application/json')

@login_required
@csrf_view_exempt
def delete_plot_stewardship(request, plot_id, activity_id):
    activity = get_object_or_404(PlotStewardship, pk=activity_id)
    activity.delete()
    change_reputation_for_user(request.user, 'remove stewardship', activity)
    return HttpResponse(
            simplejson.dumps({'success': True}),
            content_type = 'application/json')

@login_required
@csrf_view_exempt
def update_plot(request, plot_id):
    """ Update items for a given plot """
    response_dict = {'success': False, 'errors': []}
    valid_fields = ["present","width","length","type","powerline_conflict_potential",
                    "sidewalk_damage","address_street","address_city","address_zip", 
                    "owner_additional_id" ]

    post = {}
    
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    post = parse_post(request)
    plot = get_object_or_404(Plot, pk=plot_id)

    # Update fields
    for k,v in post.items():
        if hasattr(plot, k) and k in valid_fields:
            setattr(plot, k, v)
        else:
            response_dict["errors"].append("Unknown or invalid update field: %s" % k)

    try:
        plot.validate()


        if settings.PENDING_ON :
            # if the tree was added by the public, or the current user is not public, skip pending
            audit_insert_records = plot.history.filter(_audit_change_type='I')
            if len(audit_insert_records) > 0:
                insert_event_mgmt = audit_insert_records[0].last_updated_by.has_perm('auth.change_user')
            else:
                insert_event_mgmt = True # If the insert audit record is missing, assume it was created by a manager
            mgmt_user = request.user.has_perm('auth.change_user')
            if insert_event_mgmt and not mgmt_user:
                # Get a clean plot object
                plot = get_object_or_404(Plot, pk=plot_id)

                for r in create_pending_records(plot, post, request.user):
                    r.save()

            else:
                plot.last_updated_by = request.user

                # finally save the instance...
                plot._audit_diff = simplejson.dumps(post)
                plot.save()

                change_reputation_for_user(request.user, 'edit plot', plot)

        else:
            plot.last_updated_by = request.user

            # finally save the instance...
            plot._audit_diff = simplejson.dumps(post)
            plot.save()
            change_reputation_for_user(request.user, 'edit plot', plot)

    except ValidationError, e:
        if hasattr(e, 'message_dict'):
            for (fld,msgs) in e.message_dict.items():
                msg = reduce(lambda (a,b): a + b, msgs)
                response_dict["errors"].append("%s: %s" % (fld, msg))
        else:
            response_dict["errors"] += e.messages        
        
    if len(response_dict["errors"]) == 0:
        response_dict['success'] = True
        response_dict['update'] = {}
        
        plot = get_object_or_404(Plot, pk=plot_id)
        for k,v in post.items():
            response_dict['update'][k] = get_attr_or_display(plot,k)
            if settings.PENDING_ON:
                if insert_event_mgmt and not mgmt_user:
                    response_dict['update'][k] = "Pending"  

    return HttpResponse(
            simplejson.dumps(response_dict),
            content_type = 'application/json')

#TODO: This should be fixed by providing a "__dict__" method on the plot
def get_attr_or_display(model, attr):
    disp = "get_%s_display" % attr
    if hasattr(model, disp):
        return getattr(model, disp)()
    else:
        return getattr(model, attr)

#for auto reverse-geocode saving of new address, from search page map click
def plot_location_update(request):
    response_dict = {}
    post = simplejson.loads(request.raw_post_data)
    plot = Plot.objects.filter(pk=post.get('plot_id'))[0]
    plot.address_street = post.get('address').split(',')[0]
    plot.geocoded_address = post.get('address')
    plot.address_city = post.get('city')
    plot.quick_save()
    
    response_dict['success'] = True
    
    return HttpResponse(
        simplejson.dumps(response_dict, sort_keys=True, indent=4),
        content_type = 'text/plain'
    )

@login_required
def tree_add(request, tree_id = ''):
            
    if request.method == 'POST':
        form = TreeAddForm(request.POST,request.FILES)

        if validate_form(form, request):
            new_tree = form.result

            change_reputation_for_user(request.user, 'add tree', new_tree)

            if form.cleaned_data.get('target') == "add":
                form = TreeAddForm()
                messages.success(request, "Your tree was successfully added!")
            elif form.cleaned_data.get('target') == "addsame":
                messages.success(request, "Your tree was successfully added!")
                pass
            elif form.cleaned_data.get('target') == "view":
                return redirect("trees/new/%i/" % request.user.id)
            elif form.cleaned_data.get('target') == "edit":
                return redirect("plots/%i/edit/" % new_tree.id)
            else:
                return redirect("plots/%i/" % new_tree.id)
    else:
        form = TreeAddForm()
    return render_to_response('treemap/tree_add.html', RequestContext(request,{
        'user' : request.user, 
        'form' : form }))

def added_today_list(request, user_id=None, format=None):
    user = None
    past_date = timedelta(hours=24)
    start_date = datetime.now() - past_date
    end_date = datetime.now()
    new_plots = Plot.history.filter(present=True).filter(_audit_change_type__exact='I').filter(_audit_timestamp__range=(start_date, end_date))
    if user_id:
        user = User.objects.get(pk=user_id)
        new_plots = new_plots.filter(last_updated_by=user)
    plots = []
    for plot in new_plots:
        plots.append(Plot.objects.get(pk=plot.id))
    if format == 'geojson':        
        plot_json = [{
           'id':plot.id, 
           'coords':[plot.geometry.x, plot.geometry.y]} for plot in plots]
        return render_to_json(plot_json)
    return render_to_response('treemap/added_today.html', RequestContext(request,{
        'plots' : plots,
        'user': user}))


def _build_tree_search_result(request, with_benefits=True):
    # todo - optimize! OMG Clean it up! >.<
    tile_query = []
    trees = Tree.objects.filter(present=True).extra(select={'geometry': "select treemap_plot.geometry from treemap_plot where treemap_tree.plot_id = treemap_plot.id"})
    plots = Plot.objects.filter(present=True)

    geog_obj = None
    if 'location' in request.GET:
        loc = request.GET['location']
        z = ZipCode.objects.filter(zip=loc)
        if z.count():
            trees = trees.filter(plot__zipcode = z[0])
            plots = plots.filter(zipcode = z[0])
            geog_obj = z[0]
            tile_query.append("zipcode_id = %d" % z[0].id)
    elif 'distance' in request.GET:
        # geographic search handled in the plot_location_search function
        pass
    else:
        ns = None
        if 'geoName' in request.GET:
            ns = Neighborhood.objects.all().order_by('id')
            geoname = request.GET['geoName']
            ns = ns.filter(name=geoname)
        elif 'hood' in request.GET:
            ns = Neighborhood.objects.all().order_by('id')
            ns = ns.filter(name__icontains = request.GET.get('hood'))
        elif 'lat' in request.GET and 'lon' in request.GET:
            pnt = Point(float(request.GET['lon']), float(request.GET['lat']))
            ns = Neighborhood.objects.all().order_by('id')
            ns = ns.filter(geometry__contains=pnt)
        if ns:
            trees = trees.filter(plot__neighborhood = ns[0])
            plots = plots.filter(neighborhood = ns[0])
            geog_obj = ns[0]
            tile_query.append("(neighborhoods = '%d' OR neighborhoods LIKE '%% %d' OR neighborhoods LIKE '%d %%')" % (geog_obj.id, geog_obj.id, geog_obj.id)) 

    missing_current_plot_size = request.GET.get('missing_plot_size','')
    missing_current_plot_type = request.GET.get('missing_plot_type','')
    if missing_current_plot_size:
        trees = trees.filter(Q(plot__length__isnull=True) | Q(plot__width__isnull=True))
        plots = plots.filter(Q(length__isnull=True) | Q(width__isnull=True))
        tile_query.append(" (plot_length IS NULL OR plot_width IS NULL) ")

    if not missing_current_plot_size and 'plot_range' in request.GET:
        min, max = map(float,request.GET['plot_range'].split("-"))
        trees = trees.filter(Q(plot__length__gte=min) | Q(plot__width__gte=min))
        plots = plots.filter(Q(length__gte=min) | Q(width__gte=min))
        if max != 15: # TODO: Hardcoded in UI, may need to change
            trees = trees.filter(Q(plot__length__lte=max) | Q(plot__length__lte=max))
            plots = plots.filter(Q(length__lte=max) | Q(length__lte=max))
        tile_query.append("( (plot_length BETWEEN " + min.__str__() + " AND " + max.__str__() + ") OR (plot_width BETWEEN " + min.__str__() + " AND " + max.__str__() + ") )")

    if missing_current_plot_type:
        trees = trees.filter(plot__type__isnull=True)
        plots = plots.filter(type__isnull=True)
        tile_query.append(" plot_type IS NULL ")
    else:
        pt_cql = []
        pt_list = []
        for k, v in settings.CHOICES["plot_types"]:
            if v.lower().replace(' ', '_').replace('/','') in request.GET:
                pt_list.append(k)
                pt_cql.append("plot_type = " + k)
        if len(pt_cql) > 0:
            tile_query.append("(" + " OR ".join(pt_cql) + ")")
            trees = trees.filter(plot__type__in=pt_list)
            plots = plots.filter(type__in=pt_list)

    missing_sidewalk = request.GET.get("missing_sidewalk", '')
    if missing_sidewalk: 
        trees = trees.filter(plot__sidewalk_damage__isnull=True)
        plots = plots.filter(sidewalk_damage__isnull=True)
        tile_query.append("sidewalk_damage IS NULL")
    else: 
        s_cql = []
        s_list = []
        for k, v in settings.CHOICES["sidewalks"]:
            if v.lower().replace(' ', "_").replace('/','') in request.GET:
                s_list.append(k)
                s_cql.append("sidewalk_damage = " + k)
        if len(s_cql) > 0:
            tile_query.append("(" + " OR ".join(s_cql) + ")")
            trees = trees.filter(plot__sidewalk_damage__in=s_list)
            plots = plots.filter(sidewalk_damage__in=s_list)
        

    missing_powerlines = request.GET.get("missing_powerlines", '')
    if missing_powerlines:
        trees = trees.filter(plot__powerline_conflict_potential__isnull=True)
        plots = plots.filter(powerline_conflict_potential__isnull=True)
        tile_query.append("powerline_conflict_potential IS NULL")
    else:
        p_cql = []
        p_list = []
        for k, v in settings.CHOICES["powerlines"]:
            if v.lower().replace(" ", "_").replace('/','') in request.GET:
                p_list.append(k)
                p_cql.append("powerline_conflict_potential = " + k)
        if len(p_cql) > 0:
            tile_query.append("(" + " OR ".join(p_cql) + ")")
            trees = trees.filter(plot__powerline_conflict_potential__in=p_list)
            plots = plots.filter(powerline_conflict_potential__in=p_list)

    owner = request.GET.get("owner", "")
    if owner:
        users = User.objects.filter(username__icontains=owner)
        trees = trees.filter(plot__data_owner__in=users)
        plots = plots.filter(data_owner__in=users)
        user_list = []
        for u in users:
            user_list.append("data_owner_id = " + u.id.__str__())
        tile_query.append("(" + " OR ".join(user_list) + ")")

    updated_by = request.GET.get("updated_by", "")
    if updated_by:
        users = User.objects.filter(username__icontains=updated_by)
        trees = trees.filter(last_updated_by__in=users)
        plots = plots.filter(last_updated_by__in=users)
        user_list = []
        for u in users:
            user_list.append("last_updated_by_id = " + u.id.__str__())
        tile_query.append("(" + " OR ".join(user_list) + ")")

    if 'updated_range' in request.GET:
        min, max = map(float,request.GET['updated_range'].split("-"))
        min = datetime.utcfromtimestamp(min)
        max = datetime.utcfromtimestamp(max)
        trees = trees.filter(last_updated__gte=min, last_updated__lte=max)
        plots = plots.filter(last_updated__gte=min, last_updated__lte=max)
        tile_query.append("last_updated AFTER " + min.isoformat() + "Z AND last_updated BEFORE " + max.isoformat() + "Z")   

    local_cql = []
    local_list = []
    for k,v in settings.CHOICES["projects"]:
        if v.lower().replace(' ', '_').replace('/','') in request.GET:
            local = request.GET.get(v.lower().replace(' ', '_'),'')
            if local:
                local_list.append(k)
                local_cql.append("projects LIKE '%" + k + "%'")
    if len(local_cql) > 0:        
        trees = trees.filter(treeflags__key__in=local_list)
        plots = plots.filter(tree__treeflags__key__in=local_list)
        tile_query.append("(" + " OR ".join(local_cql) + ")")

    missing_species = request.GET.get('missing_species','')
    if missing_species:
        trees = trees.filter(species__isnull=True)
        plots = plots.filter(tree__species__isnull=True)
        tile_query.append("species_id IS NULL")
    
    missing_current_dbh = request.GET.get('missing_diameter','')
    if missing_current_dbh:
        trees = trees.filter(Q(dbh__isnull=True) | Q(dbh=0))
        plots = plots.filter(Q(tree__dbh__isnull=True) | Q(tree__dbh=0))
        tile_query.append(" (dbh IS NULL OR dbh = 0) ")
    elif 'diameter_range' in request.GET:
        min, max = map(float,request.GET['diameter_range'].split("-"))
        trees = trees.filter(dbh__gte=min)
        plots = plots.filter(tree__dbh__gte=min)
        if max != 50: # TODO: Hardcoded in UI, shouldn't be
            trees = trees.filter(dbh__lte=max)
            plots = plots.filter(tree__dbh__lte=max)
        tile_query.append("dbh BETWEEN " + min.__str__() + " AND " + max.__str__() + "")

    missing_current_height = request.GET.get('missing_height','')
    if missing_current_height:
        trees = trees.filter(Q(height__isnull=True) | Q(height=0))
        plots = plots.filter(Q(tree__height__isnull=True) | Q(tree__height=0))
        tile_query.append(" (height IS NULL OR height = 0) ")
    elif 'height_range' in request.GET:
        min, max = map(float,request.GET['height_range'].split("-"))
        trees = trees.filter(height__gte=min)
        plots = plots.filter(tree__height__gte=min)
        if max != 200: # TODO: Hardcoded in UI, may need to change
            trees = trees.filter(height__lte=max)
            plots = plots.filter(tree__height__lte=max)
        tile_query.append("height BETWEEN " + min.__str__() + " AND " + max.__str__() + "")

    missing_condition = request.GET.get("missing_condition", '')
    if missing_condition: 
        trees = trees.filter(condition__isnull=True)
        plots = plots.filter(tree__condition__isnull=True)
        tile_query.append("condition IS NULL")
    else:   
        c_cql = []
        c_list = []
        for k, v in settings.CHOICES["conditions"]:
            if v.lower().replace(' ', '_').replace('/','') in request.GET:
                c_list.append(k)
                c_cql.append("condition = " + k)
        if len(c_cql) > 0:
            tile_query.append("(" + " OR ".join(c_cql) + ")")
            trees = trees.filter(condition__in=c_list)
            plots = plots.filter(tree__condition__in=c_list)

    missing_photos = request.GET.get("missing_photos", '')
    if missing_photos:
        trees = trees.filter(treephoto__isnull=True)
        plots = plots.filter(tree__treephoto__isnull=True)
        tile_query.append("(photo_count IS NULL OR photo_count = 0)")
    elif 'photos' in request.GET:
        trees = trees.filter(treephoto__isnull=False)
        plots = plots.filter(tree__treephoto__isnull=False)
        tile_query.append("photo_count > 0")

    steward = request.GET.get("steward", "")
    if steward:    
        users = User.objects.filter(username__icontains=steward)
        trees = trees.filter(Q(steward_user__in=users) | Q(steward_name__icontains=steward))
        plots = plots.filter(Q(tree__steward_user__in=users) | Q(tree__steward_name__icontains=steward))
        user_list = []
        for u in users:
            user_list.append("steward_user_id = " + u.id.__str__())
        tile_query.append("(" + " OR ".join(user_list) + " OR steward_name LIKE '%" + steward + "%')")

    funding = request.GET.get("funding", "")
    if funding:
        trees = trees.filter(sponsor__icontains=funding)
        plots = plots.filter(tree__sponsor__icontains=funding)
        tile_query.append("sponsor LIKE '%" + funding + "%'")

    if 'planted_range' in request.GET:
        min, max = map(float,request.GET['planted_range'].split("-"))
        min = "%i-01-01" % min
        max = "%i-12-31" % max
        trees = trees.filter(date_planted__gte=min, date_planted__lte=max)
        plots = plots.filter(tree__date_planted__gte=min, tree__date_planted__lte=max)
        tile_query.append("date_planted AFTER " + min + "T00:00:00Z AND date_planted BEFORE " + max + "T00:00:00Z")   

    species_criteria = {'species' : 'id',
                        'native' : 'native_status',
                        'edible' : 'palatable_human',
                        'color' : 'fall_conspicuous',
                        'flowering' : 'flower_conspicuous',
                        'wildlife' : 'wildlife_value'}

    if len(set(species_criteria.keys()).intersection(set(request.GET))):
        species = Species.objects.filter(tree_count__gt=0)
        max_species_count = species.count()
        
        for k in species_criteria.keys():
            v = request.GET.get(k,'')
            if v:
                attrib = species_criteria[k]
                if v == 'true': v = True
                species = species.filter(**{attrib:v})
                
        cur_species_count = species.count()
        #TODO: This returns wrong behavior if all species in the database are 
        #      legitimately returned by the criteria above 
        if max_species_count != cur_species_count:
            trees = trees.filter(species__in=species)
            plots = plots.filter(tree__species__in=species)
            species_list = []
            for s in species:
                species_list.append("species_id = " + s.id.__str__())
            tile_query.append("(" + " OR ".join(species_list) + ")")

    stewardship_reverse = request.GET.get("stewardship_reverse", "")
    if stewardship_reverse == "true":
        stewardship_reverse = "NOT"
    else:
        stewardship_reverse = ""

    stewardship_range = request.GET.get("stewardship_range", "") 
    if stewardship_range:
        st_min, st_max = map(float,stewardship_range.split("-"))
        st_min = datetime.utcfromtimestamp(st_min)
        st_max = datetime.utcfromtimestamp(st_max)

    tree_stewardship = request.GET.get("tree_stewardship", "")
    if tree_stewardship:
        actions = tree_stewardship.split(',')
        steward_ids = [s.tree_id for s in TreeStewardship.objects.order_by("tree__id").distinct("tree__id")]
        for a in actions:
            tile_query.append("tree_stewardship_" + a + " IS " + stewardship_reverse + " NULL")
            steward_ids = [s.tree_id for s in TreeStewardship.objects.filter(tree__id__in=steward_ids).filter(activity=a)]
            if stewardship_range:
                tile_query.append("tree_stewardship_" + a + " AFTER " + st_min.isoformat() + "Z AND tree_stewardship_" + a + " BEFORE " + st_max.isoformat() + "Z") 
            
        if stewardship_reverse:
            trees = trees.filter(id__in=steward_ids)  
        else:
            trees = trees.exclude(id__in=steward_ids)
        if stewardship_range:
            trees = trees.exclude(treestewardship__performed_date__lte=st_min)
            trees = trees.exclude(treestewardship__performed_date__gte=st_max)

        plots = Plot.objects.filter(present=True).filter(tree__in=trees)
        
    plot_stewardship = request.GET.get("plot_stewardship", "")
    if plot_stewardship:
        actions = plot_stewardship.split(',')
        steward_ids = [s.plot_id for s in PlotStewardship.objects.order_by("plot__id").distinct("plot__id")]
        for a in actions:
            tile_query.append("plot_stewardship_" + a + " IS " + stewardship_reverse + " NULL")
            steward_ids = [s.plot_id for s in PlotStewardship.objects.filter(plot__id__in=steward_ids).filter(activity=a)] 
            if stewardship_range:
                tile_query.append("plot_stewardship_" + a + " AFTER " + st_min.isoformat() + "Z AND plot_stewardship_" + a + " BEFORE " + st_max.isoformat() + "Z")
        if stewardship_reverse:
            plots = plots.filter(id__in=steward_ids)
        else:
            plots = plots.exclude(id__in=steward_ids)
        if stewardship_range:
            plots = plots.exclude(plotstewardship__performed_date__lte=st_min)
            plots = plots.exclude(plotstewardship__performed_date__gte=st_max)   

        trees = Tree.objects.filter(present=True).extra(select={'geometry': "select treemap_plot.geometry from treemap_plot where treemap_tree.plot_id = treemap_plot.id"}).filter(plot__in=plots)
        
    agg_object = None
    
    if with_benefits:        
        q = request.META['QUERY_STRING'] or ''
        cached_search_agg = AggregateSearchResult.objects.filter(key=q)
        if cached_search_agg.exists() and cached_search_agg[0].ensure_recent(trees.count()):
            agg_object = cached_search_agg[0]
        else:
            fields = [x.name for x in ResourceSummaryModel._meta.fields if not x.name in ['id','aggregatesummarymodel_ptr','key','resourcesummarymodel_ptr','last_updated']]
            with_out_resources = trees.filter(treeresource=None).count() 
            with_resources = trees.count() - with_out_resources        

            agg_object = AggregateSearchResult(key=q)
            agg_object.total_trees = trees.count()
            agg_object.total_plots = plots.count()
            for f in fields:
                fn = 'treeresource__' + f
                s = trees.aggregate(Sum(fn))[fn + '__sum'] or 0.0
                if settings.EXTRAPOLATE_WITH_AVERAGE and with_resources > 0:
                    avg = float(s)/with_resources
                    s += avg * with_out_resources
                setattr(agg_object,f,s)
            try:
                agg_object.save()
            except:
                # another thread has already likely saved the same object...
                pass
    
    return trees, plots, geog_obj, agg_object, ' AND '.join(tile_query)



def zip_files(file_paths,archive_name):
        buffer = StringIO()
        with closing(zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED)) as z:
            for path in file_paths:
                for root, dirs, files in os.walk(path):
                    for f in files:
                        abs_file = os.path.join(root, f)
                        zipf = abs_file[len(path) + len(os.sep):]
                        zipf = zipf.replace('sql_statement', root.split("/")[-1]) # should be trees or plots
                        z.write(abs_file, zipf)

        z.close()
        buffer.flush()
        zip_stream = buffer.getvalue()
        buffer.close()
        return zip_stream

def ogr_conversion(output_type, named_sql, extension=None, name="trees", geo=True):   
    """ 
    given  an output type such as CSV, "ESRI ShapeFile" or KML

    plus a list of named_sql in the form of 
       named_sql =  [{
            "name":"trees", 
            "sql":"SELECT * from treemap_tree...", 
            "srs":'EPSG:4326' #optional, srs default=EPSG:4236
        },
         {
          "name":"plots", 
          "sql":"SELECT * from treemap_plot...", 
          "srs":'EPSG:4326' 
         }] 
        
    renders a response with the appropriate zip file attachment.

    requires gdal/ogr2ogr
    """ 
    
    dbsettings = settings.DATABASES['default'] 
    host = dbsettings['HOST']
    port = dbsettings['PORT']
    if host == '':
        host = 'localhost'
    if port == '':
        port = 5432

    tmp_dirs = []
    done = 0
    for s in named_sql:
        sql_name = s["name"]
        sql = s["sql"]
        srs = s["srs"] if "srs" in s else 'EPSG:4326'        
        
        tmp_dir = os.path.join(tempfile.mkdtemp(), sql_name)
        tmp_dirs.append(tmp_dir)

        if extension != None:
            os.mkdir(tmp_dir)
            tmp_name = os.path.join(tmp_dir, sql_name + "." + extension)
        else:
            tmp_name = tmp_dir
        
        #command is about to get the db password, careful.
        command = ['ogr2ogr', '-sql', sql, '-a_srs', srs, '-f', output_type, tmp_name, 
            'PG:dbname=%s host=%s port=%s password=%s user=%s' % (dbsettings['NAME'], host, port, 
            dbsettings['PASSWORD'], dbsettings['USER'])]
        
        if output_type == 'CSV' and geo:
            command.append('-lco')
            command.append('GEOMETRY=AS_WKT')
        elif output_type == 'ESRI Shapefile' and (sql_name == 'trees'):
            command.append('-nlt')
            command.append('NONE')
        elif output_type == 'ESRI Shapefile' and (sql_name == 'plots'):
            command.append('-nlt')
            command.append('POINT')

        done = None
        try:
            done = subprocess.call(command)
        except:
            raise Exception("ogr2ogr2 command failed (are the gdal binaries installed?)")

        if done != 0: 
            return render_to_json({'status':'error'})

    zipfile = zip_files(tmp_dirs, name)

    response = HttpResponse(zipfile, mimetype='application/zip')
    response['Content-Disposition'] = 'attachment; filename=' + name + '.zip'
    return response

#TODO: not sure this is used anymore
def geo_search(request):
    """
    Given a simple polygon in format: x1 y1,x2 y2,x3 y3,...,x1 y1
    return basic info about trees
    """
    if 'polygon' not in request.REQUEST:
        h = HttpResponse("Expected 'polygon' parameter")
        h.status_code = 500
        return h

    polyWkt = "POLYGON ((%s))" % request.REQUEST['polygon']

    try:
        poly = GEOSGeometry(polyWkt)
    except ValueError:
        h = HttpResponse("Polygon input must be in the format: 'x1 y1,x2 y2,x3 y3,x1 y1'")
        h.status_code = 500
        return h

    #TODO - Generate count?                                                                                                                                  
    trees = Tree.objects.filter(plot__geometry__within=poly, species__isnull=False, dbh__isnull=False).all()
    
    pruned = []
    for tree in trees:
        prune = { "id": tree.pk,
                  "dbh": tree.dbh }
        
        if tree.species and tree.dbh:
            prune["itree_code"] = tree.species.itree_code,
            prune["species"] = tree.species.scientific_name

            pruned.append(prune)

    json = { "count": len(trees), "trees": pruned }

    jsonstr = simplejson.dumps(json)

    if "callback" in request.REQUEST:
        jsonstr = "%s(%s);" % (request.REQUEST["callback"], jsonstr)

    return HttpResponse(jsonstr, mimetype='application/json')

def advanced_search(request, format='json'):
    """
        formats: json (default), geojson, shp, kml, csv
    """  
    response = {}

    trees, plots, geog_object, agg_object, tile_query = _build_tree_search_result(request, True)
    tree_count = trees.count()
    plot_count = plots.count()
    if tree_count == 0:
        tree_query = "SELECT * FROM treemap_tree LIMIT 0";
    else: 
        tree_query = str(trees.query)
    if plot_count == 0:
        plot_query = "SELECT * FROM treemap_plot LIMIT 0";
    else: 
        plot_query = str(plots.query)

    species_query = "SELECT * FROM treemap_species order by id asc"

    trees   = { 'name': 'trees', 'sql': tree_query }
    plots   = { 'name': 'plots', 'sql': plot_query }
    species = { 'name': 'species', 'sql': species_query }

    if format == "shp":
        return ogr_conversion('ESRI Shapefile', [trees, plots])
    elif format == "kml":
        return ogr_conversion('KML', [trees, plots], 'kml')
    elif format == "csv":
        return ogr_conversion('CSV', [trees, plots, species])
        
    full_count = Tree.objects.filter(present=True).count()
    full_plot_count = Plot.objects.filter(present=True).count()
        
    summaries, benefits = {}, {}
    if agg_object:
        benefits = agg_object.get_benefits()
        for field in agg_object._meta.get_all_field_names():
            if field.startswith('total') or field.startswith('annual'):
                summaries[field] = getattr(agg_object, field)

    if format == "geojson":     #still used anywhere? 
        return render_to_geojson(trees, geom_field='geometry', additional_data={'summaries': summaries, 'benefits': benefits})

    geography = None
    if geog_object:
        if hasattr(geog_object, 'geometry'):
            geography = simplejson.loads(geog_object.geometry.simplify(.0001).geojson)
            geography['name'] = str(geog_object)
        
    response.update({'tile_query' : tile_query, 'summaries' : summaries, 'benefits': benefits, 'geography' : geography, 'initial_tree_count' : tree_count, 'full_tree_count': full_count, 'full_plot_count': full_plot_count})
    return render_to_json(response)

    
def summaries(request, model, id=''):    
    location = request.GET.get('location','')
    coords = map(float,location.split(','))
    pt = Point(coords)
    ns = ns.filter(geometry__contains=pt)
    [x.name for x in AggregateSummaryModel._meta.fields if 'id' not in x.name]


def check_username(request):
    name = request.GET.get('u')
    if name:
        names = User.objects.filter(username__iexact=name)
        if names.exists():
            return render_to_json({'status':'username "%s" not available' % name})
    return render_to_json({'status':''})

#@cache_page(60*5)    
def geographies(request, model, id=''):
    """
    return list of nhbds and resource attrs, possibly in json format
    """
    format = request.GET.get('format','html')
    location = request.GET.get('location','')
    name = request.GET.get('name', '')
    list = request.GET.get('list', '')
    
    ns = model.objects.all().order_by('state','county','name')
    if location:
        coords = map(float,location.split(','))
        pt = Point(coords)
        ns = ns.filter(geometry__contains=pt)
    
    if id:
        ns = ns.filter(id=id)
    if name:
        ns = ns.filter(name__iexact=name)[:1]
        #print ns
    if list:        
        ns = ns.exclude(aggregates__total_plots=0)
    if format.lower() == 'json':
        #print ns
        return render_to_geojson(ns, simplify=.0005)
    if id:
        if format.lower() == 'infowindow':
            return render_to_response('treemap/geography_detail_infowindow.html',RequestContext(request,{'object':ns[0]}))
        return render_to_response('treemap/geography_detail.html',RequestContext(request,{'object':ns[0]}))
    return render_to_response('treemap/geography.html',RequestContext(request,{'objects':ns}))
#make some atom feeds

@cache_page(60*5)    
def zips(request):
    """
    return list of nhbds and resource attrs, possibly in json format
    """
    name = request.GET.get('name', '')
    list = request.GET.get('list', '')
    #print list
    
    ns = ZipCode.objects.all()
    
    if name:
        ns = ns.filter(zip__iexact=name)
    return render_to_geojson(ns, simplify=.0005)
    
def contact(request):
    if request.method == 'POST': 
        form = ContactForm(request.POST) 
        if form.is_valid():
            subject = form.cleaned_data['subject']
            sender = form.cleaned_data['sender']
            message = 'The following feedback was submitted from %s  \n\n' % sender 
            message += form.cleaned_data['message']
            cc_myself = form.cleaned_data['cc_myself']

            recipients = settings.CONTACT_EMAILS
            if cc_myself:
                recipients.append(sender)

            from django.core.mail import send_mail
            send_mail(subject, message, sender, recipients)

            return redirect("contact/thanks")
    else:
        form = ContactForm() # An unbound form

    return render_to_response('treemap/contact.html', {
        'form': form, 
    }, RequestContext(request))

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def clean_diff(jsonstr):
    #print jsonstr
    diff = simplejson.JSONDecoder().decode(jsonstr)
    diff_no_old = {}
    for key in diff:
        if not key.startswith('old_'):
            diff_no_old[key] = diff[key]
    return diff_no_old

def clean_key_names(jsonstr):
    if not jsonstr: return ""
    diff = simplejson.JSONDecoder().decode(jsonstr)
    diff_clean = {}
    for key in diff:
        diff_clean[key.replace('_', ' ').title()] = diff[key]
    return diff_clean    

from django.core import serializers
@login_required 
def verify_edits(request, audit_type='tree'):
        
    changes = []
    trees = Tree.history.filter(present=True).filter(_audit_user_rep__lt=1000).filter(_audit_change_type__exact='U').exclude(_audit_diff__exact='').filter(_audit_verified__exact=0)
    newtrees = Tree.history.filter(present=True).filter(_audit_user_rep__lt=1000).filter(_audit_change_type__exact='I').filter(_audit_verified__exact=0)
    plots = Plot.history.filter(present=True).filter(_audit_user_rep__lt=1000).filter(_audit_change_type__exact='U').exclude(_audit_diff__exact='').filter(_audit_verified__exact=0)
    newplots = Plot.history.filter(present=True).filter(_audit_user_rep__lt=1000).filter(_audit_change_type__exact='I').filter(_audit_verified__exact=0)
    treeactions = []
    n = None    

    if 'username' in request.GET:
        u = User.objects.filter(username__icontains=request.GET['username'])
        trees = trees.filter(last_updated_by__in=u)
        plots = plots.filter(last_updated_by__in=u)
        newtrees = newtrees.filter(last_updated_by__in=u)
        newplots = newplots.filter(last_updated_by__in=u)
    if 'address' in request.GET:
        trees = trees.filter(plot__address_street__icontains=request.GET['address'])
        plots = plots.filter(address_street__icontains=request.GET['address'])
        newtrees = newtrees.filter(plot__address_street__icontains=request.GET['address'])
        newplots = newplots.filter(address_street__icontains=request.GET['address'])
    if 'nhood' in request.GET:
        n = Neighborhood.objects.filter(id=request.GET['nhood'])[0]
        geo_trees = Tree.objects.filter(plot__geometry__within=n.geometry)
        ids = [t.id for t in geo_trees]
        trees = trees.filter(id__in=ids)
        plots = plots.filter(geometry__within=n.geometry)
        newtrees = newtrees.filter(id__in=ids)
        newplots = newplots.filter(geometry__within=n.geometry)
    
    for plot in plots:
        species = 'no species name'
        actual_plot = Plot.objects.get(pk=plot.id)
        if actual_plot.current_tree():
            species_obj = actual_plot.current_tree().species
            if species_obj:
                species = species_obj.common_name
        changes.append({
            'id': actual_plot.id,
            'species': species,
            'address_street': actual_plot.address_street,
            'last_updated_by': plot.last_updated_by.username,
            'last_updated': plot.last_updated,
            'change_description': clean_key_names(plot._audit_diff),
            'change_id': plot._audit_id,
            'type': 'plot'
        })
    for plot in newplots:
        species = 'no species name'
        actual_plot = Plot.objects.get(pk=plot.id)
        if actual_plot.current_tree():
            species_obj = actual_plot.current_tree().species
            if species_obj:
                species = species_obj.common_name
        changes.append({
            'id': actual_plot.id,
            'species': species,
            'address_street': actual_plot.address_street,
            'last_updated_by': plot.last_updated_by.username,
            'last_updated': plot.last_updated,
            'change_description': clean_key_names(plot._audit_diff),
            'change_id': plot._audit_id,
            'type': 'plot'
        })
    for tree in trees:
        species = 'no species name'
        actual_tree = Tree.objects.get(pk=tree.id)
        if actual_tree.species:
            species = actual_tree.species.common_name
        changes.append({
            'id': actual_tree.id,
            'species': species,
            'address_street': actual_tree.plot.address_street,
            'last_updated_by': tree.last_updated_by.username,
            'last_updated': tree.last_updated,
            'change_description': clean_key_names(tree._audit_diff),
            'change_id': tree._audit_id,
            'type': 'tree'
        })
    for tree in newtrees:
        species = 'no species name'
        actual_tree = Tree.objects.get(pk=tree.id)
        if actual_tree.species:
            species = actual_tree.species.common_name
        changes.append({
            'id': actual_tree.id,
            'species': species,
            'address_street': actual_tree.plot.address_street,
            'last_updated_by': tree.last_updated_by,
            'last_updated': tree.last_updated,
            'change_description': 'New Tree',
            'change_id': tree._audit_id,
            'type': 'tree'
        })
        
    changes.sort(lambda x,y: cmp(x['last_updated'], y['last_updated']))
    return render_to_response('treemap/verify_edits.html',RequestContext(request,{'changes':changes, "geometry":n}))

@login_required
@permission_required('auth.change_user') #proxy for group users
def watch_list(request):    
    watch_failures = TreeWatch.objects.filter(valid=False)
    n = None
    if 'username' in request.GET:
        u = User.objects.filter(username__icontains=request.GET['username'])
        watch_failures = watch_failures.filter(tree__last_updated_by__in=u)
    if 'address' in request.GET:
        watch_failures = watch_failures.filter(tree__address_street__icontains=request.GET['address'])
    if 'test' in request.GET: 
        for watch in watch_choices.iteritems():
            if watch[0] == request.GET['test']: 
                key = watch[1]
                watch_failures = watch_failures.filter(key=key)
                break;
    if 'nhood' in request.GET:
        n = Neighborhood.objects.filter(id=request.GET['nhood'])
        watch_failures = watch_failures.filter(tree__plot__neighborhood=n)
    
    return render_to_response('treemap/watch_list.html', RequestContext(request,{'test_names':watch_choices.iteritems(), "watches": watch_failures, "geography": n}))

@login_required
@permission_required('auth.change_user') #proxy for group users
def validate_watch(request):
    if request.method == 'POST':
        post = simplejson.loads(request.raw_post_data)
    watch_id = post.get('watch_id')
    watch = TreeWatch.objects.get(pk=watch_id)
    watch.valid = True
    watch.save()
    
    response_dict = {}
    response_dict['success'] = True
    return HttpResponse(
        simplejson.dumps(response_dict, sort_keys=True, indent=4),
        content_type = 'text/plain'
    )
@login_required
@permission_required('auth.change_user')
def user_rep_changes(request):  
    aggs = []
    distinct_dates = UserReputationAction.objects.dates('date_created', 'day', order='DESC')
    for date in distinct_dates.iterator():
        start_time = date.replace(hour = 0, minute = 0, second = 0)
        end_time = date.replace(hour = 23, minute = 59, second = 59)
        
        date_users = UserReputationAction.objects.filter(date_created__range=(start_time, end_time)).values('user').distinct('user')

        if 'username' in request.GET:
            u = User.objects.filter(username__icontains=request.GET['username'])
            date_users = date_users.filter(user__in=u)
        if 'group' in request.GET: 
            g = Group.objects.filter(name__icontains=request.GET['group'])
            date_users = date_users.filter(user__groups__in=g)

        for user_id in date_users:
            user = User.objects.get(pk=user_id['user'])
            user_date_newtrees = Tree.history.filter(present=True, last_updated_by=user, _audit_change_type__exact='I', _audit_timestamp__range=(start_time, end_time))
            user_date_treeupdate = Tree.history.filter(present=True, last_updated_by=user, _audit_change_type__exact='U', _audit_timestamp__range=(start_time, end_time)).exclude(_audit_diff__exact='')
            
            aggs.append({
                'user':user.username, 
                'new':user_date_newtrees.count(), 
                'update': user_date_treeupdate.count(), 
                'date':date
            })
    return render_to_response('treemap/rep_changes.html',RequestContext(request,{'rep':aggs}))
    

@login_required 
def verify_rep_change(request, change_type, change_id, rep_dir):
    #parse change type and retrieve change object
    if change_type == 'tree':
        change = Tree.history.filter(_audit_id__exact=change_id)[0]
        user = get_object_or_404(User, pk=change.last_updated_by_id)
        obj = get_object_or_404(Tree, pk=change.id)
    elif change_type == 'plot':
        change = Plot.history.filter(_audit_id__exact=change_id)[0]
        user = get_object_or_404(User, pk=change.last_updated_by_id)
        obj = get_object_or_404(Tree, pk=change.id)
    elif change_type == 'action':
        change = TreeAction.history.filter(_audit_id__exact=change_id)[0]
        user = get_object_or_404(User, pk=change.reported_by_id)
        obj = get_object_or_404(TreeAction, pk=change.id)
    elif change_type == 'alert':
        change = TreeAlert.history.filter(_audit_id__exact=change_id)[0]
        user = get_object_or_404(User, pk=change.reported_by_id)
        obj = get_object_or_404(TreeAlert, pk=change.id)
    elif change_type == 'flag':
        change = TreeFlags.history.filter(_audit_id__exact=change_id)[0]
        user = get_object_or_404(User, pk=change.reported_by_id)
        obj = get_object_or_404(TreeFlags, pk=change.id)

    change_reputation_for_user(user, 'edit verified', obj, sub_action=rep_dir, change_initiated_by_user=request.user)
    change._audit_verified = 1
    change.save()
    return render_to_json({'change_type': change_type, 'change_id': change_id})
    
@login_required
@permission_required('threadedcomments.change_threadedcomment')
def view_flagged(request):
    comments = ThreadedComment.objects.annotate(num_flags=Count('comment_flags__id')).filter(is_public=True, num_flags__gt=0)
    n = None
    if 'username' in request.GET:
        u = User.objects.filter(username__icontains=request.GET['username'])
        comments = comments.filter(user__in=u)
    if 'text' in request.GET:
        comments = comments.filter(comment__icontains=request.GET['text'])
    if 'nhood' in request.GET:
        n = Neighborhood.objects.get(id=request.GET['nhood'])
        comment_list = []
        loop_list = list(comments)
        for comment in loop_list: 
            plot = Plot.objects.get(pk=comment.object_id)
            if n in plot.neighborhood.all():
                comment_list.append(comment)
        return render_to_response('comments/edit.html',RequestContext(request,{'comments':comment_list, "geometry":n}))
        
    return render_to_response('comments/edit_flagged.html',RequestContext(request,{'comments': comments, "geometry":n}))
    
@login_required
@permission_required('threadedcomments.change_threadedcomment')
def view_comments(request):
    comments = ThreadedComment.objects.filter(is_public=True)
    n = None
    if 'username' in request.GET:
        u = User.objects.filter(username__icontains=request.GET['username'])
        comments = comments.filter(user__in=u)
    if 'text' in request.GET:
        comments = comments.filter(comment__icontains=request.GET['text'])
    if 'nhood' in request.GET:
        n = Neighborhood.objects.get(id=request.GET['nhood'])
        comment_list = []
        loop_list = list(comments)
        for comment in loop_list: 
            plot = Plot.objects.get(pk=comment.object_id)
            if n in plot.neighborhood.all():
                comment_list.append(comment)
        return render_to_response('comments/edit.html',RequestContext(request,{'comments':comment_list, "geometry":n}))
        
    return render_to_response('comments/edit.html',RequestContext(request,{'comments':comments, "geometry":n}))
  
@login_required  
@permission_required('threadedcomments.change_threadedcomment')
def export_comments(request, format):
    users = UserProfile.objects.filter(active=True)
    where = []
    if 'username' in request.GET:
        users = users.filter(user__username__icontains=request.GET['username'])
        where.append(" a.username ilike '%" + request.GET['username'] + "%' ")
    if 'text' in request.GET:
        where.append(" b.comment ilike '%" + request.GET['text'] + "%' ")
    if 'nhood' in request.GET:
        n = Neighborhood.objects.get(id=request.GET['nhood'])
        comment_list = []
        loop_list = list(ThreadedComments.objects.all())
        for comment in loop_list: 
            plot = Plot.objects.get(pk=comment.object_id)
            if n in plot.neighborhood.all():
                comment_list.append(comment)
        where.append("b.id in " + [c.id for c in comment_list] + " ")

    sql = "select a.username, b.date_submitted as date, b.comment as comment, b.object_id as plot_id from auth_user as a, threadedcomments_threadedcomment as b where b.user_id = a.id"
    if len(where) > 0:
        sql = sql + " and " + ' and '.join(where)
    
    return ogr_conversion('CSV', [{'name':'comments', 'sql':sql}], name="comments", geo=False)    


   
def hide_comment(request):
    response_dict = {}
    post = simplejson.loads(request.raw_post_data)
    flag_id = post.get('flag_id')
    try:
        comment = CommentFlag.objects.get(id=flag_id).comment
    except:
        comment = ThreadedComment.objects.get(id=flag_id)

    comment.is_public = False
    comment.save()
    response_dict['success'] = True
    
    return HttpResponse(
        simplejson.dumps(response_dict, sort_keys=True, indent=4),
        content_type = 'text/plain'
    )
    
@login_required
def add_flag(request, comment_id):
    user = request.user
    comment = ThreadedComment.objects.get(pk=comment_id)
    comment_flags = CommentFlag.objects.filter(comment=comment, user=user).all()

    if comment_flags and len(comment_flags) > 0:
        comment_flags[0].flagged = True
        comment_flags[0].save()
    else:
        comment_flag = CommentFlag(comment=comment, flagged=True, user=user)
        comment_flag.save()

    return HttpResponseRedirect(request.REQUEST["next"])
    

def remove_flag(request):
    response_dict = {}
    post = simplejson.loads(request.raw_post_data)
    flag_id = post.get('flag_id')

    flag = CommentFlag.objects.get(comment__id=flag_id)
    flag.delete()
    response_dict['success'] = True

    return HttpResponse(
        simplejson.dumps(response_dict, sort_keys=True, indent=4),
        content_type = 'text/plain'
    )

@login_required
@permission_required('auth.change_user') #proxy for group users
def view_images(request):
    user_images = UserProfile.objects.exclude(photo="").order_by("-user__last_login")
    tree_images = TreePhoto.objects.all().order_by("-reported")
    return render_to_response('treemap/images.html',RequestContext(request, {'user_images':user_images, 'tree_images':tree_images}))

def treemap_settings_js(request):

    context = {
        'map_center_lat': settings.MAP_CENTER_LAT,
        'map_center_lon': settings.MAP_CENTER_LON,
        'bounding_box_left': settings.BOUNDING_BOX['left'],
        'bounding_box_bottom': settings.BOUNDING_BOX['bottom'],
        'bounding_box_top': settings.BOUNDING_BOX['top'],
        'bounding_box_right': settings.BOUNDING_BOX['right'],
    }

    response = render_to_response('treemap/treemap_settings.js', RequestContext(request,context))
    response['Content-Type'] = 'application/javascript'
    return response
