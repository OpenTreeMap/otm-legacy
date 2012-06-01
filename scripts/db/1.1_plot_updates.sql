 BEGIN;

------------------------------------------------------------------------------------------
------------------------------------------------------------------------------------------
--  Add a new owner id field

ALTER TABLE treemap_plot ADD COLUMN owner_additional_id character varying(255);
ALTER TABLE treemap_plot_audit ADD COLUMN owner_additional_id character varying(255);


COMMIT;
