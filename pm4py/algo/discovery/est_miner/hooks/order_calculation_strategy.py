import abc
import math

import pm4py.objects.log.util.log as log_util
from pm4py.algo.discovery.est_miner.utils.activity_order import ActivityOrder, \
ActivityOrderBuilder

def get_abs_activity_occ(log, activities):
    abs_activity_occurrences = {}
    for a in activities:
        occurrences = 0
        for (trace_key, (freq, trace_bit_string)) in log.items():
            trace_occurrences = 0
            for e in trace_bit_string:
                if a == e:
                    trace_occurrences += 1
            occurrences += trace_occurrences * freq
        abs_activity_occurrences[a] = occurrences
    return abs_activity_occurrences

def get_abs_trace_occ(log, activities):
    abs_trace_occ = {}
    for a in activities:
        traces = 0
        for (trace_key, (freq, trace_bit_string)) in log.items():
            occ = False
            for e in trace_bit_string:
                if a == e:
                    occ = True
            if occ:
                traces += freq
        abs_trace_occ[a] = traces
    return abs_trace_occ

def get_rel_trace_occ(log, activities):
    relative_trace_occ = {}
    for a in activities:
        traces = 0
        for (trace_key, (freq, trace_bit_string)) in log.items():
            occ = False
            for e in trace_bit_string:
                if a == e:
                    occ = True
            if occ:
                traces += freq
        relative_trace_occ[a] = traces / len(log)
    return relative_trace_occ

def get_avg_trace_occ(log, activities):
    avg_trace_occ = {}
    for a in activities:
        avg_occ = 0
        for (trace_key, (freq, trace_bit_string)) in log.items():
            occ = 0
            for e in trace_bit_string:
                if a == e:
                    occ += 1
            avg_occ += freq * (occ / len(trace_bit_string))
        avg_trace_occ[a] = avg_occ / len(log)
    return avg_trace_occ

class OrderCalculationStrategy(abc.ABC):

    @abc.abstractmethod
    def execute(self, log, transitions):
        """
        Calculate two orders on the given log, one for 
        input and one for out activities.

        Parameters:
        -------------
        log: :class:`pm4py.log.log.EventLog The event log

        Returns:
        -------------
        input_order: :class:ActivityOrder - ordering on input activities
        output_order: :class:ActivityOrder - ordering on output activities
        """
        pass

class NoOrderCalculationStrategy(OrderCalculationStrategy):

    def execute(self, log, activites):
        print('Executed Order Calculation')
        return None, None

class MaxOverfedPlacesThroughAvgTraceOccOrderStrategy(OrderCalculationStrategy):

    def execute(self, log, activities):
        avg_trace_occ = get_avg_trace_occ(log, activities)

        input_order_builder  = ActivityOrderBuilder(activities)
        output_order_builder = ActivityOrderBuilder(activities)
        sorted_avg_trace_occ = sorted(avg_trace_occ.items(), key=lambda x: x[1])

        for i in reversed(range(len(sorted_avg_trace_occ))):
            for j in reversed(range(i)):
                output_order_builder.add_relation(larger=sorted_avg_trace_occ[j][0], smaller=sorted_avg_trace_occ[i][0])

        for i in range(len(sorted_avg_trace_occ)):
            for j in range(i):
                input_order_builder.add_relation(larger=sorted_avg_trace_occ[j][0], smaller=sorted_avg_trace_occ[i][0])

        return (input_order_builder.get_ordering(), output_order_builder.get_ordering())

class MaxOverfedPlacesThroughAbsTraceFreqOrderStrategy(OrderCalculationStrategy):

    def execute(self, log, activities):
        # A place is more likely to be overfed, if its' input transitions
        # are more likely to occur in a trace, than the place's output
        # transitions.
        abs_trace_occ = get_abs_trace_occ(log, activities)
        
        input_order_builder  = ActivityOrderBuilder(activities)
        output_order_builder = ActivityOrderBuilder(activities)
        sorted_abs_trace_occ = sorted(abs_trace_occ.items(), key=lambda x: x[1])
        # Build output order
        # most frequent element is minimal
        for i in reversed(range(len(sorted_abs_trace_occ))):
            for j in reversed(range(i)):
                output_order_builder.add_relation(larger=sorted_abs_trace_occ[j][0], smaller=sorted_abs_trace_occ[i][0])
        
        # Build input order
        # least frequent element is minimal
        for i in range(len(sorted_abs_trace_occ)):
            for j in range(i):
                input_order_builder.add_relation(larger=sorted_abs_trace_occ[j][0], smaller=sorted_abs_trace_occ[i][0])

        return (input_order_builder.get_ordering(), output_order_builder.get_ordering())

