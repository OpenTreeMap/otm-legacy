from django.core.management.base import BaseCommand

from optparse import make_option

from treemap.models import Tree, Plot

import sys
import json

# this was selectively copied from the migrating code on the otm2 side.
# where possible, notes are made for differences.
MODELS = {
    'tree': {
        'model_class': Tree,
        'common_fields': {'plot', 'species', 'readonly', 'canopy_height',
                          'date_planted', 'date_removed', 'height'},
        'renamed_fields': {'dbh': 'diameter',
                           'species_id': 'species', # NOT included in otm2 counterpart
                       },
        'removed_fields': {'tree_owner', 'steward_name', 'sponsor',
                           'species_other1', 'species_other2',
                           'orig_species', 'present', 'last_updated',
                           'last_updated_by', 's_order', 'photo_count',
                           'projects', 'condition', 'canopy_condition',
                           'url', 'pests', 'steward_user'},
        # NOT included in otm2 counterpart
        'foreign_events': {'Fruit or Nuts Harvested',
                           'Watered', 'Inspected', 'Pruned'}
    },
    'plot': {
        'common_fields': {'width', 'length', 'address_street', 'address_zip',
                          'address_city', 'owner_orig_id', 'readonly'},
        'renamed_fields': {'geometry': 'geom'},
        'undecided_fields': {'import_event'},
        'removed_fields': {'type', 'powerline_conflict_potential',
                           'sidewalk_damage', 'neighborhood',
                           'neighborhoods', 'zipcode', 'geocoded_accuracy',
                           'geocoded_address', 'geocoded_lat', 'geocoded_lon',
                           'present', 'last_updated', 'last_updated_by',
                           'data_owner', 'owner_additional_id',
                           'owner_additional_properties'},
    },
}

AUDIT_TYPES = {
    'I': 1,
    'D': 2,
    'U': 3
}

class AuditParseException(Exception):
    pass

def _nested_insert(d, key, nestedkey, value):
    if key in d:
        d[key][nestedkey] = value
    else:
        d[key] = { nestedkey: value }


def get_old_new_pairs(flat_hash):
    """
    Split previous ('old_' keys) and current values into nested hashes.

    otm1 audits are serialized dictionaries with keys that are either
    field names, or field names prefixed with 'old_'. This function
    splits these out to nested hashes of 'previous'/'current' values
    on a per-field basis.

    To further complicate matters, some foreign key event records are
    stored as double pairs in the format:
    {'old_key':u'', 'old_value':u'None',
     'key':'{{ event record name }}', 'value':'{{ event date }}'}
    these are homogenized and stored as pairs as described above.
    """
    clean_hash = {k: v for k, v in flat_hash.items()
                  if k not in ('value', 'old_value') }
    newhash = {}

    for k in clean_hash:
        if k == 'key':
            newkey = flat_hash['key']
            nestedkey = 'current'
            v = flat_hash['value']
        elif k == 'old_key':
            newkey = flat_hash['key']
            nestedkey = 'previous'
            v = flat_hash['old_value']
        elif k.startswith('old_'):
            newkey = k[4:]
            nestedkey = 'previous'
            v = flat_hash[k]
        else:
            newkey = k
            nestedkey = 'current'
            v = flat_hash[k]

        _nested_insert(newhash, newkey, nestedkey, v)

    return newhash

def _parse_diff(audit, model):
    """
    Turn _audit_diff field into a list of sanitized
    (field, previous, current) tuples.

    This is the main processing function of this module.
    Validate format against audit type, deserialize from JSON,
    iterate over changed values, filter out unused fields,
    sanitize values.
    """

    diff_j = audit._audit_diff

    # process record level changes
    if diff_j == '':
        if audit._audit_change_type == 'I':
            return [('id', None, audit.id)], []
        elif audit._audit_change_type == 'D':
            return [('id', audit.id, None)], []
        else:
            raise AuditParseException('No diff on an update?')

    # process field level changes
    else:
        diff = json.loads(diff_j)
        paired_diff = get_old_new_pairs(diff)
        model_rules = MODELS[model]

        changes = []
        rejects = []
        for k, v in paired_diff.iteritems():

            # TODO: Sanitize values in a centralized place
            v = None if v == 'None' else v

            if k in model_rules['removed_fields']:
                # drop these values.
                # TODO: log these
                pass

            elif k in model_rules['renamed_fields']:
                changes.append(
                    (model_rules['renamed_fields'][k], v.get('previous', None), v.get('current', None)))

            elif k in model_rules['common_fields']:
                changes.append(
                    (k, v.get('previous', None), v.get('current', None)))
            else:
                # TODO: figure out how to support these and add them
                rejects.append(
                    (k, v.get('previous', None), v.get('current', None)))

        return changes, rejects

def get_audit_dicts(qs, model_name, audit_count):
    lowercase_model_name = model_name.lower()
    audit_dicts = []
    reject_dicts = []
    skipped = 0
    for model in qs:
        history = model.history.order_by('_audit_timestamp')
        for audit in history:
            try:
                changes, rejects = _parse_diff(audit, lowercase_model_name)

                def make_audit_dict(field, previous_value, current_value):
                    return {
                        'pk': audit_count,
                        'model': 'treemap.audit',
                        'fields': {
                            'model': model_name,
                            'model_id': model.pk,
                            'field': field,
                            'previous_value': previous_value,
                            'current_value': current_value,
                            'user': model.last_updated_by.pk,
                            'action': AUDIT_TYPES[audit._audit_change_type],
                            'requires_auth': False,
                            'ref': None,
                            'created': audit._audit_timestamp.isoformat(),
                            'updated': audit._audit_timestamp.isoformat()
                        }
                    }

                for change in changes:
                    audit_count += 1
                    audit_dicts.append(make_audit_dict(*change))
                for change in rejects:
                    audit_count += 1
                    reject_dicts.append(make_audit_dict(*change))
            except AuditParseException:
                skipped += 1

    return audit_dicts, reject_dicts, skipped, audit_count

class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('-o', '--outfile',
                    action='store',
                    type='string',
                    dest='outfile',
                    help='path to export the data to'),
        make_option('-e', '--errorfile',
                    action='store',
                    type='string',
                    dest='errorfile',
                    help='path to export the data to')
    )

    def handle(self, *args, **options):
        audit_count = 1
        trees = Tree.objects.all().iterator()
        plots = Plot.objects.all().iterator()

        tree_hashes, tree_errors, tree_skipped, audit_count = get_audit_dicts(trees, 'Tree', audit_count)
        plot_hashes, plot_errors, plot_skipped, audit_count = get_audit_dicts(plots, 'Plot', audit_count)

        skipped = tree_skipped + plot_skipped

        sys.stdout.write("EXPORTED: %s audits" % (audit_count - 1))
        sys.stdout.write("SKIPPED: %s audits" % skipped)
        output = open(options['outfile'], 'w+b')
        error_output = open(options['errorfile'], 'w+b')
        json.dump(tree_hashes + plot_hashes, output)
        json.dump(tree_errors + plot_errors, error_output)
