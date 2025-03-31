import os
import pathlib

from pm4py.objects.log.importer.xes import factory as xes_importer
from pm4py.algo.filtering.log.variants import variants_filter
from pm4py.algo.filtering.log.attributes import attributes_filter

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
    os.path.join(pathlib.Path.home(), 'Documents', 'Studium', 'Masterarbeit', 'experimental-eval', 'sepsis-ten-occ'),
    os.path.join(pathlib.Path.home(), 'Documents', 'Studium', 'Masterarbeit', 'experimental-eval', 'BPIChallenge'),
    os.path.join(pathlib.Path.home(), 'Documents', 'Studium', 'Masterarbeit', 'experimental-eval', 'teleclaims-mod'),
    os.path.join(pathlib.Path.home(), 'Documents', 'Studium', 'Masterarbeit', 'experimental-eval', 'rtfm-mod'),
    os.path.join(pathlib.Path.home(), 'Documents', 'Studium', 'Masterarbeit', 'experimental-eval', 'sepsis-filtered'),
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
    'sepsis-ten-occ.xes',
    'bpi-challenge-2017-reduced.xes',
    'teleclaims-mod.xes',
    'rtfm-mod.xes',
    'sepsis-filtered.xes',
    'hospital-billing.xes',
]

def analyse_logs():
    for i in range(len(data_set_paths)):
        path = data_set_paths[i]
        file_name = data_set_file_names[i]
        print(file_name)
        log = xes_importer.import_log(os.path.join(path, file_name))
        variants = variants_filter.get_variants(log)
        activities = attributes_filter.get_attribute_values(log, "concept:name")
        print('Trace variants: ' + str(len(variants)))
        print('Activities: ' + str(len(activities)))
        print('----------------------------------')

if __name__ == "__main__":
    analyse_logs() 
