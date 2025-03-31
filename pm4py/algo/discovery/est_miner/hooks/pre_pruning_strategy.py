import abc
from collections import defaultdict
from enum import Enum

import pm4py.algo.discovery.est_miner.utils.constants as const
from pm4py.algo.discovery.est_miner.utils.constants import ParameterNames
from pm4py.algo.discovery.est_miner.utils.place import Place

class PrePruningStrategy(abc.ABC):

    @abc.abstractmethod
    def initialize(self, parameters=None):
        """
        Initialize potential heuristics.
        """
        pass

    @abc.abstractmethod
    def execute(self, candidate_place, parameters=None):
        """
        Evaluate if the given candidate place is already
        pruned.
        """
        pass

class NoPrePruningStrategy(PrePruningStrategy):

    def initialize(self, parameters=None):
        pass

    def execute(self, candidate_place, parameters=None):
        print('Executed Pre Pruning')
        return False

class PrePruneUselessPlacesStrategy(PrePruningStrategy):

    def initialize(self, parameters=None):
        pass

    def execute(self, candidate_place, parameters=None):
        assert(
                ParameterNames.START_ACTIVITY in parameters
            and ParameterNames.END_ACTIVITY in parameters
        )

        return (
            ((parameters[ParameterNames.END_ACTIVITY] & candidate_place.input_trans) != 0)
            or ((parameters[ParameterNames.START_ACTIVITY] & candidate_place.output_trans) != 0)
        )

class ImportantTracesPrePruning(PrePruningStrategy):

    def __init__(self):
        self._pre_prune_useless_places  = PrePruneUselessPlacesStrategy()
    
    def initialize(self, parameters=None):
        pass
    
    def execute(self, candidate_place, parameters=None):
        assert(ParameterNames.FITTING_PLACES in parameters)
        """
        Tests if a certain set of traces is fitted by the current set of places, including a
        new candidate place. If not, prune the candidate place and all its child places.

        necessary parameters:
        ------------
        candidate_place: The place that could be pruned or not
        start_activity:  The first activity of each trace
        end_activity:    The last activity of each trace
        fitting_places:  The list of places currently found by the search
        """
        return (
            self._pre_prune_useless_places.execute(candidate_place, parameters=parameters)
            or not self._fits_all_important_traces(
                candidate_place, 
                parameters[ParameterNames.IMPORTANT_TRACES], 
                parameters[ParameterNames.FITTING_PLACES],
                parameters[ParameterNames.ACTIVITIES],
                parameters[ParameterNames.START_ACTIVITY],
                parameters[ParameterNames.END_ACTIVITY]
            )
        )
    
    def _fits_all_important_traces(
        self,
        candidate_place,
        important_traces,
        fitting_places,
        activities,
        start_activity,
        end_activity
    ):
        places = fitting_places.copy()
        places.append(candidate_place)
        activity_as_input = dict()
        activity_as_output = dict()
        for activity in activities:
            activity_as_input[activity] = list()
            activity_as_output[activity] = list()

        for place in places:
            for activity in activities:
                if (activity & place.input_trans) != 0:
                    activity_as_input[activity].append(place)
                if (activity & place.output_trans) != 0:
                    activity_as_output[activity].append(place)
        start_place = Place(0, start_activity, 0, 1)
        sink_place = Place(end_activity, 0, 1, 0)
        activity_as_output[start_activity].append(start_place)
        activity_as_input[end_activity].append(sink_place)
        places.append(start_place)
        places.append(sink_place)

        for trace in important_traces:
            if not self._can_replay_trace(
                trace,
                activities,
                places,
                activity_as_input,
                activity_as_output,
                start_place,
                sink_place
            ):
                return False
        return True
    
    def _can_replay_trace(
        self,
        trace,
        activities,
        places,
        activity_as_input,
        activity_as_output,
        start_place,
        sink_place
    ):
        token_map = dict()
        for place in places:
            if place == start_place:
                token_map[place] = 1
            else:
                token_map[place] = 0

        # check if all events can be executed in order
        for event in trace:
            for place in activity_as_output[event]:
                if token_map[place] <= 0:
                    return False
                else:
                    token_map[place] -= 1
            for place in activity_as_input[event]:
                token_map[place] += 1

        # check if final marking is reached
        for place in places:
            if place == sink_place:
                if token_map[place] != 1:
                    return False
            else:
                if token_map[place] != 0:
                    return False

        return True

