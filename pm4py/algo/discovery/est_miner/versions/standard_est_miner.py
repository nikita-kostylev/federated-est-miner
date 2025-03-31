from pm4py.algo.discovery.est_miner.builder import EstMinerDirector, EstMinerBuilder
from pm4py.algo.discovery.est_miner.hooks.pre_processing_strategy import NoPreProcessingStrategy
from pm4py.algo.discovery.est_miner.hooks.order_calculation_strategy import LexicographicOrderStrategy

def apply(log, parameters=None):
    standard_est_miner = get_standard_est_miner()
    net, initial_marking, final_marking = standard_est_miner.apply(log, parameters=parameters)
    return net, initial_marking, final_marking

def get_standard_est_miner():
    est_miner_director = EstMinerDirector()
    standard_est_miner_builder = StandardEstMinerBuilder()
    standard_est_miner = est_miner_director.construct(standard_est_miner_builder)
    return standard_est_miner

class StandardEstMinerBuilder(EstMinerBuilder):

    def build_name(self):
        self.est_miner.name = 'standard-est-miner'

    def build_pre_processing_strategy(self):
        self.est_miner.pre_processing_strategy = NoPreProcessingStrategy()

    def build_order_calculation_strategy(self):
        self.est_miner.order_calculation_strategy = LexicographicalOrderStrategy()
    
    def build_pre_pruning_strategy(self):
        self.est_miner.pre_pruning_strategy = PrePruneUselessPlacesStrategy()
    
    def build_search_strategy(self):
        self.est_miner.search_strategy = TreeDfsStrategy()
    
    def build_post_processing_strategy(self):
        self.est_miner.post_processing_strategy = RemoveImplicitPlacesPostProcessingStrategy()

