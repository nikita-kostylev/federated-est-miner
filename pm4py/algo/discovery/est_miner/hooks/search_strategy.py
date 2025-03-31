import abc
import copy
import logging
import multiprocessing

import pm4py.objects.log.util.log as log_util
from pm4py.algo.discovery.est_miner.utils.place import Place
from pm4py.algo.discovery.est_miner.utils.place_fitness \
import PlaceFitnessEvaluator, PlaceFitness
from pm4py.algo.discovery.est_miner.utils.activity_order \
import ActivityOrder, max_element, min_element
from pm4py.algo.discovery.est_miner.utils import est_utils
from pm4py.algo.discovery.est_miner.utils.constants import ParameterNames

class SearchStrategy(abc.ABC):

    @abc.abstractmethod
    def execute(
        self,
        log,
        tau,
        pre_pruning_strategy,
        in_order,
        out_order,
        activities,
        heuristic_parameters=None,
        logger=None,
        stat_logger=None
    ):
        """
        Strategy how to search through the candidate space,
        when to cut off search and where to start and finish.
        """
        pass

class TreeDfsStrategy(SearchStrategy):
    class RootExtractor:

        @classmethod
        def get_roots(cls, activities, pre_pruning_strategy, heuristic_parameters=None):
            roots = set()
            for a1 in activities:
                for a2 in activities:
                    p = Place(a1, a2, 1, 1)
                    if not pre_pruning_strategy.execute(p, parameters=heuristic_parameters):
                        roots.add(p)
            return roots
    
    def __init__(self, restricted_edge_type):
        assert(restricted_edge_type == 'red' or restricted_edge_type == 'blue')
        self._restricted_edge_type = restricted_edge_type
    
    def execute(
        self, 
        log, 
        tau, 
        pre_pruning_strategy, 
        in_order, 
        out_order, 
        activities, 
        heuristic_parameters=None, 
        logger=None, 
        stat_logger=None
    ):
        if (logger is not None):
            logger.info('Starting Search')
        roots = self.RootExtractor.get_roots(activities, pre_pruning_strategy, heuristic_parameters=heuristic_parameters)
        return self.traverse_roots(
            roots,
            log,
            tau,
            in_order,
            out_order,
            pre_pruning_strategy,
            activities,
            heuristic_parameters=heuristic_parameters,
            logger=logger,
            stat_logger=stat_logger
        )

    def traverse_roots(
        self,
        roots,
        log,
        tau,
        in_order,
        out_order,
        pre_pruning_strategy,
        activities,
        heuristic_parameters=None,
        logger=None,
        stat_logger=None
    ):
        fitting_places = list()
        args = list()
        print('Number of roots:',len(roots))
        for root in roots:
            #fitting_places.extend(self._traverse_place(log, tau, root, in_order, out_order, pre_pruning_strategy, activities, heuristic_parameters=heuristic_parameters))#, logger=logger, stat_logger=stat_logger))
            args.append( (log, tau, 0 ,root, in_order, out_order, pre_pruning_strategy, activities, heuristic_parameters) )
            
        with multiprocessing.Pool(processes=multiprocessing.cpu_count()) as pool:
            fitting_places = pool.starmap(self._traverse_place, args)
        
        flat_result = [p for fitting in fitting_places for p in fitting]
        return flat_result
        #return fitting_places
    
    def _traverse_place(
        self,
        log,
        tau,
        depth,
        place,
        in_order,
        out_order,
        pre_pruning_strategy,
        activities,
        heuristic_parameters=None,
        logger=None,
        stat_logger=None
    ):
        if logger is not None:
            logger.info('Checking node ' + place.name)
        
        if pre_pruning_strategy.execute(place, parameters=heuristic_parameters):
            if logger is not None:
                logger.info('    Pre-pruning the node.')
            return list()
        
        fitting_places = list()
        place_fitness_states = PlaceFitnessEvaluator.evaluate_place_fitness(
            log, 
            place, 
            tau
        )

        child_places = list()
        if PlaceFitness.FITTING in place_fitness_states:
            if logger is not None:
                logger.info('    Place is fitting.')
            fitting = True 
            for important_trace in heuristic_parameters[ParameterNames.IMPORTANT_TRACES]:
                involved, fitness_states = PlaceFitnessEvaluator.trace_fitness(important_trace, place)
                if involved and not PlaceFitness.FITTING in fitness_states:
                    fitting = False 
            if fitting:
                fitting_places.append(place)
        
        if (
            PlaceFitness.OVERFED not in place_fitness_states 
            or (self._restricted_edge_type == 'red' 
            and self._cant_prune_red_subtrees(place, out_order, activities))
        ): # nodes attached by red edge
            child_places.extend(self._get_red_child_places(place, in_order, activities))
        elif stat_logger is not None:
            stat_logger.pruned_red_subtree(place)
        if (
            PlaceFitness.UNDERFED not in place_fitness_states
            or (self._restricted_edge_type == 'blue'
            and self._cant_prune_blue_subtrees(place, in_order, activities))
        ): # nodes attached by blue edge
            child_places.extend(self._get_blue_child_places(place, out_order, activities))
        elif stat_logger is not None:
            stat_logger.pruned_blue_subtree(place)
        
        if logger is not None:
            if PlaceFitness.OVERFED in place_fitness_states:
                logger.info('    Place is overfed.')
            if PlaceFitness.UNDERFED in place_fitness_states:
                logger.info('    Place is underfed.')
            logger.info('    ' + str(len(child_places)) + ' child places.')
            for p in child_places:
                logger.info('    Child Place: ' + p.name)
        if(depth<2):
            for p in child_places:
                fitting_places.extend(self._traverse_place( 
                    log,
                    tau,
                    depth+1,
                    p,
                    in_order,
                    out_order,
                    pre_pruning_strategy,
                    activities,
                    heuristic_parameters=heuristic_parameters,
                    logger=logger,
                    stat_logger=stat_logger
                ))
        if(depth == 0): print(place.name)
        return fitting_places
        
    def _cant_prune_red_subtrees(self, place, out_order, activities):
        max_output_activity = max_element(activities, place.output_trans, out_order)
        return len(out_order.is_larger_relations[max_output_activity]) > 0
    
    def _cant_prune_blue_subtrees(self, place, in_order, activities):
        max_input_activity = max_element(place.input_trans, in_order, activities)
        return len(in_order.is_larger_relations[max_input_activity]) > 0
    
    def _get_red_child_places(self, place, in_order, activities):
        if (self._restricted_edge_type == 'red'):
            if (place.num_output_trans > 1):
                return list()
        
        child_places = list()
        max_input_activity = max_element(activities, place.input_trans, in_order)
        higher_ordered_activities = in_order.is_larger_relations[max_input_activity]
        for a in higher_ordered_activities:
            new_input_trans = copy.copy(place.input_trans)
            new_input_trans = new_input_trans | a
            num_input_trans = copy.copy(place.num_input_trans) + 1
            child_places.append(Place(new_input_trans, copy.copy(place.output_trans), num_input_trans, copy.copy(place.num_output_trans)))
        return child_places
    
    def _get_blue_child_places(self, place, out_order, activities):
        if (self._restricted_edge_type == 'blue'):
            if (place.num_input_trans > 1):
                return list()
        
        child_places = list()
        max_output_activity = max_element(activities, place.output_trans, out_order)
        higher_ordered_activities = out_order.is_larger_relations[max_output_activity]
        for a in higher_ordered_activities:
            new_output_trans = copy.copy(place.output_trans)
            new_output_trans = new_output_trans | a
            num_output_trans = copy.copy(place.num_output_trans) + 1
            child_places.append(Place(copy.copy(place.input_trans), new_output_trans, copy.copy(place.num_input_trans), num_output_trans))
        return child_places

