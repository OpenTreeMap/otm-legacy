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

from django.conf import settings
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden, Http404, HttpResponseBadRequest
from django.core.paginator import Paginator
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.gis.feeds import Feed
from django.contrib.gis.geos import Point, GEOSGeometry
from django.contrib.comments.models import Comment, CommentFlag
from django.views.decorators.cache import cache_page
from django.db.models import Count, Sum, Q, Min, Max
from django.views.decorators.csrf import csrf_view_exempt
from django.contrib.gis.shortcuts import render_to_kml
from django.utils.datastructures import SortedDict
from django_reputation.models import Reputation, Permission, UserReputationAction, ReputationAction
from registration.signals import user_activated
# formsets
from django.forms.formsets import formset_factory
from django.forms.models import inlineformset_factory, modelformset_factory

from models import *
from forms import *
from profiles.models import UserProfile
from shortcuts import render_to_geojson, get_pt_or_bbox, get_summaries_and_benefits

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


app_models = {'UserProfile':'profiles','User':'auth'}

def average(seq):
    return float(sum(l))/len(l)

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


def location_map(request):
    pass

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

#@cache_page(60*1)
def result_map(request):
    # get enviro attributes for 'selected' trees
    min_year = 1970

    min_tree_year = Tree.objects.exclude(date_planted=None).exclude(present=False).aggregate(Min("date_planted"))

    if "date_planted__min" in min_tree_year and min_tree_year["date_planted__min"]:
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

    recent_trees = Tree.objects.filter(present=True).order_by("-last_updated")[0:3]
    recent_plots = Plot.objects.filter(present=True).order_by("-last_updated")[0:3]
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
    
    plots = Plot.objects.filter(present=True)
        #don't filter by geocode accuracy until we know why some new trees are getting -1
        #Q(geocoded_accuracy__gte=8)|Q(geocoded_accuracy=None)|Q(geocoded_accuracy__isnull=True)).filter(
    if geom.geom_type == 'Point':

        #print float(distance), geom, plots
        plots = plots.filter(geometry__dwithin=(
            geom, float(distance))
            ).distance(geom).order_by('distance')
    else:
      plots = plots.filter(geometry__intersects=geom)

    # needed to be able to prioritize overlapping trees

    if plots:
        extent = plots.extent()
    else:
        extent = []
    
    species = request.GET.get('species')

    if species:
        plots_filtered_by_species = plots.filter(tree__species__id=species, tree__present=True)
        # to allow clicking other trees still...
        if len(plots_filtered_by_species) > 0:
            plots = plots_filtered_by_species
    
    if len(plots) > 0:
        plots = plots[:max_plots]
    
    return render_to_geojson(plots,
                             geom_field='geometry', 
                             excluded_fields=['sidewalk_damage',
                             'address_city',
                             'length',
                             'distance',
                             'geometry',
                             'geocoded_address',
                             'last_updated_by_id',
                             'present',
                             'powerline_conflict_potential',
                             'width',
                             'geocoded_lat',
                             'geocoded_lon',
                             'type'],
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
            return 404
        coord = map(float,location.split(','))
        pt = Point(coord[0], coord[1])
        trees =  Tree.objects.filter(present=True).filter(geometry__dwithin = (pt,.001))#.distance(pt).order_by('distance').count()
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
        return ExcelResponse(species)

    #render to html    
    return render_to_response('treemap/species.html',{
        'species' : species,
        'page' : page #so template can do next page kind of stuff
        })
        

@cache_page(60*5)    
def top_species(request):
    Species.objects.all().annotate(num_trees=Count('tree')).order_by('-num_trees')        
    return 

def favorites(request, username):
    faves = User.objects.get(username=username).treefavorite_set.filter(tree__present=True)
    js = [{
       'id':f.tree.id, 
       'coords':[f.tree.geometry.x, f.tree.geometry.y]} for f in faves]
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
        
        if trees[0].present == False:
            plot = tree.plot
            if plot.present == False:
                raise Http404
            else:
                return HttpResponseRedirect('/plots/%s/' % plot.id)

        # get the last 5 edits to each tree piece
        history = trees[0].history.order_by('-last_updated')[:5]
        
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

    Reputation.objects.log_reputation_action(user, user, 'add tree', 25, tree)
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

    print recent_edits

    # sort by the date descending
    return sorted(recent_edits, key=itemgetter(1), reverse=True)

@login_required    
def tree_edit_choices(request, tree_id, type_):
    tree = get_object_or_404(Tree, pk=tree_id)
    choices = Choices().get_field_choices(type_)
    data = SortedDict(choices)
    #for item in choices: 
    #    data[item[0]] = item[1]
    if hasattr(tree, type_):
        val = getattr(tree, type_)
        #for item in choices:
        #    if item[0] = val:
        #        val = item[1]
        data['selected'] = val   
    else:
        if type_ == "condition":
            sidewalks = tree.treestatus_set.filter(key="condition").order_by("-reported")
            if sidewalks.count():
                data['selected'] = str(int(sidewalks[0].value))
        if type_ == "canopy_condition":
            sidewalks = tree.treestatus_set.filter(key="canopy_condition").order_by("-reported")
            if sidewalks.count():
                data['selected'] = str(int(sidewalks[0].value))
    return HttpResponse(simplejson.dumps(data))    

@login_required    
def plot_edit_choices(request, plot_id, type_):
    plot = get_object_or_404(Plot, pk=plot_id)
    choices = Choices().get_field_choices(type_)
    data = SortedDict(choices)
    #for item in choices: 
    #    data[item[0]] = item[1]
    if hasattr(plot, type_):
        val = getattr(plot, type_)
        #for item in choices:
        #    if item[0] = val:
        #        val = item[1]
        data['selected'] = val   
    else:
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
            return HttpResponseRedirect('/trees/%s/edit/' % tree.id)
    else:
        form = TreeEditPhotoForm(instance=tree)

    return render_to_response('add_edit_photos.html',RequestContext(request,{ 'instance': tree, 'form': form }))        
         

@login_required
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


def tree_delete(request, tree_id):
    tree = Tree.objects.get(pk=tree_id)
    tree.present = False
    tree.save()
    
    for h in tree.history.all():
        h.present = False
        h.save()
    
    return HttpResponse(
        simplejson.dumps({'success':True}, sort_keys=True, indent=4),
        content_type = 'text/plain'
    )


def plot_delete(request, plot_id):
    plot = Plot.objects.get(pk=plot_id)
    plot.present = False
    plot.save()

    if plot.current_tree():
        plot.current_tree().present = False
        plot.current_tree().save()
        for h in plot.current_tree().history.all():
            h.present = False
            h.save()
    
    for h in plot.history.all():
        h.present = False
        h.save()
    
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
        rep = Reputation.objects.reputation_for_user(user)
        #rep_gain = int(post.get('rep_total')) - rep.reputation
        user.reputation.reputation = int(post.get('rep_total'))
        user.reputation.save()
        #Reputation.objects.log_reputation_action(user, request.user, 'Administrative Action', rep_gain, user)
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
                #rep_gain = 100 - rep.reputation
                #Reputation.objects.log_reputation_action(user, request.user, 'Administrative Action', rep_gain, user)
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

@login_required
def approve_pend(request, pend_id):
    pend = TreePending.objects.get(pk=pend_id)
    if not pend:
        pend = PlotPending.objects.get(pk=pend_id)
    if not pend:
        raise Http404
    pend.approve(request.user)
    Reputation.objects.log_reputation_action(pend.submitted_by, pend.updated_by, 'edit tree', 5, pend.tree)
    return HttpResponse(
        simplejson.dumps({'success': True, 'pend_id': pend_id}, sort_keys=True, indent=4),
        content_type = 'text/plain'
    ) 

@login_required
def reject_pend(request, pend_id):
    pend = TreePending.objects.get(pk=pend_id)
    if not pend:
        pend = PlotPending.objects.get(pk=pend_id)
    if not pend:
        raise Http404
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
    # FIXME: sleep for debugging time delays
    time.sleep(1)
           
    response_dict = {'success': False, 'errors': []}
        
    parent_instance = None
    post = {}
    save_value = 5
    
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
                    insert_event_mgmt = instance.history.filter(_audit_change_type='I')[0].last_updated_by.has_perm('auth.change_user')
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

                                for key, value in Choices().get_field_choices(k):
                                    if str(key) == str(v):
                                        pend.text_value = value
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
                        Reputation.objects.log_reputation_action(request.user, request.user, action_name, save_value, instance)
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
#for auto reverse-geocode saving of new address, from search page map click
def plot_location_update(request):
    response_dict = {}
    post = simplejson.loads(request.raw_post_data)
    plot = Plot.objects.filter(pk=post.get('plot_id'))[0]
    plot.address_street = post.get('address')
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
        if form.is_valid():
            new_tree = form.save(request)
            Reputation.objects.log_reputation_action(request.user, request.user, 'add tree', 25, new_tree)
            if form.cleaned_data.get('target') == "add":
                form = TreeAddForm()
                messages.success(request, "Your tree was successfully added!")
            elif form.cleaned_data.get('target') == "addsame":
                messages.success(request, "Your tree was successfully added!")
                pass
            elif form.cleaned_data.get('target') == "edit":
                return HttpResponseRedirect('/trees/new/%i' % request.user.id)
            else:
                return HttpResponseRedirect('/trees/%i' % new_tree.id)
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


def _build_tree_search_result(request):
    # todo - optimize! OMG Clean it up! >.<
    choices = Choices()
    tile_query = []
    species = Species.objects.filter(tree_count__gt=0)
    max_species_count = species.count()
    
    species_criteria = {'species' : 'id',
                        'native' : 'native_status',
                        'edible' : 'palatable_human',
                        'color' : 'fall_conspicuous',
                        'cultivar' : 'cultivar_name',
                        'flowering' : 'flower_conspicuous'}

    trees = Tree.objects.filter(present=True, plot__present=True).extra(select={'geometry': "treemap_plot.geometry"})
    plots = Plot.objects.filter(present=True)
                        
    for k in species_criteria.keys():
        v = request.GET.get(k,'')
        if v:
            attrib = species_criteria[k]
            if v == 'true': v = True
            species = species.filter(**{attrib:v})
            print 'filtered species by %s = %s' % (species_criteria[k],v)
            print '  .. now we have %d species' % len(species)
            
    cur_species_count = species.count()
    if max_species_count != cur_species_count:
        trees = trees.filter(species__in=species)
	plots = Plot.objects.none()
        species_list = []
        for s in species:
            species_list.append("species_id = " + s.id.__str__())
        tile_query.append("(" + " OR ".join(species_list) + ")")
    #filter by nhbd or zipcode if location was specified

    geog_obj = None
    if 'location' in request.GET:
        loc = request.GET['location']
        if "," in loc:
            ns = Neighborhood.objects.all().order_by('id')
            if 'geoName' in request.GET:
                geoname = request.GET['geoName']
                ns = ns.filter(name=geoname)
            else:   
                coords = map(float,loc.split(','))
                pt = Point(coords)
                ns = ns.filter(plot__geometry__contains=pt)

            if ns.count():   
                trees = trees.filter(plot__neighborhood = ns[0])
		plots = plots.filter(neighborhood = ns[0])
                geog_obj = ns[0]
                tile_query.append("neighborhoods LIKE '%" + geog_obj.id.__str__() + "%'")
        else:
            z = ZipCode.objects.filter(zip=loc)
            if z.count():
                trees = trees.filter(plot__zipcode = z[0])
		plots = plots.filter(zipcode = z[0])
                geog_obj = z[0]
                tile_query.append("zipcode_id = " + z[0].id.__str__())
    elif 'hood' in request.GET:
        ns = Neighborhood.objects.filter(name__icontains = request.GET.get('hood'))
        if ns:
             trees = trees.filter(plot__neighborhood = ns[0])
             plots = plots.filter(neighborhood = ns[0])
             geog_obj = ns[0]
             tile_query.append("neighborhoods LIKE '%" + geog_obj.id.__str__() + "%'")

    #import pdb;pdb.set_trace()

    tree_criteria = {'project1' : '1',
                     'project2' : '2',
                     'project3' : '3',
                     'project4' : '4',
                     'project5' : '5'}
    for k in tree_criteria.keys():
        v = request.GET.get(k,'')
        if v:
            attrib = tree_criteria[k]
            trees = trees.filter(treeflags__key__exact=attrib)
            plots = Plot.objects.none()
            print 'filtered trees by %s = %s' % (tree_criteria[k],v)
            print '  .. now we have %d trees' % len(trees)
            tile_query.append("projects LIKE '%" + tree_criteria[k] + "%'")

    #filter by missing data params:
    missing_species = request.GET.get('missing_species','')
    if missing_species:
        trees = trees.filter(species__isnull=True)
        plots = Plot.objects.none()
        print 'filtered trees by missing species only - %s - %s' % (tree_criteria[k],v)
        print '  .. now we have %d trees' % len(trees)
        tile_query.append("species_id IS NULL")
    
    #
    ### TODO - add ability to show trees without "correct location"
    ##
    missing_current_dbh = request.GET.get('missing_diameter','')
    if missing_current_dbh:
        trees = trees.filter(Q(dbh__isnull=True) | Q(dbh=0))
        plots = Plot.objects.none()
        # TODO: What about ones with 0 dbh?
        print '  .. now we have %d trees' % len(trees)
        #species_list = [s.id for s in species]
        tile_query.append("dbh IS NULL")
    
    if not missing_current_dbh and 'diameter_range' in request.GET:
        min, max = map(float,request.GET['diameter_range'].split("-"))
        trees = trees.filter(dbh__gte=min)
        plots = Plot.objects.none()
        if max != 50: # TODO: Hardcoded in UI, may need to change
            trees = trees.filter(dbh__lte=max)
        tile_query.append("dbh BETWEEN " + min.__str__() + " AND " + max.__str__() + "")

    missing_current_height = request.GET.get('missing_height','')
    if missing_current_height:
        trees = trees.filter(Q(height__isnull=True) | Q(height=0))
        plots = Plot.objects.none()
        # TODO: What about ones with 0 dbh?
        print '  .. now we have %d trees' % len(trees)
        #species_list = [s.id for s in species]
        tile_query.append("height IS NULL")

    if not missing_current_height and 'height_range' in request.GET:
        min, max = map(float,request.GET['height_range'].split("-"))
        trees = trees.filter(height__gte=min)
        plots = Plot.objects.none()
        if max != 200: # TODO: Hardcoded in UI, may need to change
            trees = trees.filter(height__lte=max)
        tile_query.append("height BETWEEN " + min.__str__() + " AND " + max.__str__() + "")

    missing_current_plot_size = request.GET.get('missing_plot_size','')
    missing_current_plot_type = request.GET.get('missing_plot_type','')
    if missing_current_plot_size:
        trees = trees.filter(Q(plot__length__isnull=True) | Q(plot__width__isnull=True))
        plots = plots.filter(Q(length__isnull=True) | Q(width__isnull=True))
        # TODO: What about ones with 0 dbh?
        print '  .. now we have %d trees' % len(trees)
        #species_list = [s.id for s in species]
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
        # TODO: What about ones with 0 dbh?
        print '  .. now we have %d trees' % len(trees)
        #species_list = [s.id for s in species]
        tile_query.append(" plot_type IS NULL ")
    else:
        plot_type_choices = choices.get_field_choices('plot_type')
        pt_cql = []
        pt_list = []
        for k, v in plot_type_choices:
            if v.lower().replace(' ', '_') in request.GET:
                plot = request.GET.get(v.lower().replace(' ', '_'),'')
                if plot:
                    pt_list.append(k)
                    pt_cql.append("plot_type = " + k)
        if len(pt_cql) > 0:
            tile_query.append("(" + " OR ".join(pt_cql) + ")")
            trees = trees.filter(plot__type__in=pt_list)
            plots = plots.filter(type__in=pt_list)

    missing_condition = request.GET.get("missing_condition", '')
    if missing_condition: 
        trees = trees.filter(condition__isnull=True)
        plots = Plot.objects.none()
        #species_list = [s.id for s in species]
        tile_query.append("condition IS NULL")
    else: 
        condition_choices = choices.get_field_choices('condition')    
        c_cql = []
        c_list = []
        for k, v in condition_choices:
            if v.lower().replace(' ', '_') in request.GET:
                cond = request.GET.get(v.lower().replace(' ', '_'),'')
                if cond:
                    c_list.append(k)
                    c_cql.append("condition = " + k)
        if len(c_cql) > 0:
            tile_query.append("(" + " OR ".join(c_cql) + ")")
            trees = trees.filter(condition__in=c_list)
            plots = Plot.objects.none()

    missing_sidewalk = request.GET.get("missing_sidewalk", '')
    if missing_sidewalk: 
        trees = trees.filter(plot__sidewalk_damage__isnull=True)
        plots = plots.filter(sidewalk_damage__isnull=True)
        #species_list = [s.id for s in species]
        tile_query.append("sidewalk_damage IS NULL")
    else: 
        sidewalk_choices = choices.get_field_choices('sidewalk_damage')    
        s_cql = []
        s_list = []
        for k, v in sidewalk_choices:
            if v.lower().split(' ')[0] in request.GET:
                sw = request.GET.get(v.lower().split(' ')[0],'')
                if sw:
                    s_list.append(k)
                    s_cql.append("sidewalk_damage = " + k)
        if len(s_cql) > 0:
            tile_query.append("(" + " OR ".join(s_cql) + ")")
            trees = trees.filter(plot__sidewalk_damage__in=s_list)
            plots = plots.filter(sidewalk_damage__in=s_list)
        

    missing_powerlines = request.GET.get("missing_powerlines", '')
    if missing_powerlines:
        trees = trees.filter(Q(plot__powerline_conflict_potential__isnull=True) | Q(plot__powerline_conflict_potential=3))
        plots = plots.filter(Q(powerline_conflict_potential__isnull=True) | Q(powerline_conflict_potential=3))
        #species_list = [s.id for s in species]
        tile_query.append("(powerline_conflict_potential = 3 OR powerline_conflict_potential IS NULL)")
    else:
        powerline_choices = choices.get_field_choices('powerline_conflict_potential')    
        p_cql = []
        p_list = []
        for k, v in powerline_choices:
            if v.lower() in request.GET:
                sw = request.GET.get(v.lower(),'')
                if sw:
                    p_list.append(k)
                    p_cql.append("powerline_conflict_potential = " + k)
        if len(p_cql) > 0:
            tile_query.append("(" + " OR ".join(p_cql) + ")")
            trees = trees.filter(plot__powerline_conflict_potential__in=p_list)
            plots = plots.filter(powerline_conflict_potential__in=p_list)

    missing_photos = request.GET.get("missing_photos", '')
    if missing_photos:
        trees = trees.filter(treephoto__isnull=True)
        plots = Plot.objects.none()
        #species_list = [s.id for s in species]
        tile_query.append("(photo_count IS NULL OR photo_count = 0)")
    if not missing_photos and 'photos' in request.GET:
        trees = trees.filter(treephoto__isnull=False)
        plots = Plot.objects.none()
        tile_query.append("photo_count > 0")

    steward = request.GET.get("steward", "")
    if steward:    
        users = User.objects.filter(username__icontains=steward)
        trees = trees.filter(steward_user__in=users)
        plots = Plot.objects.none()
        user_list = []
        for u in users:
            user_list.append("steward_user_id = " + u.id.__str__())
        tile_query.append("(" + " OR ".join(user_list) + ")")

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

    funding = request.GET.get("funding", "")
    if funding:
        trees = trees.filter(sponsor__icontains=funding)
        plots = Plot.objects.none()
        tile_query.append("sponsor LIKE '%" + funding + "%'")

    if 'planted_range' in request.GET:
        min, max = map(float,request.GET['planted_range'].split("-"))
        min = "%i-01-01" % min
        max = "%i-12-31" % max
        trees = trees.filter(date_planted__gte=min, date_planted__lte=max)
        plots = Plot.objects.none()
        tile_query.append("date_planted AFTER " + min + "T00:00:00Z AND date_planted BEFORE " + max + "T00:00:00Z")   
 
    if 'updated_range' in request.GET:
        min, max = map(float,request.GET['updated_range'].split("-"))
        min = datetime.utcfromtimestamp(min)
        max = datetime.utcfromtimestamp(max)
        trees = trees.filter(last_updated__gte=min, last_updated__lte=max)
        plots = plots.filter(last_updated__gte=min, last_updated__lte=max)
        tile_query.append("last_updated AFTER " + min.isoformat() + "Z AND last_updated BEFORE " + max.isoformat() + "Z")   

    if not geog_obj:
        q = request.META['QUERY_STRING'] or ''
        cached_search_agg = AggregateSearchResult.objects.filter(key=q)
        if cached_search_agg.exists() and cached_search_agg[0].ensure_recent(trees.count()):
            geog_obj = cached_search_agg[0]
        else:
            geog_obj = AggregateSearchResult(key=q)
            geog_obj.total_trees = trees.count()
            geog_obj.total_plots = plots.count()
            #TODO figure out how to summarize diff stratum stuff
            fields = [x.name for x in ResourceSummaryModel._meta.fields 
                if not x.name in ['id','aggregatesummarymodel_ptr','key','resourcesummarymodel_ptr','last_updated']]
            for f in fields:
                    fn = 'treeresource__' + f
                    s = trees.aggregate(Sum(fn))[fn + '__sum'] or 0.0
                    #print geog_obj,f,s
                    setattr(geog_obj,f,s)
            try:
                geog_obj.save()
            except:
                # another thread has already likely saved the same object...
                pass


    return trees, plots, geog_obj, ' AND '.join(tile_query)



def zip_file(file_path,archive_name):
        buffer = StringIO()
        with closing(zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED)) as z:
            for root, dirs, files in os.walk(file_path):
                for f in files:
                    abs_file = os.path.join(root, f)
                    zipf = abs_file[len(file_path) + len(os.sep):]
                    zipf = zipf.replace('sql_statement', 'trees')
                    z.write(abs_file, zipf)
        z.close()
        buffer.flush()
        zip_stream = buffer.getvalue()
        buffer.close()
        return zip_stream