class MaxOverfedPlacesThroughRelativeTraceFreqOrderStrategy(OrderCalculationStrategy):

    def execute(self, log, activities):
        # A place is more likely to be overfed, if its' input transitions
        # are more likely to occur in a trace, than the place's output
        # transitions.
        rel_trace_occ = get_rel_trace_occ(log, activities)
        
        input_order_builder  = ActivityOrderBuilder(activities)
        output_order_builder = ActivityOrderBuilder(activities)
        sorted_rel_trace_occ = sorted(rel_trace_occ.items(), key=lambda x: x[1])
        # Build output order
        # most frequent element is minimal
        for i in reversed(range(len(sorted_rel_trace_occ))):
            for j in reversed(range(i)):
                output_order_builder.add_relation(larger=sorted_rel_trace_occ[j][0], smaller=sorted_rel_trace_occ[i][0])
        
        # Build input order
        # least frequent element is minimal
        for i in range(len(sorted_rel_trace_occ)):
            for j in range(i):
                input_order_builder.add_relation(larger=sorted_rel_trace_occ[j][0], smaller=sorted_rel_trace_occ[i][0])

        return (input_order_builder.get_ordering(), output_order_builder.get_ordering())

class MaxUnderfedPlacesThroughAFOIOrderStrategy(OrderCalculationStrategy):

    def execute(self, log, activities):
        avg_first_occ_index = self._avg_first_occ_index(log, activities)

        input_order_builder = ActivityOrderBuilder(activities)
        output_order_builder = ActivityOrderBuilder(activities)
        sorted_avg_first_occ_index = sorted(avg_first_occ_index.items(), key=lambda x: x[1])
        print(sorted_avg_first_occ_index)

        for i in range(len(sorted_avg_first_occ_index)):
            for j in reversed(range(i)):
                input_order_builder.add_relation(larger=sorted_avg_first_occ_index[j][0], smaller=sorted_avg_first_occ_index[i][0])
                output_order_builder.add_relation(larger=sorted_avg_first_occ_index[i][0], smaller=sorted_avg_first_occ_index[j][0])
        
        return (input_order_builder.get_ordering(), output_order_builder.get_ordering())

    def _avg_first_occ_index(self, log, activities):
        avg_first_occ_index = dict()
        for a in activities:
            sum = 0
            num_of_occurring_traces = 0
            for (trace_key, (freq, trace_bit_string)) in log.items():
                first_occurrence_index = -1
                index = 1
                for e in trace_bit_string:
                    if e == a:
                        if first_occurrence_index == -1:
                            first_occurrence_index = index
                    index += 1
                if first_occurrence_index != -1:
                    sum += freq * first_occurrence_index
                    num_of_occurring_traces += freq
            if (num_of_occurring_traces > 0):
                avg_first_occ_index[a] = (sum / num_of_occurring_traces)
            else:
                avg_first_occ_index[a] = math.inf
        return avg_first_occ_index

class MaxUnderfedPlacesThroughAvgTraceOccOrderStrategy(OrderCalculationStrategy):

    def execute(self, log, activities):
        avg_trace_occ = get_avg_trace_occ(log, activities)
        
        input_order_builder  = ActivityOrderBuilder(activities)
        output_order_builder = ActivityOrderBuilder(activities)
        sorted_avg_trace_occ = sorted(avg_trace_occ.items(), key=lambda x: x[1])
        # Build input order
        # most frequent element is minimal
        #for i in reversed(range(len(sorted_avg_trace_occ))):
        #    for j in reversed(range(i)):
                #input_order_builder.add_relation(larger=sorted_avg_trace_occ[j][0], smaller=sorted_avg_trace_occ[i][0])

        for i in range(len(sorted_avg_trace_occ)):
            for j in range(i):
                input_order_builder.add_relation(larger=sorted_avg_trace_occ[j][0], smaller=sorted_avg_trace_occ[i][0])
        
        # Build output order
        # least frequent element is minimal
        for i in range(len(sorted_avg_trace_occ)):
            for j in range(i):
                output_order_builder.add_relation(larger=sorted_avg_trace_occ[j][0], smaller=sorted_avg_trace_occ[i][0])

        return (input_order_builder.get_ordering(), output_order_builder.get_ordering())

