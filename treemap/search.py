from models import *
from django.contrib.gis.geos import Point

class Search (object):
    def __init__(self, trees, plots, tile_query, geog_obj, aggr_obj):
        self.trees = trees
        self.plots = plots
        self.tile_query = tile_query
        self.geog_obj = geog_obj
        self.aggr_obj = aggr_obj

def apply_location_filter(request, search):
    geog_obj = None
    if 'location' in request:
        loc = request['location']
        z = ZipCode.objects.filter(zip=loc)
        if z.count():
            search.trees = search.trees.filter(plot__zipcode = z[0])
            search.plots = search.plots.filter(zipcode = z[0])
            search.geog_obj = z[0]
            search.tile_query.append("zipcode_id = %d" % z[0].id)
    elif 'distance' in request:
        # geographic search handled in the plot_location_search function
        pass
    else:
        if 'geoName' in request or \
           'hood' in request or \
           'lat' in request:

            ns = Neighborhood.objects.all().order_by('id')
            hood = None

            if 'geoName' in request:
                ns = ns.filter(name=request['geoName'])
            elif 'hood' in request:
                ns = ns.filter(name__icontains=request['hood'])
            elif 'lat' in request and 'lon' in request:
                pnt = Point(float(request['lon']), float(request['lat']))
                ns = ns.filter(geometry__contains=pnt)

            hood = ns[0]

            search.trees = search.trees.filter(plot__neighborhood = hood)
            search.plots = search.plots.filter(neighborhood = hood)
            search.geog_obj = hood
            search.tile_query.append(
                "(neighborhoods = '%(id)d' OR "
                "neighborhoods LIKE '%% %(id)d' OR "
                "neighborhoods LIKE '%(id)d %%')" % { "id": hood.id })

    return search


def apply_plot_size_filter(request, search):
    """ This filter supports both a "missing" and "actual" value """
    if 'missing_plot_size' in request:
        search.trees = search.trees.filter(Q(plot__length__isnull=True) |
                                           Q(plot__width__isnull=True))

        search.plots = search.plots.filter(Q(length__isnull=True) |
                                           Q(width__isnull=True))

        search.tile_query.append(
            " (plot_length IS NULL OR plot_width IS NULL) ")

    elif 'plot_range' in request:
        sizemin, sizemax = [float(z) for z in request['plot_range'].split("-")]

        search.trees = search.trees.filter(
            Q(plot__length__gte=sizemin) | Q(plot__width__gte=sizemin))

        search.plots = search.plots.filter(
            Q(length__gte=sizemin) | Q(width__gte=sizemin))

        # TODO: Hardcoded in UI, may need to change
        # (From original, should be <= 15?)
        if sizemax != 15:
            search.trees = search.trees.filter(
                Q(plot__length__lte=sizemax) | Q(plot__width__lte=sizemax))

            search.plots = search.plots.filter(
                Q(length__lte=sizemax) | Q(width__lte=sizemax))
            
        search.tile_query.append(
            "( (plot_length BETWEEN %(min)d AND %(max)d ) OR "
            "  (plot_width  BETWEEN %(min)d AND %(max)d ) )" \
            % { "min": sizemin, "max": sizemax })

    return search

