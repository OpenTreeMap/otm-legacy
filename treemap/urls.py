from django.conf.urls.defaults import *
from views import *
from treemap.models import Neighborhood, SupervisorDistrict, Tree, TreeFavorite
from classfaves.views import CreateFavorite, DeleteFavorite, UserFavorites

create_favorite = CreateFavorite(TreeFavorite, Tree)
delete_favorite = DeleteFavorite(TreeFavorite, Tree)
most_recent = lambda qs: qs.order_by('-date_created')
user_favorites = UserFavorites(TreeFavorite, Tree, extra_filter=most_recent)


urlpatterns = patterns('',
    (r'^$', static, {'template':'index.html'}),
    (r'^robots.txt/$', static, {'template':'robots.txt'}),
    
    
    (r'^map/$', result_map),
    
    (r'^neighborhoods/$', geographies, {'model' : Neighborhood}),
    (r'^neighborhoods/(?P<id>\d+)/$', geographies, {'model' : Neighborhood}),
    (r'^zipcodes/$', geographies, {'model' : ZipCode}),
    (r'^zipcodes/(?P<id>\d+)/$', geographies, {'model' : ZipCode}),
    
    (r'^update/$', object_update),
    (r'^trees/$', trees),
    (r'^trees/batch_edit/$', batch_edit),
    (r'^trees/add/$', tree_add),
    url(r'^trees/(?P<tree_id>\d+)/edit/$', tree_edit, name="treemap_tree_edit"),
    url(r'^trees/(?P<tree_id>\d+)/photos/$', tree_add_edit_photos, name="treemap_add_edit_photos"),
    (r'^trees/(?P<tree_id>\d+)/edit/choices/(?P<type_>[a-z_]*)/$', tree_edit_choices),
    (r'^trees/(?P<tree_id>\d+)/ecosystem/$', trees),
    url(r'^trees/(?P<tree_id>\d+)/$', trees, name="treemap_tree_detail"),
    (r'^trees/location/$', tree_location_search),
    
    
    url(r'^trees/favorites/create/(?P<pk>\d+)/$', create_favorite, name='treeemap_favorite_create'), 
    url(r'^trees/favorites/delete/(?P<pk>\d+)/$', delete_favorite, name='treeemap_favorite_delete'), 
    url(r'^trees/favorites/$', user_favorites, name='treeemap_my_favorites'), 
    url(r'^trees/favorites/(?P<username>[a-zA-Z0-9_-]+)/$', user_favorites, name='treeemap_user_favorites'),
    url(r'^trees/favorites/(?P<username>[a-zA-Z0-9_-]+)/geojson/$', favorites),
    
    
    (r'^species/$', species),
    (r'^species/(?P<format>(json|html|csv))/$', species),
    (r'^species/(?P<selection>(all|in-use|nearby))/$', species),
    (r'^species/(?P<selection>(all|in-use|nearby))/(?P<format>(json|html|csv))/$', species),
    (r'^species/(?P<code>[-\w]+)/$', species),
    
    
    (r'^search/$', advanced_search),
    (r'^search/(?P<format>.*)/$', advanced_search),
    
    (r'^check_username/$', check_username),

    (r'^contact/$', contact),
    (r'^contact/thanks/$', static, {'template':'contact_thanks.html'}),

    url(r'^verify/$', verify_edits, name='treemap_verify_edits'),
    #TODO: add filters for other verifyable objects
    #url(r'^verify/(?P<audit_type>(tree|other))/$', verify_edits, name='treemap_verify_by_type'),
    
)
    
