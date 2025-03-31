import abc

from pm4py.algo.discovery.alpha import factory as alpha_factory
from pm4py.algo.discovery.est_miner.template.est_miner_template import EstMiner
from pm4py.algo.discovery.est_miner.hooks.pre_processing_strategy import NoPreProcessingStrategy

from pm4py.algo.discovery.est_miner.hooks.order_calculation_strategy \
import NoOrderCalculationStrategy, LexicographicalOrderStrategy, MaxUnderfedPlacesThroughAbsTraceFreqOrderStrategy, \
MaxUnderfedPlacesThroughRelativeTraceFreqOrderStrategy, MaxOverfedPlacesThroughAbsTraceFreqOrderStrategy, \
MaxOverfedPlacesThroughRelativeTraceFreqOrderStrategy, MaxUnderfedPlacesThroughAvgTraceOccOrderStrategy, \
MaxUnderfedPlacesThroughAFOIOrderStrategy, MaxCutoffsThroughAbsoluteActivityFreqOrderStrategy

from pm4py.algo.discovery.est_miner.hooks.search_strategy \
import NoSearchStrategy, TreeDfsStrategy, TreeDfsStrategyWithGaps

from pm4py.algo.discovery.est_miner.hooks.post_processing_strategy \
import NoPostProcessingStrategy, DeleteDuplicatePlacesPostProcessingStrategy, \
RemoveRedundantPlacesLPPostProcessingStrategy, RemoveRedundantAndImplicitPlacesPostProcessingStrategy, \
RemoveImplicitPlacesLPPostProcessingStrategy, RemoveConcurrentAndStructuralImplicitPlacesPostProcessingStrategy, \
RemoveImplicitPlacesPostProcessingStrategy, RemoveImplicitPlacesAndReduceArcsPostProcessingStrategy, RemoveImplicitPlacesPostProcessingStrategyModified

from pm4py.algo.discovery.est_miner.hooks.pre_pruning_strategy \
import NoPrePruningStrategy, PrePruneUselessPlacesStrategy, InterestingPlacesPrePruning, \
InterestingPlacesWithoutLoopsPrePruning, RestrictNumInputOutputTransPrePruning, \
ImportantTracesPrePruning, InterestingPlacesAndEnforeSimplicityPrePruningStrategy \
#SimilarColoredIngoingEdges, SimilarColoredShortestPath PruneSelfLoopsPrePruningStrategy TODO removed for compatibility, missing in original file

class EstMinerDirector:
    """
    Construct a new version of the EstMiner from the given
    as code description.
    """

    def __init__(self):
        self._builder = None
    
    def construct(self, builder):
        self._builder = builder
        self._builder.build_name()
        self._builder.build_pre_processing_strategy()
        self._builder.build_order_calculation_strategy()
        self._builder.build_pre_pruning_strategy()
        self._builder.build_search_strategy()
        self._builder.build_post_processing_strategy()

class EstMinerBuilder(abc.ABC):
    """
    Interface for defining how to construct different versions 
    of the EstMiner.
    """

    def __init__(self):
        self._est_miner = EstMiner()
    
    @property
    def est_miner(self):
        return self._est_miner

    @abc.abstractmethod
    def build_name(self):
        pass
    
    @abc.abstractmethod
    def build_pre_processing_strategy(self):
        pass
    
    @abc.abstractmethod
    def build_order_calculation_strategy(self):
        pass
    
    @abc.abstractmethod
    def build_pre_pruning_strategy(self):
        pass
    
    @abc.abstractmethod
    def build_search_strategy(self):
        pass
    
    @abc.abstractmethod
    def build_post_processing_strategy(self):
        pass
    

class TestEstMinerBuilder(EstMinerBuilder):

    def build_name(self):
        self.est_miner.name = 'TEM'

    def build_pre_processing_strategy(self):
        self.est_miner.pre_processing_strategy = NoPreProcessingStrategy()
    
    def build_order_calculation_strategy(self):
        self.est_miner.order_calculation_strategy = NoOrderCalculationStrategy()
    
    def build_pre_pruning_strategy(self):
        self.est_miner.pre_pruning_strategy = NoPrePruningStrategy()
    
    def build_search_strategy(self):
        self.est_miner.search_strategy = NoSearchStrategy()
    
    def build_post_processing_strategy(self):
        self.est_miner.post_processing_strategy = NoPostProcessingStrategy()

