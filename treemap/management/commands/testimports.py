import os

from subprocess import Popen, PIPE, STDOUT
from django.core.management.base import BaseCommand, CommandError
from OpenTreeMap.treemap.models import Tree, Plot
# ID - number
# POINT_X - EPSG:4326
# POINT_Y - EPSG:4326
# SCIENTIFIC - Genus species (ex: Tilia americana) must exist in DB
# ADDRESS - Geocodable street address
# PLOTTYPE - one of the DB plot choices, case insensitive
# PLOTLENGTH - number, feet
# PLOTWIDTH - number, feet
# POWERLINE - True/False
# OWNER - property or tree owner name, not a site user
# DATEPLANTED - postgres-recognizable format
# DIAMETER - number, inches
# HEIGHT - number, feet
# CANOPYHEIGHT - number, feet
# CONDITION - one of the db condition choices, case sensitive
# CANOPYCONDITION - one of the DB canopy condition choices, case sensitive

# POINT_X,POINT_Y,SCIENTIFIC,ADDRESS,PLOTTYPE,PLOTLENGTH,PLOTWIDTH,POWERLINE,OWNER,DATEPLANTED,DIAMETER,HEIGHT,CANOPYHEIGHT,CONDITION,CANOPYCONDITION

# -75.154724121093,39.910583496096,Tilia americana,,,,,,,2000-10-20,12,20,,,

class TestCase(object):
    def __init__(self, name, infiles, Pnum, Tnum):
        self.name = name
        self.infiles = infiles
        self.Pnum = Pnum
        self.Tnum = Tnum
        
    def run(self, uid):
        Tree.objects.all().delete()
        Plot.objects.all().delete()

        for name in self.infiles:
            path = os.path.join("testdata", name)
            cmd = ['python', 'manage.py', 'uimport', path, str(uid), '--verbose']
            p = Popen(cmd, stdout=PIPE)
            output = p.stdout.read()
            print "OUTPUT", output
            p.wait()

        n = len(Plot.objects.all())
        t = len(Tree.objects.all())
        if self.Pnum == n and self.Tnum == t:
            print "%-20s PASSED" % self.name
        else:
            print "%-20s FAILED Plots:(%d != %d) or Trees:(%d != %d)" % (self.name, n, self.Pnum, t, self.Tnum)

class Command(BaseCommand):
    args = '<test_case_name, verbose>'
    option_list = BaseCommand.option_list
    
    tests = [
        #TestCase("single", ['test1.csv'], 35),
        TestCase("duplicates", ['sparse.csv', 'sparse.csv'], 1, 0),
        TestCase("sparse-update", ['rich.csv', 'sparse.csv'], 1, 1),
        TestCase("rich-update", ['sparse.csv', 'rich.csv'], 1, 1),
        TestCase("sparse-11ft", ['sparse.csv', 'sparseoff11.csv'], 2, 0),    
        TestCase("sparse-9ft", ['sparse.csv', 'sparseoff9.csv'], 1, 0),        
        TestCase("sparse-4ft", ['sparse.csv', 'sparseoff4.csv'], 1, 0),
        TestCase("unknown_collisions", ['speciespairs.csv', 'unk_species.csv'], 12, 8),
        TestCase("species_collisions", ['speciespairs.csv', 'A_species.csv'], 12, 8),
    ]

    def handle(self, *args, **options):
        if args and args[0]:
            for t in self.tests:
                if t.name == args[0]: t.run(1)
        else:
            for t in self.tests:
                t.run(1)