def apply_stewardship_filter(request, search):
    stewardship_reverse = request.get('stewardship_reverse',False) == "true"

    if 'stewardship_range' in request:
        (start_date, end_date) = [datetime.utcfromtimestamp(float(z))
                                  for z in request['stewardship_range'].split('-')]

    def tile_query_for_stewardship_actions(actions, tree_or_plot):
        tq = []
        for a in actions:
            if stewardship_reverse:
                tq.append(
                    "%s_stewardship_%s IS NOT NULL" % (tree_or_plot,a))
            else:
                tq.append(
                    "%s_stewardship_%s IS NOT NULL" % (tree_or_plot,a))

                if start_date and end_date:
                    tq.append(
                        "%(tree)s_stewardship_%(action)s AFTER %(start)sZ AND "
                        "%(tree)s_stewardship_%(action)s BEFORE %(end)sZ" %
                        { "action": a, 
                          "start": start_date.isoformat(),
                          "end": end_date.isoformat(),
                          "tree": tree_or_plot })
        return tq

    if 'tree_stewardship' in request:
        tree_stewardship = request['tree_stewardship']
        actions = tree_stewardship.split(',')

        steward_ids = Stewardship.trees_with_activities(actions)
        search.tile_query += tile_query_for_stewardship_actions(actions, "tree")
            
        if stewardship_reverse:
            search.trees = search.trees.filter(id__in=steward_ids)  
        else:
            search.trees = search.trees.exclude(id__in=steward_ids)

        if start_date and end_date:
            search.trees = search.trees.exclude(
                treestewardship__performed_date__lte=start_date,
                treestewardship__performed_date__gte=end_date)

        # Also not clear why this goes here...
        # reset plots search?
        search.plots = Plot.objects.filter(present=True).filter(tree__in=search.trees)
        
    if 'plot_stewardship' in request:
        plot_stewardship = request["plot_stewardship"]
        actions = plot_stewardship.split(',')

        steward_ids = Stewardship.plots_with_activities(actions)
        search.tile_query += tile_query_for_stewardship_actions(actions, "plot")

        if stewardship_reverse:
            search.plots = search.plots.filter(id__in=steward_ids)
        else:
            search.plots = search.plots.exclude(id__in=steward_ids)

        if start_date and end_date:
            search.plots = search.plots.exclude(
                plotstewardship__performed_date__lte=start_date,
                plotstewardship__performed_date__gte=end_date)

        # Not sure why this goes in under the plot_stewardship
        # if block....
        search.trees = Tree.objects.filter(present=True).extra(select={'geometry': "select treemap_plot.geometry from treemap_plot where treemap_tree.plot_id = treemap_plot.id"}).filter(plot__in=search.plots)

    return search

def apply_missing_plot_filter(fld, search, cqlfld=None, cql=None):
    return apply_missing_filter(fld, False, search, cqlfld=cqlfld, cql=cql)

def apply_missing_tree_filter(fld, search, cqlfld=None, cql=None):
    return apply_missing_filter(fld, True, search, cqlfld=cqlfld, cql=cql)

def apply_missing_filter(fld, istree, search, cqlfld=None, cql=None):
    if istree:
        treefld = "%s__isnull" % fld
        plotfld = "tree__%s__isnull" % fld
    else:
        plotfld = "%s__isnull" % fld
        treefld = "plot__%s__isnull" % fld

    if not cqlfld:
        cqlfld = fld

    kwtree = { treefld: True }
    kwplot = { plotfld: True }

    search.trees = search.trees.filter(**kwtree)
    search.plots = search.plots.filter(**kwplot)

    if cql:
        search.tile_query.append(cql)
    else:
        search.tile_query.append(" %s IS NULL " % cqlfld)

    return search

def extract_choices(request, key):
    selected = []
    for k, v in settings.CHOICES[key]:
        if v.lower().replace(' ', '_').replace('/','') in request:
            selected.append((k,v))

    return selected

def apply_plot_type_filter(request, search):
    if request.get('missing_plot_type', False):
        search = apply_missing_plot_filter("type", search, cqlfld="plot_type")
    else:
        ids = [k for (k,v) in extract_choices(request, 'plot_types')]
        cqltypes = ["plot_type = %s" % t for t in ids]

        if ids:
            search.trees = search.trees.filter(plot__type__in=ids)
            search.plots = search.plots.filter(type__in=ids)
            search.tile_query.append(
                "( %s )" % " OR ".join(cqltypes))

    return search

