from celery import task

from importer.models import TreeImportRow

@task()
def run_import_event_validation(ie):
    filevalid = ie.validate_main_file()

    rows = ie.rows()
    if filevalid:
        for row in rows:
            row.validate_row()

@task()
def commit_import_event(ie):
    filevalid = ie.validate_main_file()

    rows = ie.rows()
    success = []
    failed = []

    #TODO: When using OTM ID field, don't include
    #      that tree in proximity check (duh)
    if filevalid:
        for row in rows:
            #TODO: Refactor out [Tree]ImportRow.SUCCESS
            # this works right now because they are the same
            # value (0) but that's not really great
            if row.status != TreeImportRow.SUCCESS:
                if row.commit_row():
                    success.append(row)
                else:
                    failed.append(row)
            else:
                success.append(row)

        return (success, failed)
    else:
        return False