class StandardEstMinerBuilder(EstMinerBuilder):

    def build_name(self):
        self.est_miner.name = 'eST-Miner'

    def build_pre_processing_strategy(self):
        self.est_miner.pre_processing_strategy = NoPreProcessingStrategy()

    def build_order_calculation_strategy(self):
        self.est_miner.order_calculation_strategy = LexicographicalOrderStrategy()
    
    def build_pre_pruning_strategy(self):
        self.est_miner.pre_pruning_strategy = PrePruneUselessPlacesStrategy()
    
    def build_search_strategy(self):
        self.est_miner.search_strategy = TreeDfsStrategy(restricted_edge_type='red')
    
    def build_post_processing_strategy(self):
        self.est_miner.post_processing_strategy = RemoveImplicitPlacesPostProcessingStrategy()
        #self.est_miner.post_processing_strategy = NoPostProcessingStrategy()

class MaxCutoffsAbsoluteActivityFrequencyEstMinerBuilder(EstMinerBuilder):

    def build_name(self):
        self.est_miner.name = 'abs_activity_freq'

    def build_pre_processing_strategy(self):
        self.est_miner.pre_processing_strategy = NoPreProcessingStrategy()

    def build_order_calculation_strategy(self):
        self.est_miner.order_calculation_strategy = MaxCutoffsThroughAbsoluteActivityFreqOrderStrategy()
    
    def build_pre_pruning_strategy(self):
        self.est_miner.pre_pruning_strategy = PrePruneUselessPlacesStrategy()
    
    def build_search_strategy(self):
        self.est_miner.search_strategy = TreeDfsStrategy(restricted_edge_type='red')
    
    def build_post_processing_strategy(self):
        self.est_miner.post_processing_strategy = RemoveImplicitPlacesPostProcessingStrategy() 

class MaxCutoffsAbsoluteTraceFrequencyEstMinerBuilder(EstMinerBuilder):

    def build_name(self):
        self.est_miner.name = 'abs_trace_freq'

    def build_pre_processing_strategy(self):
        self.est_miner.pre_processing_strategy = NoPreProcessingStrategy()

    def build_order_calculation_strategy(self):
        self.est_miner.order_calculation_strategy = MaxUnderfedPlacesThroughAbsTraceFreqOrderStrategy()
    
    def build_pre_pruning_strategy(self):
        self.est_miner.pre_pruning_strategy = PrePruneUselessPlacesStrategy()
    
    def build_search_strategy(self):
        self.est_miner.search_strategy = TreeDfsStrategy(restricted_edge_type='red')
    
    def build_post_processing_strategy(self):
        self.est_miner.post_processing_strategy = RemoveImplicitPlacesPostProcessingStrategy()

class MaxCutoffsAverageTraceOccurrenceEstMinerBuilder(EstMinerBuilder):

    def build_name(self):
        self.est_miner.name = 'avg_trace_occ'

    def build_pre_processing_strategy(self):
        self.est_miner.pre_processing_strategy = NoPreProcessingStrategy()

    def build_order_calculation_strategy(self):
        self.est_miner.order_calculation_strategy = MaxUnderfedPlacesThroughAvgTraceOccOrderStrategy()
    
    def build_pre_pruning_strategy(self):
        self.est_miner.pre_pruning_strategy = PrePruneUselessPlacesStrategy()
    
    def build_search_strategy(self):
        self.est_miner.search_strategy = TreeDfsStrategy(restricted_edge_type='red')
    
    def build_post_processing_strategy(self):
        self.est_miner.post_processing_strategy = RemoveImplicitPlacesPostProcessingStrategy()

class MaxCutoffsAverageFirstOccurrenceIndexEstMinerBuilder(EstMinerBuilder):

    def build_name(self):
        self.est_miner.name = 'avg_first_occ_index'

    def build_pre_processing_strategy(self):
        self.est_miner.pre_processing_strategy = NoPreProcessingStrategy()

    def build_order_calculation_strategy(self):
        self.est_miner.order_calculation_strategy = MaxUnderfedPlacesThroughAFOIOrderStrategy()
    
    def build_pre_pruning_strategy(self):
        self.est_miner.pre_pruning_strategy = PrePruneUselessPlacesStrategy()
    
    def build_search_strategy(self):
        self.est_miner.search_strategy = TreeDfsStrategy(restricted_edge_type='red')
    
    def build_post_processing_strategy(self):
        self.est_miner.post_processing_strategy = RemoveImplicitPlacesPostProcessingStrategy()

