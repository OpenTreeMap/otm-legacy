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
