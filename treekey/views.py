from django.http import HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.template import Context, Template
from django.template.loader import render_to_string
from treekey.models import Node, Species


def nodes(request):
    return render_to_response('treekey/base.html',
                              {'display': index_maker()})

# Warning! Recursion here! Tread carefully!
def index_maker():
    rootnode = Node.objects.order_by('id')[0]
    def _index(node):
        list = node.child_set.all()
        for child in list:
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
def trail_maker(n):
    node_trail = []
    while n.has_parent():
        node_trail.insert(0, n)
        n = n.parent_node
        
    return node_trail

def first_node(request):
    f = Node.objects.order_by('id')[0]
    return render_to_response('treekey/node.html', {'node':f, 'display':index_maker(), 'trail':trail_maker(f)})

def node(request, node_id):
    n = get_object_or_404(Node, pk=node_id)
    if n.has_children():
        return render_to_response('treekey/node.html', {'node':n, 'display':index_maker(), 'trail':trail_maker(n)})
    return render_to_response('treekey/leaf.html', {'leaf':n, 'display':index_maker(), 'trail':trail_maker(n)})    

    
def species(request, species_id):
    s = get_object_or_404(Species, pk=species_id)
    n = s.node_set.all()[0];
    return render_to_response('treekey/species.html', {'species':s, 'display':index_maker(), 'trail':trail_maker(n)})
    