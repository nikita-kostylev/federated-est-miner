import abc
import copy
import random
from collections import defaultdict

from gurobipy import *

from progress.bar import ShadyBar

from pm4py.algo.discovery.est_miner.utils.place import Place
from pm4py.algo.discovery.est_miner.utils import constants as const
from pm4py.algo.discovery.est_miner.utils.constants import ParameterNames
from pm4py.algo.discovery.est_miner.utils import est_utils as utils


class PostProcessingStrategy(abc.ABC):
    @abc.abstractmethod
    def execute(self, candidate_places, parameters=None, logger=None):
        """
        Remove redundant places from the found candidate places
        to make the resulting network better interpretable by 
        human readers.
        """
        pass


class NoPostProcessingStrategy(PostProcessingStrategy):
    def execute(self, candidate_places, parameters=None, logger=None):
        print('Executed Post Processing')
        return candidate_places


class RemoveRedundantPlacesLPPostProcessingStrategy(PostProcessingStrategy):
    def execute(self, candidate_places, parameters=None, logger=None):
        """
        Removes redundant places [1].

        Parameters:
        -----------
        candidate_places: Set of fitting places, discovered in the search phase
        transitions: Set of transitions occurring in the log
        logger: Possible logger instance

        Returns:
        -----------
        A set of places that do not contain any redundant places.
        But still have implicit places.

        References
        -----------
        Wil M. P. van der Aalst, "Discovering the "Glue" Connecting Activities
        - Exploiting Monotonicity to Learn Places Faster"
        """
        if (logger is not None):
            logger.info('Starting Post Processing')
        pre = {}
        post = {}
        for p in candidate_places:
            for t in parameters[ParameterNames.ACTIVITIES]:
                if (t & p.input_trans) != 0:
                    pre[p, t] = 1
                else:
                    pre[p, t] = 0

                if (t & p.output_trans) != 0:
                    post[p, t] = 1
                else:
                    post[p, t] = 0

        pruned_set = set(candidate_places)
        for p_test in candidate_places:
            if self.is_redundant(p_test, parameters[ParameterNames.ACTIVITIES],
                                 pre, post, pruned_set):
                if (logger is not None):
                    logger.info('Removing redundant place ' + p_test.name)
                pruned_set.discard(p_test)
        return pruned_set

    def is_redundant(self, p_test, transitions, pre, post, pruned_set):
        redundant = False
        model = Model('Redundant Place Test')
        y = {}

        for p in pruned_set.difference({p_test}):
            y[p] = model.addVar(vtype=GRB.BINARY)
        model.update()
        model.setObjective(
            quicksum(y[p] for p in pruned_set.difference({p_test})),
            GRB.MINIMIZE)

        # Constraints
        for t in transitions:
            model.addConstr(
                quicksum(y[p] * pre[p, t] for p in pruned_set.difference(
                    {p_test})) == pre[p_test, t])
            model.addConstr(
                quicksum(y[p] * post[p, t] for p in pruned_set.difference(
                    {p_test})) == post[p_test, t])
            model.addConstr(
                quicksum(y[p] * pre[p, t]
                         for p in pruned_set.difference({p_test})) <= 1)
            model.addConstr(
                quicksum(y[p] * post[p, t]
                         for p in pruned_set.difference({p_test})) <= 1)

        model.optimize()
        if model.status == GRB.OPTIMAL:
            redundant = True

        return redundant


