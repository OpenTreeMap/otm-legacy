
CREATE TABLE treemap_choices (
    id integer NOT NULL,
    field character varying(255) NOT NULL,
    value character varying(255) NOT NULL,
    key character varying(255) DEFAULT ''::character varying NOT NULL,
    key_type character varying DEFAULT ''::character varying NOT NULL
);


CREATE SEQUENCE treemap_choices_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;

SELECT pg_catalog.setval('treemap_choices_id_seq', 79, true);

ALTER TABLE treemap_choices ALTER COLUMN id SET DEFAULT nextval('treemap_choices_id_seq'::regclass);

INSERT INTO treemap_choices (id, field, value, key, key_type) VALUES (2, 'factoid', 'Interesting Quote', '2', 'int');
INSERT INTO treemap_choices (id, field, value, key, key_type) VALUES (3, 'factoid', 'How You Can Help', '3', 'int');
INSERT INTO treemap_choices (id, field, value, key, key_type) VALUES (4, 'factoid', 'Editing', '4', 'int');
INSERT INTO treemap_choices (id, field, value, key, key_type) VALUES (5, 'factoid', 'Interesting Fact', '5', 'int');
INSERT INTO treemap_choices (id, field, value, key, key_type) VALUES (12, 'status', 'Height (in feet)', '1', 'int');
INSERT INTO treemap_choices (id, field, value, key, key_type) VALUES (13, 'status', 'Diameter (in inches)', '2', 'int');
INSERT INTO treemap_choices (id, field, value, key, key_type) VALUES (14, 'alert', 'Needs Watering', '1', 'int');
INSERT INTO treemap_choices (id, field, value, key, key_type) VALUES (15, 'alert', 'Needs Pruning', '2', 'int');
INSERT INTO treemap_choices (id, field, value, key, key_type) VALUES (16, 'alert', 'Should Be Removed', '3', 'int');
INSERT INTO treemap_choices (id, field, value, key, key_type) VALUES (17, 'alert', 'Pest or Disease present', '4', 'int');
INSERT INTO treemap_choices (id, field, value, key, key_type) VALUES (18, 'alert', 'Guard Should be Removed', '5', 'int');
INSERT INTO treemap_choices (id, field, value, key, key_type) VALUES (19, 'alert', 'Stakes and Ties Should be Removed', '6', 'int');
INSERT INTO treemap_choices (id, field, value, key, key_type) VALUES (20, 'alert', 'Construction Work in the Area', '7', 'int');
INSERT INTO treemap_choices (id, field, value, key, key_type) VALUES (21, 'alert', 'Touching Wires', '8', 'int');
INSERT INTO treemap_choices (id, field, value, key, key_type) VALUES (22, 'alert', 'Blocking Signs or Traffic Signals', '9', 'int');
INSERT INTO treemap_choices (id, field, value, key, key_type) VALUES (23, 'alert', 'Improperly Pruned or Topped', '10', 'int');
INSERT INTO treemap_choices (id, field, value, key, key_type) VALUES (24, 'action', 'Watered', '1', 'int');
INSERT INTO treemap_choices (id, field, value, key, key_type) VALUES (25, 'action', 'Pruned', '2', 'int');
INSERT INTO treemap_choices (id, field, value, key, key_type) VALUES (26, 'action', 'Fruit or Nuts Harvested', '3', 'int');
INSERT INTO treemap_choices (id, field, value, key, key_type) VALUES (27, 'action', 'Removed', '4', 'int');
INSERT INTO treemap_choices (id, field, value, key, key_type) VALUES (28, 'action', 'Inspected', '5', 'int');
INSERT INTO treemap_choices (id, field, value, key, key_type) VALUES (29, 'local', 'Landmark Tree', '1', 'int');
INSERT INTO treemap_choices (id, field, value, key, key_type) VALUES (30, 'local', 'Local Carbon Fund', '2', 'int');
INSERT INTO treemap_choices (id, field, value, key, key_type) VALUES (31, 'local', 'Fruit Gleaning Project', '3', 'int');
INSERT INTO treemap_choices (id, field, value, key, key_type) VALUES (32, 'local', 'Historically Significant Tree', '4', 'int');
INSERT INTO treemap_choices (id, field, value, key, key_type) VALUES (1, 'factoid', 'General', '1', 'int');
INSERT INTO treemap_choices (id, field, value, key, key_type) VALUES (33, 'sidewalk_damage', 'Minor or No Damage', '1', 'int');
INSERT INTO treemap_choices (id, field, value, key, key_type) VALUES (34, 'sidewalk_damage', 'Raised More Than 3/4 Inch', '2', 'int');
INSERT INTO treemap_choices (id, field, value, key, key_type) VALUES (35, 'condition', 'Dead', '1', 'int');
INSERT INTO treemap_choices (id, field, value, key, key_type) VALUES (36, 'condition', 'Critical', '2', 'int');
INSERT INTO treemap_choices (id, field, value, key, key_type) VALUES (37, 'condition', 'Poor', '3', 'int');
INSERT INTO treemap_choices (id, field, value, key, key_type) VALUES (38, 'condition', 'Fair', '4', 'int');
INSERT INTO treemap_choices (id, field, value, key, key_type) VALUES (39, 'condition', 'Good', '5', 'int');
INSERT INTO treemap_choices (id, field, value, key, key_type) VALUES (40, 'condition', 'Very Good', '6', 'int');
INSERT INTO treemap_choices (id, field, value, key, key_type) VALUES (41, 'condition', 'Excellent', '7', 'int');
INSERT INTO treemap_choices (id, field, value, key, key_type) VALUES (42, 'bool_set', 'Yes', 'True', 'bool');
INSERT INTO treemap_choices (id, field, value, key, key_type) VALUES (43, 'bool_set', 'No', 'False', 'bool');
INSERT INTO treemap_choices (id, field, value, key, key_type) VALUES (71, 'canopy_condition', 'Small Gaps (up to 25% missing)', '2', 'int');
INSERT INTO treemap_choices (id, field, value, key, key_type) VALUES (70, 'canopy_condition', 'Full - No Gaps', '1', 'int');
INSERT INTO treemap_choices (id, field, value, key, key_type) VALUES (72, 'canopy_condition', 'Moderate Gaps (up to 50% missing)', '3', 'int');
INSERT INTO treemap_choices (id, field, value, key, key_type) VALUES (73, 'canopy_condition', 'Large Gaps (up to 75% missing)', '4', 'int');
INSERT INTO treemap_choices (id, field, value, key, key_type) VALUES (74, 'canopy_condition', 'Little or None (up to 100% missing)', '5', 'int');
INSERT INTO treemap_choices (id, field, value, key, key_type) VALUES (75, 'plot_type', 'Other', '7', 'int');
INSERT INTO treemap_choices (id, field, value, key, key_type) VALUES (76, 'plot_type', 'Natural Area', '8', 'int');
INSERT INTO treemap_choices (id, field, value, key, key_type) VALUES (6, 'plot_type', 'Well or Pit', '1', 'int');
INSERT INTO treemap_choices (id, field, value, key, key_type) VALUES (7, 'plot_type', 'Median', '2', 'int');
INSERT INTO treemap_choices (id, field, value, key, key_type) VALUES (8, 'plot_type', 'Tree Lawn', '3', 'int');
INSERT INTO treemap_choices (id, field, value, key, key_type) VALUES (9, 'plot_type', 'Island', '4', 'int');
INSERT INTO treemap_choices (id, field, value, key, key_type) VALUES (10, 'plot_type', 'Planter', '5', 'int');
INSERT INTO treemap_choices (id, field, value, key, key_type) VALUES (11, 'plot_type', 'Open', '6', 'int');
INSERT INTO treemap_choices (id, field, value, key, key_type) VALUES (77, 'powerline_conflict_potential', 'Yes', '1', 'int');
INSERT INTO treemap_choices (id, field, value, key, key_type) VALUES (78, 'powerline_conflict_potential', 'No', '2', 'int');
INSERT INTO treemap_choices (id, field, value, key, key_type) VALUES (79, 'powerline_conflict_potential', 'Unknown', '3', 'int');

ALTER TABLE ONLY treemap_choices
    ADD CONSTRAINT treemap_choices_pkey PRIMARY KEY (id);

