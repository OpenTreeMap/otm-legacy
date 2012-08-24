##################################################
#
#  For smaller datasets, this script can be run from within 
#  django's shell. For larger datasets, copy this script into
#  the handle method within the management command resave_trees
#  file and run as a manage.py command. 

from treemap.models import *

plots = Plot.objects.all()
counter = 0
for p in plots:
   counter = counter + 1
   p.neighborhoods = ""
   p.neighborhood.clear()
   n = Neighborhood.objects.filter(geometry__contains=p.geometry)
   if n:
     for nhood in n:
       p.neighborhoods = p.neighborhoods + " " + nhood.id.__str__()
       p.neighborhood.add(nhood)
   p.quick_save()
   if counter%50 = 0: print counter