def ogr_conversion(output_type, sql, extension=None):   
    dbsettings = settings.DATABASES['default'] 
    tmp_dir = tempfile.mkdtemp() + "/trees" 

    host = dbsettings['HOST']
    port = dbsettings['PORT']
    if host == '':
        host = 'localhost'
    if port == '':
        port = 5432

    if extension != None:
        os.mkdir(tmp_dir)
        tmp_name = tmp_dir + "/sql_statement." + extension
    else: 
        tmp_name = tmp_dir

    if output_type == 'CSV':
        geometry = 'GEOMETRY=AS_WKT'
    else: 
        geometry = ''

    command = ['ogr2ogr', '-sql', sql, '-f', output_type, tmp_name, 'PG:dbname=%s host=%s port=%s password=%s user=%s' % (dbsettings['NAME'], host, dbsettings['PORT'], dbsettings['PASSWORD'], dbsettings['USER']), '-lco', geometry ]
    done = subprocess.call(command)

    if done != 0: 
        return render_to_json({'status':'error'})
    else: 
        zipfile = zip_file(tmp_dir,'trees')
        response = HttpResponse(zipfile, mimetype='application/zip')
        response['Content-Disposition'] = 'attachment; filename=trees.zip'
        return response

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
    urlparams:
     - location
     - geoName if zip or neighborhood found
     - species
     # todo:  lat/lng (should be separate from search location 
     # what type of geography to return in case of zero or too many trees)
    return either
     - trees and associated summaries
     - neighborhood or zipcode and associated   summaries
    """
    if settings.TILED_SEARCH_RESPONSE:
        maximum_trees_for_display = 0
    else:
        maximum_trees_for_display = 500   
    maximum_trees_for_summary = 200000  
    response = {}

    trees, plots, geog_obj, tile_query = _build_tree_search_result(request)
    if format == "geojson":    
        return render_to_geojson(trees, geom_field='geometry', additional_data={'summaries': esj})
    elif format == "shp":
        return ogr_conversion('ESRI Shapefile', str(trees.query))
    elif format == "kml":
        return ogr_conversion('KML', str(trees.query), 'kml')
    elif format == "csv":
        return ogr_conversion('CSV', str(trees.query))
        
        
    geography = None
    summaries, benefits = None, None
    if geog_obj:
        summaries, benefits = get_summaries_and_benefits(geog_obj)
        if hasattr(geog_obj, 'geometry'):
            geography = simplejson.loads(geog_obj.geometry.simplify(.0001).geojson)
            geography['name'] = str(geog_obj)
        else:
            pass#geography = {}
            #geography['name'] = ''
        
    #else we're doing the simple json route .. ensure we return summary info
    tree_count = trees.count()
    plot_count = plots.count()
    full_count = Tree.objects.filter(present=True).count()
    full_plot_count = Plot.objects.filter(present=True).count()
    esj = {}
    esj['total_trees'] = tree_count
    esj['total_plots'] = plot_count

    if tree_count > maximum_trees_for_summary:
        trees = []
        if geog_obj:
            esj = summaries
            esj['benefits'] = benefits
        else:
            #someone selected a single species w/too many tree results.  dang....
            # TODO - need to pull from cached results...
            summaries = {}
        

    else:
        #esj['distinct_species'] = len(trees.values("species").annotate(Count("id")).order_by("species"))
        #print 'we have %s  ..' % esj
        #print 'aggregating..'

        r = ResourceSummaryModel()
        
        with_out_resources = trees.filter(treeresource=None).count()
        #print 'without resourcesums:', with_out_resources
        resources = tree_count - with_out_resources
        #print 'have resourcesums:', resources
        
        EXTRAPOLATE_WITH_AVERAGE = True

        for f in r._meta.get_all_field_names():
            if f.startswith('total') or f.startswith('annual'):
                fn = 'treeresource__' + f
                s = trees.aggregate(Sum(fn))[fn + '__sum'] or 0.0
                # TODO - need to make this logic accesible from shortcuts.get_summaries_and_benefits
                # which is also a location where summaries are calculated
                # also add likely to treemap/update_aggregates.py (not really sure how this works)
                if EXTRAPOLATE_WITH_AVERAGE and resources:
                    avg = float(s)/resources
                    s += avg * with_out_resources
                        
                setattr(r,f,s)
                esj[f] = s
        esj['benefits'] = r.get_benefits()

        #print 'aggregated...'
    
    
    if tree_count > maximum_trees_for_display:   
         trees = []
         response.update({'tile_query' : tile_query})
        
  
    tj = [{
          'id': t.id,
          'lon': '%.12g' % t.plot.geometry.x, 
          'lat' : '%.12g' % t.plot.geometry.y,
          'cmplt' : t.is_complete()
          } for t in trees]
    pj = [{
          'id': p.id,
          'lon': '%.12g' % p.geometry.x,
          'lat' : '%.12g' % p.geometry.y
          } for p in plots]


    response.update({'trees' : tj, 'plots': pj, 'summaries' : esj, 'geography' : geography, 'initial_tree_count' : tree_count, 'full_tree_count': full_count, 'full_plot_count': full_plot_count})
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

            return HttpResponseRedirect('/contact/thanks/') # Redirect after POST
    else:
        form = ContactForm() # An unbound form

    return render_to_response('treemap/contact.html', {
        'form': form, 
    })

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
    treeactions = []
    
    if 'username' in request.GET:
        u = User.objects.filter(username__icontains=request.GET['username'])
        trees = trees.filter(last_updated_by__in=u)
        plots = plots.filter(last_updated_by__in=u)
        newtrees = newtrees.filter(last_updated_by__in=u)
    if 'address' in request.GET:
        trees = trees.filter(plot__address_street__icontains=request.GET['address'])
        plots = plots.filter(address_street__icontains=request.GET['address'])
        newtrees = newtrees.filter(plot__address_street__icontains=request.GET['address'])
    if 'nhood' in request.GET:
        n = Neighborhood.objects.filter(name=request.GET['nhood'])[0].geometry
        trees = trees.filter(plot__geometry__within=n)
        plots = plots.filter(geometry__within=n)
        newtrees = newtrees.filter(plot__geometry__within=n)
    
    for plot in plots:
        species = 'no species name'
        actual_plot = Plot.objects.get(pk=plot.id)
        if actual_plot.current_tree():
            species = actual_plot.current_tree().species.common_name
        changes.append({
            'id': actual_plot.current_tree().id,
            'species': species,
            'address_street': actual_tree.plot.address_street,
            'last_updated_by': tree.last_updated_by.username,
            'last_updated': tree.last_updated,
            'change_description': clean_key_names(tree._audit_diff),
            'change_id': tree._audit_id,
            'type': 'plot'
        })
    for tree in trees:
        species = 'no species name'
        if tree.species:
            species = tree.species.common_name
        actual_tree = Tree.objects.get(pk=tree.id)
        changes.append({
            'id': tree.id,
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
        if tree.species:
            species = tree.species.common_name
        actual_tree = Tree.objects.get(pk=tree.id)
        changes.append({
            'id': tree.id,
            'species': species,
            'address_street': actual_tree.plot.address_street,
            'last_updated_by': tree.last_updated_by,
            'last_updated': tree.last_updated,
            'change_description': 'New Tree',
            'change_id': tree._audit_id,
            'type': 'tree'
        })
        
    changes.sort(lambda x,y: cmp(x['last_updated'], y['last_updated']))
    return render_to_response('treemap/verify_edits.html',RequestContext(request,{'changes':changes}))

@login_required
@permission_required('auth.change_user') #proxy for group users
def watch_list(request):    
    watch_failures = TreeWatch.objects.filter(valid=False)
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
        n = Neighborhood.objects.filter(name=request.GET['nhood'])
        watch_failures = watch_failures.filter(tree__neighborhood=n)
    
    return render_to_response('treemap/watch_list.html', RequestContext(request,{'test_names':watch_choices.iteritems(), "watches": watch_failures}))

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
    
        
    #do the rep adjustment
    if rep_dir == 'up':
        rep_gain = 5
    elif rep_dir == 'down':
        rep_gain= -10
    elif rep_dir == 'neutral':
        rep_gain = 1
    
    Reputation.objects.log_reputation_action(user, request.user, 'edit verified', rep_gain, obj)
    change._audit_verified = 1
    change.save()
    return render_to_json({'change_type': change_type, 'change_id': change_id})
    
@login_required
@permission_required('comments.can_moderate')
def view_flagged(request):
    flags = CommentFlag.objects.filter(comment__is_public=True)
    if 'username' in request.GET:
        u = User.objects.filter(username__icontains=request.GET['username'])
        flags = flags.filter(user__in=u)
    if 'text' in request.GET:
        flags = flags.filter(comment__comment__icontains=request.GET['text'])
    if 'nhood' in request.GET:
        n = Neighborhood.objects.filter(name=request.GET['nhood'])
        f_list = list(flags)
        for f in f_list:            
            if Tree.objects.filter(pk=f.comment.object_pk, neighborhood=n).count() == 0:
                f_list.remove(f)
        return render_to_response('comments/edit_flagged.html',RequestContext(request,{'flags':f_list}))
        
    return render_to_response('comments/edit_flagged.html',RequestContext(request,{'flags':flags}))
    
@login_required
@permission_required('comments.can_moderate')
def view_comments(request):
    comments = Comment.objects.filter(is_public=True)
    
    if 'username' in request.GET:
        u = User.objects.filter(username__icontains=request.GET['username'])
        comments = comments.filter(user__in=u)
    if 'text' in request.GET:
        comments = comments.filter(comment__icontains=request.GET['text'])
    if 'nhood' in request.GET:
        n = Neighborhood.objects.filter(name=request.GET['nhood'])
        c_list = list(comments)
        for c in c_list:            
            if Tree.objects.filter(pk=c.object_pk, neighborhood=n).count() == 0:
                c_list.remove(c)
        return render_to_response('comments/edit.html',RequestContext(request,{'comments':c_list}))
        
    return render_to_response('comments/edit.html',RequestContext(request,{'comments':comments}))
    
   
def hide_comment(request):
    response_dict = {}
    post = simplejson.loads(request.raw_post_data)
    flag_id = post.get('flag_id')
    try:
        comment = CommentFlag.objects.get(id=flag_id).comment
    except:
        comment = Comment.objects.get(id=flag_id)
    comment.is_public = False
    comment.save()
    response_dict['success'] = True
    
    return HttpResponse(
        simplejson.dumps(response_dict, sort_keys=True, indent=4),
        content_type = 'text/plain'
    )
    
def remove_flag(request):
    response_dict = {}
    post = simplejson.loads(request.raw_post_data)
    flag_id = post.get('flag_id')
    flag = CommentFlag.objects.get(id=flag_id)    
    flag.delete()
    response_dict['success'] = True

    return HttpResponse(
        simplejson.dumps(response_dict, sort_keys=True, indent=4),
        content_type = 'text/plain'
    )

@login_required
@permission_required('auth.change_user') #proxy for group users
def build_admin_panel(request):
    return render_to_response('treemap/admin.html',RequestContext(request))

@login_required
@permission_required('auth.change_user') #proxy for group users
def view_images(request):
    user_images = UserProfile.objects.exclude(photo="").order_by("-user__last_login")
    tree_images = TreePhoto.objects.all().order_by("-reported")
    return render_to_response('treemap/images.html',RequestContext(request, {'user_images':user_images, 'tree_images':tree_images}))