class MaxCutoffsAbsFreqEstMinerBuilder(EstMinerBuilder):

    def build_name(self):
        self.est_miner.name = 'MUAEM'

    def build_pre_processing_strategy(self):
        self.est_miner.pre_processing_strategy = NoPreProcessingStrategy()

    def build_order_calculation_strategy(self):
        self.est_miner.order_calculation_strategy = MaxUnderfedPlacesThroughAbsTraceFreqOrderStrategy()
    
    def build_pre_pruning_strategy(self):
        self.est_miner.pre_pruning_strategy = PrePruneUselessPlacesStrategy()
    
    def build_search_strategy(self):
        self.est_miner.search_strategy = TreeDfsStrategy(restricted_edge_type='red')
    
    def build_post_processing_strategy(self):
        self.est_miner.post_processing_strategy = RemoveImplicitPlacesPostProcessingStrategy()

class MaxCutoffsRelTraceFreqEstMinerBuilder(EstMinerBuilder):

    def build_name(self):
        self.est_miner.name = 'MUREM'
    
    def build_pre_processing_strategy(self):
        self.est_miner.pre_processing_strategy = NoPreProcessingStrategy()

    def build_order_calculation_strategy(self):
        self.est_miner.order_calculation_strategy = MaxUnderfedPlacesThroughRelativeTraceFreqOrderStrategy()
    
    def build_pre_pruning_strategy(self):
        self.est_miner.pre_pruning_strategy = PrePruneUselessPlacesStrategy()
    
    def build_search_strategy(self):
        self.est_miner.search_strategy = TreeDfsStrategy(restricted_edge_type='red')
    
    def build_post_processing_strategy(self):
        self.est_miner.post_processing_strategy = RemoveImplicitPlacesPostProcessingStrategy()

class MaxUnderfedAvgFirstOccIndexEstMinerBuilder(EstMinerBuilder):

    def build_name(self):
        self.est_miner.name = 'MUAFOIEM'
    
    def build_pre_processing_strategy(self):
        self.est_miner.pre_processing_strategy = NoPreProcessingStrategy()
    
    def build_order_calculation_strategy(self):
        self.est_miner.order_calculation_strategy = MaxUnderfedPlacesThroughAFOIOrderStrategy()
    
    def build_pre_pruning_strategy(self):
        self.est_miner.pre_pruning_strategy = PrePruneUselessPlacesStrategy()
    
    def build_search_strategy(self):
        self.est_miner.search_strategy = TreeDfsStrategy(restricted_edge_type='red')
    
    def build_post_processing_strategy(self):
        self.est_miner.post_processing_strategy = RemoveImplicitPlacesPostProcessingStrategy()

class MaxUnderfedAvgTraceOccEstMinerBuilder(EstMinerBuilder):

    def build_name(self):
        self.est_miner.name = 'MUATOEM'
    
    def build_pre_processing_strategy(self):
        self.est_miner.pre_processing_strategy = NoPreProcessingStrategy()
    
    def build_order_calculation_strategy(self):
        self.est_miner.order_calculation_strategy = MaxUnderfedPlacesThroughAvgTraceOccOrderStrategy()
    
    def build_pre_pruning_strategy(self):
        self.est_miner.pre_pruning_strategy = PrePruneUselessPlacesStrategy()
    
    def build_search_strategy(self):
        self.est_miner.search_strategy = TreeDfsStrategy(restricted_edge_type='red')
    
    def build_post_processing_strategy(self):
        #self.est_miner.post_processing_strategy = RemoveConcurrentAndStructuralImplicitPlacesPostProcessingStrategy()
        self.est_miner.post_processing_strategy = RemoveImplicitPlacesPostProcessingStrategy()

class RestrictBlueEdgesAndMaxCutoffsAbsTraceFreqEstMinerBuilder(EstMinerBuilder):

    def build_name(self):
        self.est_miner.name = 'MOAEM'
    
    def build_pre_processing_strategy(self):
        self.est_miner.pre_processing_strategy = NoPreProcessingStrategy()
    
    def build_order_calculation_strategy(self):
        self.est_miner.order_calculation_strategy = MaxOverfedPlacesThroughAbsTraceFreqOrderStrategy()
    
    def build_pre_pruning_strategy(self):
        self.est_miner.pre_pruning_strategy = PrePruneUselessPlacesStrategy()
    
    def build_search_strategy(self):
        self.est_miner.search_strategy = TreeDfsStrategy(restricted_edge_type='blue')
    
    def build_post_processing_strategy(self):
        self.est_miner.post_processing_strategy = RemoveImplicitPlacesPostProcessingStrategy()

# class AlphaMinerRefinementSearchEstMinerBuilder(EstMinerBuilder):

#     def build_name(self):
#         self.est_miner.name = 'AMRS'
    
#     def build_pre_processing_strategy(self):
#         self.est_miner.pre_processing_strategy = NoPreProcessingStrategy()

#     def build_order_calculation_strategy(self):
#         self.est_miner.order_calculation_strategy = MaxUnderfedPlacesThroughAbsTraceFreqOrderStrategy()
    