class RemoveImplicitPlacesPostProcessingStrategy(PostProcessingStrategy):

    def _order_candidate_places(self, candidate_places):
        return sorted(candidate_places, key=lambda p: p.num_input_trans + p.num_output_trans, reverse=True)

    def execute(self, candidate_places, parameters=None, logger=None):
        # create source and sink place (remove them at the end again)
        source = Place(0, parameters[ParameterNames.START_ACTIVITY], 0, 1)
        sink = Place(parameters[ParameterNames.END_ACTIVITY], 0, 1, 0)
        candidate_places.append(source)
        candidate_places.append(sink)
        candidate_places = self._order_candidate_places(candidate_places)
        # build pre and post
        pre = {}
        post = {}
        for p in candidate_places:
            for t in parameters[ParameterNames.ACTIVITIES]:
                if (t & p.input_trans) != 0:
                    pre[p, t] = 1
                else:
                    pre[p, t] = 0
                if (t & p.output_trans) != 0:
                    post[p, t] = 1
                else:
                    post[p, t] = 0
        # build initial marking
        initial_marking = {}
        for p in candidate_places:
            if p == source:
                initial_marking[p] = 1
            else:
                initial_marking[p] = 0

        # remove all implicit places
        bar = ShadyBar('Removing Structural Implicit Places',
                       max=len(candidate_places))
        for q in candidate_places:
            implicit = False
            model = Model('Implicit Place Test')
            model.setParam('OutputFlag', 0)
            remaining_places = candidate_places.copy()
            remaining_places.remove(q)
            y = {}
            for p in remaining_places:
                y[p] = model.addVar(vtype=GRB.BINARY)
            mu = model.addVar(vtype=GRB.INTEGER)
            model.update()
            model.setObjective(
                quicksum(y[p] * initial_marking[p]
                         for p in remaining_places) + mu, GRB.MINIMIZE)
            for t in parameters[ParameterNames.ACTIVITIES]:
                model.addConstr(
                    quicksum(y[p] * (post[p, t] - pre[p, t])
                             for p in remaining_places) + mu >= post[q, t] -
                    pre[q, t])
            for p in remaining_places:
                model.addConstr(y[p] >= 0)
            for t in parameters[ParameterNames.ACTIVITIES]:
                if (t & q.output_trans) != 0:
                    model.addConstr(
                        quicksum(y[p] * pre[p, t]
                                 for p in remaining_places) + mu >= pre[q, t])
            model.optimize()
            if model.status == GRB.OPTIMAL:
                if model.objVal <= initial_marking[q]:
                    implicit = True
            if implicit:
                candidate_places = remaining_places
            bar.next()
        bar.finish()
        if source in candidate_places:
            candidate_places.remove(source)
        if sink in candidate_places:
            candidate_places.remove(sink)
        return candidate_places


class RemoveImplicitPlacesLPPostProcessingStrategy(PostProcessingStrategy):
    def execute(self, candidate_places, parameters=None, logger=None):
        """
        Removes implicit places as in [1].

        Parameters:
        -----------
        candidate_places: Set of fitting places, discovered in the search phase
        transitions: Set of transitions occurring in the log
        logger: Possible logger instance

        Returns:
        -----------
        A set of places that do not contain any implicit places.

        References
        -----------
        J.M. Colom and M. Silva, "Improving the Linearly Based Characterization
        of P/T Nets"
        """
        if (logger is not None):
            logger.info('Starting Post Processing')

        activity_to_place_dependencies = dict()
        for a in parameters[ParameterNames.ACTIVITIES]:
            activity_to_place_dependencies[a] = set()
            for p in candidate_places:
                if (p.output_trans & a) != 0:
                    activity_to_place_dependencies[a].add(p.copy())

        pre = {}
        post = {}
        for p in candidate_places:
            for t in parameters[ParameterNames.ACTIVITIES]:
                if (t & p.input_trans) != 0:
                    pre[p, t] = 1
                else:
                    pre[p, t] = 0

                if (t & p.output_trans) != 0:
                    post[p, t] = 1
                else:
                    post[p, t] = 0

        pruned_set = set(candidate_places)
        bar = ShadyBar('Removing Structural Implicit Places',
                       max=len(candidate_places))
        for p_test in candidate_places:
            if self.is_implicit(p_test, parameters[ParameterNames.ACTIVITIES],
                                pre, post, pruned_set,
                                parameters[ParameterNames.START_ACTIVITY],
                                parameters[ParameterNames.END_ACTIVITY],
                                activity_to_place_dependencies):
                if (logger is not None):
                    logger.info('Removing implicit place ' + p_test.name)
                pruned_set.discard(p_test)
            bar.next()
        bar.finish()

        return pruned_set

    def is_implicit(self, p_test, transitions, pre, post, pruned_set,
                    start_activity, end_activity,
                    activity_to_place_dependencies):
        implicit = False
        model = Model('Implicit Place Test')
        model.setParam('OutputFlag', 0)
        y = {}
        #        m_0 = {}

        for p in pruned_set.difference({p_test}):
            y[p] = model.addVar(vtype=GRB.BINARY)


