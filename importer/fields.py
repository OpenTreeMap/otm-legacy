# X/Y are required
POINT_X = 'point x'
POINT_Y = 'point y'

# This is a pseudo field which is filled in
# when data is cleaned and contains a GEOS
# point object
POINT = 'calc__point'

# This is a pseudo field which is filled in
# when data is cleaned and may contain a
# OTM Species object, if the species was
# matched
SPECIES_OBJECT = 'calc__species_object'

# Plot Fields
ADDRESS = 'address'
PLOT_WIDTH = 'plot width'
PLOT_LENGTH = 'plot length'

READ_ONLY = 'read only'
OPENTREEMAP_ID_NUMBER = 'opentreemap id number'
ORIG_ID_NUMBER = 'original id number'

TREE_PRESENT = 'tree present'

# Choice fields
PLOT_TYPE = 'plot type'
POWERLINE_CONFLICT = 'powerline conflict'
SIDEWALK = 'sidewalk'

# Tree Fields
GENUS = 'genus'
SPECIES = 'species'
CULTIVAR = 'cultivar'
SCI_NAME = 'other part of scientific name'
DIAMETER = 'diameter'
TREE_HEIGHT = 'tree height'
CANOPY_HEIGHT = 'canopy height'
DATE_PLANTED = 'date planted'
DATA_SOURCE = 'data source'
OWNER = 'tree owner'
SPONSOR = 'tree sponsor'
STEWARD = 'tree steward'
NOTES = 'notes'
URL = 'tree url'

# Choice Fields
TREE_CONDITION = 'condition'
CANOPY_CONDITION = 'canopy condition'
ACTIONS = 'actions'
PESTS = 'pests and diseases'
LOCAL_PROJECTS = 'local projects'

# Some plot choice fields aren't automatically
# converting to choice values. This set determine
# which are pre-converted
PLOT_CHOICES = {
    PLOT_TYPE,
    SIDEWALK,
    POWERLINE_CONFLICT
}

CHOICE_MAP = {
    PLOT_TYPE: 'plot_types',
    POWERLINE_CONFLICT: 'powerlines',
    SIDEWALK: 'sidewalks',
    TREE_CONDITION: 'conditions',
    CANOPY_CONDITION: 'canopy_conditions',
    ACTIONS: 'actions',
    PESTS: 'pests',
    LOCAL_PROJECTS: 'projects'
}

ALL = { POINT_X, POINT_Y, ADDRESS, PLOT_WIDTH,
        PLOT_LENGTH, READ_ONLY, OPENTREEMAP_ID_NUMBER,
        TREE_PRESENT, PLOT_TYPE, POWERLINE_CONFLICT,
        SIDEWALK, GENUS, SPECIES, CULTIVAR,
        SCI_NAME, DIAMETER, ORIG_ID_NUMBER,
        CANOPY_HEIGHT, DATE_PLANTED, TREE_CONDITION,
        CANOPY_CONDITION, ACTIONS, PESTS,
        LOCAL_PROJECTS, URL, NOTES, OWNER,
        SPONSOR, STEWARD, DATA_SOURCE, TREE_HEIGHT }