class RestrictNumInputOutputTransPrePruning(PrePruningStrategy):

    def __init__(self):
        self._pre_prune_useless_places = PrePruneUselessPlacesStrategy()
    
    def initialize(self, parameters=None):
        pass

    def execute(self, candidate_place, parameters=None):
        assert(
                ParameterNames.ALLOWED_IN_ACTIVITIES in parameters 
            and ParameterNames.ALLOWED_OUT_ACTIVITIES in parameters
        )
        """
        Checks if the place has too many input or output transitions, because
        this could make the net hardly readable. If yes, we prune the place.
        """

        return (
            self._pre_prune_useless_places.execute(candidate_place, parameters=parameters)
            or self._too_many_input_transitions(candidate_place, parameters[ParameterNames.ALLOWED_IN_ACTIVITIES])
            or self._too_many_output_transitions(candidate_place, parameters[ParameterNames.ALLOWED_OUT_ACTIVITIES])
        )
    
    def _too_many_input_transitions(self, candidate_place, threshold):
        return candidate_place.num_input_trans > threshold
    
    def _too_many_output_transitions(self, candidate_place, threshold):
        return candidate_place.num_output_trans > threshold

class InterestingPlacesWithoutLoopsPrePruning(PrePruningStrategy):

    def __init__(self):
        self._pre_prune_useless_places = PrePruneUselessPlacesStrategy()
        self._threshold = None
        self._log = None
        self._activities = None
    
    def initialize(self, parameters=None):
        pass

    def execute(self, candidate_place, parameters=None):
        assert(ParameterNames.INTERESTING_PLACES_THRESHOLD in parameters)
        """
        Pre prunes all places that are not interesting (see thesis for definition).

        necessary parameters:
        start_activity
        end_activity
        interesting_places_threshold
        """
        return (
            self._pre_prune_useless_places.execute(candidate_place, parameters=parameters) or
            self._only_interesting_relations(
                parameters[ParameterNames.LOG], 
                parameters[ParameterNames.ACTIVITIES], 
                parameters[ParameterNames.INTERESTING_PLACES_THRESHOLD], 
                candidate_place
            )
        )
    
    def _only_interesting_relations(self, log, activities, threshold, place):
        for a in activities:
            for b in activities:
                if (a & place.input_trans != 0) and (b & place.output_trans != 0) and (a != b):
                    supporting_traces = 0
                    normalization = 0
                    for (trace_key, (freq, trace_bit_map)) in log.items():
                        if self._contains_a_and_b(a, b, trace_bit_map):
                            normalization += freq
                            if (
                                self._contains_required_sequence(a, b, place, trace_bit_map) 
                                and not self._contains_forbidden_sequence(a, b, trace_bit_map)
                            ):
                                supporting_traces += freq
                    if (normalization > 0):
                        if (supporting_traces / normalization) < threshold:
                            return True
        return False

    def _contains_a_and_b(self, a, b, trace_bit_map):
        found_a, found_b = False, False
        for e in trace_bit_map:
            if e == a:
                found_a = True
            if e == b:
                found_b = True
        return (found_a and found_b)
    
    def _contains_required_sequence(self, a, b, place, trace_bit_map):
        found_a, found_sequence = False, False
        for e in trace_bit_map:
            if e == a:
                found_a = True
            if found_a and (e & place.input_trans != 0) and e != a:
                return False
            if found_a and e == b:
                found_sequence = True
        return found_sequence
    
    def _contains_forbidden_sequence(self, a, b, trace_bit_map):
        found_b, found_sequence = False, False
        for e in trace_bit_map:
            if e == b:
                found_b = True
            if found_b and e == a:
                found_sequence = True
        return found_sequence

