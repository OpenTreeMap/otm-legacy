# 
# This module contains functions and views to be used for
# exporting data to various formats using ogr2ogr
#
# This is a pure python module. It can be tested by
# running from the command-line by running:
#
# python export.py
#
# from the directory the file is located in.

import re

####################################
## (PURE) PUBLIC FUNCTIONS
####################################

def sanitize_raw_sql(query):
    """
    Takes a raw sql string and performs some dangerous sql surgery.

    This fixes a big bug in the design of this app.
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
## (PURE) PRIVATE FUNCTIONS
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

####################################
## TESTS
####################################

def _test_condition_query():
    condition_query = """
SELECT "treemap_resourcesummarymodel"."id", "treemap_resourcesummarymodel"."annual_stormwater_management", "treemap_resourcesummarymodel"."annual_electricity_conserved", "treemap_resourcesummarymodel"."annual_energy_conserved", "treemap_resourcesummarymodel"."annual_natural_gas_conserved", "treemap_resourcesummarymodel"."annual_air_quality_improvement", "treemap_resourcesummarymodel"."annual_co2_sequestered", "treemap_resourcesummarymodel"."annual_co2_avoided", "treemap_resourcesummarymodel"."annual_co2_reduced", "treemap_resourcesummarymodel"."total_co2_stored", "treemap_resourcesummarymodel"."annual_ozone", "treemap_resourcesummarymodel"."annual_nox", "treemap_resourcesummarymodel"."annual_pm10", "treemap_resourcesummarymodel"."annual_sox", "treemap_resourcesummarymodel"."annual_voc", "treemap_resourcesummarymodel"."annual_bvoc", "treemap_treeresource"."resourcesummarymodel_ptr_id", "treemap_treeresource"."tree_id" FROM "treemap_treeresource" INNER JOIN "treemap_resourcesummarymodel" ON ("treemap_treeresource"."resourcesummarymodel_ptr_id" = "treemap_resourcesummarymodel"."id") WHERE "treemap_treeresource"."tree_id" IN (SELECT U0."id" FROM "treemap_tree" U0 WHERE (U0."present" = True  AND U0."condition" IN (3, 5, 7)))
"""
    condition_query = _sanitize_membership_test_field("condition", condition_query)
    assert("('3', '5', '7')" in condition_query)

def _test_multiple_fields_query():
    condition_characteristic_query = """
SELECT (
            SELECT treemap_plot.geometry
            FROM treemap_plot
            WHERE treemap_tree.plot_id = treemap_plot.id
            ) AS "geometry", "treemap_tree"."id", "treemap_tree"."plot_id", "treemap_tree"."tree_owner", "treemap_tree"."steward_name", "treemap_tree"."steward_user_id", "treemap_tree"."sponsor", "treemap_tree"."species_id", "treemap_tree"."species_other1", "treemap_tree"."species_other2", "treemap_tree"."orig_species", "treemap_tree"."dbh", "treemap_tree"."height", "treemap_tree"."canopy_height", "treemap_tree"."date_planted", "treemap_tree"."date_removed", "treemap_tree"."present", "treemap_tree"."last_updated", "treemap_tree"."last_updated_by_id", "treemap_tree"."s_order", "treemap_tree"."photo_count", "treemap_tree"."projects", "treemap_tree"."import_event_id", "treemap_tree"."condition", "treemap_tree"."canopy_condition", "treemap_tree"."readonly", "treemap_tree"."url", "treemap_tree"."pests" FROM "treemap_tree" WHERE ("treemap_tree"."present" = True  AND "treemap_tree"."condition" IN (2, 3, 4, 5, 6, 7) AND "treemap_tree"."species_id" IN (SELECT U0."id" FROM "treemap_species" U0 WHERE (U0."tree_count" > 0  AND U0."native_status" = True )))
"""
    new_condition_characteristic_query = _sanitize_native_status_field(condition_characteristic_query)
    new_condition_characteristic_query = _sanitize_membership_test_field("condition", new_condition_characteristic_query)

    assert('"native_status" = \'True\'' in new_condition_characteristic_query)
    assert("('2', '3', '4', '5', '6', '7')" in new_condition_characteristic_query)

    new_condition_characteristic_query = sanitize_raw_sql(condition_characteristic_query)
    assert('"native_status" = \'True\'' in new_condition_characteristic_query)
    assert("('2', '3', '4', '5', '6', '7')" in new_condition_characteristic_query)

def _tests():
    _test_condition_query()
    _test_multiple_fields_query()
    print "tests pass!"

if __name__ == '__main__':
    _tests()

