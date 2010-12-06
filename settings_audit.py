from django.db import models

def get_user_rep(instance):
    if hasattr(instance, 'reported_by'):  #a TreeItem instance
        return instance.reported_by.reputation.reputation
    else:  #a Tree instance
        return instance.last_updated_by.reputation.reputation

# Populate the fields that every Audit model in this app will use.
GLOBAL_TRACK_FIELDS = (
    ('user_rep', models.IntegerField(), get_user_rep),
)
