import csv
import json
from datetime import datetime

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings

from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.contrib.auth.models import User

from treemap.models import Species, Neighborhood, Plot,\
    Tree, ExclusionMask

from importer.models import TreeImportEvent, TreeImportRow

def lowerkeys(h):
    h2 = {}
    for (k,v) in h.iteritems():
        h2[k.lower().strip()] = v.strip()

    return h2

def start(request):
    return render_to_response('importer/index.html', RequestContext(request,{}))

def create(request):
    process_csv(request)

    return HttpResponseRedirect(reverse('importer.views.list_imports'))

def list_imports(request):
    return render_to_response(
        'importer/list.html',
        RequestContext(
            request,
            {'events': TreeImportEvent.objects.all()}))

def show_import_status(request, import_event_id):
    return render_to_response(
        'importer/status.html',
        RequestContext(
            request,
            {'event': TreeImportEvent.objects.get(pk=import_event_id)}))

def update_row(request, import_event_row_id):
    update_keys = { key.split('update__')[1]
                    for key
                    in request.REQUEST.keys()
                    if key.startswith('update__') }

    row = TreeImportRow.objects.get(pk=import_event_row_id)

    basedata = row.datadict

    for key in update_keys:
        basedata[key] = request.REQUEST['update__%s' % key]

    row.datadict = basedata
    row.save()
    row.validate_row()

    return HttpResponseRedirect(reverse('importer.views.show_import_status',
                                        args=(row.import_event.pk,)))

def results(request, import_event_id, subtype):
    """ Return a json array for each row of a given subtype
    where subtype is a valid status for a TreeImportRow
    """
    status_map = {
        'success': TreeImportRow.SUCCESS,
        'error': TreeImportRow.ERROR,
        'waiting': TreeImportRow.WAITING,
        'watch': TreeImportRow.WATCH,
        'verified': TreeImportRow.VERIFIED
    }

    page_size = 50
    page = int(request.REQUEST.get('page', 0))
    page_start = page_size * page
    page_end = page_size * (page + 1)

    ie = TreeImportEvent.objects.get(pk=import_event_id)

    header = None
    output = {}
    query = ie.treeimportrow_set\
              .filter(status=status_map[subtype])\
              .order_by('idx')

    count = query.count()
    total_pages = int(float(count) / page_size + 1)

    output['total_pages'] = total_pages
    output['count'] = count
    output['rows'] = []

    header_keys = None
    for row in query:
        if header is None:
            header_keys = row.datadict.keys()

        plot_pk = None

        if row.plot:
            plot_pk = row.plot.pk

        output['rows'].append({
            'plot_id': plot_pk,
            'row': row.idx,
            'errors': row.errors_as_array(),
            'data': [row.datadict[k] for k in header_keys]
        })

    output['fields'] = header_keys or \
                       ie.treeimportrow_set.all()[0].datadict.keys()

    return HttpResponse(
        json.dumps(output),
        content_type = 'application/json')


def commit(request, import_event_id):
    #TODO:!!! NEED TO ADD TREES TO WATCH LIST
    #TODO:!!! Trees in the same import event should not cause
    #         proximity issues
    #TODO:!!! NEED TO INDICATE TREES TO BE ADDED TO WATCH LIST
    #TODO:!!! NEED TO CLEAR TILE CACHE
    #TODO:!!! If 'Plot' already exists on row *update* when changed
    ie = TreeImportEvent.objects.get(pk=import_event_id)

    commit_import_event(ie)

    return HttpResponse(
        json.dumps({'status': 'done'}),
        content_type = 'application/json')

def process_csv(request):
    files = request.FILES
    filename = files.keys()[0]
    fileobj = files[filename]

    owner = User.objects.all()[0]
    ie = TreeImportEvent(file_name=filename,
                         owner=owner)
    ie.save()

    rows = create_rows_for_event(ie, fileobj)

    #TODO: Celery
    if rows:
        run_import_event_validation(ie)

    return HttpResponse(
        json.dumps({'id': ie.pk}),
        content_type = 'application/json')

def process_commit(request, import_id):
    ie = TreeImportEvent.objects.get(pk=import_id)

    rslt = commit_import_event(ie)

    # TODO: What to return here?
    return HttpResponse(
        json.dumps({'status': 'success'}),
        content_type = 'application/json')

def run_import_event_validation(ie):
    filevalid = ie.validate_main_file()

    rows = ie.treeimportrow_set.all()
    if filevalid:
        for row in rows:
            row.validate_row()

def commit_import_event(ie):
    filevalid = ie.validate_main_file()

    rows = ie.treeimportrow_set.all()
    success = []
    failed = []

    if filevalid:
        for row in rows:
            if row.plot is None or row.status != TreeImportRow.SUCCESS:
                if row.commit_row():
                    success.append(row)
                else:
                    failed.append(row)
            else:
                success.append(row)

        return (success, failed)
    else:
        return False

def create_rows_for_event(importevent, csvfile):
    rows = []
    reader = csv.DictReader(csvfile)

    idx = 0
    for row in reader:
        rows.append(
            TreeImportRow.objects.create(
                data=json.dumps(lowerkeys(row)),
                import_event=importevent, idx=idx))

        # First row
        if idx == 0:
            # Break out early if there was an error
            # with the basic file structure
            importevent.validate_main_file()
            if importevent.has_errors():
                return False

        idx += 1

    return rows
