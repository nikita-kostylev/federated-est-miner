import pandas

from pm4py import util as pmutil
from pm4py.objects.log.util import general as log_util
from pm4py.objects.log.util import xes as xes_util
from pm4py.objects.conversion.log import factory as log_conversion
from pm4py.algo.discovery.est_miner.versions import standard_est_miner, ip_est_miner
from pm4py.objects.log.importer import xes as xes_importer


LOCAL_FITNESS_THRESHOLD = 'tau'
GLOBAL_MIN_FITTING_TRACES = 'theta'
MIN_PLACES_INTEREST_SCORE = 'lambda'

STANDARD_EST_MINER = 'standard-est'
INTERESTING_PLACES_EST_MINER = 'ip-est'

DEFAULT_VARIANT = STANDARD_EST_MINER

VERSIONS = {STANDARD_EST_MINER: standard_est_miner.apply, INTERESTING_PLACES_EST_MINER: ip_est_miner.apply}

def apply(log, parameters=None, variant=DEFAULT_VARIANT):
    if parameters == None:
        parameters = {}
    parameters = add_defaults_for_unspecified_required_log_parameters(parameters)
    parameters = add_defaults_for_unspecified_required_est_parameters(parameters)
    return VERSIONS[variant](log, parameters=parameters)

def add_defaults_for_unspecified_required_log_parameters(parameters):
    if pmutil.constants.PARAMETER_CONSTANT_ACTIVITY_KEY not in parameters:
        parameters[pmutil.constants.PARAMETER_CONSTANT_ACTIVITY_KEY] = xes_util.DEFAULT_NAME_KEY
    if pmutil.constants.PARAMETER_CONSTANT_TIMESTAMP_KEY not in parameters:
        parameters[pmutil.constants.PARAMETER_CONSTANT_TIMESTAMP_KEY] = xes_util.DEFAULT_TIMESTAMP_KEY
    if pmutil.constants.PARAMETER_CONSTANT_CASEID_KEY not in parameters:
        parameters[pmutil.constants.PARAMETER_CONSTANT_CASEID_KEY] = log_util.CASE_ATTRIBUTE_GLUE
    if 'split' not in parameters:
        parameters['split'] = []
    return parameters

def add_defaults_for_unspecified_required_est_parameters(parameters):
    if LOCAL_FITNESS_THRESHOLD not in parameters:
        parameters[LOCAL_FITNESS_THRESHOLD] = 1.0
    if GLOBAL_MIN_FITTING_TRACES not in parameters:
        parameters[GLOBAL_MIN_FITTING_TRACES] = 0.0
    if MIN_PLACES_INTEREST_SCORE not in parameters:
        parameters[MIN_PLACES_INTEREST_SCORE] = 1.0
    return parameters

