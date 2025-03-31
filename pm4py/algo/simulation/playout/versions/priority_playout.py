from copy import copy
from random import shuffle
from functools import reduce

from pm4py.objects.petri import semantics


from pm4py.objects.log import log as log_instance

#import pm4py.objects.log.log as log_instance


def apply_playout(net, initial_marking, prio_list=[], no_traces=100, max_trace_length=100):
    """
    Do the playout of a Petrinet generating a log

    Parameters
    ----------
    net
        Petri net to play-out
    initial_marking
        Initial marking of the Petri net
    no_traces
        Number of traces to generate
    max_trace_length
        Maximum number of events per trace (do break)
    """
    activity_list=[]
    trans_list = net.transitions
    for x in prio_list:
        for y in trans_list:
            if y.label==x: 
                activity_list.append(y)
    log = log_instance.EventLog()
    for i in range(no_traces):
        trace = log_instance.Trace()
        trace.attributes["concept:name"] = str(i)
        marking = copy(initial_marking)
        for j in range(100000):
            if not semantics.enabled_transitions(net, marking):
                break
            all_enabled_trans = semantics.enabled_transitions(net, marking)
            selected_way = None 
            for activity in activity_list:
                if activity in all_enabled_trans: selected_way = activity
            if selected_way == None:
                for activity in activity_list:
                    list1= activity.in_arcs
                    list2 = []
                    for source in list1 : list2.append(source.source) 
                    marking_dict = marking.__repr_dict__()
                    unmarked_places = filter(lambda act: not act.name in marking_dict,list2)
                    setlist = []
                    for place in unmarked_places:
                        list3= []
                        for arc in place.in_arcs:
                            list3.append(arc.source)
                        setlist.append(set(map(lambda trans:trans.label,list3)))
                    predacessor = reduce(lambda x, y: x & y , setlist) 
                    filtered_predacessor = list(predacessor & all_enabled_trans)
                    if filtered_predacessor!=[]: 
                        selected_way = list(filter(lambda trans: trans.label==filtered_predacessor[0],list(net.transitions)))[0]
                        if selected_way in activity_list:
                           activity_list.remove(selected_way)
                        break  
            if selected_way is None: selected_way = list(all_enabled_trans)[0]        
            if selected_way.label is not None:
                event = log_instance.Event()
                event["concept:name"] = selected_way.label
                trace.append(event)
            marking = semantics.execute(selected_way, net, marking)
            if len(trace) > max_trace_length:
                break
        if len(trace) > 0:
            log.append(trace)
    return log



def apply(net, initial_marking, parameters=None):
    """
    Do the playout of a Petrinet generating a log

    Parameters
    -----------
    net
        Petri net to play-out
    initial_marking
        Initial marking of the Petri net
    parameters
        Parameters of the algorithm:
            noTraces -> Number of traces of the log to generate
            maxTraceLength -> Maximum trace length
    """
    if parameters is None:
        parameters = {}
    no_traces = 100
    max_trace_length = 100
    prio_list = []
    if "noTraces" in parameters:
        no_traces = parameters["noTraces"]
    if "maxTraceLength" in parameters:
        max_trace_length = parameters["maxTraceLength"]
    if "prioList" in parameters:
        prio_list = parameters["prioList"]    

    return apply_playout(net, initial_marking, prio_list=prio_list, max_trace_length=max_trace_length, no_traces=no_traces)

