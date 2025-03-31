import datetime
import itertools
import random
from pm4py.objects.log.exporter.xes import factory as exporter
from pm4py.objects.log.importer.xes import factory as xes_importer
from pm4py.objects.petri.importer import pnml as petri_importer
import pm4py.objects.log.log as log_instance
from pm4py.objects.petri import semantics
from pm4py.algo.discovery.alpha import factory as alpha_discovery
from pm4py.visualization.petrinet.factory import apply,save
from pm4py.objects.log.util import log as variant_extractor
from pm4py.objects.log.log import Event,Trace
import math
import time




import copy

#Helper Methods     

def name(input):
    if isinstance(input,Event):
        return input['concept:name']
    if isinstance(input,Trace):
        return [event['concept:name'] for event in input]

def hashable_trace(trace):
    if isinstance(trace,list):
        return tuple(event for event in trace)
    else:
        return tuple(name(event) for event in trace)

def ori_act_delt_list_to_dict(log,lyst,sublog):
    result_dict = {}
    activities = variant_extractor.get_event_labels(sublog,'concept:name')
    for trace in log:
        inplace = result_dict.setdefault(tuple(filter(lambda x : x in activities,[name(event) for event in trace])),{})
        val = tuple(lyst.pop(0))
        inplacev = inplace.setdefault(val,0)
        inplacev += 1 
        inplace[val] = inplacev
        result_dict[tuple(filter(lambda x : x in activities,[name(event) for event in trace]))]=inplace
    return result_dict   





# Generate Logs

def recursive_trace_generation(net,trace, marking, depth, final_marking,start_time):
        if start_time + 2970 < time.monotonic():
            return []
        if depth == 0:
            return []
        if marking == final_marking:
            return [trace]
        traces = []
        enabled_transitions = list(semantics.enabled_transitions(net, marking))
        if not enabled_transitions:  #cannot fire but did not finish
            return []
        for transition in enabled_transitions:
            new_trace = copy.deepcopy(trace)
            new_marking = copy.deepcopy(marking)
            if transition.label is not None:
                event = log_instance.Event()
                event["concept:name"] = transition.label
                event["time:timestamp"] = datetime.datetime(2023,1,1,12,12,34,0)
                new_trace.append(event)
            new_marking = semantics.execute(transition, net, marking)
            traces.extend(recursive_trace_generation(net,new_trace, new_marking, depth - 1,final_marking,start_time))
        return traces

def apply_playout(net, initial_marking,final_marking):
    """
    Perform the playout of a Petri net generating all possible traces using iterative deepening.
    """
    log = log_instance.EventLog()

    trace = log_instance.Trace()

    depth = 12

    start = time.monotonic()

    traces = recursive_trace_generation(net, trace, initial_marking,depth,final_marking,start)

    for i in traces:
        log.append(i)

    if time.monotonic() - start > 2970:
        print("Timeout")
    return log

def create_test_sublog(log,chance):
    sublog = log_instance.EventLog()
    all_activities = variant_extractor.get_event_labels(log,'concept:name')
    selected_activities = [x for x in all_activities if random.random()<chance]
    print("selected activities",selected_activities)
    for trace in log:
        reduced_trace = log_instance.Trace()
        for event in trace:
            if event['concept:name'] in selected_activities:  reduced_trace.append(event)
        sublog.append(reduced_trace)
    return sublog

def create_test_sublog_with_act(log,selected_activities):
    sublog = log_instance.EventLog()
    for trace in log:
        reduced_trace = log_instance.Trace()
        for event in trace:
            if event['concept:name'] in selected_activities:  reduced_trace.append(event)
        sublog.append(reduced_trace)
    return sublog

def create_test_sublog_iteratively(log,max_n): # does not work correctly
    sublog = log_instance.EventLog()
    all_activities = variant_extractor.get_event_labels(log,'concept:name')
    combination_list = []
    for n in range(1,min(len(all_activities)+1,max_n)):
        for combination in itertools.combinations(all_activities,n):
            for trace in log:
                reduced_trace = log_instance.Trace()
                for event in trace:
                    if event['concept:name'] in combination:  reduced_trace.append(event)
                sublog.append(reduced_trace)
            combination_list.append(sublog)
    return combination_list       

