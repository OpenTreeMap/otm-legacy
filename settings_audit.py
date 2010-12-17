from django.db import models

def get_user_rep(instance):
    if hasattr(instance, 'reported_by'):  #a TreeItem instance
        return instance.reported_by.reputation.reputation
    else:  #a Tree instance
        return instance.last_updated_by.reputation.reputation
        
def get_diff(instance):
    #get the previous change of this object
    if hasattr(instance, '_audit_diff'):
        return instance._audit_diff
    return ''

# Populate the fields that every Audit model in this app will use.
GLOBAL_TRACK_FIELDS = (
    ('_audit_user_rep', models.IntegerField(), get_user_rep),
    ('_audit_diff', models.TextField(), get_diff),
    ('_audit_verified', models.IntegerField(), 0)
)
