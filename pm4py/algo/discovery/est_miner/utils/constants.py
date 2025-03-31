from enum import Enum

START_ACTIVITY = '[start>'
END_ACTIVITY = '[end]'

class ParameterNames(Enum):
    END_ACTIVITY                 = 'end_activity'
    START_ACTIVITY               = 'start_activity'
    LOG                          = 'log'
    NUM_TRACES                   = 'num_traces'
    ACTIVITIES                   = 'activities'
    IMPORTANT_TRACES             = 'important_traces'
    FITTING_PLACES               = 'fitting_places'
    ALLOWED_IN_ACTIVITIES        = 'allowed_in_activities'
    ALLOWED_OUT_ACTIVITIES       = 'allowed_out_activities'
    INTERESTING_PLACES_THRESHOLD = 'interesting_places_threshold'
    MAX_CONNECTED_ARCS           = 'max_connceted_arcs'
    REVERSE_MAPPING              = 'reverse_mapping'
