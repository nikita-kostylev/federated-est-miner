import pathlib
import os

from pm4py.algo.filtering.log.variants import variants_filter
from pm4py.algo.filtering.log.attributes import attributes_filter
from pm4py.statistics.traces.log import case_statistics
from pm4py.objects.log.importer.xes import factory as xes_importer
from pm4py.objects.log.exporter.xes import factory as xes_exporter
from pm4py.util import constants

data_set_paths = [
    os.path.join(pathlib.Path.home(), 'Documents', 'Studium', 'Masterarbeit', 'experimental-eval', 'dominiks-log'),
    os.path.join(pathlib.Path.home(), 'Documents', 'Studium', 'Masterarbeit', 'experimental-eval', 'artificial-xor-test-set'),
    os.path.join(pathlib.Path.home(), 'Documents', 'Studium', 'Masterarbeit', 'experimental-eval', 'two-trans-set'),
    os.path.join(pathlib.Path.home(), 'Documents', 'Studium', 'Masterarbeit', 'experimental-eval', 'repair-set'),
    os.path.join(pathlib.Path.home(), 'Documents', 'Studium', 'Masterarbeit', 'experimental-eval', 'reviewing-set'),
    os.path.join(pathlib.Path.home(), 'Documents', 'Studium', 'Masterarbeit', 'experimental-eval', 'teleclaims-set'),
    os.path.join(pathlib.Path.home(), 'Documents', 'Studium', 'Masterarbeit', 'experimental-eval', 'sepsis-mod-set'),
    os.path.join(pathlib.Path.home(), 'Documents', 'Studium', 'Masterarbeit', 'experimental-eval', 'road-traffic-fine-set'),
    os.path.join(pathlib.Path.home(), 'Documents', 'Studium', 'Masterarbeit', 'experimental-eval', 'sepsis-pre-processed'),
    os.path.join(pathlib.Path.home(), 'Documents', 'Studium', 'Masterarbeit', 'experimental-eval', 'basILP40'),
    os.path.join(pathlib.Path.home(), 'Documents', 'Studium', 'Masterarbeit', 'experimental-eval', 'LogXOR-AND'),
    os.path.join(pathlib.Path.home(), 'Documents', 'Studium', 'Masterarbeit', 'experimental-eval', 'LogXOR2'),
    os.path.join(pathlib.Path.home(), 'Documents', 'Studium', 'Masterarbeit', 'experimental-eval', 'alpha++-fail1'),
    os.path.join(pathlib.Path.home(), 'Documents', 'Studium', 'Masterarbeit', 'experimental-eval', 'one-choice-log'),
    os.path.join(pathlib.Path.home(), 'Downloads'),
    os.path.join(pathlib.Path.home(), 'Documents', 'Studium', 'Masterarbeit', 'experimental-eval', 'hospital-billing'),
]

data_set_file_names = [
    'APM_Assignment_1.xes',
    'Log-dependencyXOR1.xes',
    'TwoActivities.xes',
    'repairExample.xes',
    'reviewing.xes',
    'teleclaims.xes',
    'sepsis.xes',
    'road-traffic-fines.xes',
    'Sepsis-doubletracesout.xes',
    'test40.xes',
    'Log-xor-and.xes',
    'Log-dependencyXOR2.xes',
    'alpha++fail1.xes',
    'one-choice-log.xes',
    'bpi-challenge-2017.xes',
    'hospital-billing.xes',
]

def create_filtered_dataset(dataset_index,  required_freq, output_path, filtered_log_name):
    log = xes_importer.apply(os.path.join(data_set_paths[dataset_index], data_set_file_names[dataset_index]))
    filtered_log = get_trace_frequency_filtered_log(log, required_trace_freq=required_freq)
    xes_exporter.apply(filtered_log, os.path.join(output_path, filtered_log_name))

def get_trace_frequency_filtered_log(log, required_trace_freq=1):
    variants_count = case_statistics.get_variant_statistics(log)
    variants_count = sorted(variants_count, key=lambda x:x['count'], reverse=True)
    frequent_enough_traces = list()
    for variant_count in variants_count:
        if variant_count['count'] >= required_trace_freq:
            frequent_enough_traces.append(variant_count['variant'])
    filtered_log = variants_filter.apply(log, frequent_enough_traces)
    return filtered_log

def most_common_trace_variants(log, percentage=1):
    variants_count = case_statistics.get_variant_statistics(log)
    variants_count = sorted(variants_count, key=lambda x: x['count'], reverse=True)
    num_variants = len(variants_count)
    num_most_common_traces = round(percentage * num_variants)
    variants = list()
    for i in range(num_most_common_traces):
        variants.append(variants_count[i]['variant'])
    filtered_log = variants_filter.apply(log, variants)
    return filtered_log

