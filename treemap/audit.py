from django.dispatch import dispatcher
from django.contrib.gis.db import models
from django.core.exceptions import ImproperlyConfigured
from django.contrib import admin
import copy
import re
import types
try:
    import settings_audit
except ImportError:
    settings_audit = None
value_error_re = re.compile("^.+'(.+)'$")

class AuditTrail(object):
    def __init__(self, show_in_admin=False, save_change_type=True, audit_deletes=True,
                 track_fields=None):
        self.opts = {}
        self.opts['show_in_admin'] = show_in_admin
        self.opts['save_change_type'] = save_change_type
        self.opts['audit_deletes'] = audit_deletes
        if track_fields:
            self.opts['track_fields'] = track_fields
        else:
            self.opts['track_fields'] = []

    def contribute_to_class(self, cls, name):
        # This should only get added once the class is otherwise complete
        def _contribute(sender, **kwargs):
            model = create_audit_model(sender, **self.opts)
            if self.opts['show_in_admin']:
                # Enable admin integration
                # If ModelAdmin needs options or different base class, find
                # some way to make the commented code work
                #   cls_admin_name = cls.__name__ + 'Admin'
                #   clsAdmin = type(cls_admin_name, (admin.ModelAdmin,),{})
                #   admin.site.register(cls, clsAdmin)
                # Otherwise, register class with default ModelAdmin
                admin.site.register(model)
            descriptor = AuditTrailDescriptor(model._default_manager, sender._meta.pk.attname)
            setattr(sender, name, descriptor)

            def _audit_track(instance, field_arr, **kwargs):
                field_name = field_arr[0]
                try:
                    return getattr(instance, field_name)
                except:
                    if len(field_arr) > 2:
                        if callable(field_arr[2]):
                            fn = field_arr[2]
                            return fn(instance)
                        else:
                            return field_arr[2]

            def _audit(sender, instance, created, **kwargs):
                # Write model changes to the audit model.
                # instance is the current (non-audit) model.
                kwargs = {}
                for field in sender._meta.fields:
                    #kwargs[field.attname] = getattr(instance, field.attname)
                    kwargs[field.name] = getattr(instance, field.name)
                if self.opts['save_change_type']:
                    if created:
                        kwargs['_audit_change_type'] = 'I'
                    else:
                        kwargs['_audit_change_type'] = 'U'
                for field_arr in model._audit_track:
                    kwargs[field_arr[0]] = _audit_track(instance, field_arr)
                model._default_manager.create(**kwargs)
            ## Uncomment this line for pre r8223 Django builds
            #dispatcher.connect(_audit, signal=models.signals.post_save, sender=cls, weak=False)
            ## Comment this line for pre r8223 Django builds
            models.signals.post_save.connect(_audit, sender=cls, weak=False)

            if self.opts['audit_deletes']:
                def _audit_delete(sender, instance, **kwargs):
                    # Write model changes to the audit model
                    kwargs = {}
                    for field in sender._meta.fields:
                        kwargs[field.name] = getattr(instance, field.name)
                    if self.opts['save_change_type']:
                        kwargs['_audit_change_type'] = 'D'
                    for field_arr in model._audit_track:
                        kwargs[field_arr[0]] = _audit_track(instance, field_arr)
                    model._default_manager.create(**kwargs)
                ## Uncomment this line for pre r8223 Django builds
                #dispatcher.connect(_audit_delete, signal=models.signals.pre_delete, sender=cls, weak=False)
                ## Comment this line for pre r8223 Django builds
                models.signals.pre_delete.connect(_audit_delete, sender=cls, weak=False)
        
        ## Uncomment this line for pre r8223 Django builds
        #dispatcher.connect(_contribute, signal=models.signals.class_prepared, sender=cls, weak=False)
        ## Comment this line for pre r8223 Django builds
        models.signals.class_prepared.connect(_contribute, sender=cls, weak=False)

class AuditTrailDescriptor(object):
    def __init__(self, manager, pk_attribute):
        self.manager = manager
        self.pk_attribute = pk_attribute

    def __get__(self, instance=None, owner=None):
        if instance == None:
            #raise AttributeError, "Audit trail is only accessible via %s instances." % type.__name__
            return create_audit_manager_class(self.manager)
        else:
            return create_audit_manager_with_pk(self.manager, self.pk_attribute, instance._get_pk_val())

    def __set__(self, instance, value):
        raise AttributeError, "Audit trail may not be edited in this manner."

