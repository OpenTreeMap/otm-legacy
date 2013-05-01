import csv
import json
from datetime import datetime

from django.http import HttpResponse
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
        h2[k.lower()] = v

    return h2


def process_csv(request):
    owner = User.objects.all()[0]
    ie = TreeImportEvent(file_name=request.REQUEST['name'],
                         owner=owner)
    ie.save()

    create_rows_for_event(ie, request.FILES.values()[0])

    #TODO: Celery
    run_import_event_validation(ie)

    return HttpResponse(
        json.dumps({'id': ie.pk}),
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
            if row.commit_row():
                success.append(row)
            else:
                failed.append(row)

        return (success, failed)
    else:
        return False

def process_status(request, import_id):
    ie = TreeImportEvent.objects.get(pk=import_id)

    resp = None
    if ie.errors:
        resp = {'status': 'file_error',
                'errors': json.loads(ie.errors)}
    else:
        errors = []
        for row in ie.treeimportrow_set.all():
            if row.errors:
                errors.append((row.idx, json.loads(row.errors)))

        if len(errors) > 0:
            resp = {'status': 'row_error',
                    'errors': dict(errors)}

    if resp is None:
        resp = {'status': 'success',
                'rows': ie.treeimportrow_set.count()}

    return HttpResponse(
        json.dumps(resp),
        content_type = 'application/json')

def process_commit(request, import_id):
    ie = TreeImportEvent.objects.get(pk=import_id)

    rslt = commit_import_event(ie)

    # TODO: What to return here?
    return HttpResponse(
        json.dumps({'status': 'success'}),
        content_type = 'application/json')

def create_rows_for_event(importevent, csvfile):
    rows = []
    reader = csv.DictReader(csvfile)

    idx = 0
    for row in reader:
        rows.append(
            TreeImportRow.objects.create(
                data=json.dumps(lowerkeys(row)),
                import_event=importevent, idx=idx))

        idx += 1

    return rows