def remove_n_least_common_events(log, n=0):
    activities = attributes_filter.get_attribute_values(log, "concept:name")
    print(activities)
    print(n)
    number_of_remaining_activities = len(activities) - n
    print(number_of_remaining_activities)
    kept_activities = list()
    for i in range(number_of_remaining_activities, len(activities)): 
        kept_activities.append(list(activities.keys())[i])
    print(kept_activities)
    print(len(kept_activities))
    filtered_log = attributes_filter.apply_events(log, kept_activities, parameters={
        constants.PARAMETER_CONSTANT_ATTRIBUTE_KEY: "concept:name",
        "positive": False 
    })
    activities = attributes_filter.get_attribute_values(filtered_log, "concept:name")
    print(activities)
    return filtered_log

if __name__ == "__main__":
    # Hospital Billing filtered
    #hospital_billing_filtered_path = os.path.join(pathlib.Path.home(), 'Documents', 'Studium', 'Masterarbeit',
    #        'experimental-eval', 'hospital-billing-filtered')
    #hospital_billing_filtered_file = 'hospital-billing-filtered.xes'
    #if not os.path.exists(hospital_billing_filtered_path):
    #    os.makedirs(hospital_billing_filtered_path)
    #log = xes_importer.apply(os.path.join(data_set_paths[15], data_set_file_names[15]))
    #filtered_log = get_trace_frequency_filtered_log(log, required_trace_freq=100)
    #xes_exporter.apply(filtered_log, os.path.join(hospital_billing_filtered_path, hospital_billing_filtered_file))

    # Sepsis filtered
    sepsis_at_least_ten_occ_path = os.path.join(pathlib.Path.home(), 'Documents', 'Studium', 'Masterarbeit', 
            'experimental-eval', 'sepsis-filtered')
    sepsis_at_least_ten_occ_file = 'sepsis-filtered.xes'
    if not os.path.exists(sepsis_at_least_ten_occ_path):
        os.makedirs(sepsis_at_least_ten_occ_path)
    ##create_filtered_dataset(6, 10, sepsis_at_least_ten_occ_path, sepsis_at_least_ten_occ_file)
    log = xes_importer.apply(os.path.join(data_set_paths[6], data_set_file_names[6]))
    filtered_log = remove_n_least_common_events(log, n=9)
    #filtered_log = most_common_trace_variants(log, percentage=0.01)
    xes_exporter.apply(filtered_log, os.path.join(sepsis_at_least_ten_occ_path, sepsis_at_least_ten_occ_file))

    # RTFM filtered
    #rtfm_at_least_one_hundred_path = os.path.join(pathlib.Path.home(), 'Documents', 'Studium', 'Masterarbeit',
    #        'experimental-eval', 'rtfm-mod')
    #rtfm_at_least_one_hundred_file = 'rtfm-mod.xes'
    #if not os.path.exists(rtfm_at_least_one_hundred_path):
    #    os.makedirs(rtfm_at_least_one_hundred_path)
    #log = xes_importer.apply(os.path.join(data_set_paths[7], data_set_file_names[7]))
    #filtered_log = most_common_trace_variants(log, percentage=0.05)
    #xes_exporter.apply(filtered_log, os.path.join(rtfm_at_least_one_hundred_path, rtfm_at_least_one_hundred_file))
    #create_filtered_dataset(7, 100, rtfm_at_least_one_hundred_path, rtfm_at_least_one_hundred_file)

    # BPI Challenge 2017
    #bpi_challenge_reduced_path = os.path.join(pathlib.Path.home(), 'Documents', 'Studium', 'Masterarbeit',
    #        'experimental-eval', 'BPIChallenge')
    #bpi_challenge_reduced_file = 'bpi-challenge-2017-reduced.xes'
    #if not os.path.exists(bpi_challenge_reduced_path):
    #    os.makedirs(bpi_challenge_reduced_path)
    #log = xes_importer.apply(os.path.join(data_set_paths[14], data_set_file_names[14]))
    #filtered_log = most_common_trace_variants(log, percentage=0.1)
    #xes_exporter.apply(filtered_log, os.path.join(bpi_challenge_reduced_path, bpi_challenge_reduced_file))
    #

    ## Teleclaims
    #teleclaims_mod_path = os.path.join(pathlib.Path.home(), 'Documents', 'Studium', 'Masterarbeit',
    #        'experimental-eval', 'teleclaims-mod')
    #teleclaims_mod_file = 'teleclaims-mod.xes'
    #if not os.path.exists(teleclaims_mod_path):
    #    os.makedirs(teleclaims_mod_path)
    #log = xes_importer.apply(os.path.join(data_set_paths[5], data_set_file_names[5])) 
    #filtered_log = attributes_filter.apply_events(log, ["end"], parameters={
    #    constants.PARAMETER_CONSTANT_ATTRIBUTE_KEY: "concept:name", "positive": False})
    #filtered_log = most_common_trace_variants(filtered_log, percentage=0.85)
    #xes_exporter.apply(filtered_log, os.path.join(teleclaims_mod_path, teleclaims_mod_file))