def create_audit_manager_with_pk(manager, pk_attribute, pk):
    """Create an audit trail manager based on the current object"""
    class AuditTrailWithPkManager(manager.__class__):
        def __init__(self, *arg, **kw):
            super(AuditTrailWithPkManager, self).__init__(*arg, **kw)
            self.model = manager.model

        def get_query_set(self):
            qs = super(AuditTrailWithPkManager, self).get_query_set().filter(**{pk_attribute: pk})
            if self._db is not None:
                qs = qs.using(self._db)
            return qs
    return AuditTrailWithPkManager()

def create_audit_manager_class(manager):
    """Create an audit trail manager based on the current object"""
    class AuditTrailManager(manager.__class__):
        def __init__(self, *arg, **kw):
            super(AuditTrailManager, self).__init__(*arg, **kw)
            self.model = manager.model
    return AuditTrailManager()

def create_audit_model(cls, **kwargs):
    """Create an audit model for the specific class"""
    name = cls.__name__ + 'Audit'

    class Meta:
        db_table = '%s_audit' % cls._meta.db_table
        app_label = cls._meta.app_label
        verbose_name_plural = '%s audit trail' % cls._meta.verbose_name
        ordering = ['-_audit_timestamp']

    # Set up a dictionary to simulate declarations within a class
    attrs = {
        '__module__': cls.__module__,
        'Meta': Meta,
        '_audit_id': models.AutoField(primary_key=True),
        '_audit_timestamp': models.DateTimeField(auto_now_add=True, db_index=True),
        '_audit__str__': cls.__str__.im_func,
        '__str__': lambda self: '%s as of %s' % (self._audit__str__(), self._audit_timestamp),
        '_audit_track': _track_fields(track_fields=kwargs['track_fields'], unprocessed=True)
    }

    if 'save_change_type' in kwargs and kwargs['save_change_type']:
        attrs['_audit_change_type'] = models.CharField(max_length=1)

    # Copy the fields from the existing model to the audit model
    for field in cls._meta.fields:
        #if field.attname in attrs:
        if field.name in attrs:
            raise ImproperlyConfigured, "%s cannot use %s as it is needed by AuditTrail." % (cls.__name__, field.attname)
        if isinstance(field, models.AutoField):
            # Audit models have a separate AutoField
            attrs[field.name] = models.IntegerField(db_index=True, editable=False)
        else:
            attrs[field.name] = copy.copy(field)
            # If 'unique' is in there, we need to remove it, otherwise the index
            # is created and multiple audit entries for one item fail.
            attrs[field.name]._unique = False
            # If a model has primary_key = True, a second primary key would be
            # created in the audit model. Set primary_key to false.
            attrs[field.name].primary_key = False

            # Rebuild and replace the 'rel' object to avoid foreign key clashes.
            # Borrowed from the Basie project - please check if adding this is allowed by the license.
            if isinstance(field, models.ForeignKey):
                rel = copy.copy(field.rel)
                rel.related_name = '_audit_' + field.related_query_name()
                attrs[field.name].rel = rel
            if isinstance(field, models.PointField):
                attrs['objects'] = models.GeoManager()

    for track_field in _track_fields(kwargs['track_fields']):
        if track_field['name'] in attrs:
            raise NameError('Field named "%s" already exists in audit version of %s' % (track_field['name'], cls.__name__))
        attrs[track_field['name']] = copy.copy(track_field['field'])
    
    return type(name, (models.Model,), attrs)

def _build_track_field(track_item):
    track = {}
    track['name'] = track_item[0]
    if isinstance(track_item[1], models.Field):
        track['field'] = track_item[1]
    elif issubclass(track_item[1], models.Model):
        track['field'] = models.ForeignKey(track_item[1])
    else:
        raise TypeError('Track fields only support items that are Fields or Models.')
    return track

def _track_fields(track_fields=None, unprocessed=False):
    # Add in the fields from the Audit class "track" attribute.
    tracks_found = []
    
    if settings_audit:
        global_track_fields = getattr(settings_audit, 'GLOBAL_TRACK_FIELDS', [])
        for track_item in global_track_fields:
            if unprocessed:
                tracks_found.append(track_item)
            else:
                tracks_found.append(_build_track_field(track_item))
    
    if track_fields:
        for track_item in track_fields:
            if unprocessed:
                tracks_found.append(track_item)
            else:
                tracks_found.append(_build_track_field(track_item))
    return tracks_found