#            if p.input_trans == 0 and p.output_trans == start_activity:
#                m_0[p] = 1
#            else:
#                m_0[p] = 0

        mu = model.addVar(vtype=GRB.INTEGER)

        model.update()
        model.setObjective(mu, GRB.MINIMIZE)

        # Constraints
        for t in transitions:
            model.addConstr(
                quicksum(y[p] * (post[p, t] - pre[p, t])
                         for p in pruned_set.difference({p_test})) <=
                post[p_test, t] - pre[p_test, t])

        for t in transitions:
            if (t & p_test.output_trans) != 0:
                model.addConstr(
                    quicksum(y[p] * pre[p, t] + mu
                             for p in pruned_set.difference({p_test})) >=
                    pre[p_test, t])

        model.optimize()
        if model.status == GRB.OPTIMAL:
            if model.objVal <= 0:
                implicit = True

        if implicit:
            for t in transitions:
                if (t & p_test.output_trans) != 0:
                    if len(activity_to_place_dependencies[t]) == 1:
                        return False
                    else:
                        activity_to_place_dependencies[t].remove(p_test)
            return True
        else:
            return False


class RemoveConcurrentImplicitPlacesPostProcessingStrategy(
        PostProcessingStrategy):
    def execute(self, candidate_places, parameters=None, logger=None):
        if (logger is not None):
            logger.info('Starting Post Processing')

        activity_to_place_dependencies = dict()
        for a in parameters[ParameterNames.ACTIVITIES]:
            activity_to_place_dependencies[a] = set()
            for p in candidate_places:
                if (p.output_trans & a) != 0:
                    activity_to_place_dependencies[a].add(p.copy())

        pre = {}
        post = {}
        for p in candidate_places:
            for t in parameters[ParameterNames.ACTIVITIES]:
                if (t & p.input_trans) != 0:
                    pre[p, t] = 1
                else:
                    pre[p, t] = 0

                if (t & p.output_trans) != 0:
                    post[p, t] = 1
                else:
                    post[p, t] = 0

        pruned_set = set(candidate_places)
        bar = ShadyBar('Removing Concurrent Implicit Places',
                       max=len(candidate_places))
        for p_test in candidate_places:
            if self.is_concurrent_implicit(
                    p_test, parameters[ParameterNames.ACTIVITIES], pre, post,
                    pruned_set, parameters[ParameterNames.START_ACTIVITY],
                    parameters[ParameterNames.END_ACTIVITY],
                    activity_to_place_dependencies):
                if (logger is not None):
                    logger.info('Removing implicit place ' + p_test.name)
                pruned_set.discard(p_test)
            bar.next()
        bar.finish()

        return pruned_set

    def is_concurrent_implicit(self, p_test, transitions, pre, post,
                               pruned_set, start_activity, end_activity,
                               activity_to_place_dependencies):
        #if (p_test.input_trans & start_activity) != 0 and (p_test.output_trans & end_activity) != 0 and p_test.num_input_trans == 2 and p_test.num_output_trans == 2:
        #    return False
        concurrent_implicit = False
        model = Model('Concurrent Implicit Place Test')
        model.setParam('OutputFlag', 0)
        y = {}
        z = {}

        for p in pruned_set.difference({p_test}):
            y[p] = model.addVar(vtype=GRB.BINARY)

            z[p] = model.addVar(vtype=GRB.BINARY)

        mu = model.addVar(vtype=GRB.INTEGER)

        model.update()
        model.setObjective(mu, GRB.MAXIMIZE)

        # Constraints
        for t in transitions:
            model.addConstr(
                quicksum(y[p] * (post[p, t] - pre[p, t])
                         for p in pruned_set.difference({p_test})) <=
                post[p_test, t] - pre[p_test, t])

        for t in transitions:
            if (t & p_test.output_trans) != 0:
                model.addConstr(
                    quicksum(z[p] * pre[p, t] + mu
                             for p in pruned_set.difference({p_test})) >=
                    pre[p_test, t])

        model.addConstr(mu <= 0)

        model.optimize()
        if model.status == GRB.OPTIMAL:
            if model.objVal <= 0:
                concurrent_implicit = True

        if concurrent_implicit:
            for t in transitions:
                if (t & p_test.output_trans) != 0:
                    if len(activity_to_place_dependencies[t]) == 1:
                        return False
                    else:
                        activity_to_place_dependencies[t].remove(p_test)
            return True
        else:
            return False


