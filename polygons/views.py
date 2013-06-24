import json

from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.core.exceptions import PermissionDenied
from django.core.files.base import ContentFile

from django.contrib.auth.decorators import login_required
from django.contrib.gis.geos import Point

from models import TreeRegionPolygon, TreeRegionEntry, DBHClass
from treemap.models import Species

def polygons2dict(polygons):
    polys = {}
    for polygon in polygons:
        entries = TreeRegionEntry.objects.filter(polygon=polygon)

        data = {e.species.pk: {} for e in entries}
        for entry in entries:
            species = data[entry.species.pk]
            species[entry.dbhclass.label] = entry.count

        polys[polygon.pk] = data

    return polys

def merge_histories(qs, to_dict_fn):
    edits_to_each_object = [object.history.all() for object in qs]

    merged_edits = []
    for edits in edits_to_each_object:
        for edit in edits:
            if edit._audit_diff:
                merged_edits.append(to_dict_fn(edit))
    return merged_edits

def entry_edit_to_dict(edit):
    return {
        'polygon': edit.polygon.id,
        'last_updated_by': edit.last_updated_by,
        'last_updated': edit.last_updated,
        'species': edit.species,
        'dbhclass': edit.dbhclass,
        'audit_diff': edit._audit_diff,
    }

def polygon_edit_to_dict(edit):
    return {
        'polygon': edit.id,
        'last_updated_by': edit.last_updated_by,
        'last_updated': edit.last_updated,
        'species': None,
        'dbhclass': None,
        'audit_diff': edit._audit_diff,
    }

def get_recent_edits_for_polygon(polygon_id):

    polygon = TreeRegionPolygon.objects.get(id=polygon_id)

    # first, get edits to the actual polygon
    # which should only be photo changes.
    polygon_edits = polygon.history.all()

    polygon_entries = TreeRegionEntry.objects.filter(polygon=polygon_id)

    entry_edits = merge_histories(polygon_entries, entry_edit_to_dict)

    all_edits = []

    all_edits += map(polygon_edit_to_dict, list(polygon_edits))

    all_edits += list(entry_edits)

    sort_by_recent_updates(all_edits)

    return all_edits

def sort_by_recent_updates(seq):
    seq.sort(key=(lambda x: x['last_updated']), reverse=True)

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
        entries = TreeRegionEntry.objects.filter(polygon=polygon,count__gt=0)

        species = list({e.species.pk for e in entries})
        classes = {e.dbhclass.pk: e.dbhclass for e in entries}.values()

        sorted(classes, key=lambda a: a.dbh_min)

        polys[polygon.pk] = {"species": species,
                             "classes": [c.label for c in classes]}

    return HttpResponse(json.dumps(polys),
                        content_type='application/json')

@login_required
def polygon_update(request, polygon_id):
    rep = request.user.reputation

    if rep.reputation < 1000:
        raise PermissionDenied('%s cannot access this view because they do not have the required permission' % request.user.username)

    polygon = TreeRegionPolygon.objects.get(pk=polygon_id)

    all_species = []

    for key in request.POST.keys():
        if key.startswith('pval_'):
            new_data = key.split('_')[1:]
            (pgonid, speciesid, dbhid) = new_data
            if pgonid != polygon_id:
                raise Exception("Invalid polygon id: %s" % pgonid)

            species = Species.objects.get(pk=speciesid)

            t, created = TreeRegionEntry.objects.get_or_create(
                polygon=polygon,
                dbhclass=DBHClass.objects.get(pk=dbhid),
                species=species,
                last_updated_by=request.user)

            all_species.append(species)

            old_count = None if created else t.count
            new_count = int(request.POST[key])
            t.count = new_count

            if old_count != new_count:
                t._audit_diff = "Changed count from %s to %s" % (old_count, new_count)

            t.save()

    TreeRegionEntry.objects\
                   .filter(polygon=polygon)\
                   .exclude(species__in=all_species)\
                   .delete()

    return HttpResponseRedirect(
        reverse('polygons.views.polygon_view', args=(polygon_id,)))

@login_required
def polygon_edit(request, polygon_id):
    rep = request.user.reputation

    if rep.reputation < 1000:
        raise PermissionDenied('%s cannot access this view because they do not have the required permission' % request.user.username)

    return polygon_view(request, polygon_id, template='polygons/edit.html')

@login_required
def polygon_update_photo(request, polygon_id):
    polygon = TreeRegionPolygon.objects.get(pk=polygon_id)

    rfile = request.FILES['photo']
    file_content = ContentFile(rfile.read())
    fname = rfile.name

    polygon.photo.save(fname, file_content, save=False)

    polygon.last_updated_by = request.user
    polygon._audit_diff = "Uploaded a new photo"
    polygon.save()

    polygon_url = reverse('polygons.views.polygon_view', args=(polygon_id,))
    next_url = request.REQUEST.get('currentpage', polygon_url)

    return HttpResponseRedirect(next_url)


def polygon_view(request, polygon_id,template='polygons/view.html'):

    showedit = request.user.is_authenticated() and \
               request.user.reputation.reputation >= 1000

    polygon = TreeRegionPolygon.objects.get(pk=polygon_id)
    alldbhs = DBHClass.objects.order_by("dbh_min")

    poly = []
    for (species, dbhs) in polygons2dict([polygon])[polygon.pk].iteritems():
        s = Species.objects.get(pk=species)
        row = [[s.pk,s.scientific_name]]

        for dbh in alldbhs:
            row.append([dbh.pk , dbhs.get(dbh.label,"")])

        poly.append(row)

    recent_edits = get_recent_edits_for_polygon(polygon_id)[:5]

    return render_to_response(
        template,
        RequestContext(
            request,
            {'showedit': showedit,
             'polygonobj': polygon,
             'polygon': poly,
             'recent_edits': recent_edits,
             'classes': alldbhs}))

@login_required
def recent_edits(request):
    rep = request.user.reputation

    if rep.reputation < 1000:
        raise PermissionDenied('%s cannot access this view because they do not have the required permission' % request.user.username)

    recent_edits = []
    recent_entries = TreeRegionEntry.objects.order_by('-polygon__last_updated')[:100]
    recent_edits += merge_histories(recent_entries, entry_edit_to_dict)
    recent_photos = TreeRegionPolygon.objects.filter(last_updated__isnull=False).order_by('-last_updated')[:100]
    recent_edits += merge_histories(recent_photos, polygon_edit_to_dict)

    sort_by_recent_updates(recent_edits)
    return render_to_response('polygons/recent_edits.html',
                              RequestContext(request,
                                  {'recent_edits': recent_edits}))