def recreate_frequency(sublog,alidict): 
    result = log_instance.EventLog()
    sub_variants = variant_extractor.get_trace_variants(sublog)[0]
    numbers = {}
    for subtrace in sublog:
        if hashable_trace(subtrace) not in numbers: numbers[hashable_trace(subtrace)] = 0
        numbers[hashable_trace(subtrace)] += 1
    for sub_var in sub_variants:
        number_of_aligned_traces = len(alidict[hashable_trace(sub_var)]) if hashable_trace(sub_var) in alidict else 0
        number_of_occurences_of_subtrace = numbers[hashable_trace(sub_var)]
        for i in range (0,number_of_aligned_traces):
            for j in range(0,(number_of_occurences_of_subtrace//number_of_aligned_traces)+(i<number_of_occurences_of_subtrace%number_of_aligned_traces)):
                result.append(alidict[hashable_trace(sub_var)][i])
    return result            

def generate_original_activity_delta(log,sublog):
    resultlist = []
    for k in range(0,len(log)):
        trace = log[k]
        subtrace = sublog[k]
        i,j = 0,0
        direct = False
        deltalist = []
        while j<len(trace) and i<len(subtrace):
            if name(subtrace[i])==name(trace[j]):
                i += 1
                j += 1
                if direct==True and i>1:
                    deltalist.append(0)
                elif i>1:
                    deltalist.append(1)
                direct = True
            else:
                j += 1
                direct = False    
        resultlist.append(deltalist)      
    return resultlist      

def recreate_frequency_with_delta(sublog,alidict,oriactdelta,minedactdeltas): 
    result = log_instance.EventLog()
    sub_variants = variant_extractor.get_trace_variants(sublog)[0]
    for sub_var in sub_variants:
        seT = {}
        for i in range(0,(len(alidict[hashable_trace(sub_var)]) if hashable_trace(sub_var) in alidict else 0)):
            if tuple(minedactdeltas[hashable_trace(sub_var)][i]) in oriactdelta[hashable_trace(sub_var)]:
                seT.setdefault(tuple(minedactdeltas[hashable_trace(sub_var)][i]),[]).append(alidict[hashable_trace(sub_var)][i])     
        for key in seT:
            number_of_aligned_traces = len(seT[key])
            number_of_occurences_of_subtrace =  oriactdelta[hashable_trace(sub_var)][key]
            for i in range(0,number_of_aligned_traces):
                for _ in range(0,(number_of_occurences_of_subtrace//number_of_aligned_traces)+(i<number_of_occurences_of_subtrace%number_of_aligned_traces)):
                    result.append(seT[key][i])
    return result  




            



# Metrics

def case_disclosure(log):
    activities = net.transitions
    activities = list(map(str,activities))
    n_values = []
    for length in range(1,len(activities)+1):
        values = []
        for combination in itertools.combinations(activities,length):
            comb_list =list(combination)
            variant_number = 0
            for  variant in log:
                if set(comb_list).issubset(set([x['concept:name'] for x in variant])):
                    variant_number += 1
            if(variant_number>0):
                values.append(1/variant_number)
            #else:                          need to count 0 values?
            #    values.append(0)
        if values.__len__() > 0:      
            n_values.append(round(sum(values)/len(values),4))  
        else:
            break   
            
    return n_values        

def trace_disclosure(log):
    activities = list(map(str,net.transitions))
    newlog = log_instance.EventLog()
    for trace in log:
        newtrace = [{'concept:name': event['concept:name']} for event in trace]
        newlog.append(newtrace)
    n_values = []
    for length in range(1,len(activities)):
        values = []
        for combination in itertools.combinations(activities,length):
            comb_list =list(combination)
            correct_traces = {}
            for  variant in log:
                variant = tuple(event['concept:name'] for event in variant)
                if set(comb_list).issubset(set(variant)):
                    if variant in correct_traces.keys():
                        correct_traces[variant] += 1
                    else:
                        correct_traces[variant] = 1 
            ent = 0
            max_ent = 0
            if correct_traces:
                ent = 0 - sum(map(lambda key: correct_traces[key]/len(newlog)*math.log2(correct_traces[key]/len(newlog)),correct_traces.keys()))
                max_ent = math.log2(len(list(correct_traces)))
                #print("correcttraces",correct_traces.values())
                values.append(ent / max_ent)
        if len(values) > 0:      
            n_values.append(round(sum(values)/len(values),4))  
        else:
            break   
    return n_values

def ali_case_disclosure(log,sublog):
    values = []
    for subtrace in sublog:
        variant_number = 0
        for trace in log:
            i,j = 0,0
            while i<len(subtrace) and j<len(trace):
                if subtrace[i]['concept:name']==trace[j]['concept:name']:
                    i += 1
                    j += 1
                else:
                    j += 1
            if i==len(subtrace):
                variant_number += 1        
        if variant_number>0:
            values.append(1/variant_number)    
    if len(values) > 0:      
        return round(sum(values)/len(values),4)  
    else:
        return -1      

def ali_case_disclosure_with_recursion(log,sublog,fullfindings):
    comp_ff = fullfindings
    for subtrace in sublog:
        variant_found = False
        variable_trace = []
        for trace in log:
            i,j = 0,0
            while i<len(subtrace) and j<len(trace):
                if subtrace[i]['concept:name']==trace[j]['concept:name']:
                    i += 1
                    j += 1
                else:
                    j += 1
            if i==len(subtrace):
                if not variant_found:
                    variable_trace = trace
                    variant_found = True
                else:
                    variant_found = False
                    break
        if variant_found and variable_trace!=[]:
            newlog = log_instance.EventLog()
            newsublog = log_instance.EventLog()
            for trace in log:
                if trace!= variable_trace:
                    newlog.append(trace)
            for trace in sublog:
                if trace!= subtrace:
                    newsublog.append(trace)        
            log = newlog
            sublog = newsublog
            fullfindings += 1        
    if fullfindings>comp_ff:      
        return ali_case_disclosure_with_recursion(log,sublog,fullfindings)
    elif fullfindings == comp_ff:
        loglen = len(log)
        acd = ali_case_disclosure(log,sublog)  
        return round((acd*loglen+fullfindings)/(loglen+fullfindings),4)   
    
def ali_case_disclosure_reverse(log,sublog,is_metric):
    sublog_act = variant_extractor.get_event_labels(sublog,'concept:name')
    sublog = variant_extractor.get_trace_variants(sublog)[0]
    trace_mapping = {}
    hit,total = 0,0
    for trace in log:
        mod_trace = [act['concept:name'] for act in trace if act['concept:name'] in sublog_act]
        intersection = [mod_trace for subtrace in sublog if list(subtrace)==mod_trace]
        if len(intersection) == 1: 
            hit += 1
            trace_mapping.setdefault(hashable_trace(intersection[0]),[]).append(trace)
        total += 1
    if is_metric:
        return round(hit/total,4)   
    if not is_metric:
        return trace_mapping

def log_differential(log1,log2):
    log1 = variant_extractor.project_traces(log1)
    log2 = variant_extractor.project_traces(log2)
    miss_l2 = 0
    for trace in log1:
        if trace[1:-1] not in log2: 
            miss_l2 += 1
    return (miss_l2,len(log2)-(len(log1)-miss_l2))    

def log_differential_variants(log1,log2):
    log1 = variant_extractor.get_trace_variants(log1)
    log2 = variant_extractor.get_trace_variants(log2)

    missl2 = 0
    for trace in log1:
        if trace not in log2: missl2 += 1
    return (missl2,len(log2)-(len(log1)-missl2))    # missl1 = l2 - all intersection of both logs

def log_differential_variants_sss(log1,log2,show_traces=False):
    if show_traces:
        print("logdiff start")
    log1 = variant_extractor.project_traces(log1)
    log2 = variant_extractor.project_traces(log2)

    missl2 = 0
    for trace in log1:
        if trace not in log2: 
            missl2 += 1
            if show_traces: print(trace)
    if not show_traces:
        return (missl2,len(log2)-(len(log1)-missl2))    # missl1 = l2 - all intersection of both logs
    else:
        missl1 = 0
        for trace in log2:
            if trace not in log1: 
                missl1 += 1
                print(trace)
        return (missl1,missl2)


def activity_delta(alidict):
    blidict = {}
    for key in alidict:
        list = alidict[key]
        keydeltalist = []
        for trace in list:
            i,j = 0,0
            direct = False
            deltalist = []
            while j<len(trace)-1 and i<len(key):
                if key[i]==trace[j]['concept:name']:
                    i += 1
                    j += 1
                    if direct==True and i>1:
                        deltalist.append(0)
                    elif i>1:
                        deltalist.append(1)
                    direct = True
                else:
                    j += 1
                    direct = False     
            keydeltalist.append(deltalist)
        blidict[key]=keydeltalist
    return blidict     
                
def guess_chance(sublog,alidict): 
    hit,total = 0,0
    sub_variants = variant_extractor.get_trace_variants(sublog)[0]
    numbers = {}
    for subtrace in sublog:
        if subtrace not in numbers: numbers[hashable_trace(subtrace)] = 0
        numbers[hashable_trace(subtrace)] += 1
    for sub_var in sub_variants:
        candidates = len(alidict[hashable_trace(sub_var)]) if hashable_trace(sub_var) in alidict else -1
        occured = numbers[hashable_trace(sub_var)]
        if candidates >= 0:
            hit += (1/candidates)*occured
        total += occured
    return hit/total   

def gap_diff(sublog,alidict):
    hit,total = 0,0
    sub_variants = map(lambda x: tuple(x),variant_extractor.get_trace_variants(sublog)[0])
    numbers = {}
    for subtrace in sublog:
        numbers[hashable_trace(subtrace)] = numbers.setdefault(hashable_trace(subtrace),0) + 1
    for sub_var in sub_variants:
        print(sub_var)
        print(numbers[sub_var])
        list_of_lists = [[]]
        i = 0
        if sub_var not in alidict: continue
        if len(alidict[sub_var])==1:
            hit += numbers[sub_var]
            continue
        for full_possible_trace in alidict[sub_var]:
            list_of_lists[i].append([])
            for event in full_possible_trace[1:-1]:
                event = name(event)
                if event in sub_var:
                    list_of_lists[i].append([])
                elif event not in sub_var:
                    list_of_lists[i][-1].append(event)    
            print("lol_indented",list_of_lists[i])
            list_of_lists.append([])
            i += 1
        for i in range(0,len(sub_var)+1):
            if all(list_of_lists[0][i]==bab for bab in [lisst[i] for lisst in list_of_lists if lisst]):
                hit += len(list_of_lists[0][i])*numbers[sub_var]/len([item for sublist in list_of_lists for item in sublist])
            elif all(set(list_of_lists[0][i])==bab for bab in [set(lisst[i]) for lisst in list_of_lists if lisst]): 
                hit += (numbers[sub_var]/len(list_of_lists[0][i]))/len([item for sublist in list_of_lists for item in sublist]) 
            print("hit",i,hit)       
        total += numbers[sub_var]
    return hit/total

                
def guess_chance2(log,sublog,alidict): 
    hit,total = 0,0
    variants = variant_extractor.get_trace_variants(log)[0]
    sub_variants = variant_extractor.get_trace_variants(sublog)[0]

    numbers = {}
    for subtrace in sublog:
        if subtrace not in numbers: numbers[hashable_trace(subtrace)] = 0
        numbers[hashable_trace(subtrace)] += 1
    for sub_var in sub_variants:
        candidates = len(alidict[hashable_trace(sub_var)]) if hashable_trace(sub_var) in alidict else -1
        occured = numbers[hashable_trace(sub_var)]
        full_trace_real = variant_extractor.project_traces(alidict[hashable_trace(sub_var)]) if hashable_trace(sub_var) in alidict else "no" in variants
        if candidates >= 0 and full_trace_real:
            hit += (1/candidates)*occured
        total += occured
    return hit/total   




# Import Files

net, initial_marking, final_marking = petri_importer.import_net('./logandother/phone/tau=0.9/petri_net.pnml')

original_log = xes_importer.import_log('./logandother/phone/phone.xes')

# Generate Logs

event_log = apply_playout(net,initial_marking,final_marking)

sub_log = create_test_sublog(original_log,0.7)

ali_dict = ali_case_disclosure_reverse(event_log,sub_log,False)

reconstructed_log = recreate_frequency(sub_log,ali_dict)

# Export Files

exporter.apply(reconstructed_log, './logandother/phone/tau=0.9/fulllog.xes')

# Use Metrics

print("td original:",trace_disclosure(original_log))
print("cd original:",case_disclosure(original_log))
print("ali original:", ali_case_disclosure_reverse(event_log,sub_log,True))

print("td reconstruct:",trace_disclosure(reconstructed_log))
print("cd reconstruct:",case_disclosure(reconstructed_log))

act_delta = activity_delta(ali_dict)
ori_act_delt = generate_original_activity_delta(original_log,sub_log)
ori_act_delt_dict = ori_act_delt_list_to_dict(original_log,ori_act_delt,sub_log)

rfwd = recreate_frequency_with_delta(sub_log,ali_dict,ori_act_delt_dict,act_delta) 

exporter.apply(rfwd, './logandother/phone/fyllyg.xes')

print("chanceguess",guess_chance(sub_log,ali_dict))
print("logdiff:",log_differential(reconstructed_log,original_log))


#print("gapdiff",gap_diff(sub_log,ali_dict))


#print("log diff:",log_differential(event_log,original_log))

#all_sublogs = create_test_sublog_iteratively(original_log,2)

#values = []
#print("a sublogs",all_sublogs,"end sublogs")

#for sublog in all_sublogs:
#    val = ali_case_disclosure_reverse(event_log,sublog,True)
#    print("subsub",sublog)
#    print("busbus",sub_log_ori)
#    values.append(val)
#print(len(values))    
#print("different ali test",round(sum(values)/len(values),4))


#for i in range(1,80):
#    subsub = create_test_sublog(original_log,0.9)
#    val = ali_case_disclosure_reverse(event_log,subsub,True)
#    values.append(val)
#print(sum(values)/len(values))



taus = ["0.4","0.5","0.6","0.7","0.8","0.9"]


splits = [
        {1:['B', 'D', 'A', 'W', 'L'],2:['K', 'C', 'N', 'F', 'X', 'G', 'E', 'Y', 'M']},
        {1:['C', 'A', 'N', 'X', 'E', 'L'],2:['K', 'D', 'W', 'Y', 'F', 'M', 'G', 'B']},
        {1:['N', 'F', 'X', 'L'],2:['M', 'C', 'A', 'Y', 'D', 'G', 'W', 'K', 'B', 'E']},
        {1:['F', 'Y', 'K', 'L', 'M', 'E'],2:['C', 'B', 'A', 'W', 'D', 'G', 'N', 'X']},
        {1:['N', 'B', 'W', 'C'],2:['D', 'X', 'E', 'L', 'F', 'A', 'M', 'Y', 'K', 'G']},
        {1:['A', 'L', 'K', 'F'],2:['N', 'E', 'G', 'C', 'B', 'Y', 'M', 'W', 'D', 'X']},
        {1:['Y', 'N', 'D', 'F', 'W', 'M'],2:['K', 'A', 'X', 'G', 'E', 'L', 'C', 'B']},
        {1:['Y', 'K', 'M', 'G', 'L', 'X', 'N', 'B'],2:['W', 'E', 'A', 'D', 'C', 'F']},
        {1:['X', 'K', 'E', 'C', 'G', 'W'],2:['M', 'N', 'A', 'B', 'D', 'Y', 'F', 'L']},
        {1:['A', 'X', 'B', 'Y', 'C', 'G', 'D', 'E'],2:['N', 'L', 'M', 'F', 'K', 'W']}
    ]


log = xes_importer.apply('./logandother/random letters/random_letters.xes')

#sublogi = xes_importer.apply('./logandother/random letters/random_letters_sub1.xes')


for tau in taus:
    print("Tau value:",tau)
    net, initial_marking, final_marking    = petri_importer.import_net('./logandother/random letters/{}/tau='+tau+'/petri_net.pnml')
    log = apply_playout(net,initial_marking,final_marking)


    for split in splits:
        net2, initial_marking2, final_marking2 = petri_importer.import_net('./logandother/random letters/'+str(split)+'/tau='+tau+'/petri_net.pnml')
        log2 = apply_playout(net2,initial_marking2,final_marking2)
        sublog = create_test_sublog_with_act(log,split[1])

        ali_dict_zero = ali_case_disclosure_reverse(log,sublog,False)
        gc_zero = round(guess_chance2(log,sublog,ali_dict_zero),4)

        ali_dict_split = ali_case_disclosure_reverse(log2,sublog,False)
        gc_split = round(guess_chance2(log,sublog,ali_dict_split),4)

        print("GC for",split,gc_zero,"vs",gc_split)

        #res = log_differential_variants_sss(log,log2)  
        #print("log diff for",split,":",res,len(log2))

'''
        print("log")
        for trace in log:
            print(name(trace))
        print("log2")
        for trace in log2:
            print(name(trace))
'''

