from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.gis.geos.collections import MultiPolygon
from django.contrib.gis.geos.point import Point
from django.contrib.gis.geos.polygon import Polygon
from django_reputation.models import ReputationAction, Reputation
from api.models import APILog, APIKey
from profiles.models import UserProfile
from treemap.models import Species, BenefitValues, Resource, Neighborhood, ZipCode, ExclusionMask, AggregateNeighborhood, ImportEvent, Tree, Plot


def mkPlot(u, geom=Point(50,50)):
    p = Plot(geometry=geom, last_updated_by=u, import_event=ImportEvent.objects.all()[0],present=True, data_owner=u)
    p.save()

    return p

def mkTree(u, plot=None, species=None):
    if not plot:
        plot = mkPlot(u)

    if species:
        s = species
    else:
        s = Species.objects.all()[0]

    t = Tree(plot=plot, species=s, last_updated_by=u, import_event=ImportEvent.objects.all()[0])
    t.save()

    return t

def setupTreemapEnv():
    settings.GEOSERVER_GEO_LAYER = ""
    settings.GEOSERVER_GEO_STYLE = ""
    settings.GEOSERVER_URL = ""

    r1 = ReputationAction(name="edit verified", description="blah")
    r2 = ReputationAction(name="edit tree", description="blah")
    r3 = ReputationAction(name="Administrative Action", description="blah")
    r4 = ReputationAction(name="add tree", description="blah")
    r5 = ReputationAction(name="edit plot", description="blah")
    r6 = ReputationAction(name="add plot", description="blah")

    for r in [r1,r2,r3,r4,r5,r6]:
        r.save()

    bv = BenefitValues(co2=0.02, pm10=9.41, area="InlandValleys",
        electricity=0.1166,voc=4.69,ozone=5.0032,natural_gas=1.25278,
        nox=12.79,stormwater=0.0078,sox=3.72,bvoc=4.96)

    bv.save()

    dbh = "[1.0, 2.0, 3.0]"

    rsrc = Resource(meta_species="BDM_OTHER", electricity_dbh=dbh, co2_avoided_dbh=dbh,
        aq_pm10_dep_dbh=dbh, region="Sim City", aq_voc_avoided_dbh=dbh,
        aq_pm10_avoided_dbh=dbh, aq_ozone_dep_dbh=dbh, aq_nox_avoided_dbh=dbh,
        co2_storage_dbh=dbh,aq_sox_avoided_dbh=dbh, aq_sox_dep_dbh=dbh,
        bvoc_dbh=dbh, co2_sequestered_dbh=dbh, aq_nox_dep_dbh=dbh,
        hydro_interception_dbh=dbh, natural_gas_dbh=dbh)
    rsrc.save()

    u = User.objects.filter(username="jim")

    if u:
        u = u[0]
    else:
        u = User.objects.create_user("jim","jim@test.org","jim")
        u.is_staff = True
        u.is_superuser = True
        u.save()
        up = UserProfile(user=u)
        up.save()
        u.reputation = Reputation(user=u)
        u.reputation.save()

    amy_filter_result = User.objects.filter(username="amy")
    if not amy_filter_result:
        amy = User.objects.create_user("amy","amy@test.org","amy")
    else:
        amy = amy_filter_result[0]
    amy.is_staff = False
    amy.is_superuser = False
    amy.save()
    amy_profile = UserProfile(user=amy)
    amy_profile.save()
    amy.reputation = Reputation(user=amy)
    amy.reputation.save()

    n1geom = MultiPolygon(Polygon(((0,0),(100,0),(100,100),(0,100),(0,0))))
    n2geom = MultiPolygon(Polygon(((0,101),(101,101),(101,200),(0,200),(0,101))))

    n1 = Neighborhood(name="n1", region_id=2, city="c1", state="PA", county="PAC", geometry=n1geom)
    n2 = Neighborhood(name="n2", region_id=2, city="c2", state="NY", county="NYC", geometry=n2geom)

    n1.save()
    n2.save()

    z1geom = MultiPolygon(Polygon(((0,0),(100,0),(100,100),(0,100),(0,0))))
    z2geom = MultiPolygon(Polygon(((0,100),(100,100),(100,200),(0,200),(0,100))))

    z1 = ZipCode(zip="19107",geometry=z1geom)
    z2 = ZipCode(zip="10001",geometry=z2geom)

    z1.save()
    z2.save()

    exgeom1 = MultiPolygon(Polygon(((0,0),(25,0),(25,25),(0,25),(0,0))))
    ex1 = ExclusionMask(geometry=exgeom1, type="building")

    ex1.save()

    agn1 = AggregateNeighborhood(
        annual_stormwater_management=0.0,
        annual_electricity_conserved=0.0,
        annual_energy_conserved=0.0,
        annual_natural_gas_conserved=0.0,
        annual_air_quality_improvement=0.0,
        annual_co2_sequestered=0.0,
        annual_co2_avoided=0.0,
        annual_co2_reduced=0.0,
        total_co2_stored=0.0,
        annual_ozone=0.0,
        annual_nox=0.0,
        annual_pm10=0.0,
        annual_sox=0.0,
        annual_voc=0.0,
        annual_bvoc=0.0,
        total_trees=0,
        total_plots=0,
        location = n1)

    agn2 = AggregateNeighborhood(
        annual_stormwater_management=0.0,
        annual_electricity_conserved=0.0,
        annual_energy_conserved=0.0,
        annual_natural_gas_conserved=0.0,
        annual_air_quality_improvement=0.0,
        annual_co2_sequestered=0.0,
        annual_co2_avoided=0.0,
        annual_co2_reduced=0.0,
        total_co2_stored=0.0,
        annual_ozone=0.0,
        annual_nox=0.0,
        annual_pm10=0.0,
        annual_sox=0.0,
        annual_voc=0.0,
        annual_bvoc=0.0,
        total_trees=0,
        total_plots=0,
        location = n2)

    agn1.save()
    agn2.save()

    s1 = Species(symbol="s1",genus="testus1",species="specieius1")
    s2 = Species(symbol="s2",genus="testus2",species="specieius2")

    s1.save()
    s2.save()

    ie = ImportEvent(file_name='site_add')
    ie.save()

def teardownTreemapEnv():
    for r in APILog.objects.all():
        r.delete()

    for r in APIKey.objects.all():
        r.delete()

    for r in BenefitValues.objects.all():
        r.delete()

    for u in User.objects.all():
        u.delete()

    for r in Neighborhood.objects.all():
        r.delete()

    for r in ZipCode.objects.all():
        r.delete()

    for r in ExclusionMask.objects.all():
        r.delete()

    for r in AggregateNeighborhood.objects.all():
        r.delete()

    for r in Species.objects.all():
        r.delete()

    for r in ImportEvent.objects.all():
        r.delete()

    for r in Tree.objects.all():
        r.delete()

    for r in Plot.objects.all():
        r.delete()

    for r in ReputationAction.objects.all():
        r.delete()
