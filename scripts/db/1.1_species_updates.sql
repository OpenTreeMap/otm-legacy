 BEGIN;

------------------------------------------------------------------------------------------
------------------------------------------------------------------------------------------
--  Additions to other tables
--  -- Add gender to species, species_other text to trees

ALTER TABLE treemap_species ADD COLUMN gender character varying(50);
ALTER TABLE treemap_tree ADD COLUMN species_other1 character varying(255);
ALTER TABLE treemap_tree ADD COLUMN species_other2 character varying(255);
ALTER TABLE treemap_tree_audit ADD COLUMN species_other1 character varying(255);
ALTER TABLE treemap_tree_audit ADD COLUMN species_other2 character varying(255);


COMMIT;