class MaxUnderfedPlacesThroughAbsTraceFreqOrderStrategy(OrderCalculationStrategy):

    def execute(self, log, activities):
        # A place is more likely to be underfed, if its' output transitions
        # are more likely to occur in a trace, than the place's input transitons.
        abs_trace_occ = get_abs_trace_occ(log, activities)
        
        input_order_builder  = ActivityOrderBuilder(activities)
        output_order_builder = ActivityOrderBuilder(activities)
        sorted_abs_trace_occ = sorted(abs_trace_occ.items(), key=lambda x: x[1])
        # Build input order
        # most frequent element is minimal
        for i in range(len(sorted_abs_trace_occ)):
            for j in range(i):
                input_order_builder.add_relation(larger=sorted_abs_trace_occ[j][0], smaller=sorted_abs_trace_occ[i][0])
        
        # Build output order
        # least frequent element is minimal
        for i in range(len(sorted_abs_trace_occ)):
            for j in range(i):
                output_order_builder.add_relation(larger=sorted_abs_trace_occ[j][0], smaller=sorted_abs_trace_occ[i][0])

        return (input_order_builder.get_ordering(), output_order_builder.get_ordering())

class MaxUnderfedPlacesThroughRelativeTraceFreqOrderStrategy(OrderCalculationStrategy):

    def execute(self, log, activities):
        # A place is more likely to be underfed, if its' output transitions
        # are more likely to occur in a trace, than the place's input transitons.
        rel_trace_occ = get_rel_trace_occ(log, activities)
        
        input_order_builder  = ActivityOrderBuilder(activities)
        output_order_builder = ActivityOrderBuilder(activities)
        sorted_rel_trace_occ = sorted(rel_trace_occ.items(), key=lambda x: x[1])
        # Build input order
        # most frequent element is minimal
        for i in range(len(sorted_rel_trace_occ)):
            for j in range(i):
                input_order_builder.add_relation(larger=sorted_rel_trace_occ[j][0], smaller=sorted_rel_trace_occ[i][0])
        
        # Build output order
        # least frequent element is minimal
        for i in range(len(sorted_rel_trace_occ)):
            for j in range(i):
                output_order_builder.add_relation(larger=sorted_rel_trace_occ[j][0], smaller=sorted_rel_trace_occ[i][0])

        return (input_order_builder.get_ordering(), output_order_builder.get_ordering())

class MaxCutoffsThroughAbsoluteActivityFreqOrderStrategy(OrderCalculationStrategy):

    def execute(self, log, activities):
        abs_activity_freq = get_abs_activity_occ(log, activities)
        input_order_builder = ActivityOrderBuilder(activities)
        output_order_builder = ActivityOrderBuilder(activities)
        sorted_abs_activity_freq = sorted(abs_activity_freq.items(), key=lambda x: x[1])

        for i in range(len(sorted_abs_activity_freq)):
            for j in range(i):
                input_order_builder.add_relation(larger=sorted_abs_activity_freq[j][0], smaller=sorted_abs_activity_freq[i][0])
                output_order_builder.add_relation(larger=sorted_abs_activity_freq[j][0], smaller=sorted_abs_activity_freq[i][0])
        return (input_order_builder.get_ordering(), output_order_builder.get_ordering())

class LexicographicalOrderStrategy(OrderCalculationStrategy):

    def execute(self, log, activities):
        input_order_builder  = ActivityOrderBuilder(activities)
        output_order_builder = ActivityOrderBuilder(activities)

        sorted_activities = sorted(activities)
        for i in range(0, len(sorted_activities)):
            for j in range(i, len(sorted_activities)):
                if (sorted_activities[i] != sorted_activities[j]):
                    input_order_builder.add_relation(larger=sorted_activities[j], smaller=sorted_activities[i])
                    output_order_builder.add_relation(larger=sorted_activities[j], smaller=sorted_activities[i])
        return (input_order_builder.get_ordering(), output_order_builder.get_ordering())