#     def build_pre_pruning_strategy(self):
#         self.est_miner.pre_pruning_strategy = PrePruneUselessPlacesStrategy()
    
#     def build_search_strategy(self):
#         self.est_miner.search_strategy = RefinementSearch(alpha_factory)
    
#     def build_post_processing_strategy(self):
#         self.est_miner.post_processing_strategy = RemoveConcurrentAndStructuralImplicitPlacesPostProcessingStrategy()

class InterestingPlacesEstMinerBuilder(EstMinerBuilder):

    def build_name(self):
        self.est_miner.name = 'ip-eST'
    
    def build_pre_processing_strategy(self):
        self.est_miner.pre_processing_strategy = NoPreProcessingStrategy()
    
    def build_order_calculation_strategy(self):
        self.est_miner.order_calculation_strategy = MaxUnderfedPlacesThroughAFOIOrderStrategy()
    
    def build_pre_pruning_strategy(self):
        self.est_miner.pre_pruning_strategy = InterestingPlacesPrePruning()
    
    def build_search_strategy(self):
        self.est_miner.search_strategy = TreeDfsStrategy(restricted_edge_type='red')
    
    def build_post_processing_strategy(self):
        self.est_miner.post_processing_strategy = RemoveImplicitPlacesPostProcessingStrategy()
        #self.est_miner.post_processing_strategy = NoPostProcessingStrategy()

class AlternativeInterestingPlacesEstMinerBuilder(EstMinerBuilder):

    def build_name(self):
        self.est_miner.name = 'AIPEM'
    
    def build_pre_processing_strategy(self):
        self.est_miner.pre_processing_strategy = NoPreProcessingStrategy()

    def build_order_calculation_strategy(self):
        self.est_miner.order_calculation_strategy = MaxUnderfedPlacesThroughAFOIOrderStrategy()
    
    def build_pre_pruning_strategy(self):
        self.est_miner.pre_pruning_strategy = InterestingPlacesWithoutLoopsPrePruning()
    
    def build_search_strategy(self):
        self.est_miner.search_strategy = TreeDfsStrategy(restricted_edge_type='red')
    
    def build_post_processing_strategy(self):
        self.est_miner.post_processing_strategy = RemoveImplicitPlacesPostProcessingStrategy()

class RestrictNumInAndOutTransitionsEstMinerBuilder(EstMinerBuilder):

    def build_name(self):
        self.est_miner.name  ='RNIOTEM'
    
    def build_pre_processing_strategy(self):
        self.est_miner.pre_processing_strategy = NoPreProcessingStrategy()

    def build_order_calculation_strategy(self):
        self.est_miner.order_calculation_strategy = MaxUnderfedPlacesThroughAFOIOrderStrategy()

    def build_pre_pruning_strategy(self):
        self.est_miner.pre_pruning_strategy = RestrictNumInputOutputTransPrePruning()
    
    def build_search_strategy(self):
        self.est_miner.search_strategy = TreeDfsStrategy(restricted_edge_type='red')
    
    def build_post_processing_strategy(self):
        self.est_miner.post_processing_strategy = RemoveImplicitPlacesPostProcessingStrategy()

class ImportantTracesEstMinerBuilder(EstMinerBuilder):

    def build_name(self):
        self.est_miner.name = 'ITEM'
    
    def build_pre_processing_strategy(self):
        self.est_miner.pre_processing_strategy = NoPreProcessingStrategy()
    
    def build_order_calculation_strategy(self):
        #self.est_miner.order_calculation_strategy = MaxUnderfedPlacesThroughAFOIOrderStrategy()
        self.est_miner.order_calculation_strategy = MaxUnderfedPlacesThroughAvgTraceOccOrderStrategy()
    
    def build_pre_pruning_strategy(self):
        self.est_miner.pre_pruning_strategy = ImportantTracesPrePruning()
    
    def build_search_strategy(self):
        self.est_miner.search_strategy = TreeDfsStrategy(restricted_edge_type='red')
    
    def build_post_processing_strategy(self):
        self.est_miner.post_processing_strategy = RemoveImplicitPlacesPostProcessingStrategy()
        #self.est_miner.post_processing_strategy = NoPostProcessingStrategy()

