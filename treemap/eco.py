from treemap.localization import convert_dbh_to_inches

RESOURCE_NAMES = ['Hydro interception',
                  'AQ Ozone dep',
                  'AQ NOx dep',
                  'AQ PM10 dep',
                  'AQ SOx dep',
                  'AQ NOx avoided',
                  'AQ PM10 avoided',
                  'AQ SOx avoided',
                  'AQ VOC avoided',
                  'BVOC',
                  'CO2 sequestered',
                  'CO2 avoided',
                  'Natural Gas',
                  'Electricity',
                  'CO2 Storage']

def set_environmental_summaries(tree):
    from treemap.models import TreeResource

    species = tree.species
    dbh = tree.dbh

    if not species or not dbh:
        return None

    dbh = convert_dbh_to_inches(dbh)

    tr = TreeResource.objects.filter(tree=tree)
    resources = species.resource.all()

    if not resources:
        if tr:
            tr.delete()

        return False


    resource = resources[0]

    if tr:
        tr = tr[0]
    else:
        tr = TreeResource(tree=tree)

    base_resources = calc_base_resources(resource, RESOURCE_NAMES, dbh)
    results = calc_resource_summaries(base_resources)

    if not results:
        if tr.id:
            tr.delete()
        return None 

    for k,v in results.items():
        setattr(tr, k, v)

    tr.save()
    return True


def calc_base_resources(tree_resource, resource_list, dbh):
    """
    example: treeobject.species.resource_species.calc_base_resources(['Electricity'], 36.2)
    """
    index, interp = get_interpolated_location(dbh)
    index2, interp2 = get_interpolated_location(dbh, True)

    results = {}
    for resource in resource_list:
        fname = "%s_dbh" % resource.lower().replace(' ','_')

        # get two values of interest - TODO FIX for sketchy eval
        dbhs= (eval(getattr(tree_resource, fname)))

        if len(dbhs) > 9:
            # start at same list index as dbh_list, and figure
            # out what interp value is here
            local_interp = float(dbhs[index2] - dbhs[index2-1]) * interp2
            results[fname] = dbhs[index2-1] + local_interp
        else:
            # start at same list index as dbh_list, and figure
            # out what interp value is here
            local_interp = float(dbhs[index] - dbhs[index-1]) * interp 
            results[fname] = dbhs[index-1] + local_interp

    return results

def get_interpolated_location(dbh, long_list=False):
    """
    return how far along we are along the dbh_list, and interpolated %
    """
    dbh_list = [3.81,11.43,22.86,38.10,53.34,68.58,83.82,99.06,114.30]
    if long_list:
        dbh_list = [2.54,5.08,7.62,10.16,12.7,15.24,17.78,20.32,22.86,25.4,27.94,30.48,33.02,35.56,38.1,40.64,43.18,45.72,48.26,50.8,53.34,55.88,58.42,60.96,63.5,66.04,68.58,71.12,73.66,76.2,78.74,81.28,83.82,86.36,88.9,91.44,93.98,96.52,99.06,101.6,104.14,106.68,109.22,111.76,114.3]
    #convert from cm to inches
    dbh_list = [d * 0.393700787 for d in dbh_list]

    if dbh < dbh_list[0]:
        return[1,0]
    if dbh >= dbh_list[-1]:
        return[len(dbh_list)-1,1]
    for i, d in enumerate(dbh_list):
        if dbh < d:
            interp_between = (float(dbh - dbh_list[i-1]) / float(dbh_list[i] - dbh_list[i-1]))
            return i, interp_between


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