class InterestingPlacesPrePruning(PrePruningStrategy):

    def __init__(self):
        self._relation_support  = None
        self._pre_prune_useless_places = PrePruneUselessPlacesStrategy()
    
    def initialize(self, parameters=None):
        self._relation_support = self._build_relation_support(
            parameters[ParameterNames.LOG], 
            parameters[ParameterNames.ACTIVITIES]
        )
    
    def execute(self, candidate_place, parameters=None):
        assert(
                ParameterNames.ACTIVITIES in parameters
            and ParameterNames.LOG in parameters
            and ParameterNames.INTERESTING_PLACES_THRESHOLD in parameters
        )
        return (
                self._pre_prune_useless_places.execute(candidate_place, parameters=parameters)
            or  self._score_place(
                    parameters[ParameterNames.ACTIVITIES], 
                    candidate_place, 
                    parameters[ParameterNames.LOG],
                    parameters[ParameterNames.INTERESTING_PLACES_THRESHOLD]
                )
        )
    
    def _build_relation_support(self, log, activites):
        per_trace_support = self._build_per_trace_support(log, activites)
        relation_support = dict()
        for a1 in activites:
            for a2 in activites:
                score = 0
                normalization_factor = 0
                for (trace_key, (freq, trace_bit_map)) in log.items():
                    score += freq * per_trace_support[trace_key, a1, a2]

                    found_a1 = False
                    found_a2 = False
                    for e in trace_bit_map:
                        if e == a1:
                            found_a1 = True
                        if e == a2:
                            found_a2 = True
                    if (found_a1 and found_a2):
                        normalization_factor += freq
                if (normalization_factor == 0):
                    relation_support[a1, a2] = 0
                else:
                    relation_support[a1, a2] = (score / normalization_factor) 
        return relation_support
    
    def _build_per_trace_support(self, log, activites):
        per_trace_support = dict()
        for (trace_key, (freq, trace_bit_map)) in log.items():
            for a1 in activites:
                for a2 in activites:
                    per_trace_support[trace_key, a1, a2] = self._follows(a1, a2, trace_bit_map)
        return per_trace_support

    def _follows(self, a1, a2, trace_bit_map):
        # Returns True, if a2 eventually follows a1 in the trace
        found_a1 = False
        follows  = 0
        for e in trace_bit_map:
            if found_a1:
                if e == a2:
                    follows = 1
            if e == a1:
                found_a1 = True
        return follows
    
    def _score_place(self, activities, place, log, threshold):
        # Place score should give what percentage of pairwise relations between 
        # input and output activities are important (supported by the log).
        #
        # Assume every pair of input and output activities of the place is contained
        # in each trace, then this place gives an important restriction. If only 
        # some are important, then splitting the place might be a good choice, meaning
        # the place itself and its subplaces are not interesting.
        for a in activities:
            for b in activities:
                if (a & place.input_trans != 0) and (b & place.output_trans != 0):
                    if (self._relation_support[a, b] < threshold) and (a != b):
                        return True
        return False

class InterestingPlacesAndEnforeSimplicityPrePruningStrategy(PrePruningStrategy):

    def __init__(self):
        self._interesting_places_pre_pruning = InterestingPlacesPrePruning()
    
    def initialize(self, parameters=None):
        self._interesting_places_pre_pruning.initialize(parameters=parameters)
    
    def execute(self, candidate_place, parameters=None):
        return (
            self._interesting_places_pre_pruning.execute(candidate_place, parameters=parameters)
            or self._place_too_complicated(candidate_place, parameters=parameters)
        )
    
    def _place_too_complicated(self, candidate_place, parameters=None):
        return (
            candidate_place.num_input_trans >= parameters[ParameterNames.ALLOWED_IN_ACTIVITIES]
            and candidate_place.num_output_trans >= parameters[ParameterNames.ALLOWED_OUT_ACTIVITIES]
        )


# TODO Missing  PruneSelfLoopsPrePruningStrategy, SimilarColoredIngoingEdges, SimilarColoredShortestPath