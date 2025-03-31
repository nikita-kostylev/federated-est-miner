from datetime import datetime, time
import math
import pickle

from pm4py.algo.discovery.est_miner.utils.place import Place
import pm4py.algo.discovery.est_miner.utils.constants as const
from pm4py.algo.discovery.est_miner.utils.activity_order import max_element

time_transformation = {
    'ms': lambda time_in_seconds: time_in_seconds * 1000,
    's':  lambda time_in_seconds: time_in_seconds,
    'm':  lambda time_in_seconds: time_in_seconds / 60,
    'h':  lambda time_in_seconds: time_in_seconds / 3600
}

class RuntimeStatisticsLogger:

    def __init__(self, est_miner_name, transitions, input_order, output_order):
        self._est_miner_name       = est_miner_name
        self._transitions          = transitions
        self._input_order          = input_order
        self._output_order         = output_order
        self._blue_pruned_places   = list()
        self._red_pruned_places    = list()
        self._algo_start_time      = None
        self._algo_finish_time     = None
        self._search_start_time    = None
        self._search_finish_time   = None
        self._post_proc_start_time = None
        self._post_proc_fin_time   = None
        self._time_replaying       = None
        self._replay_start_time    = None
    
    @property
    def est_miner_name(self):
        return self._est_miner_name
    
    @property
    def algo_start_time(self):
        return self._algo_start_time
    
    @property
    def algo_finish_time(self):
        return self._algo_finish_time
    
    @property
    def search_start_time(self):
        return self._search_start_time
    
    @property
    def search_finish_time(self):
        return self._search_finish_time
    
    @property
    def post_proc_start_time(self):
        return self._post_proc_start_time
    
    @property
    def post_proc_finish_time(self):
        return self._post_proc_fin_time
    
    def replay_started(self):
        self._replay_start_time = self._now()
    
    def replay_finished(self):
        delta = self._now() - self._replay_start_time
        if (self._time_replaying is None):
            self._time_replaying = delta
        else:
            self._time_replaying += delta
    
    def replay_runtime(self, unit='ms'):
        return time_transformation[unit](self._time_replaying.total_seconds())
    
    def algo_started(self):
        self._algo_start_time = self._now()
    
    def algo_finished(self):
        self._algo_finish_time = self._now()
    
    def search_started(self):
        self._search_start_time = self._now()
    
    def search_finished(self):
        self._search_finish_time = self._now()
    
    def post_processing_started(self):
        self._post_proc_start_time = self._now()
    
    def post_processing_finished(self):
        self._post_proc_fin_time = self._now()
    
    def pruned_blue_subtree(self, place):
        self._blue_pruned_places.append(place.copy())
    
    def pruned_red_subtree(self, place):
        self._red_pruned_places.append(place.copy())
    
    def algo_runtime(self, unit='ms'):
        delta = self._algo_finish_time - self._algo_start_time
        return time_transformation[unit](delta.total_seconds())
    
    def search_runtime(self, unit='ms'):
        delta = self._search_finish_time - self._search_start_time
        return time_transformation[unit](delta.total_seconds())
    
    def post_processing_runtime(self, unit='ms'):
        delta = self._post_proc_fin_time - self._post_proc_start_time
        return time_transformation[unit](delta.total_seconds())
    
    def num_pruned_blue_places(self):
        num = 0
        for p in self._blue_pruned_places:
            num += self._blue_subtree_size(p)
        return num
    
    def num_pruned_red_places(self):
        num = 0
        for p in self._red_pruned_places:
            num += self._red_subtree_size(p)
        return num
    
    def total_pruned_places(self):
        return self.num_pruned_blue_places() + self.num_pruned_red_places()
    
    def to_file(self, path):
        with open(path, 'wb') as file:
            pickle.dump(self, file)
    
    def _blue_subtree_size(self, p):
        a_max = max_element(self._transitions, p.output_trans, self._output_order)
        missing_output_trans = set(self._output_order.is_larger_relations[a_max]).difference({const.START_ACTIVITY})
        return pow(2, len(missing_output_trans)) - 1
    
    def _red_subtree_size(self, p):
        if p.num_output_trans > 1:
            return 0
        else:
            a_max = max_element(self._transitions, p.input_trans, self._input_order)
            missing_input_trans = set(self._input_order.is_larger_relations[a_max]).difference({const.END_ACTIVITY})
            return pow(2, len(missing_input_trans)) - 1

    def _now(self):
        return datetime.now()

class ConformanceLogger:

    def __init__(self):
        self._fitness    = None
        self._precision  = None
        self._simplicity = None