import time

from pm4py.algo.discovery.est_miner.utils import est_utils
from pm4py.algo.discovery.est_miner.utils import constants as const
import pm4py.objects.log.util.log as log_util
from pm4py.objects import petri
from pm4py.objects.petri.petrinet import Marking
from pm4py.objects.petri.petrinet import PetriNet
from pm4py.algo.discovery.est_miner.utils.place import Place
from pm4py.algo.discovery.est_miner.utils.constants import ParameterNames

from experiments.logging.logger import RuntimeStatisticsLogger

class EstMiner:

    def __init__(self):
        self._name = None
        self._pre_processing_strategy = None
        self._order_calculation_strategy = None
        self._pre_pruning_strategy = None
        self._search_strategy = None
        self._post_processing_strategy = None
    
    @property
    def name(self):
        return self._name
    
    @name.setter
    def name(self, name):
        self._name = name
    
    @property
    def pre_processing_strategy(self):
        return self._pre_processing_strategy
    
    @pre_processing_strategy.setter
    def pre_processing_strategy(self, strategy):
        self._pre_processing_strategy = strategy
    
    @property
    def order_calculation_strategy(self):
        return self._order_calculation_strategy

    @order_calculation_strategy.setter
    def order_calculation_strategy(self, strategy):
        self._order_calculation_strategy = strategy
    
    @property
    def pre_pruning_strategy(self):
        return self._pre_pruning_strategy

    @pre_pruning_strategy.setter
    def pre_pruning_strategy(self, strategy):
        self._pre_pruning_strategy = strategy
    
    @property
    def search_strategy(self):
        return self._search_strategy

    @search_strategy.setter
    def search_strategy(self, strategy):
        self._search_strategy = strategy
    
    @property
    def post_processing_strategy(self):
        return self._post_processing_strategy

    @post_processing_strategy.setter
    def post_processing_strategy(self, strategy):
        self._post_processing_strategy = strategy

    def apply(self, log, parameters=None, logger=None):
        """
        This method executes the current version of the est miner configured
        through the builder pattern [1].

        Paramters:
        ----------
        log: :class:`pm4py.log.log.EventLog`
            Event log to use in the est-miner
        parameters:
            Parameters for the algorithm:
                - tau: Noise filtering technique (see paper)
        Returns
        -------
        net: :class:`pm4py.entities.petri.petrinet.PetriNet`
        A Petri net describing the event log that is provided as an input
        initial marking: :class:`pm4py.models.net.Marking`
        marking object representing the initial marking
        final marking: :class:`pm4py.models.net.Marking`
        marking object representing the final marking, not guaranteed that it is actually reachable!

        References
        ----------
        Lisa L. Mannel, Wil M. P. van der Aalst, "Finding Complex Process-Structures by Exploiting
        the Token-Game"
        """
        self._ready_for_execution_invariant()
        log = self.pre_processing_strategy.execute(log)

        #ab hier stressing

        log = est_utils.insert_unique_start_and_end_activity(log)
        optimized_for_replay_log, activities, start_activity, end_activity, reverse_mapping = est_utils.optimize_for_replay(log, parameters['key'])
        #most_common_traces = est_utils.most_common_traces(optimized_for_replay_log, num_most_common=0)
        most_common_traces = est_utils.get_most_common_traces_quantil(optimized_for_replay_log, quantil=0.8)
        most_important_traces_including_all_activties = est_utils.most_important_traces_including_all_activities(optimized_for_replay_log, activities)
        print(most_common_traces)
        in_order, out_order = self.order_calculation_strategy.execute(optimized_for_replay_log, activities)
        stat_logger = RuntimeStatisticsLogger(self.name, activities, in_order, out_order)
        heuristic_parameters = {
            ParameterNames.ACTIVITIES:                   activities,
            ParameterNames.ALLOWED_IN_ACTIVITIES:        2,
            ParameterNames.ALLOWED_OUT_ACTIVITIES:       3,
            ParameterNames.START_ACTIVITY:               start_activity,
            ParameterNames.END_ACTIVITY:                 end_activity,
            ParameterNames.INTERESTING_PLACES_THRESHOLD: 1.0,
            ParameterNames.LOG:                          optimized_for_replay_log,
            ParameterNames.NUM_TRACES:                   len(log),
            ParameterNames.FITTING_PLACES:               list(),
            ParameterNames.IMPORTANT_TRACES:             [],#most_common_traces,
            ParameterNames.REVERSE_MAPPING:              reverse_mapping,
            ParameterNames.MAX_CONNECTED_ARCS:           2,
            'split':                                     parameters.get("split", {})
        }


        #ab hier gut

        self.pre_pruning_strategy.initialize(parameters=heuristic_parameters)
        stat_logger.algo_started()
        stat_logger.search_started()

        #hier vllt ändern

        candidate_places = self.search_strategy.execute(
            optimized_for_replay_log,
            parameters['tau'],
            self.pre_pruning_strategy,
            in_order,
            out_order,
            activities,
            heuristic_parameters=heuristic_parameters,
            logger=logger,
            stat_logger=stat_logger
        )


        #alles clear


        stat_logger.search_finished()
        stat_logger.post_processing_started()

        resulting_places = self.post_processing_strategy.execute(
            candidate_places,
            parameters=heuristic_parameters,
            logger=logger
        )
        #resulting_places = candidate_places
        stat_logger.post_processing_finished()
        stat_logger.algo_finished()
        net, src, sink = self._construct_net(log, activities, resulting_places, reverse_mapping)
        return net, Marking({src: 1}), Marking({sink: 1}), stat_logger

    async def asyncapply(self, log, activities, parameters=None, logger=None):
        """
        This method executes the current version of the est miner configured
        through the builder pattern [1].

        Paramters:
        ----------
        log: :class:`pm4py.log.log.EventLog`
            Event log to use in the est-miner
        parameters:
            Parameters for the algorithm:
                - tau: Noise filtering technique (see paper)
        Returns
        -------
        net: :class:`pm4py.entities.petri.petrinet.PetriNet`
        A Petri net describing the event log that is provided as an input
        initial marking: :class:`pm4py.models.net.Marking`
        marking object representing the initial marking
        final marking: :class:`pm4py.models.net.Marking`
        marking object representing the final marking, not guaranteed that it is actually reachable!

        References
        ----------
        Lisa L. Mannel, Wil M. P. van der Aalst, "Finding Complex Process-Structures by Exploiting
        the Token-Game"
        """
        self._ready_for_execution_invariant()
        log = self.pre_processing_strategy.execute(log)

        log = [[0] + trace + [1] for trace in log]

        #events = log_util.get_event_labels(log, key) einf nur die activities
        events_to_bitmasks = dict()
        bitmasks_to_events = dict()
        activitiesnum = list()
        start_activity     = 0
        end_activity       = 0
        for i in range(len(activities)):
            bitmask = ''
            for j in range(len(activities)):
                if (i == j):
                    bitmask += '1'
                else:
                    bitmask += '0'
            encoded_event = int(bitmask, 2)
            events_to_bitmasks[activities[i]] = encoded_event # Encoded as integer
            bitmasks_to_events[encoded_event] = activities[i]
            if (activities[i] == "[start>"):
                start_activity = encoded_event
            if (activities[i] == "[end]"):
                end_activity = encoded_event
            activitiesnum.append(encoded_event)
        print(activities)
        print(events_to_bitmasks)
        print(activitiesnum)
        
        in_order, out_order = self.order_calculation_strategy.execute(log, activitiesnum)  
        stat_logger = RuntimeStatisticsLogger(self.name, activities, in_order, out_order)
        heuristic_parameters = {
            ParameterNames.ACTIVITIES:                   activitiesnum,
            ParameterNames.ALLOWED_IN_ACTIVITIES:        2,
            ParameterNames.ALLOWED_OUT_ACTIVITIES:       3,
            ParameterNames.START_ACTIVITY:               start_activity,
            ParameterNames.END_ACTIVITY:                 end_activity,
            ParameterNames.INTERESTING_PLACES_THRESHOLD: 1.0,
            ParameterNames.LOG:                          log,
            ParameterNames.NUM_TRACES:                   len(log),
            ParameterNames.FITTING_PLACES:               list(),
            ParameterNames.REVERSE_MAPPING:              bitmasks_to_events,
            ParameterNames.MAX_CONNECTED_ARCS:           2,
            'split':                                     parameters.get("split", {})
        }

        self.pre_pruning_strategy.initialize(parameters=heuristic_parameters)
        stat_logger.algo_started()
        stat_logger.search_started()

        #hier vllt ändern

        candidate_places = await self.search_strategy.execute(
            log,
            parameters['tau'],
            self.pre_pruning_strategy,
            in_order,
            out_order,
            activitiesnum,
            heuristic_parameters=heuristic_parameters,
            logger=logger,
            stat_logger=stat_logger
        )


        #alles clear


        stat_logger.search_finished()
        stat_logger.post_processing_started()

        resulting_places = self.post_processing_strategy.execute(
            candidate_places,
            parameters=heuristic_parameters,
            logger=logger
        )
        #resulting_places = candidate_places
        stat_logger.post_processing_finished()
        stat_logger.algo_finished()
        net, src, sink = self._construct_net(log, activitiesnum, resulting_places, bitmasks_to_events)
        return net, Marking({src: 1}), Marking({sink: 1}), stat_logger
    
    def _construct_net(self, log, activities, resulting_places, reverse_mapping):
        transition_dict = dict()
        net = PetriNet('est_miner_net' + str(time.time()))
        for a in activities:
            transition_dict[reverse_mapping[a]] = PetriNet.Transition(reverse_mapping[a], reverse_mapping[a])
            net.transitions.add(transition_dict[reverse_mapping[a]])
        
        source = PetriNet.Place('startPlace')
        net.places.add(source)
        petri.utils.add_arc_from_to(source, transition_dict[const.START_ACTIVITY], net)

        sink = PetriNet.Place('endPlace')
        net.places.add(sink)
        petri.utils.add_arc_from_to(transition_dict[const.END_ACTIVITY], sink, net)

        for p in resulting_places:
            place = PetriNet.Place(p.name)
            net.places.add(place)
            for a in activities:
                if (a & p.input_trans) != 0:
                    petri.utils.add_arc_from_to(transition_dict[reverse_mapping[a]], place, net)
                if (a & p.output_trans) != 0:
                    petri.utils.add_arc_from_to(place, transition_dict[reverse_mapping[a]], net)
        return net, source, sink
    
    def _ready_for_execution_invariant(self):
        assert(self.name is not None)
        assert(self.pre_processing_strategy is not None) 
        assert(self.order_calculation_strategy is not None)
        assert(self.pre_pruning_strategy is not None)
        assert(self.search_strategy is not None)
        assert(self.post_processing_strategy is not None)