def apply_sidewalk_damage_filter(request, search):
    if request.get("missing_sidewalk", False):
        search = apply_missing_plot_filter(
            "sidewalk_damage", search, cql="sidewalk_damage")
    else: 
        ids = [k for (k,v) in extract_choices(request, 'sidewalks')]
        cqltypes = ["sidewalk_damage = %s" % t for t in ids]

        if ids:
            search.trees = search.trees.filter(plot__sidewalk_damage__in=ids)
            search.plots = search.plots.filter(sidewalk_damage__in=ids)
            search.tile_query.append(
                "( %s )" % " OR ".join(cqltypes))

    return search

def apply_pests_filter(request, search):
    pests = [k.split("_")[1] for (k,v) in request.items() if "pests_" in k and v]
    if pests:
        pests_cql = ["pests = %s" % k for k in pests]
        
        search.trees = search.trees.filter(pests__in=pests)
        search.plots = search.plots.filter(tree__pests__in=pests)

        search.tile_query.append(
            "( %s )" % " OR ".join(pests_cql))

    return search

def apply_powerlines_filter(request, search):
    if request.get('missing_powerlines', False):
        search = apply_missing_plot_filter(
            "powerline_conflict_potential", search)
    else:
        ids = [k for (k,v) in extract_choices(request, 'powerlines')]
        cqltypes = ["powerline_conflict_potential = %s" % t for t in ids]

        if ids:
            search.trees = search.trees.filter(
                plot__powerline_conflict_potential__in=ids)

            search.plots = search.plots.filter(
                powerline_conflict_potential__in=ids)

            search.tile_query.append(
                "( %s )" % " OR ".join(cqltypes))

    return search


def apply_owner_filter(request, search):
    if 'owner' in request:
        owner = request['owner']
        users = User.objects.filter(username__icontains=owner)

        search.trees = search.trees.filter(plot__data_owner__in=users)
        search.plots = search.plots.filter(data_owner__in=users)
        
        cql_users = ['data_owner_id = %s' % u.id for u in users]
        
        search.tile_query.append(
            "( %s )" % " OR ".join(cql_users))

    return search

def apply_updated_by_filter(request, search):
    if 'updated_by' in request:
        updated_by = request['updated_by']
        users = User.objects.filter(username__icontains=updated_by)

        search.trees = search.trees.filter(last_updated_by__in=users)
        search.plots = search.plots.filter(last_updated_by__in=users)

        cql_users = ['last_updated_by_id = %d' % u.id for u in users]
        
        search.tile_query.append(
            "( %s )" % " OR ".join(cql_users))

    return search

def apply_updated_range_filter(request, search):
    if 'updated_range' in request:
        mindate, maxdate = [datetime.utcfromtimestamp(float(z))
                            for z in request['updated_range'].split("-")]

        search.trees = search.trees.filter(last_updated__gte=mindate, 
                             last_updated__lte=maxdate)

        search.plots = search.plots.filter(last_updated__gte=mindate, 
                             last_updated__lte=maxdate)
        
        search.tile_query.append(
            "last_updated AFTER %sZ AND "
            "last_updated BEFORE %sZ" %
            (mindate.isoformat(), maxdate.isoformat()))

    return search

def apply_projects_filter(request, search):
    pids = [k for (k,v) in extract_choices(request, 'projects')]
    cql_projects = ["projects LIKE '%%%s%%'" % p for p in pids]

    if pids:
        search.trees = search.trees.filter(treeflags__key__in=pids)
        search.plots = search.plots.filter(tree__treeflags__key__in=pids)

        search.tile_query.append(
            "( %s )" % " OR ".join(cql_projects))

    return search

def apply_missing_species_filter(request, search):
    if request.get('missing_species',False):
        search = apply_missing_tree_filter("species",search,cqlfld="species_id")

    return search

