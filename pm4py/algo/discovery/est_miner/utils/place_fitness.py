from enum import Enum

from pm4py.algo.discovery.est_miner.utils.place import Place

class PlaceFitness(Enum):
    FITTING = 1
    OVERFED = 2
    UNDERFED = 3
    UNFITTING = 4

class PlaceFitnessEvaluator:

    @classmethod
    def evaluate_place_fitness(cls, log, place, tau):
        overfed_traces = 0
        underfed_traces = 0
        fitting_traces = 0
        involved_traces = 0

        for (trace_key, (freq, trace_bit_string)) in log.items():
            (involved, states) = cls.trace_fitness(trace_bit_string, place)
            if PlaceFitness.UNDERFED in states: underfed_traces += freq
            if PlaceFitness.OVERFED  in states: overfed_traces  += freq
            if PlaceFitness.FITTING  in states: fitting_traces  += freq
            if involved:                        involved_traces += freq
        
        return cls.place_states(
            place,
            overfed_traces,
            underfed_traces,
            fitting_traces,
            involved_traces,
            tau
        )

    @classmethod
    def trace_fitness(cls, trace_bit_string, place):
        tokens = 0
        involved = False
        states = set()
        for event in trace_bit_string:
            if (event & place.output_trans) != 0:
                involved = True
                tokens -= 1
            if tokens < 0:
                states.add(PlaceFitness.UNDERFED)
            if (event & place.input_trans) != 0:
                involved = True
                tokens += 1

        if tokens > 0:
            states.add(PlaceFitness.OVERFED)
        elif tokens == 0 and PlaceFitness.UNDERFED not in states and involved:
            states.add(PlaceFitness.FITTING)

        return (involved, states)
    
    @classmethod
    def place_states(cls, place, overfed_traces, underfed_traces, fitting_traces, involved_traces, tau):
        states = set()

        if cls.is_overfed(overfed_traces, involved_traces, tau):   states.add(PlaceFitness.OVERFED)
        if cls.is_underfed(underfed_traces, involved_traces, tau): states.add(PlaceFitness.UNDERFED)
        if cls.is_fitting(fitting_traces, involved_traces, tau):   states.add(PlaceFitness.FITTING)
        else:                                                      states.add(PlaceFitness.UNFITTING)
        return states
    
    @classmethod
    def is_overfed(cls, overfed_traces, involved_traces, tau):
        return (
            involved_traces > 0
            and (overfed_traces / involved_traces) > (1 - tau)
        )
    
    @classmethod
    def is_underfed(cls, underfed_traces, involved_traces, tau):
        return (
            involved_traces > 0
            and (underfed_traces / involved_traces) > (1 - tau)
        )
    
    @classmethod
    def is_fitting(cls, fitting_traces, involved_traces, tau):
        return (
            involved_traces > 0 
            and (fitting_traces / involved_traces) >= tau
        )