class RemoveConcurrentAndStructuralImplicitPlacesPostProcessingStrategy(
        PostProcessingStrategy):
    def execute(self, candidate_places, parameters=None, logger=None):
        structural_impl_places_remover = RemoveImplicitPlacesLPPostProcessingStrategy()
        concurrent_impl_places_remover = RemoveConcurrentImplicitPlacesPostProcessingStrategy()

        without_structural_impl_places = structural_impl_places_remover.execute(
            candidate_places, parameters=parameters, logger=logger
        )

        without_concurrent_impl_places = concurrent_impl_places_remover.execute(
            without_structural_impl_places,
            parameters=parameters,
            logger=logger
        )
        return without_concurrent_impl_places


class RemoveRedundantAndImplicitPlacesPostProcessingStrategy(
        PostProcessingStrategy):
    def execute(self, candidate_places, parameters=None, logger=None):
        redundant_places_remover = RemoveRedundantPlacesLPPostProcessingStrategy()
        implicit_places_remover = RemoveImplicitPlacesLPPostProcessingStrategy()

        without_redundant_places = redundant_places_remover.execute(
            candidate_places, parameters=parameters, logger=logger
        )

        without_implicit_places = implicit_places_remover.execute(
            without_redundant_places, parameters=parameters, logger=logger
        )
        return without_implicit_places


class DeleteDuplicatePlacesPostProcessingStrategy(PostProcessingStrategy):
    def execute(self, candidate_places, parameters=None):
        return set(candidate_places)


class RemoveImplicitPlacesAndReduceArcsPostProcessingStrategy(PostProcessingStrategy):

    def __init__(self):
        self._implicit_places_removal = RemoveImplicitPlacesPostProcessingStrategy()

    def execute(self, candidate_places, parameters=None, logger=None):
        candidate_places = self._implicit_places_removal.execute(
            candidate_places, parameters=parameters)
        for t in parameters[ParameterNames.ACTIVITIES]:
            candidate_places = self._enforce_max_arcs_condition(
                    candidate_places, t, parameters=parameters)
        return candidate_places

    def _enforce_max_arcs_condition(
        self,
        candidate_places,
        transition,
        parameters=None
    ):
        if transition == parameters[ParameterNames.END_ACTIVITY]:
            return candidate_places
        place_importance = dict()
        for p in candidate_places:
            if (p.output_trans & transition) != 0:
                importance = self._place_importance_for_transition(
                            p, transition, parameters=parameters)
                place_importance[p] = importance
        sorted_by_place_importance = sorted(place_importance.items(), key=lambda tupel: tupel[1])
        sorted_by_place_importance.reverse()
        untouched_places_and_importances = sorted_by_place_importance[:parameters[ParameterNames.MAX_CONNECTED_ARCS]]
        untouched_places = [tup[0] for tup in untouched_places_and_importances] 
        resulting_places = list()
        for p in candidate_places:
            if (p.output_trans & transition != 0):
                if p in untouched_places:
                    resulting_places.append(p.copy())
                else:
                    new_place = Place(
                        p.input_trans,
                        p.output_trans ^ transition,
                        p.num_input_trans,
                        p.num_output_trans - 1
                    )
                    if new_place.num_output_trans > 0:
                        resulting_places.append(new_place)
                    else:
                        resulting_places.append(p.copy())
            else:
                resulting_places.append(p.copy())
        return resulting_places

    def _place_importance_for_transition(
        self,
        place,
        transition,
        parameters=None
    ):
        place_importance = 0.0
        for a in parameters[ParameterNames.ACTIVITIES]:
            if (a & place.input_trans) != 0:
                # number of times a --> t - number of times t --> a / num_traces
                place_importance += (
                    self._num_eventually_follows(
                        a, transition, parameters[ParameterNames.LOG]) -
                    self._num_eventually_follows(
                        transition, a, parameters[ParameterNames.LOG])
                ) / parameters[ParameterNames.NUM_TRACES]
        return place_importance / place.num_input_trans

    def _num_eventually_follows(self, a1, a2, log):
        # number of traces for which a1 --> a2
        res = 0
        for (trace_key, (freq, trace_bit_map)) in log.items():
            if utils.eventually_follows(a1, a2, trace_bit_map):
                res += freq
        return res