def apply_dbh_filter(request, search):
    if request.get('missing_diameter', False):
        search.trees = search.trees.filter(Q(dbh__isnull=True) | Q(dbh=0))
        search.plots = search.plots.filter(Q(tree__dbh__isnull=True) | Q(tree__dbh=0))

        search.tile_query.append(" (dbh IS NULL OR dbh = 0) ")

    elif 'diameter_range' in request:
        dmin, dmax = [float(d) for d in request['diameter_range'].split('-')]

        search.trees = search.trees.filter(dbh__gte=dmin)
        search.plots = search.plots.filter(tree__dbh__gte=dmin)
        # TODO: Hardcoded in UI, shouldn't be
        # ^^^^ previous comment, not too sure what this
        # means and why it is different than
        # the tile_query thing below (should it be < 50?)
        if dmax != 50: 
            search.trees = search.trees.filter(dbh__lte=dmax)
            search.plots = search.plots.filter(tree__dbh__lte=dmax)

        search.tile_query.append(
            "dbh BETWEEN %d AND %d" % (dmin,dmax))

    return search

def apply_tree_height_filter(request, search):
    if request.get('missing_height', False):
        search.trees = search.trees.filter(
            Q(height__isnull=True) |
            Q(height=0))

        search.plots = search.plots.filter(
            Q(tree__height__isnull=True) | 
            Q(tree__height=0))

        search.tile_query.append(" (height IS NULL OR height = 0) ")

    elif 'height_range' in request:
        hmin, hmax = [float(z) for z in request['height_range'].split('-')]

        search.trees = search.trees.filter(height__gte=hmin)
        search.plots = search.plots.filter(tree__height__gte=hmin)

        # TODO: Hardcoded in UI, may need to change
        # Same old same old....
        if max != 200: 
            search.trees = search.trees.filter(height__lte=hmax)
            search.plots = search.plots.filter(tree__height__lte=hmax)

        search.tile_query.append(
            " height BETWEEN %d AND %d " % (hmin, hmax))

    return search


def apply_tree_condition_filter(request, search):
    if request.get("missing_condition", False):
        search = apply_missing_tree_filter('condition', search)
    else:   
        ids = [k for (k,v) in extract_choices(request, 'conditions')]
        cqls = ["condition = %s" % i for i in ids]

        if ids:
            search.trees = search.trees.filter(condition__in=ids)
            search.plots = search.plots.filter(tree__condition__in=ids)

            search.tile_query.append(
                "( %s )" % " OR ".join(cqls))

    return search

def apply_canopy_condition_filter(request, search):
    if request.get("missing_canopy_condition", False):
        search = apply_missing_tree_filter("canopy_condition", search)
    else:   
        ids = []
        # This is the new (preferred?) style of using
        # a_n where {a} is a choices key and {n} is the id
        # so: canopy_conditions_5 or pests_9
        for k, v in settings.CHOICES["canopy_conditions"]:
            if ("canopy_%s" % k) in request:
                ids.append(k)


        cqls = ["canopy_condition = '%s'" % d for d in ids]
        
        if ids:
            search.trees = search.trees.filter(canopy_condition__in=ids)
            search.plots = search.plots.filter(tree__canopy_condition__in=ids)

            search.tile_query.append(
                "( %s )" % " OR ".join(cqls))

    return search

def apply_tree_owner_filter(request, search):
    if request.get("tree_owner", False):
        tree_owner = request["tree_owner"]

        search.trees = search.trees.filter(
            tree_owner__icontains=tree_owner)

        search.plots = search.plots.filter(
            tree__tree_owner__icontains=tree_owner)

        search.tile_query.append(
            "tree_owner LIKE '%%%s%%'" % tree_owner)

    return search

def apply_photos_filter(request, search):
    if request.get("missing_photos", False):
        search = apply_missing_tree_filter(
            "treephoto", search,
            cql="(photo_count IS NULL OR photo_count = 0)")

    elif 'photos' in request:
        search.trees = search.trees.filter(treephoto__isnull=False)
        search.plots = search.plots.filter(tree__treephoto__isnull=False)
        search.tile_query.append("photo_count > 0")

    return search

