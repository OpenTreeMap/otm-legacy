BEGIN;

------------------------------------------------------------------------------------------
------------------------------------------------------------------------------------------
--  -- Table: treemap_plot

CREATE TABLE treemap_plot
(
  id serial NOT NULL,
  present boolean NOT NULL,
  width double precision,
  length double precision,
  type character varying(256),
  powerline_conflict_potential character varying(256),
  sidewalk_damage character varying(256),
  address_street character varying(256),
  address_city character varying(256),
  address_zip character varying(30),
  neighborhoods character varying(150),
  zipcode_id integer,
  geocoded_accuracy integer,
  geocoded_address character varying(256),
  geocoded_lat double precision,
  geocoded_lon double precision,
  region character varying(256) NOT NULL,
  last_updated timestamp with time zone NOT NULL,
  last_updated_by_id integer NOT NULL,
  import_event_id integer NOT NULL,
  geometry geometry NOT NULL,
  geocoded_geometry geometry,
  owner_geometry geometry,
  tree_id integer NOT NULL,
  CONSTRAINT treemap_plot_pkey PRIMARY KEY (id),
  CONSTRAINT treemap_plot_import_event_id_fkey FOREIGN KEY (import_event_id)
      REFERENCES treemap_importevent (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION DEFERRABLE INITIALLY DEFERRED,
  CONSTRAINT treemap_plot_last_updated_by_id_fkey FOREIGN KEY (last_updated_by_id)
      REFERENCES auth_user (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION DEFERRABLE INITIALLY DEFERRED,
  CONSTRAINT treemap_plot_zipcode_id_fkey FOREIGN KEY (zipcode_id)
      REFERENCES treemap_zipcode (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION DEFERRABLE INITIALLY DEFERRED,
  CONSTRAINT enforce_dims_geocoded_geometry CHECK (st_ndims(geocoded_geometry) = 2),
  CONSTRAINT enforce_dims_geometry CHECK (st_ndims(geometry) = 2),
  CONSTRAINT enforce_dims_owner_geometry CHECK (st_ndims(owner_geometry) = 2),
  CONSTRAINT enforce_geotype_geocoded_geometry CHECK (geometrytype(geocoded_geometry) = 'POINT'::text OR geocoded_geometry IS NULL),
  CONSTRAINT enforce_geotype_geometry CHECK (geometrytype(geometry) = 'POINT'::text OR geometry IS NULL),
  CONSTRAINT enforce_geotype_owner_geometry CHECK (geometrytype(owner_geometry) = 'POINT'::text OR owner_geometry IS NULL),
  CONSTRAINT enforce_srid_geocoded_geometry CHECK (st_srid(geocoded_geometry) = 4326),
  CONSTRAINT enforce_srid_geometry CHECK (st_srid(geometry) = 4326),
  CONSTRAINT enforce_srid_owner_geometry CHECK (st_srid(owner_geometry) = 4326)
)
WITH (
  OIDS=FALSE
);
ALTER TABLE treemap_plot OWNER TO phillytreemap;

CREATE INDEX treemap_plot_geocoded_geometry_id
  ON treemap_plot
  USING gist
  (geocoded_geometry);

CREATE INDEX treemap_plot_geometry_id
  ON treemap_plot
  USING gist
  (geometry);

CREATE INDEX treemap_plot_import_event_id
  ON treemap_plot
  USING btree
  (import_event_id);

CREATE INDEX treemap_plot_last_updated_by_id
  ON treemap_plot
  USING btree
  (last_updated_by_id);

CREATE INDEX treemap_plot_owner_geometry_id
  ON treemap_plot
  USING gist
  (owner_geometry);

CREATE INDEX treemap_plot_zipcode_id
  ON treemap_plot
  USING btree
  (zipcode_id);

CREATE INDEX treemap_plot_tree_id
  ON treemap_plot
  USING btree
  (tree_id);

------------------------------------------------------------------------------------------
------------------------------------------------------------------------------------------
-- Table: treemap_plot_audit


CREATE TABLE treemap_plot_audit
(
  _audit_user_rep integer NOT NULL,
  _audit_diff text NOT NULL,
  _audit_verified integer NOT NULL,
  present boolean NOT NULL,
  width double precision,
  length double precision,
  type character varying(256),
  powerline_conflict_potential character varying(256),
  sidewalk_damage character varying(256),
  address_street character varying(256),
  address_city character varying(256),
  address_zip character varying(30),
  neighborhoods character varying(150),
  zipcode_id integer,
  geocoded_accuracy integer,
  geocoded_address character varying(256),
  geocoded_lat double precision,
  geocoded_lon double precision,
  region character varying(256) NOT NULL,
  last_updated timestamp with time zone NOT NULL,
  last_updated_by_id integer NOT NULL,
  import_event_id integer NOT NULL,
  _audit_id serial NOT NULL,
  _audit_timestamp timestamp with time zone NOT NULL,
  _audit_change_type character varying(1) NOT NULL,
  id integer NOT NULL,
  geometry geometry NOT NULL,
  geocoded_geometry geometry,
  owner_geometry geometry,
  CONSTRAINT treemap_plot_audit_pkey PRIMARY KEY (_audit_id),
  CONSTRAINT treemap_plot_audit_import_event_id_fkey FOREIGN KEY (import_event_id)
      REFERENCES treemap_importevent (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION DEFERRABLE INITIALLY DEFERRED,
  CONSTRAINT treemap_plot_audit_last_updated_by_id_fkey FOREIGN KEY (last_updated_by_id)
      REFERENCES auth_user (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION DEFERRABLE INITIALLY DEFERRED,
  CONSTRAINT treemap_plot_audit_zipcode_id_fkey FOREIGN KEY (zipcode_id)
      REFERENCES treemap_zipcode (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION DEFERRABLE INITIALLY DEFERRED,
  CONSTRAINT enforce_dims_geocoded_geometry CHECK (st_ndims(geocoded_geometry) = 2),
  CONSTRAINT enforce_dims_geometry CHECK (st_ndims(geometry) = 2),
  CONSTRAINT enforce_dims_owner_geometry CHECK (st_ndims(owner_geometry) = 2),
  CONSTRAINT enforce_geotype_geocoded_geometry CHECK (geometrytype(geocoded_geometry) = 'POINT'::text OR geocoded_geometry IS NULL),
  CONSTRAINT enforce_geotype_geometry CHECK (geometrytype(geometry) = 'POINT'::text OR geometry IS NULL),
  CONSTRAINT enforce_geotype_owner_geometry CHECK (geometrytype(owner_geometry) = 'POINT'::text OR owner_geometry IS NULL),
  CONSTRAINT enforce_srid_geocoded_geometry CHECK (st_srid(geocoded_geometry) = 4326),
  CONSTRAINT enforce_srid_geometry CHECK (st_srid(geometry) = 4326),
  CONSTRAINT enforce_srid_owner_geometry CHECK (st_srid(owner_geometry) = 4326)
)
WITH (
  OIDS=FALSE
);
ALTER TABLE treemap_plot_audit OWNER TO phillytreemap;

CREATE INDEX treemap_plot_audit__audit_timestamp
  ON treemap_plot_audit
  USING btree
  (_audit_timestamp);

CREATE INDEX treemap_plot_audit_geocoded_geometry_id
  ON treemap_plot_audit
  USING gist
  (geocoded_geometry);

CREATE INDEX treemap_plot_audit_geometry_id
  ON treemap_plot_audit
  USING gist
  (geometry);

CREATE INDEX treemap_plot_audit_id
  ON treemap_plot_audit
  USING btree
  (id);

CREATE INDEX treemap_plot_audit_import_event_id
  ON treemap_plot_audit
  USING btree
  (import_event_id);

CREATE INDEX treemap_plot_audit_last_updated_by_id
  ON treemap_plot_audit
  USING btree
  (last_updated_by_id);

CREATE INDEX treemap_plot_audit_owner_geometry_id
  ON treemap_plot_audit
  USING gist
  (owner_geometry);

CREATE INDEX treemap_plot_audit_zipcode_id
  ON treemap_plot_audit
  USING btree
  (zipcode_id);

ALTER TABLE treemap_tree_audit ALTER COLUMN geocoded_address DROP NOT NULL;
ALTER TABLE treemap_tree_audit ALTER COLUMN geometry DROP NOT NULL;

------------------------------------------------------------------------------------------
------------------------------------------------------------------------------------------
-- Table: treemap_plot_neighborhood

CREATE TABLE treemap_plot_neighborhood
(
  id serial NOT NULL,
  plot_id integer NOT NULL,
  neighborhood_id integer NOT NULL,
  CONSTRAINT treemap_plot_neighborhood_pkey PRIMARY KEY (id),
  CONSTRAINT plot_id_refs_id_5769cdc3 FOREIGN KEY (plot_id)
      REFERENCES treemap_plot (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION DEFERRABLE INITIALLY DEFERRED,
  CONSTRAINT treemap_plot_neighborhood_neighborhood_id_fkey FOREIGN KEY (neighborhood_id)
      REFERENCES treemap_neighborhood (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION DEFERRABLE INITIALLY DEFERRED,
  CONSTRAINT treemap_plot_neighborhood_plot_id_key UNIQUE (plot_id, neighborhood_id)
)
WITH (
  OIDS=FALSE
);
ALTER TABLE treemap_plot_neighborhood OWNER TO phillytreemap;

CREATE INDEX treemap_plot_neighborhood_neighborhood_id
  ON treemap_plot_neighborhood
  USING btree
  (neighborhood_id);

CREATE INDEX treemap_plot_neighborhood_plot_id
  ON treemap_plot_neighborhood
  USING btree
  (plot_id);

------------------------------------------------------------------------------------------
------------------------------------------------------------------------------------------
--  Make a Plot for each Tree and then write the primary key for the new Plot id back into
--  Tree as a foreign key. Afterward, removed the temporary tree_id column from the Plot
--  since it is no longer needed.

--  Run Time ~ 30s
-- Triggers need to be disabled to run the inserts inside a transaction
ALTER TABLE treemap_plot DISABLE TRIGGER ALL;
INSERT INTO treemap_plot (present, width, length, type, powerline_conflict_potential, sidewalk_damage, address_street,
  address_city, address_zip, neighborhoods, zipcode_id, geocoded_accuracy, geocoded_address, geocoded_lat, geocoded_lon,
  region, last_updated, last_updated_by_id, import_event_id, geometry, geocoded_geometry, owner_geometry, tree_id)
SELECT present, plot_width AS width, plot_length AS length, plot_type AS type, powerline_conflict_potential,
  sidewalk_damage, address_street, address_city, address_zip, neighborhoods, zipcode_id, geocoded_accuracy,
  geocoded_address, geocoded_lat, geocoded_lon, region, last_updated, last_updated_by_id, import_event_id,
  geometry geometry, geocoded_geometry, owner_geometry, id as tree_id
FROM treemap_tree;
ALTER TABLE treemap_plot ENABLE TRIGGER ALL;

-- Vacuum cannot run in a transaction
-- VACUUM FULL ANALYZE treemap_plot;

ALTER TABLE treemap_tree ADD COLUMN plot_id integer NULL;
ALTER TABLE treemap_tree_audit ADD COLUMN plot_id integer NULL;

-- Run Time ~ 40s
-- Triggers need to be disabled to run the inserts inside a transaction
ALTER TABLE treemap_tree DISABLE TRIGGER ALL;
UPDATE treemap_tree SET plot_id = (SELECT id from treemap_plot where treemap_plot.tree_id = treemap_tree.id);
ALTER TABLE treemap_tree ENABLE TRIGGER ALL;

ALTER TABLE treemap_tree ALTER COLUMN plot_id SET NOT NULL;

DROP INDEX IF EXISTS treemap_plot_tree_id;
ALTER TABLE treemap_plot DROP COLUMN tree_id;

------------------------------------------------------------------------------------------
------------------------------------------------------------------------------------------
-- Rename the existing treepending table and create the new pending, treepending, and
-- plotpending tables which will replace it.

ALTER TABLE treemap_treepending RENAME TO treemap_treepending_1_0;
ALTER INDEX treemap_treepending_tree_id RENAME TO treemap_treepending_1_0_tree_id;

CREATE TABLE "treemap_pending" (
    "id" serial NOT NULL PRIMARY KEY,
    "field" varchar(255) NOT NULL,
    "value" varchar(255),
    "text_value" varchar(255),
    "submitted" timestamp with time zone NOT NULL,
    "submitted_by_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED,
    "status" varchar(10) NOT NULL,
    "updated" timestamp with time zone NOT NULL,
    "updated_by_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED
);
CREATE INDEX "treemap_pending_submitted_by_id" ON "treemap_pending" ("submitted_by_id");
CREATE INDEX "treemap_pending_updated_by_id" ON "treemap_pending" ("updated_by_id");
ALTER TABLE treemap_pending OWNER TO phillytreemap;

CREATE TABLE "treemap_treepending" (
    "pending_ptr_id" integer NOT NULL PRIMARY KEY REFERENCES "treemap_pending" ("id") DEFERRABLE INITIALLY DEFERRED,
    "tree_id" integer NOT NULL REFERENCES "treemap_tree" ("id") DEFERRABLE INITIALLY DEFERRED
);
CREATE INDEX "treemap_treepending_tree_id" ON "treemap_treepending" ("tree_id");
ALTER TABLE treemap_treepending OWNER TO phillytreemap;

CREATE TABLE "treemap_plotpending" (
    "pending_ptr_id" integer NOT NULL PRIMARY KEY REFERENCES "treemap_pending" ("id") DEFERRABLE INITIALLY DEFERRED,
    "plot_id" integer NOT NULL REFERENCES "treemap_plot" ("id") DEFERRABLE INITIALLY DEFERRED
);
CREATE INDEX "treemap_plotpending_plot_id" ON "treemap_plotpending" ("plot_id");
SELECT AddGeometryColumn('treemap_plotpending', 'geometry', 4326, 'POINT', 2);
CREATE INDEX "treemap_plotpending_geometry_id" ON "treemap_plotpending" USING GIST ( "geometry" GIST_GEOMETRY_OPS );
ALTER TABLE treemap_plotpending OWNER TO phillytreemap;

------------------------------------------------------------------------------------------
------------------------------------------------------------------------------------------
-- Iterate over the original treepending table and use the values to create records in the
-- new pending, treepending, and plotpending tables.

CREATE OR REPLACE FUNCTION fill_treemap_pending() RETURNS VOID AS $$
DECLARE
  pending_1_0 RECORD;
  geom geometry;
  new_pending_id INT;
  plot_id_from_tree INT;
BEGIN
  FOR pending_1_0 IN SELECT * FROM treemap_treepending_1_0 LOOP
    EXECUTE 'INSERT INTO treemap_pending (field, value, text_value, submitted, submitted_by_id, status, updated, updated_by_id) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)'
    USING pending_1_0.field, pending_1_0.value, pending_1_0.text_value, pending_1_0.submitted,
    pending_1_0.submitted_by_id, pending_1_0.status, pending_1_0.updated, pending_1_0.updated_by_id;

    SELECT currval('treemap_pending_id_seq') INTO new_pending_id;
    raise notice 'pending_1_0.tree_id %', pending_1_0.tree_id;
    SELECT plot_id INTO plot_id_from_tree FROM treemap_tree WHERE treemap_tree.id = pending_1_0.tree_id;
    raise notice '%', plot_id_from_tree;

    SELECT geometry into geom from treemap_treegeopending where treepending_ptr_id = pending_1_0.id;
    IF FOUND THEN
      EXECUTE 'INSERT INTO treemap_plotpending (pending_ptr_id, plot_id, geometry) VALUES ($1, $2, $3)'
      USING new_pending_id, plot_id_from_tree, geom;
    ELSE
      -- The tree and plot pends are in different tables so that the Django models can have different update and delete
      -- methods.
      IF pending_1_0.field = 'plot_width' OR pending_1_0.field = 'plot_length' OR pending_1_0.field = 'plot_type' OR pending_1_0.field = 'powerline_conflict_potential' OR pending_1_0.field = 'sidewalk_damage' OR pending_1_0.field = 'address_street' OR pending_1_0.field = 'address_state' OR pending_1_0.field = 'address_zip'
      THEN
        EXECUTE 'INSERT INTO treemap_plotpending (pending_ptr_id, plot_id) VALUES ($1, $2)'
        USING new_pending_id, plot_id_from_tree;
      ELSE
        EXECUTE 'INSERT INTO treemap_treepending (pending_ptr_id, tree_id) VALUES ($1, $2)'
        USING new_pending_id, pending_1_0.tree_id;
      END IF;
    END IF;

  END LOOP;
END $$ LANGUAGE plpgsql;

SELECT * FROM fill_treemap_pending();
DROP FUNCTION fill_treemap_pending();

COMMIT;
