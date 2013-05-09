# 
# This module contains functions to be used for
# exporting data to various formats using ogr2ogr
#

import re

def sanitize_raw_sql(query):
    """
    Takes a raw sql string and performs some sql surgery to
    make queries valid on postgres
    """
    new_query = query

    new_query = _sanitize_native_status_field(new_query)


    for qualified_field in ('U0."last_updated"',
                            '"treemap_tree"."last_updated"',
                            '"treemap_plot"."last_updated"'):
        new_query = _sanitize_date_comparison_field(qualified_field, new_query)

    for qualified_field in ('U0."username"',
                  'U0."tree_owner"',
                  '"treemap_tree"."tree_owner"',
                  '"treemap_tree"."sponsor"'):
        new_query = _sanitize_string_like_upper_field(qualified_field, new_query)

    for field in ("sidewalk_damage",
                  "condition",
                  "canopy_condition",
                  "pests"):
        new_query = _sanitize_membership_test_field(field, new_query)

    return new_query

####################################
## PRIVATE FUNCTIONS
####################################

def _quote_integers_in_pattern(pattern, query):
    def quote_integer(matchobj):
        return "'" + matchobj.group() + "'"

    def quote_integers(matchobj):
        return re.sub(r'(\d)', quote_integer, matchobj.group())

    return re.sub(pattern, quote_integers, query)

def _sanitize_native_status_field(query):
    return query.replace('"native_status" = True', '"native_status" = \'True\'')

def _sanitize_membership_test_field(field_name, query):
    pattern = '"%s" IN \([0-9, ]+\)' % field_name
    return _quote_integers_in_pattern(pattern, query)

def _sanitize_string_like_upper_field(qualified_field_name, query):
    pattern = 'UPPER\({}::text\) LIKE UPPER\(%([\w.@+-]+)%\)'.format(qualified_field_name)
    replacement = r"""UPPER({}::text) LIKE UPPER('%\1%')""".format(qualified_field_name)
    return re.sub(pattern, replacement, query)

def _sanitize_date_comparison_field(qualified_field_name, query):
    pattern = '%s (>=|<=) (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})' % qualified_field_name
    replacement = r"""{} \1 '\2'""".format(qualified_field_name)
    return re.sub(pattern, replacement, query)
