from celery import task

from importer.models import TreeImportRow

@task()
def validate_rows(rows):
    for row in rows:
        row.validate_row()

@task()
def run_import_event_validation(ie):
    block_size = 250
    filevalid = ie.validate_main_file()

    rows = ie.rows()
    if filevalid:
        for i in xrange(0,rows.count(), block_size):
            validate_rows.delay(rows[i:(i+block_size)])

@task()
def commit_rows(rows):
    #TODO: Refactor out [Tree]ImportRow.SUCCESS
    # this works right now because they are the same
    # value (0) but that's not really great
    if row.status != TreeImportRow.SUCCESS:
        row.commit_row()

@task()
def commit_import_event(ie):
    filevalid = ie.validate_main_file()

    rows = ie.rows()
    success = []
    failed = []

    #TODO: When using OTM ID field, don't include
    #      that tree in proximity check (duh)
    if filevalid:
        for i in xrange(0,rows.count(), block_size):
            commit_rows.delay(rows[i:(i+block_size)])
