 BEGIN;

------------------------------------------------------------------------------------------
------------------------------------------------------------------------------------------
--  Create a tree_search view
--    This view is used by geoserver to run cql queries from the search page.
--    Fields not included in the advanced filters may be removed. Check the views code 
--    to make sure a field does not help resolve some other fileter before removing.
--
--    Stewardship date columns may need to be altered if the choices for stewardship
--    fields are changed. 
--
--    Add this view as a layer to geoserver and use it as the GEOSERVER_GEO_LAYER setting

CREATE OR REPLACE VIEW tree_search AS 
 SELECT treemap_tree.id, treemap_tree.species_id, treemap_plot.geometry, treemap_plot.neighborhoods, 
        treemap_plot.zipcode_id, treemap_tree.projects, treemap_tree.dbh, treemap_tree.height, 
        treemap_plot.length AS plot_length, treemap_plot.width AS plot_width, treemap_plot.type AS plot_type, 
        treemap_tree.condition, treemap_plot.sidewalk_damage, treemap_plot.powerline_conflict_potential, 
        treemap_tree.photo_count, treemap_tree.steward_user_id, treemap_plot.data_owner_id, 
        treemap_tree.last_updated_by_id, treemap_tree.sponsor, treemap_tree.date_planted, treemap_tree.last_updated, 

        (select s.performed_date 
         from treemap_stewardship as s, treemap_plotstewardship as p
         where p.stewardship_ptr_id = s.id and p.activity='1' and p.plot_id = treemap_plot.id
         order by s.performed_date limit 1
        ) as plot_stewardship_1,

        (select s.performed_date 
         from treemap_stewardship as s, treemap_plotstewardship as p
         where p.stewardship_ptr_id = s.id and p.activity='2' and p.plot_id = treemap_plot.id
         order by s.performed_date limit 1
        ) as plot_stewardship_2, 

        (select s.performed_date 
         from treemap_stewardship as s, treemap_plotstewardship as p
         where p.stewardship_ptr_id = s.id and p.activity='3' and p.plot_id = treemap_plot.id
         order by s.performed_date limit 1
        ) as plot_stewardship_3, 

        (select s.performed_date 
         from treemap_stewardship as s, treemap_plotstewardship as p
         where p.stewardship_ptr_id = s.id and p.activity='4' and p.plot_id = treemap_plot.id
         order by s.performed_date limit 1
        ) as plot_stewardship_4,

        (select s.performed_date 
         from treemap_stewardship as s, treemap_treestewardship as t
         where t.stewardship_ptr_id = s.id and t.activity='1' and t.tree_id = treemap_tree.id
         order by s.performed_date limit 1
        ) as tree_stewardship_1,

        (select s.performed_date 
         from treemap_stewardship as s, treemap_treestewardship as t
         where t.stewardship_ptr_id = s.id and t.activity='2' and t.tree_id = treemap_tree.id
         order by s.performed_date limit 1
        ) as tree_stewardship_2,

        (select s.performed_date 
         from treemap_stewardship as s, treemap_treestewardship as t
         where t.stewardship_ptr_id = s.id and t.activity='3' and t.tree_id = treemap_tree.id
         order by s.performed_date limit 1
        ) as tree_stewardship_3,

        (select s.performed_date 
         from treemap_stewardship as s, treemap_treestewardship as t
         where t.stewardship_ptr_id = s.id and t.activity='4' and t.tree_id = treemap_tree.id
         order by s.performed_date limit 1
        ) as tree_stewardship_4



   FROM treemap_plot, treemap_tree
  WHERE treemap_tree.present AND treemap_plot.present AND treemap_tree.plot_id = treemap_plot.id;

COMMIT;