class ImportantPlacesPrePruningAndEnforcedSimplicityEstMinerBuilder(EstMinerBuilder):

    def build_name(self):
        self.est_miner.name = 'IPPESEM'

    def build_pre_processing_strategy(self):
        self.est_miner.pre_processing_strategy = NoPreProcessingStrategy()

    def build_order_calculation_strategy(self):
        self.est_miner.order_calculation_strategy = MaxUnderfedPlacesThroughAvgTraceOccOrderStrategy()

    def build_pre_pruning_strategy(self):
        self.est_miner.pre_pruning_strategy = InterestingPlacesAndEnforeSimplicityPrePruningStrategy()

    def build_search_strategy(self):
        self.est_miner.search_strategy = TreeDfsStrategy(restricted_edge_type='red')

    def build_post_processing_strategy(self):
        self.est_miner.post_processing_strategy = RemoveImplicitPlacesPostProcessingStrategy()

class PrePruningAndReduceComplexityPostProcessingEstMinerBuilder(EstMinerBuilder):

    def build_name(self):
        self.est_miner.name = 'RCEM'

    def build_pre_processing_strategy(self):
        self.est_miner.pre_processing_strategy = NoPreProcessingStrategy()

    def build_order_calculation_strategy(self):
        self.est_miner.order_calculation_strategy = MaxUnderfedPlacesThroughAvgTraceOccOrderStrategy()

    def build_pre_pruning_strategy(self):
        self.est_miner.pre_pruning_strategy = InterestingPlacesPrePruning()

    def build_search_strategy(self):
        self.est_miner.search_strategy = TreeDfsStrategy(restricted_edge_type='red')

    def build_post_processing_strategy(self):
        self.est_miner.post_processing_strategy = RemoveImplicitPlacesAndReduceArcsPostProcessingStrategy()



""" Not working because of missing PruneSelfLoopsPrePruniningStrategy   TODO Removed for compatibility

class IntersetingPlacesAntiSelfLoopsEstMinerBuilder(EstMinerBuilder):

    def build_name(self):
        self.est_miner.name = 'nslipeST'

    def build_pre_processing_strategy(self):
        self.est_miner.pre_processing_strategy = NoPreProcessingStrategy()

    def build_order_calculation_strategy(self):
        self.est_miner.order_calculation_strategy = MaxUnderfedPlacesThroughAvgTraceOccOrderStrategy()

    def build_pre_pruning_strategy(self):
        self.est_miner.pre_pruning_strategy = PruneSelfLoopsPrePruningStrategy()

    def build_search_strategy(self):
        self.est_miner.search_strategy = TreeDfsStrategy(restricted_edge_type='red')

    def build_post_processing_strategy(self):
        self.est_miner.post_processing_strategy = RemoveImplicitPlacesAndReduceArcsPostProcessingStrategy() 
"""




"""class ColoredDfgEstMinerBuilder(EstMinerBuilder):   TODO removed for compatibility


    def build_name(self):
        self.est_miner.name = 'coloredeST'
    
    def build_pre_processing_strategy(self):
        self.est_miner.pre_processing_strategy = NoPreProcessingStrategy()

    def build_order_calculation_strategy(self):
        self.est_miner.order_calculation_strategy = MaxUnderfedPlacesThroughAvgTraceOccOrderStrategy()

    def build_pre_pruning_strategy(self):
        self.est_miner.pre_pruning_strategy = SimilarColoredShortestPath()    #this function is missing and cannot be imported

    def build_search_strategy(self):
        self.est_miner.search_strategy = TreeDfsStrategy(restricted_edge_type='red')

    def build_post_processing_strategy(self):
        self.est_miner.post_processing_strategy = RemoveImplicitPlacesPostProcessingStrategy()"""


class ModifiedStandardEstMinerBuilder(EstMinerBuilder):

    def build_name(self):
        self.est_miner.name = 'ModiTest'

    def build_pre_processing_strategy(self):
        self.est_miner.pre_processing_strategy = NoPreProcessingStrategy()

    def build_order_calculation_strategy(self):
        self.est_miner.order_calculation_strategy = MaxCutoffsThroughAbsoluteActivityFreqOrderStrategy()

    
    def build_pre_pruning_strategy(self):
        self.est_miner.pre_pruning_strategy = PrePruneUselessPlacesStrategy()
    
    def build_search_strategy(self):
        #self.est_miner.search_strategy = TreeDfsStrategyWithGaps(restricted_edge_type='red')  IGNORE due to test. Old tree strategy with new Post processing
        self.est_miner.search_strategy = TreeDfsStrategy(restricted_edge_type='red')
    
    def build_post_processing_strategy(self):
        self.est_miner.post_processing_strategy = RemoveImplicitPlacesPostProcessingStrategyModified()
        #self.est_miner.post_processing_strategy = RemoveImplicitPlacesPostProcessingStrategy()   USE OTHER VERSION TEMPORARY
        #self.est_miner.post_processing_strategy = NoPostProcessingStrategy()