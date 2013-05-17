from celery import task

from importer.models import TreeImportRow, GenericImportEvent, \
    GenericImportRow

BLOCK_SIZE = 250

def has_waiting_rows(ie):
    return ie.rows()\
             .filter(status=GenericImportRow.WAITING)\
             .exists()


@task()
def validate_rows(ie, i):
    for row in ie.rows()[i:(i+BLOCK_SIZE)]:
        row.validate_row()

    if not has_waiting_rows(ie):
        ie.status = GenericImportEvent.FINISHED_VERIFICATION
        ie.save()

@task()
def run_import_event_validation(ie):
    filevalid = ie.validate_main_file()

    ie.status = GenericImportEvent.VERIFIYING
    ie.save()

    rows = ie.rows()
    if filevalid:
        for i in xrange(0,rows.count(), BLOCK_SIZE):
            validate_rows.delay(ie, i)

@task()
def commit_rows(ie, i):
    #TODO: Refactor out [Tree]ImportRow.SUCCESS
    # this works right now because they are the same
    # value (0) but that's not really great
    for row in ie.rows()[i:(i + BLOCK_SIZE)]:
        if row.status != TreeImportRow.SUCCESS:
            row.commit_row()

    if not has_waiting_rows(ie):
        ie.status = GenericImportEvent.FINISHED_CREATING
        ie.save()

@task()
def commit_import_event(ie):
    filevalid = ie.validate_main_file()

    rows = ie.rows()
    success = []
    failed = []

    #TODO: When using OTM ID field, don't include
    #      that tree in proximity check (duh)
    if filevalid:
        for i in xrange(0,rows.count(), BLOCK_SIZE):
            commit_rows.delay(ie, i)
