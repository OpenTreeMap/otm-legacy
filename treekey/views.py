from django.template import RequestContext
from django.http import HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.template import Context, Template
from django.template.loader import render_to_string
from treekey.models import Node, Species

# Create a tree heirarchy to display node relationships
def nodes(request):
    return render_to_response('treekey/base.html',
                              {'display': index_maker()})

# Warning! Recursion here! Tread carefully!
# Recursively generates a tree of nodes in their parent-child relationships
def index_maker():
    rootnode = Node.objects.order_by('id')[0]
    def _index(node):
        for child in node.child_set.all():
            if child.has_children():
                yield render_to_string('treekey/list_branch.html',
                                           {'node': child,
                                           'leaves': _index(child)})
                continue

            yield render_to_string('treekey/list_branch.html',
                {'node': child,
                'leaves': None})
    return _index(rootnode)

# Warning! Inner-loop reassignment here! Tread carefully!
# Generates a bread-crumb trail from a node up the parent tree to the start
def trail_maker(n):
    node_trail = []
    while n.has_parent():
        node_trail.insert(0, n)
        n = n.parent_node
        
    return node_trail

# Returns the starting node for the key. Must be the first record in the database.
def first_node(request):
    f = Node.objects.order_by('id')[0]
    return render_to_response('treekey/node.html', RequestContext(request, {'request': request, 'node':f, 'display':index_maker(), 'trail':trail_maker(f)}))

# Returns a node or leaf depending on the child objects
def node(request, node_id):
    n = get_object_or_404(Node, pk=node_id)
    if n.has_children():
        return render_to_response('treekey/node.html', RequestContext(request, {'request': request, 'node':n, 'display':index_maker(), 'trail':trail_maker(n)}))
    return render_to_response('treekey/leaf.html', RequestContext(request, {'request': request, 'leaf':n, 'display':index_maker(), 'trail':trail_maker(n)})    )

# Returns species information with parent node trail/index information
def species(request, species_id):
    s = get_object_or_404(Species, pk=species_id)
    n = s.node_set.all()[0];
    return render_to_response('treekey/species.html', RequestContext(request, {'request': request, 'species':s, 'display':index_maker(), 'trail':trail_maker(n)}))
    
def browse(request):
    f = Node.objects.order_by('id')[0]
    species = Species.objects.all().order_by('common_name')
    return render_to_response('treekey/browse.html', RequestContext(request, {'request': request, 'species':species, 'display':index_maker(), 'trail':trail_maker(f)}))
    
