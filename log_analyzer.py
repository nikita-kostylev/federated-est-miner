import pathlib
import os
import csv

from pm4py.objects.log.importer.xes import factory as xes_importer
from pm4py.algo.filtering.log.variants import variants_filter
from pm4py.algo.filtering.log.attributes import attributes_filter

data_set_paths = [
#    os.path.join(pathlib.Path.home(), 'Documents', 'Studium', 'Masterarbeit', 'experimental-eval', 'dominiks-log'),
#    os.path.join(pathlib.Path.home(), 'Documents', 'Studium', 'Masterarbeit', 'experimental-eval', 'artificial-xor-test-set'),
#    os.path.join(pathlib.Path.home(), 'Documents', 'Studium', 'Masterarbeit', 'experimental-eval', 'two-trans-set'),
#    os.path.join(pathlib.Path.home(), 'Documents', 'Studium', 'Masterarbeit', 'experimental-eval', 'repair-set'),
#    os.path.join(pathlib.Path.home(), 'Documents', 'Studium', 'Masterarbeit', 'experimental-eval', 'reviewing-set'),
#    os.path.join(pathlib.Path.home(), 'Documents', 'Studium', 'Masterarbeit', 'experimental-eval', 'teleclaims-set'),
#    os.path.join(pathlib.Path.home(), 'Documents', 'Studium', 'Masterarbeit', 'experimental-eval', 'sepsis-mod-set'),
    os.path.join(pathlib.Path.home(), 'Documents', 'Studium', 'Masterarbeit', 'experimental-eval', 'road-traffic-fine-set'),
    os.path.join(pathlib.Path.home(), 'Documents', 'Studium', 'Masterarbeit', 'experimental-eval', 'sepsis-pre-processed'),
#    os.path.join(pathlib.Path.home(), 'Documents', 'Studium', 'Masterarbeit', 'experimental-eval', 'basILP40'),
#    os.path.join(pathlib.Path.home(), 'Documents', 'Studium', 'Masterarbeit', 'experimental-eval', 'LogXOR-AND'),
#    os.path.join(pathlib.Path.home(), 'Documents', 'Studium', 'Masterarbeit', 'experimental-eval', 'LogXOR2'),
#    os.path.join(pathlib.Path.home(), 'Documents', 'Studium', 'Masterarbeit', 'experimental-eval', 'alpha++-fail1'),
]

data_set_file_names = [
#    'APM_Assignment_1.xes',
#    'Log-dependencyXOR1.xes',
#    'TwoActivities.xes',
#    'repairExample.xes',
#    'reviewing.xes',
#    'teleclaims.xes',
#    'sepsis.xes',
    'road-traffic-fines.xes',
    'Sepsis-doubletracesout.xes',
#    'test40.xes',
#    'Log-xor-and.xes',
#    'Log-dependencyXOR2.xes',
#    'alpha++fail1.xes',
]

def analyze_logs():
    for i in range(0, len(data_set_paths)):
        log = xes_importer.apply(os.path.join(data_set_paths[i], data_set_file_names[i]))
        variants = variants_filter.get_variants(log)
        print('Number of variants: ' + str(len(variants)))
        activities = attributes_filter.get_attribute_values(log, "concept:name")
        print('Number of activities: ' + str(len(activities)))

if __name__ == "__main__":
    analyze_logs()
