from treemap.localization import convert_dbh_to_inches
from django.conf import settings
from eco import benefits

RESOURCE_NAMES = {'Hydro interception': 'hydro_interception',
                  'AQ Ozone dep': 'aq_ozone_dep',
                  'AQ NOx dep': 'aq_nox_dep',
                  'AQ PM10 dep': 'aq_pm10_dep',
                  'AQ SOx dep': 'aq_sox_dep',
                  'AQ NOx avoided': 'aq_nox_avoided',
                  'AQ PM10 avoided': 'aq_pm10_avoided',
                  'AQ SOx avoided': 'aq_sox_avoided',
                  'AQ VOC avoided': 'aq_voc_avoided',
                  'BVOC': 'bvoc',
                  'CO2 sequestered': 'co2_sequestered',
                  'CO2 avoided': 'co2_avoided',
                  'Natural Gas': 'natural_gas',
                  'Electricity': 'electricity',
                  'CO2 Storage': 'co2_storage'}

INCHES_PER_CM = 2.54

def set_environmental_summaries(tree):
    from treemap.models import TreeResource, ClimateZone

    species = tree.species
    dbh = tree.dbh

    if not species or not dbh:
        return None

    dbh_cm = convert_dbh_to_inches(dbh) * INCHES_PER_CM

    tr = TreeResource.objects.filter(tree=tree)

    # Determine which region the tree is currently in:
    if settings.MULTI_REGION_ITREE_ENABLED:
        target_region = tree.plot.itree_region()

        if target_region is None:
            return False

        resources = species.resource.filter(region=target_region)
    else:
        resources = species.resource.all()

    if not resources:
        if tr:
            tr.delete()

        return False

    region = resources[0].region
    code = resources[0].meta_species

    if tr:
        tr = tr[0]
    else:
        tr = TreeResource(tree=tree)

    base_resources = calc_base_resources(code, dbh_cm, RESOURCE_NAMES, region)
    results = calc_resource_summaries(base_resources)

    if not results:
        if tr.id:
            tr.delete()
        return None

    for k,v in results.items():
        setattr(tr, k, v)

    tr.save()
    return True


def calc_base_resources(itree_code, dbh_cm, resource_list, region=None):
    if region is None:
        region = settings.ITREE_REGION

    results = {}
    for tr_key, resource_key in resource_list.iteritems():
        fname = "%s_dbh" % tr_key.lower().replace(' ','_')

        results[fname] = benefits.get_factor_for_trees(
            region, resource_key, [(itree_code, dbh_cm)])

    return results


def calc_resource_summaries(br):
    summaries = {}
    summaries['annual_stormwater_management'] = br['hydro_interception_dbh'] * 264.1
    summaries['annual_electricity_conserved'] = br['electricity_dbh']
    # http://sftrees.securemaps.com/ticket/25#comment:7
    summaries['annual_natural_gas_conserved'] = br['natural_gas_dbh'] * 0.293
    summaries['annual_air_quality_improvement'] = (
        br['aq_ozone_dep_dbh'] +
        br['aq_nox_dep_dbh'] +
        br['aq_pm10_dep_dbh'] +
        br['aq_sox_dep_dbh'] +
        br['aq_nox_avoided_dbh'] +
        br['aq_pm10_avoided_dbh'] +
        br['aq_sox_avoided_dbh'] +
        br['aq_voc_avoided_dbh'] +
        br['bvoc_dbh']) * 2.2
    summaries['annual_ozone'] = br['aq_ozone_dep_dbh'] * 2.2
    summaries['annual_nox'] = br['aq_nox_dep_dbh'] + br['aq_nox_avoided_dbh'] * 2.2
    summaries['annual_pm10'] = br['aq_pm10_dep_dbh'] + br['aq_pm10_avoided_dbh'] * 2.2
    summaries['annual_sox'] = br['aq_sox_dep_dbh'] + br['aq_sox_avoided_dbh'] * 2.2
    summaries['annual_voc'] = br['aq_voc_avoided_dbh'] * 2.2
    summaries['annual_bvoc'] = br['bvoc_dbh'] * 2.2
    summaries['annual_co2_sequestered'] = br['co2_sequestered_dbh'] * 2.2
    summaries['annual_co2_avoided'] = br['co2_avoided_dbh'] * 2.2
    summaries['annual_co2_reduced'] = (br['co2_sequestered_dbh'] + br['co2_avoided_dbh']) * 2.2
    summaries['total_co2_stored'] = br['co2_storage_dbh'] * 2.2
    summaries['annual_energy_conserved'] = br['electricity_dbh'] + br['natural_gas_dbh'] * 0.293
    return summaries