class NoSearchStrategy(SearchStrategy):

    def execute(
        self, 
        log,
        key,
        tau,
        pre_pruning_strategy,
        in_order,
        out_order,
        activities
    ):
        print('Exectued Search')
        return None


class TreeDfsStrategyWithGaps(SearchStrategy):
    class RootExtractor:

        @classmethod
        def get_roots(cls, activities, pre_pruning_strategy, heuristic_parameters=None):
            roots = set()
            for a1 in activities:
                for a2 in activities:
                    p = Place(a1, a2, 1, 1)
                    if not pre_pruning_strategy.execute(p, parameters=heuristic_parameters):
                        roots.add(p)
            return roots
    
    def __init__(self, restricted_edge_type):
        assert(restricted_edge_type == 'red' or restricted_edge_type == 'blue')
        self._restricted_edge_type = restricted_edge_type
    
    def execute(
        self, 
        log, 
        tau, 
        pre_pruning_strategy, 
        in_order, 
        out_order, 
        activities, 
        heuristic_parameters=None, 
        logger=None, 
        stat_logger=None
    ):
        if (logger is not None):
            logger.info('Starting Search')
        roots = self.RootExtractor.get_roots(activities, pre_pruning_strategy, heuristic_parameters=heuristic_parameters)
        return self.traverse_roots(
            roots,
            log,
            tau,
            in_order,
            out_order,
            pre_pruning_strategy,
            activities,
            heuristic_parameters=heuristic_parameters,
            logger=logger,
            stat_logger=stat_logger
        )

    def traverse_roots(
        self,
        roots,
        log,
        tau,
        in_order,
        out_order,
        pre_pruning_strategy,
        activities,
        heuristic_parameters=None,
        logger=None,
        stat_logger=None
    ):
        fitting_places = list()
        args = list()
        print('Number of roots:',len(roots))
        for root in roots:
            #fitting_places.extend(self._traverse_place(log, tau, root, in_order, out_order, pre_pruning_strategy, activities, heuristic_parameters=heuristic_parameters))#, logger=logger, stat_logger=stat_logger))
            args.append( (log, tau, 0 ,root, in_order, out_order, pre_pruning_strategy, activities, heuristic_parameters) )
            
        with multiprocessing.Pool(processes=multiprocessing.cpu_count()) as pool:
            fitting_places = pool.starmap(self._traverse_place, args)
        
        flat_result = [p for fitting in fitting_places for p in fitting]
        return flat_result
        #return fitting_places
    
    def _traverse_place(
        self,
        log,
        tau,
        depth,
        place,
        in_order,
        out_order,
        pre_pruning_strategy,
        activities,
        heuristic_parameters=None,
        logger=None,
        stat_logger=None
    ):
        if logger is not None:
            logger.info('Checking node ' + place.name)
        
        if pre_pruning_strategy.execute(place, parameters=heuristic_parameters):
            if logger is not None:
                logger.info('    Pre-pruning the node.')
            return list()
        
        fitting_places = list()
        place_fitness_states = PlaceFitnessEvaluator.evaluate_place_fitness(
            log, 
            place, 
            tau
        )

        child_places = list()




        if PlaceFitness.FITTING in place_fitness_states:
            if logger is not None:
                logger.info('    Place is fitting.')
            fitting = True 
            for important_trace in heuristic_parameters[ParameterNames.IMPORTANT_TRACES]:
                involved, fitness_states = PlaceFitnessEvaluator.trace_fitness(important_trace, place)
                if involved and not PlaceFitness.FITTING in fitness_states:
                    fitting = False    

            if type(place)=="pm4py.objects.petri.petrinet.PetriNet.Place":        
                activities_involved = list(map(lambda x : x.source() , place.in_arcs) + map(lambda x : x.target() ,place.out_arcs))
            ignore = False
            

            places_test = []
            places_test_labels = []
            for key in heuristic_parameters['split']:
                places_test = [2**i for i, bit in enumerate(bin(place.input_trans)[:1:-1]) if bit == '1'] + [2**i for i, bit in enumerate(bin(place.output_trans)[:1:-1]) if bit == '1']
                places_test_labels = list(map(lambda x : heuristic_parameters[ParameterNames.REVERSE_MAPPING][x],places_test))
                if all(map(lambda x : x in heuristic_parameters['split'][key], places_test_labels)): 
                    ignore = True
            if fitting and not ignore:
                fitting_places.append(place)
        
        if (
            PlaceFitness.OVERFED not in place_fitness_states 
            or (self._restricted_edge_type == 'red' 
            and self._cant_prune_red_subtrees(place, out_order, activities))
        ): # nodes attached by red edge
            child_places.extend(self._get_red_child_places(place, in_order, activities))
        elif stat_logger is not None:
            stat_logger.pruned_red_subtree(place)
        if (
            PlaceFitness.UNDERFED not in place_fitness_states
            or (self._restricted_edge_type == 'blue'
            and self._cant_prune_blue_subtrees(place, in_order, activities))
        ): # nodes attached by blue edge
            child_places.extend(self._get_blue_child_places(place, out_order, activities))
        elif stat_logger is not None:
            stat_logger.pruned_blue_subtree(place)
        
        if logger is not None:
            if PlaceFitness.OVERFED in place_fitness_states:
                logger.info('    Place is overfed.')
            if PlaceFitness.UNDERFED in place_fitness_states:
                logger.info('    Place is underfed.')
            logger.info('    ' + str(len(child_places)) + ' child places.')
            for p in child_places:
                logger.info('    Child Place: ' + p.name)
        if(depth<2):
            for p in child_places:
                fitting_places.extend(self._traverse_place( 
                    log,
                    tau,
                    depth+1,
                    p,
                    in_order,
                    out_order,
                    pre_pruning_strategy,
                    activities,
                    heuristic_parameters=heuristic_parameters,
                    logger=logger,
                    stat_logger=stat_logger
                ))
        if(depth == 0): print("Following root finished:",place.name)
        return fitting_places
        
    def _cant_prune_red_subtrees(self, place, out_order, activities):
        max_output_activity = max_element(activities, place.output_trans, out_order)
        return len(out_order.is_larger_relations[max_output_activity]) > 0
    
    def _cant_prune_blue_subtrees(self, place, in_order, activities):
        max_input_activity = max_element(place.input_trans, in_order, activities)
        return len(in_order.is_larger_relations[max_input_activity]) > 0
    
    def _get_red_child_places(self, place, in_order, activities):
        if (self._restricted_edge_type == 'red'):
            if (place.num_output_trans > 1):
                return list()
        
        child_places = list()
        max_input_activity = max_element(activities, place.input_trans, in_order)
        higher_ordered_activities = in_order.is_larger_relations[max_input_activity]
        for a in higher_ordered_activities:
            new_input_trans = copy.copy(place.input_trans)
            new_input_trans = new_input_trans | a
            num_input_trans = copy.copy(place.num_input_trans) + 1
            child_places.append(Place(new_input_trans, copy.copy(place.output_trans), num_input_trans, copy.copy(place.num_output_trans)))
        return child_places
    
    def _get_blue_child_places(self, place, out_order, activities):
        if (self._restricted_edge_type == 'blue'):
            if (place.num_input_trans > 1):
                return list()
        
        child_places = list()
        max_output_activity = max_element(activities, place.output_trans, out_order)
        higher_ordered_activities = out_order.is_larger_relations[max_output_activity]
        for a in higher_ordered_activities:
            new_output_trans = copy.copy(place.output_trans)
            new_output_trans = new_output_trans | a
            num_output_trans = copy.copy(place.num_output_trans) + 1
            child_places.append(Place(copy.copy(place.input_trans), new_output_trans, copy.copy(place.num_input_trans), num_output_trans))
        return child_places

