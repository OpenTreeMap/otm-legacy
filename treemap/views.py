import os
from operator import itemgetter
from django.conf import settings
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden, Http404
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib.gis.feeds import Feed
from django.contrib.gis.geos import Point
from django.contrib.comments.models import Comment, CommentFlag
from django.views.decorators.cache import cache_page
from django.db.models import Count, Sum, Q
from django.views.decorators.csrf import csrf_view_exempt
from django.contrib.gis.shortcuts import render_to_kml
from django.utils.datastructures import SortedDict
from django_reputation.models import Reputation, Permission, UserReputationAction
from registration.signals import user_activated
# formsets
from django.forms.formsets import formset_factory
from django.forms.models import inlineformset_factory, modelformset_factory

from shapes.views import ShpResponder

import simplejson 

from models import *
from forms import *
from profiles.models import UserProfile
from shortcuts import render_to_geojson, get_pt_or_bbox, get_summaries_and_benefits
from spreadsheet import ExcelResponse
import time
from time import mktime, strptime


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
    print rep
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
    recent_trees = Tree.objects.filter(present=True).order_by("-last_updated")[0:3]
    recent_status = TreeStatus.objects.filter(tree__present=True).order_by("-reported")[0:3]
    recent_flags = TreeFlags.objects.filter(tree__present=True).order_by("-reported")[0:3]
    
    feeds['recent_edits'] = unified_history(recent_trees, recent_status, recent_flags)
    feeds['recent_photos'] = TreePhoto.objects.exclude(tree__present=False).order_by("-reported")[0:8]
    feeds['species'] = Species.objects.all().annotate(num_trees=Count('tree')).order_by('-num_trees')[0:4]
    
    #TODO: change from most populated neighborhood to most updates in neighborhood
    nhoods = Tree.objects.filter(present=True).aggregate(Sum('neighborhood'))
    feeds['active_nhoods'] = sorted(nhoods, key=itemgetter(1), reverse=True)[0:4]
    
    return render_to_response('treemap/index.html', RequestContext(request,{'feeds': feeds}))

#@cache_page(60*1)
def result_map(request):
    #top_species = Species.objects.all().annotate(
    #    num_trees=Count('tree')).order_by('-num_trees')[:20]
    
    #latest_maint = MaintenanceRecord.objects.filter(
    #    tree__species__gt=0).filter(tree__dbh__gt=0).order_by('-date')[:5]
        
    #interesting_trees = Tree.objects.filter(species=30).filter(dbh__gt=0)[:5]
    
    # neighborhoods = {}
    # zipcodes = {}
    # for n in Neighborhood.objects.all():
        # neighborhoods[n.id] = {'distinct_species' : n.aggregates.distinct_species, 
                              # 'total_trees' : n.aggregates.total_trees, 
                              # 'geom' : eval(n.geometry.simplify(.0002).geojson)['coordinates'][0], 
                              # 'name' : n.name}
    # for z in ZipCode.objects.all():
        # zipcode[z.id] = {'distinct_species' : z.aggregates.distinct_species, 
                            # 'total_trees' : z.aggregates.total_trees, 
                            # 'geom' : eval(z.geometry.simplify(.0002).geojson)['coordinates'][0], 
                            # 'name' : z.zipcode}
                      

    # get enviro attributes for 'selected' trees
    min_year = 1970
    planted_trees = Tree.objects.exclude(date_planted=None).exclude(present=False).order_by("date_planted")
    if planted_trees.count():
        min_year = Tree.objects.exclude(date_planted=None).exclude(present=False).order_by("date_planted")[0].date_planted.year
    current_year = datetime.now().year    

    # TODO: Fix this to include updates to treestatus and treeflag objects
    min_updated = 0
    max_updated = 0 
    updated = Tree.objects.exclude(last_updated=None, present=False).order_by("last_updated")
    if updated.exists():
        min_updated = mktime(updated[0].last_updated.timetuple())
        max_updated = mktime(updated[updated.count()-1].last_updated.timetuple())

    recent_trees = Tree.objects.filter(present=True).order_by("-last_updated")[0:3]
    recent_status = TreeStatus.objects.filter(tree__present=True).order_by("-reported")[0:3]
    recent_flags = TreeFlags.objects.filter(tree__present=True).order_by("-reported")[0:3]

    recent_edits = unified_history(recent_trees, recent_status, recent_flags)

    #TODO return the recent_edits instead
    latest_trees = Tree.objects.filter(present=True).order_by("-last_updated")[0:3]
    latest_photos = TreePhoto.objects.exclude(tree__present=False).order_by("-reported")[0:8]

    return render_to_response('treemap/results.html',RequestContext(request,{
        #'top_species' : top_species,
        #'latest_maint' : latest_maint,
        #'interesting_trees' : interesting_trees,
        #'neighborhoods' : simplejson.dumps(neighborhoods),
        #'zipcodes' : simplejson.dumps(zipcodes)
        'latest_trees': latest_trees,
        'latest_photos': latest_photos,
        'min_year': min_year,
        'current_year': current_year,
        'min_updated': min_updated,
        'max_updated': max_updated,
        }))


