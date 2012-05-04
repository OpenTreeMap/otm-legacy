from django.conf.urls.defaults import *
from views import *
from treemap.models import Neighborhood, SupervisorDistrict, Tree, TreeFavorite
from classfaves.views import CreateFavorite, DeleteFavorite, UserFavorites
from django.views.generic.simple import direct_to_template

create_favorite = CreateFavorite(TreeFavorite, Tree)
delete_favorite = DeleteFavorite(TreeFavorite, Tree)
most_recent = lambda qs: qs.order_by('-date_created')
user_favorites = UserFavorites(TreeFavorite, Tree, extra_filter=most_recent)

urlpatterns = patterns('',
    #(r'^$', direct_to_template, {'template':'under_construction.html'}),
    (r'^$', home_feeds),
    (r'^home/$', home_feeds),
    (r'^home/feeds/$', home_feeds),
    (r'^robots.txt/$', static, {'template':'robots.txt'}),
    
    (r'^export/csv$', get_all_csv),
    (r'^export/kmz$', get_all_kmz),
    
    (r'^map/$', result_map),

    (r'^geocode/$', get_geocode),
    (r'^geocode/reverse/$', get_reverse_geocode),
    
    (r'^neighborhoods/$', geographies, {'model' : Neighborhood}),
    (r'^neighborhoods/(?P<id>\d+)/$', geographies, {'model' : Neighborhood}),
    (r'^zipcodes/$', zips),
    (r'^zipcodes/(?P<id>\d+)/$', zips),

    (r'^update/$', object_update),

    url(r'^plots/(?P<plot_id>\d+)/$', plot_detail, name="treemap_plot_detail"),
    (r'^plots/(?P<plot_id>\d+)/addtree/$', plot_add_tree),
    (r'^plots/(?P<plot_id>\d+)/edit/$', plot_edit),
    (r'^plots/(?P<plot_id>\d+)/delete/$', plot_delete),
    (r'^plots/location/$', plot_location_search),
    (r'^plots/location/update/$', plot_location_update),
    (r'^plots/(?P<plot_id>\d+)/edit/choices/(?P<type_>[a-z_]*)/$', plot_edit_choices),
    (r'^plots/(?P<plot_id>\d+)/update/$', update_plot),
    (r'^plots/(?P<plot_id>\d+)/stewardship/$', add_plot_stewardship),
    (r'^plots/(?P<plot_id>\d+)/stewardship/(?P<activity_id>\d+)/delete/$', delete_plot_stewardship),

    (r'^trees/$', trees),
    (r'^trees/batch_edit/$', batch_edit),
    (r'^trees/add/$', tree_add),
    url(r'^trees/(?P<tree_id>\d+)/edit/$', tree_edit, name="treemap_tree_edit"),
    url(r'^trees/(?P<tree_id>\d+)/photos/$', tree_add_edit_photos, name="treemap_add_edit_photos"),
    (r'^trees/(?P<tree_id>\d+)/edit/choices/(?P<type_>[a-z_]*)/$', tree_edit_choices),
    (r'^trees/(?P<tree_id>\d+)/delete/$', tree_delete),
    (r'^trees/(?P<tree_id>\d+)/deletephoto/(?P<photo_id>\d+)$', photo_delete),
    (r'^trees/(?P<tree_id>\d+)/ecosystem/$', trees),
    (r'^trees/(?P<tree_id>\d+)/stewardship/$', add_tree_stewardship),
    (r'^trees/(?P<tree_id>\d+)/stewardship/(?P<activity_id>\d+)/delete/$', delete_tree_stewardship),
    url(r'^trees/(?P<tree_id>\d+)/$', trees, name="treemap_tree_detail"),
    (r'^trees/new/$', added_today_list),   
    (r'^trees/new/(?P<format>(geojson))/$', added_today_list),   
    (r'^trees/new/(?P<user_id>\d+)/$', added_today_list),
    (r'^trees/new/(?P<user_id>\d+)/(?P<format>(geojson))/$', added_today_list),

    (r'^trees/pending/$', view_pends),
    (r'^trees/pending/(?P<pend_id>\d+)/approve/$', approve_pend),  
    (r'^trees/pending/(?P<pend_id>\d+)/reject/$', reject_pend),    

    (r'^trees/watch/$', watch_list),
    (r'^watch/validate/$', validate_watch),
    
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
    (r'^search/geo$', geo_search),
    (r'^search/(?P<format>.*)/$', advanced_search),
    
    (r'^check_username/$', check_username),
    (r'^users/$', edit_users),
    (r'^users/update/$', update_users),
    (r'^users/ban/$', ban_user),
    (r'^users/activate/$', unban_user),
    (r'^users/activity/$', user_rep_changes),
    (r'^users/opt-in/$', user_opt_in_list),
    (r'^users/opt-in/(?P<format>.*)/$', user_opt_export),
    (r'^profiles/(?P<username>[a-zA-Z0-9_-]+)/deletephoto/', userphoto_delete),
    
    (r'^comments/flag/(?P<comment_id>[0-9]+)/$', add_flag),
    (r'^comments/moderate/$', view_flagged),
    (r'^comments/all/$', view_comments),
    (r'^comments/all/(?P<format>.*)/$', export_comments),
    (r'^comments/hide/$', hide_comment),
    (r'^comments/unflag/$', remove_flag),

    (r'^contact/$', contact),
    (r'^contact/thanks/$', static, {'template':'contact_thanks.html'}),

    url(r'^verify/$', verify_edits, name='treemap_verify_edits'),
    url(r'^verify/(?P<change_type>[a-z_]*)/(?P<change_id>\d+)/(?P<rep_dir>(up|neutral|down))', verify_rep_change),
    
    (r'^stewardship/', view_stewardship),

    (r'^images/$', view_images),
    
)
    
