 BEGIN;

------------------------------------------------------------------------------------------
------------------------------------------------------------------------------------------
--  Create a tree_search view
--    This view is used by geoserver to run cql queries from the search page.
--    Add this view as a layer to geoserver and use it as the GEOSERVER_GEO_LAYER setting

CREATE VIEW tree_search AS
 SELECT treemap_tree.id, treemap_tree.species_id, treemap_plot.geometry, treemap_plot.neighborhoods, treemap_plot.zipcode_id, treemap_tree.projects, treemap_tree.dbh, treemap_tree.height, treemap_plot.length AS plot_length, treemap_plot.width AS plot_width, treemap_plot.type AS plot_type, treemap_tree.condition, treemap_plot.sidewalk_damage, treemap_plot.powerline_conflict_potential, treemap_tree.photo_count, treemap_tree.steward_user_id, treemap_plot.data_owner_id, treemap_tree.last_updated_by_id, treemap_tree.sponsor, treemap_tree.date_planted, treemap_tree.last_updated
   FROM treemap_plot, treemap_tree
  WHERE treemap_tree.present AND treemap_plot.present AND treemap_tree.plot_id = treemap_plot.id;

COMMIT;