def apply_steward_filter(request, search):
    if 'steward' in request:
        steward = request['steward']
        users = User.objects.filter(username__icontains=steward)

        search.trees = search.trees.filter(
            Q(steward_user__in=users) | 
            Q(steward_name__icontains=steward))

        search.plots = search.plots.filter(
            Q(tree__steward_user__in=users) | 
            Q(tree__steward_name__icontains=steward))

        cqls = ["steward_user_id = %d" % u.id for u in users]
        cql = " OR ".join(cqls)

        search.tile_query.append(
            "( %s OR steward_name LIKE '%%%s%%' )" %
            (cql, steward))

    return search

def apply_funding_filter(request, search):
    if 'funding' in request:
        funding = request['funding']

        search.trees = search.trees.filter(
            sponsor__icontains=funding)

        search.plots = search.plots.filter(
            tree__sponsor__icontains=funding)

        search.tile_query.append(
            "sponsor LIKE '%%%s%%'" % funding)

    return search

def apply_planted_range_filter(request, search):
    if 'planted_range' in request:
        mind, maxd = [int(z) for z in request['planted_range'].split('-')]

        # Because this isn't sketchy at all
        mind = "%d-01-01" % mind
        maxd = "%d-12-31" % maxd

        search.trees = search.trees.filter(
            date_planted__gte=mind, 
            date_planted__lte=maxd)

        search.plots = search.plots.filter(
            tree__date_planted__gte=mind, 
            tree__date_planted__lte=maxd)

        search.tile_query.append(
            "date_planted AFTER %sT00:00:00Z AND "
            "date_planted BEFORE %sT00:00:00Z" %
            (mind, maxd))

    return search

def apply_species_filters(request, search):
    species = Species.objects.filter(tree_count__gt=0)

    species_criteria = {'native' : 'native_status',
                        'edible' : 'palatable_human',
                        'color' : 'fall_conspicuous',
                        'flowering' : 'flower_conspicuous',
                        'wildlife' : 'wildlife_value'}

    found_species = False

    # Wouldn't want to make these the same...?
    # These handle the boolean fields
    for (requestparam, dbname) in species_criteria.items():
        if requestparam in request:
            found_species = True  
            filterparam = { dbname: True }

            species = species.filter(**filterparam)

    if 'species' in request:
        found_species = True
        species = species.filter(id=request['species'])

    if found_species:
        search.trees = search.trees.filter(species__in=species)
        search.plots = search.plots.filter(tree__species__in=species)

        cqls = ["species_id = %d" % s.id for s in species]
        search.tile_query.append(
            "( %s )" % " OR ".join(cqls))

    return search


DEFAULT_FILTERS = [apply_location_filter,
                   apply_plot_size_filter,
                   apply_plot_type_filter,
                   apply_sidewalk_damage_filter,
                   apply_pests_filter,
                   apply_powerlines_filter,
                   apply_owner_filter,
                   apply_updated_by_filter,
                   apply_updated_range_filter,
                   apply_projects_filter,
                   apply_missing_species_filter,
                   apply_dbh_filter,
                   apply_tree_height_filter,
                   apply_tree_condition_filter,
                   apply_canopy_condition_filter,
                   apply_tree_owner_filter,
                   apply_photos_filter,
                   apply_steward_filter,
                   apply_funding_filter,
                   apply_planted_range_filter,
                   apply_species_filters,
                   apply_stewardship_filter]

def search(request, filters):
    tile_query = []
    trees = Tree.objects.filter(present=True)
    plots = Plot.objects.filter(present=True)

    treees = trees.extra(
        select= { 
            'geometry': 
            """
            SELECT treemap_plot.geometry
            FROM treemap_plot
            WHERE treemap_tree.plot_id = treemap_plot.id
            """ })

    s = Search(trees, plots, tile_query, None, None)

    return apply_filters(request, s, filters)

def apply_filters(request, search, filters):
    for f in filters:
        search = f(request, search)

    return search