class RemoveImplicitPlacesPostProcessingStrategyModified(PostProcessingStrategy):

    def _order_candidate_places(self, candidate_places):
        return sorted(candidate_places, key=lambda p: p.num_input_trans + p.num_output_trans, reverse=True)

    def execute(self, candidate_places, parameters=None, logger=None):

        print("Candidate places",[place.name for place in candidate_places])

        cand_places_implicitless = RemoveImplicitPlacesPostProcessingStrategy().execute(candidate_places, parameters=parameters, logger=logger)

        if parameters['split'] is None or parameters['split'] == {}:
            return cand_places_implicitless

        cpi_non_iterable = copy.deepcopy(cand_places_implicitless)
        intermediate_places_to_remove = []
        names = []
        baustell = set()
        for place in cand_places_implicitless:
            places_test_in  = [2**i for i, bit in enumerate(bin(place.input_trans)[:1:-1])  if bit == '1']
            places_test_out = [2**i for i, bit in enumerate(bin(place.output_trans)[:1:-1]) if bit == '1']
            places_labels_in = list(map(lambda x : parameters[ParameterNames.REVERSE_MAPPING][x],places_test_in))
            places_labels_out = list(map(lambda x : parameters[ParameterNames.REVERSE_MAPPING][x],places_test_out))
            places_test_labels = (places_labels_in , places_labels_out)
            names.append((places_test_labels,place))
            for key in parameters['split']:
                if all(map(lambda x : x in parameters['split'][key], places_test_labels[0]+places_test_labels[1])): 
                    intermediate_places_to_remove.append(places_test_labels)
        activities = list(set(parameters[ParameterNames.REVERSE_MAPPING].values()))
        for act in activities:
            random_list_in = []
            random_list_out = []
            for placeholder in names:
                place = placeholder[0]
                if   act in place[0] and place in intermediate_places_to_remove:
                    random_list_out.append(place)
                elif act in place[0] and place not in intermediate_places_to_remove:
                    baustell.add(""+act+"out")
                if   act in place[1] and place in intermediate_places_to_remove:
                    random_list_in.append(place)
                elif act in place[1] and place not in intermediate_places_to_remove:
                    baustell.add(""+act+"in")
            if ""+act+"out" not in baustell and random_list_out:
                stay = random.choice(random_list_out)
                intermediate_places_to_remove.remove(stay)
            if ""+act+"in" not in baustell and random_list_in:
                stay = random.choice(random_list_in)
                intermediate_places_to_remove.remove(stay)
        for place in intermediate_places_to_remove:
            cpi_non_iterable.remove([val[1] for val in names if val[0] == place][0])
                
                

        return cpi_non_iterable