def tree_location_search(request):
    geom = get_pt_or_bbox(request.GET)
    if not geom:
        raise Http404
    distance = request.GET.get('distance', .0015)
    max_trees = request.GET.get('max_trees', 1)
    if max_trees > 500: max_trees = 500
    
    trees = Tree.objects.filter(present=True)
        #don't filter by geocode accuracy until we know why some new trees are getting -1
        #Q(geocoded_accuracy__gte=8)|Q(geocoded_accuracy=None)|Q(geocoded_accuracy__isnull=True)).filter(

    if geom.geom_type == 'Point':
        trees = trees.filter(geometry__dwithin=(
            geom, float(distance))
            ).distance(geom).order_by('distance')
    #else bbox
    else:
      trees = trees.filter(geometry__intersects=geom)
    # needed to be able to prioritize overlapping trees
    species = request.GET.get('species')
    if species:
        # first try to restrict search to the active tree species
        species_trees = trees.filter(species__symbol=species)
        # to allow clicking other trees still...
        if species_trees.exists():
            trees = species_trees
    if trees.exists():
        trees = trees[:max_trees]
    return render_to_geojson(trees, 
                             geom_field='geometry', 
                             excluded_fields=['sidewalk_damage',
                             'address_city',                              
                             'condition_wood',
                             'region_id',
                             'plot_length',
                             'distance',
                             'orig_species',
                             'geometry',
                             'native',
                             'geocoded_address',
                             'photo',
                             'last_updated_by_id',
                             'data_owner_id',
                             'flowering',
                             'present',
                             'owner_additional_properties',
                             'region',
                             'powerline_conflict_potential',
                             'steward_user_id',
                             'owner_orig_id',
                             'condition_leaves',
                             'height',
                             'plot_height',
                             'private_property',
                             'geocoded_lat',
                             'geocoded_lon',
                             'site_type'])

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
        print 'filtering by nearby'
        location = request.GET.get('location','')
        if not location:
            return 404
        coord = map(float,location.split(','))
        print coord
        pt = Point(coord[0], coord[1])
        trees =  Tree.objects.filter(present=True).filter(geometry__dwithin = (pt,.001))#.distance(pt).order_by('distance').count()
        species = Species.objects.filter(tree__in=trees)
    
    if selection == 'all':
        species = Species.objects.all().order_by('common_name')
    
    if format == 'json':
        res = [{"symbol":str(x.accepted_symbol or ''), 
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
    faves = User.objects.get(username=username).treefavorite_set.all()
    js = [{
       'id':f.tree.id, 
       'coords':[f.tree.geometry.x, f.tree.geometry.y]} for f in faves]
    return render_to_json(js)
    
def trees(request, tree_id=''):
    trees = Tree.objects.filter(present=True)
    # testing - to match what you get in /location query and in map tiles.
    favorite = False
    recent_edits = []
    if tree_id:
        trees = trees.filter(pk=tree_id)
        
        if not trees.exists():
            raise Http404
        
        # get the last 5 edits to each tree piece
        history = trees[0].history.order_by('-last_updated')[:5]
        status = TreeStatus.history.filter(tree=trees).order_by('-reported')[:5]
        flags = TreeFlags.history.filter(tree=trees).order_by('-reported')[:5]
        
        recent_edits = unified_history(history, status, flags)
    
        if request.user.is_authenticated():
            favorite = TreeFavorite.objects.filter(user=request.user,
                tree=trees).count() > 0
    else:
        trees = trees.filter(Q(geocoded_accuracy__gte=8)|Q(geocoded_accuracy=None))

    
    if request.GET.get('format','') == 'json':
        return render_to_geojson(trees, geom_field='geometry')
    first = None
    if trees.exists():
        first = trees[0]
    else:
        raise Http404
    if request.GET.get('format','') == 'base_infowindow':
        return render_to_response('treemap/tree_detail_infowindow.html',RequestContext(request,{'tree':first}))
    if request.GET.get('format','') == 'eco_infowindow':
        return render_to_response('treemap/tree_detail_eco_infowindow.html',RequestContext(request,{'tree':first}))
    else:
        return render_to_response('treemap/tree_detail.html',RequestContext(request,{'favorite': favorite, 'tree':first, 'recent': recent_edits}))
     

def unified_history(trees, status, flags):
    recent_edits = []
    for t in trees:
        recent_edits.append((t.last_updated_by.username, t.last_updated))
    for s in status:
        recent_edits.append((s.reported_by, s.reported))
    for f in flags:
        recent_edits.append((f.reported_by, f.reported))    
    # sort by the date descending
    return sorted(recent_edits, key=itemgetter(1), reverse=True)

@login_required    
def tree_edit_choices(request, tree_id, type_):
    tree = get_object_or_404(Tree, pk=tree_id)
    if type_ in STATUS_CHOICES.keys():
        choices = STATUS_CHOICES[type_]
    else:
        raise Http404
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
        if type_ == "sidewalk_damage":
            sidewalks = tree.treestatus_set.filter(key="sidewalk_damage").order_by("-reported")
            if sidewalks.count():
                data['selected'] = str(int(sidewalks[0].value))
        if type_ == "condition":
            sidewalks = tree.treestatus_set.filter(key="condition").order_by("-reported")
            if sidewalks.count():
                data['selected'] = str(int(sidewalks[0].value))
        if type_ == "canopy_condition":
            sidewalks = tree.treestatus_set.filter(key="canopy_condition").order_by("-reported")
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
    
    dbh = tree.treestatus_set.filter(key="dbh").order_by("-reported")
    if dbh.count():
        diams = [tree.treestatus_set.filter(key="dbh").order_by("-reported")[0]]
    else:
        diams = []
    diam = {'type':'diameter_field',
         'name': 'dbh',
         'label': "Trunk diameter (inches)",
         'diams': str([x.value for x in diams]), 
         'display': tree.get_dbh()
        }
    
    height = {'type':'status_field',
         'name': 'height',
         'label': "Tree height (feet)",
        }
    heights = tree.treestatus_set.filter(key="height").order_by("-reported")
    if heights.count():
        height['value'] = heights[0].value
        height['display'] = heights[0].value
    
    c_height = {'type':'status_field',
         'name': 'canopy_height',
         'label': "Canopy height (feet)",
        }
    c_heights = tree.treestatus_set.filter(key="canopy_height").order_by('-reported')
    if c_heights.count():
        c_height['value'] = c_heights[0].value
        c_height['display'] = c_heights[0].value
    
    c_condition = {'type':'status_field',
             'name': 'canopy_condition',
             'label': "Canopy condition",
             'jsOptions': ", 'type':'select', 'loadurl':'choices/canopy_condition/'"
            }
    c_conditions = tree.treestatus_set.filter(key="canopy_condition").order_by('-reported')
    if c_conditions.count():
        c_condition['value'] = c_conditions[0].value
        c_condition['display'] = c_conditions[0].display
        
    sidewalk = {'type':'status_field',
         'name': 'sidewalk_damage',
         'label': "Sidewalk damage",
         'jsOptions': ", 'type':'select', 'loadurl':'choices/sidewalk_damage/'"
        }
    sidewalks = tree.treestatus_set.filter(key="sidewalk_damage").order_by("-reported")
    if sidewalks.count():
        sidewalk['value'] = sidewalks[0].value
        sidewalk['display'] = sidewalks[0].display
    
    condition = {'type':'status_field',
         'name': 'condition',
         'label': "Tree condition",
         'jsOptions': ", 'type':'select', 'loadurl':'choices/condition/'"
        }
    conditions = tree.treestatus_set.filter(key="condition").order_by("-reported")
    if conditions.count():
        condition['value'] = conditions[0].value
        condition['display'] = conditions[0].display
    
    perm = Permission.objects.get(name = 'can_edit_condition')
    rep = Reputation.objects.reputation_for_user(request.user)
    
    data = [
        {'type':'header',
         'text': "General Tree Information"
        },
        {'type':'species_field',
         'name': 'species_id',
         'label': 'Scientific name',
         'value': tree.get_scientific_name()
        },
        {'type':'field_noedit',
         'name': 'species',
         'label': 'Common name',
         'value': tree.species and tree.species.common_name
        },
        diam,
    ]

    height_data = [
        height,
        c_height,
    ]
    if rep.reputation >= perm.required_reputation or request.user.is_superuser:
        data.extend(height_data)
        
    further_data = [
        {'type':'field',
         'name': 'address_street',
         'label':"Street",
         'value': tree.address_street
        },
        {'type':'field',
         'name': 'address_city',
         'label':"City",
         'value': tree.address_city
        },
        {'type':'field_noedit',
         'name': 'address_zip',
         'label':"Zip code",
         'value': tree.address_zip
        },
        {'type':'date_field',
         'name': 'date_planted',
         'label':"Date planted",
         'value': tree.date_planted
        },
        {'type':'header',
         'text': "Environment"
        },
        {'type':'field',
         'name': 'plot_length',
         'label':"Plot length (feet)",
         'value': tree.plot_length
        },
        {'type':'field',
         'name': 'plot_width',
         'label':"Plot width (feet)",
         'value': tree.plot_width
        },
        {'type':'field_choices',
         'name': 'plot_type',
         'label':"Plot type",
         'value': tree.get_plot_type_display()
        },
        {'type':'field_choices',
         'name': 'powerline_conflict_potential',
         'label':"Is there a powerline overhead?",
         'value': tree.get_powerline_conflict_potential_display()
        },
    ]
    data.extend(further_data)
    
    optional_data = [
        sidewalk,
        condition,
        c_condition,
    ]    
    status_data = [  
        {'type':'header',
         'text': "Status"
        },
    ]
    if not tree.data_owner or tree.data_owner.id != 11:
        status_data.extend(optional_data)    
    status_data.append({
        'type':'local',
        'name': 'local',
        'label':"Local",
        'value': tree.treeflags_set.all()
    })
    
    if rep.reputation >= perm.required_reputation or request.user.is_superuser:
        data.extend(status_data)


    return render_to_response('treemap/tree_edit.html',RequestContext(request,{ 'instance': tree, 'data': data}))           

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
@permission_required('change_user')
def edit_users(request):        
    users = User.objects.all()
    if 'username' in request.GET:
        users = users.filter(username__icontains=request.GET['username'])
    if 'user' in request.GET:
        users = users.filter(Q(first_name__icontains=request.GET['user']) | Q(last_name__icontains=request.GET['user']) | Q(email__icontails=request.GET['user']))
    if 'group' in request.GET:
        g = Group.objects.filter(name__icontains=request.GET['group'])
        if g.count() == 1:
            users = users.filter(groups=g)
        else:
            users = users.filter(groups__in=g)
    
    groups = Group.objects.all()
    return render_to_response('treemap/user_edit.html',RequestContext(request, {'users': users, 'groups': groups}))

@permission_required('change_user')
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

@permission_required('change_user')
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
    
@permission_required('change_user')
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
                            cleaned = fld.clean(v,instance)
                            if k == 'species_id':
                                response_dict['update']['old_' + k] = instance.get_scientific_name()
                                instance.set_species(v,commit=False)
                            else:
                                # old value for non-status objects only, status objects return None
                                # and are handled after parent model is set
                                response_dict['update']['old_' + k] = getattr(instance,k).__str__()
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
                            print "instance set"
                            if response_dict['update'].has_key('old_value'):
                                history = model_object.history.filter(tree__id__exact=instance.tree.id).filter(key__exact=instance.key).filter(_audit_change_type__exact="U").order_by('-reported')
                                if history.count() == 0:
                                    history = model_object.history.filter(tree__id__exact=instance.tree.id).filter(key__exact=instance.key).filter(_audit_change_type__exact="I").order_by('reported')
                                if history.count() > 0:
                                    if isinstance(history[0].value, datetime):
                                        response_dict['update']['old_value'] = history[0].value.strftime("%b %d %Y")
                                    else:
                                        response_dict['update']['old_value'] = history[0].value.__str__()
                        except Exception, e:
                            response_dict['errors'].append('Error setting related obj: %s: %s' % (sys.exc_type,str(e)))

            # finally save the instance...
            try:
                if not delete:
                    instance._audit_diff = simplejson.dumps(response_dict["update"])
                    instance.save()
                    print "instance save"
                    if post['model'] in  ["Tree", "TreeStatus", "TreeAlert", "TreeFlags"] :
                        Reputation.objects.log_reputation_action(request.user, request.user, 'edit tree', save_value, instance)
                    if hasattr(instance, 'validate_all'):
                        instance.validate_all()
                if parent_instance:
                    pass
                    #parent_instance.save()
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
            #content_type = 'application/javascript; charset=utf8'
            content_type = 'text/plain'
            )
#for auto reverse-geocode saving of new address, from search page map click
def tree_location_update(request):
    response_dict = {}
    post = simplejson.loads(request.raw_post_data)
    tree = Tree.objects.filter(pk=post.get('tree_id'))[0]
    tree.address_street = post.get('address')
    tree.address_city = post.get('city')
    tree.quick_save()
    
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
            print 'saved %s' % new_tree
            Reputation.objects.log_reputation_action(request.user, request.user, 'add tree', 25, new_tree)
            
            return HttpResponseRedirect('/trees/%s/edit/' % new_tree.id)
    else:
        form = TreeAddForm()

    return render_to_response('treemap/tree_add.html', RequestContext(request,{
        'user' : request.user, 
        'form' : form }))
    

def _build_tree_search_result(request):
    # todo - optimize!
    species = Species.objects.filter(tree_count__gt=0)
    max_species_count = species.count()
    
    species_criteria = {'species' : 'accepted_symbol',
                        'native' : 'native_status',
                        'edible' : 'palatable_human',
                        'color' : 'fall_conspicuous',
                        'cultivar' : 'cultivar_name',
                        'flowering' : 'flower_conspicuous'}
                        
    for k in species_criteria.keys():
        v = request.GET.get(k,'')
        if v:
            attrib = species_criteria[k]
            species = species.filter(**{attrib:v})
            print 'filtered species by %s = %s' % (species_criteria[k],v)
            print '  .. now we have %d species' % len(species)
            
    cur_species_count = species.count()
    if max_species_count == cur_species_count:
        trees = Tree.objects.filter(present=True).filter(Q(geocoded_accuracy__gte=7)|Q(geocoded_accuracy=None)|(Q(geocoded_accuracy=-1) & Q(owner_geometry__isnull=False)) )
    else:
        trees = Tree.objects.filter(species__in=species, present=True).filter(Q(geocoded_accuracy__gte=7)|Q(geocoded_accuracy=None))
    #filter by nhbd or zipcode if location was specified

    geog_obj = None
    if 'location' in request.GET:
        loc = request.GET['location']
        if "," in loc:
            ns = Neighborhood.objects.all().order_by('id')
            coords = map(float,loc.split(','))
            pt = Point(coords)
            ns = ns.filter(geometry__contains=pt)
            if ns.count():
                trees = trees.filter(neighborhood = ns[0])
                geog_obj = ns[0]
        else:
            z = ZipCode.objects.filter(zip=loc)
            if z.count():
                trees = trees.filter(zipcode = z[0])
                geog_obj = z[0]
    elif 'hood' in request.GET:
        ns = Neighborhood.objects.filter(name__icontains = request.GET.get('hood'))
        if ns:
             trees = trees.filter(neighborhood = ns[0])
             geog_obj = ns[0]

    #import pdb;pdb.set_trace()

    tree_criteria = {'carbon' : '2',
                     'gleaning' : '3',
                     'landmark' : '1'}
    for k in tree_criteria.keys():
        v = request.GET.get(k,'')
        if v:
            attrib = tree_criteria[k]
            trees = trees.filter(treeflags__key__exact=attrib)
            print 'filtered trees by %s = %s' % (tree_criteria[k],v)
            print '  .. now we have %d trees' % len(trees)

    #filter by missing data params:
    missing_species = request.GET.get('missing_species','')
    if missing_species:
        trees = trees.filter(species__isnull=True)
        print 'filtered trees by missing species only - %s - %s' % (tree_criteria[k],v)
        print '  .. now we have %d trees' % len(trees)
    
    #
    ### TODO - add ability to show trees without "correct location"
    ##
    missing_current_dbh = request.GET.get('missing_diameter','')
    if missing_current_dbh:
        trees = trees.filter(Q(current_dbh__isnull=True) | Q(current_dbh=0))
        # TODO: What about ones with 0 current_dbh?
        print '  .. now we have %d trees' % len(trees)
     
    if not missing_current_dbh and 'diameter_range' in request.GET:
        min, max = map(float,request.GET['diameter_range'].split("-"))
        trees = trees.filter(current_dbh__gte=min)
        if max != 50: # TODO: Hardcoded in UI, may need to change
            trees = trees.filter(current_dbh__lte=max)
    
    if 'planted_range' in request.GET:
        min, max = map(float,request.GET['planted_range'].split("-"))
        min = "%i-01-01" % min
        max = "%i-12-31" % max
        trees = trees.filter(date_planted__gte=min, date_planted__lte=max)
    
    if 'updated_range' in request.GET:
        min, max = map(float,request.GET['updated_range'].split("-"))
        min = datetime.fromtimestamp(min)
        max = datetime.fromtimestamp(max)
        trees = trees.filter(last_updated__gte=min, last_updated__lte=max)
    if not geog_obj:
        q = request.META['QUERY_STRING'] or ''
        cached_search_agg = AggregateSearchResult.objects.filter(key=q)
        if cached_search_agg.exists() and cached_search_agg[0].ensure_recent(trees.count()):
            geog_obj = cached_search_agg[0]
            print 'found cached agg object for query:', q
        else:
            #geog_obj = cache_search_aggs(query_pairs=({'trees':trees,'query':q},),return_first=True)
            geog_obj = AggregateSearchResult(key=q)
            geog_obj.total_trees = trees.count()
            geog_obj.distinct_species = trees.values("species").annotate(Count("id")).order_by("species").count()
            #TODO figure out how to summarize diff stratum stuff
            fields = [x.name for x in ResourceSummaryModel._meta.fields 
                if not x.name in ['id','aggregatesummarymodel_ptr','key','resourcesummarymodel_ptr','last_updated']]
            #r = ResourceSummaryModel()
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


    return trees, geog_obj
        
def advanced_search(request, format='json'):
    """
    urlparams:
     - location
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
        maximum_trees_for_display = 1000   
    maximum_trees_for_summary = 200000  
    response = {}

    trees, geog_obj = _build_tree_search_result(request)
    print "here"
    #todo missing geometry
    if format == "geojson":    
        return render_to_geojson(trees, geom_field='geometry', additional_data={'summaries': esj})
    elif format == "shp":
        print 'shp for %s trees' % len(trees)
        return ShpResponder(trees,geo_field='geometry')
    elif format == "kml":
        print 'kml for %s trees' % len(trees)
        trees = trees.kml()
        print 'kml for %s trees' % len(trees)
        return render_to_kml("treemap/kml_output.kml", {'trees': trees,'root_url':settings.ROOT_URL})
    elif format == "csv":
        return ExcelResponse(trees, force_csv=True)

        
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
    esj = {}
    esj['total_trees'] = tree_count
    print 'tree count', tree_count   

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
        esj['distinct_species'] = len(trees.values("species").annotate(Count("id")).order_by("species"))
        print 'we have %s  ..' % esj
        print 'aggregating..'

        r = ResourceSummaryModel()
        
        with_out_resources = trees.filter(treeresource=None).count()
        print 'without resourcesums:', with_out_resources
        resources = tree_count - with_out_resources
        print 'have resourcesums:', resources
        
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

        print 'aggregated...'
    
    
    if tree_count > maximum_trees_for_display:   
         trees = []
         response.update({'tile_query' : request.META['QUERY_STRING']})
        
  
    tj = [{
          'id': t.id,
          'lon': '%.12g' % t.geometry.x, 
          'lat' : '%.12g' % t.geometry.y,
          'cmplt' : t.is_complete()
          } for t in trees]

    response.update({'trees' : tj, 'summaries' : esj, 'geography' : geography, 'initial_tree_count' : tree_count})
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

@cache_page(60*5)    
def geographies(request, model, id=''):
    """
    return list of nhbds and resource attrs, possibly in json format
    """
    format = request.GET.get('format','html')
    location = request.GET.get('location','')
    name = request.GET.get('name', '')
    list = request.GET.get('list', '')
    print list
    
    ns = model.objects.all().order_by('state','county','name')
    
    if location:
        coords = map(float,location.split(','))
        pt = Point(coords)
        ns = ns.filter(geometry__contains=pt)
    
    if id:
        ns = ns.filter(id=id)
    if name:
        ns = ns.filter(name__iexact=name)
    if list:        
        ns = ns.exclude(aggregates__total_trees=0)
    if format.lower() == 'json':
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
    print list
    
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


from django.core import serializers
@login_required 
def verify_edits(request, audit_type='tree'):
    
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
        
    changes = []
    trees = Tree.history.filter(present=True).filter(_audit_user_rep__lt=1000).filter(_audit_change_type__exact='U').exclude(_audit_diff__exact='').filter(_audit_verified__exact=0)
    newtrees = Tree.history.filter(present=True).filter(_audit_user_rep__lt=1000).filter(_audit_change_type__exact='I').filter(_audit_verified__exact=0)
    treestatus = TreeStatus.history.filter(tree__present=True).filter(_audit_user_rep__lt=1000).filter(_audit_change_type__exact='U').filter(_audit_verified__exact=0)
    treeactions = []
    if (request.user.reputation.reputation >= 1000):
       treeflags = TreeFlags.history.filter(tree__present=True).filter(_audit_change_type__exact='U').filter(_audit_verified__exact=0)
    
    if 'username' in request.GET:
        u = User.objects.filter(username__icontains=request.GET['username'])
        trees = trees.filter(last_updated_by__in=u)
        newtrees = newtrees.filter(last_updated_by__in=u)
        treestatus = treestatus.filter(reported_by__in=u)
        treeflags = treeflags.filter(reported_by__in=u)
    if 'address' in request.GET:
        trees = trees.filter(address_street__icontains=request.GET['address'])
        newtrees = newtrees.filter(address_street__icontains=request.GET['address'])
        treestatus = treestatus.filter(tree__address_street__icontains=request.GET['address'])
        treeflags = treeflags.filter(tree__address_street__icontains=request.GET['address'])
    if 'nhood' in request.GET:
        n = Neighborhood.objects.filter(name=request.GET['nhood'])
        trees = trees.filter(neighborhood=n)
        newtrees = newtrees.filter(neighborhood=n)
        treestatus = treestatus.filter(tree__neighborhood=n)
        treeflags = treeflags.filter(tree__neighborhood=n)
    
    
    for tree in trees:
        species = 'no species name'
        if tree.species:
            species = tree.species.common_name
        changes.append({
            'id': tree.id,
            'species': species,
            'address_street': tree.address_street,
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
        changes.append({
            'id': tree.id,
            'species': species,
            'address_street': tree.address_street,
            'last_updated_by': tree.last_updated_by,
            'last_updated': tree.last_updated,
            'change_description': 'New Tree',
            'change_id': tree._audit_id,
            'type': 'tree'
        })
    for status in treestatus:
        species = 'no species name'
        if status.tree.species:
            species = status.tree.species.common_name
        
        diff = simplejson.JSONDecoder().decode(status._audit_diff)
        diff_no_old = {}
        for key in diff:
            if not key == 'old_key':
                diff_no_old[key] = diff[key]
        changes.append({
            'id': status.tree.id,
            'species': species,
            'address_street': status.tree.address_street,
            'last_updated_by': status.reported_by,
            'last_updated': status.reported,
            'change_description': diff_no_old,
            'change_id': status._audit_id,
            'type': 'status'
        })
    for flags in treeflags:
        species = 'no species name'
        if flags.tree.species:
            species = flags.tree.species.common_name

        changes.append({
            'id': flags.tree.id,
            'species': species,
            'address_street': flags.tree.address_street,
            'last_updated_by': flags.reported_by,
            'last_updated': flags.reported,
            'change_description':  clean_diff(flags._audit_diff),
            'change_id': flags._audit_id,
            'type': 'flag'
        })
        
    return render_to_response('treemap/verify_edits.html',RequestContext(request,{'changes':changes}))

@login_required
@permission_required('change_user') #proxy for group users
def watch_list(request):    
    watch_failures = TreeWatch.objects.filter(valid=False)
    if 'username' in request.GET:
        u = User.objects.filter(username__icontains=request.GET['username'])
        watch_failures = watch_failures.filter(tree__last_updated_by=u)
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
@permission_required('change_user') #proxy for group users
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
@permission_required('change_user')
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
            user_date_treestatusupdate = TreeStatus.history.filter(tree__present=True, reported_by=user, _audit_change_type__exact='U',_audit_timestamp__range=(start_time, end_time))
            user_date_treeflagsupdate = TreeFlags.history.filter(tree__present=True, reported_by=user, _audit_change_type__exact='U', _audit_timestamp__range=(start_time, end_time))

            aggs.append({
                'user':user.username, 
                'new':user_date_newtrees.count(), 
                'update': user_date_treeupdate.count(), 
                'status': user_date_treestatusupdate.count(),
                'flags': user_date_treeflagsupdate.count(),
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
    elif change_type == 'status':
        change = TreeStatus.history.filter(_audit_id__exact=change_id)[0]
        user = get_object_or_404(User, pk=change.reported_by_id)
        obj = get_object_or_404(TreeStatus, pk=change.id)
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
@permission_required('moderate_comments')
def view_flagged(request):
    flags = CommentFlag.objects.filter(comment__is_public=True)
    if 'username' in request.GET:
        u = User.objects.filter(username__icontains=request.GET['username'])
        flags = flags.filter(user__in=u)
    if 'text' in request.GET:
        flags = flags.filter(comment__icontains=request.GET['text'])
    if 'nhood' in request.GET:
        n = Neighborhood.objects.filter(name=request.GET['nhood'])
        f_list = list(flags)
        for f in f_list:            
            if Tree.objects.filter(pk=f.comment.object_pk, neighborhood=n).count() == 0:
                f_list.remove(f)
        return render_to_response('comments/edit_flagged.html',RequestContext(request,{'flags':f_list}))
        
    return render_to_response('comments/edit_flagged.html',RequestContext(request,{'flags':flags}))
    
@login_required
@permission_required('moderate_comments')
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
    comment = CommentFlag.objects.get(id=flag_id).comment
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
@permission_required('change_user') #proxy for group users
def build_admin_panel(request):
    return render_to_response('treemap/admin.html',RequestContext(request))

@login_required
@permission_required('change_user') #proxy for group users
def view_images(request):
    user_images = UserProfile.objects.exclude(photo="").order_by("-user__last_login")
    tree_images = TreePhoto.objects.all().order_by("-reported")
    return render_to_response('treemap/images.html',RequestContext(request, {'user_images':user_images, 'tree_images':tree_images}))
