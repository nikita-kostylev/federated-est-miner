import pathlib
import logging
import os
import csv
import time
import copy
from itertools import combinations,chain
import networkx as nx 
from functools import reduce

from pm4py.algo.discovery.est_miner.builder \
import EstMinerDirector, TestEstMinerBuilder, StandardEstMinerBuilder, \
MaxCutoffsAbsFreqEstMinerBuilder, MaxCutoffsRelTraceFreqEstMinerBuilder, \
RestrictBlueEdgesAndMaxCutoffsAbsTraceFreqEstMinerBuilder, \
MaxUnderfedAvgTraceOccEstMinerBuilder, MaxUnderfedAvgFirstOccIndexEstMinerBuilder, \
AlternativeInterestingPlacesEstMinerBuilder, RestrictNumInAndOutTransitionsEstMinerBuilder, \
MaxCutoffsAverageFirstOccurrenceIndexEstMinerBuilder, \
MaxCutoffsAverageTraceOccurrenceEstMinerBuilder, \
MaxCutoffsAbsoluteTraceFrequencyEstMinerBuilder, MaxCutoffsAbsoluteActivityFrequencyEstMinerBuilder, \
InterestingPlacesEstMinerBuilder,ModifiedStandardEstMinerBuilder

# InterestingPlacesAntiSelfLoopsEstMinerBuilder    TODO removed for compatibility
# ColoredDfgEstMinerBuilder    TODO removed for compatibility
from pm4py.algo.discovery.est_miner.utils.place import Place
from pm4py.objects.log.importer.xes import factory as xes_importer
from pm4py.objects.petri.check_soundness import check_petri_wfnet_and_soundness
from pm4py.visualization.petrinet.factory import apply, view, save
from pm4py.evaluation.generalization import factory as generalization_factory
from pm4py.evaluation.precision import factory as precision_factory
from pm4py.evaluation.replay_fitness import factory as fitness_factory
from pm4py.evaluation.simplicity import factory as simplicity_factory
from experiments.logging.logger import RuntimeStatisticsLogger
import experiments.visualization.charts as charts
from pm4py.algo.discovery.inductive import factory as inductive_miner
from pm4py.algo.discovery.alpha import factory as alpha_miner
from pm4py.algo.filtering.log.variants import variants_filter
from pm4py.statistics.traces.log import case_statistics
from pm4py.objects.petri.exporter import pnml as pnml_exporter
from pm4py.objects import petri


data_set_paths = [
#    os.path.join(pathlib.Path.home(), 'Documents', 'Studium', 'Masterarbeit', 'experimental-eval', 'dominiks-log'),
#    os.path.join(pathlib.Path.home(), 'Documents', 'Studium', 'Masterarbeit', 'experimental-eval', 'artificial-xor-test-set'),
     #os.path.join(pathlib.Path.home(),'GitRepos', 'eST-MIner Python Master', 'eST-Python', 'Python', 'logandother','nointerrupt'),
     #os.path.join(pathlib.Path.home(),'GitRepos', 'eST-MIner Python Master', 'eST-Python', 'Python', 'logandother','phone'),
     #os.path.join(pathlib.Path.home(),'GitRepos', 'eST-MIner Python Master', 'eST-Python', 'Python', 'logandother','soc'),
     #os.path.join(pathlib.Path.home(),'GitRepos', 'eST-MIner Python Master', 'eST-Python', 'Python', 'logandother','silicon'),
     #os.path.join(pathlib.Path.home(),'GitRepos', 'eST-MIner Python Master', 'eST-Python', 'Python', 'logandother','battery'),
     #os.path.join(pathlib.Path.home(),'GitRepos', 'eST-MIner Python Master', 'eST-Python', 'Python', 'logandother','screen'),
     #os.path.join(pathlib.Path.home(),'GitRepos','eST-MIner Python Master','eST-Python','Python','logandother','random letters')
     os.path.join(pathlib.Path.home(),'GitRepos','eST-MIner Python Master','eST-Python','Python','logandother','bpi13')
     #os.path.join(pathlib.Path.home(),'GitRepos','eST-MIner Python Master','eST-Python','Python','homomorph code')
    
]


data_set_file_names = [
#    'APM_Assignment_1.xes',
#    'Log-dependencyXOR1.xes',
     #'reducedXXX.xes',
     #'TestFileS.xes'
     #'a.xes'
     #'onlyoneorg.xes'
     #'keinefehler.xes'
     #'phone.xes',
     #'soc.xes',
     #'silicon.xes',
     #'battery.xes',
     #'screen.xes',
     #'random_letters.xes',
     #'reduced_log.xes',
     'BPI13.xes'
]

tau_folder    = 'tau={tau}'
result_folder = 'res'
log_folder    = 'out-logs'
charts_folder = 'charts'
statistics_file_name = 'statistics.csv'
conformance_stats_file = 'conformance.csv'

NUM_RUNS = 1

'''def evaluate_net(log, net, initial_marking, final_marking, path):                TODO maybe reactivate again when comparing modified eSTMiner to original
    fitness = fitness_factory.apply(log, net, initial_marking, final_marking)
    precision = precision_factory.apply(log, net, initial_marking, final_marking)
    generalization = generalization_factory.apply(log, net, initial_marking, final_marking)
    simplicity = simplicity_factory.apply(net)
    avg_trans_in_degree, avg_trans_out_degree, avg_place_in_degree, avg_place_out_degree = simplicity_factory.apply(net, variant="avg_degree")
    num_edges = simplicity_factory.apply(net, variant="num_edges")
    column_names = [
        'fitness', 
        'precision', 
        'generalization', 
        'simplicity', 
        'avg-trans-in-degree', 
        'avg-trans-out-degree',
        'avg-place-in-degree',
        'avg-place-out-degree',
        'num-edges'
    ]
    row = []
    row.append(fitness)
    row.append(precision)
    row.append(generalization)
    row.append(simplicity)
    row.append(avg_trans_in_degree)
    row.append(avg_trans_out_degree)
    row.append(avg_place_in_degree)
    row.append(avg_place_out_degree)
    row.append(num_edges)
    
    with open(os.path.join(path, conformance_stats_file), 'w') as file:
        writer = csv.writer(file)
        writer.writerow(column_names)
        writer.writerow(row)
    file.close()
    #charts.plot_evaluation(fitness, precision, generalization, simplicity, os.path.join(path, est_miner_name, charts_folder, 'metrics.pdf'))'''

def execute_miner(est_miner, parameters, folder, log_file_name,split_string):
    tau_sub_folder = tau_folder.format(tau=parameters['tau'])
    #est_miner.name = "Standart"
    # make sure all folders are there
    if not os.path.exists(os.path.join(folder, split_string)):    
        os.makedirs(os.path.join(folder, split_string))
    if not os.path.exists(os.path.join(folder, split_string, tau_sub_folder, charts_folder)):
        os.makedirs(os.path.join(folder, split_string, tau_sub_folder, charts_folder))
    if not os.path.exists(os.path.join(folder, split_string, tau_sub_folder)):
        os.makedirs(os.path.join(folder, split_string, tau_sub_folder))
    if not os.path.exists(os.path.join(folder, split_string, tau_sub_folder, result_folder)):
        os.makedirs(os.path.join(folder, split_string, tau_sub_folder, result_folder))
    if not os.path.exists(os.path.join(folder, split_string, tau_sub_folder, log_folder)):
        os.makedirs(os.path.join(folder, split_string, tau_sub_folder, log_folder))
    if not os.path.exists(os.path.join(folder, split_string, tau_sub_folder, charts_folder)):
        os.makedirs(os.path.join(folder, split_string, tau_sub_folder, charts_folder))

    # activate logging
    #file_handler = logging.FileHandler(os.path.join(folder, tau_sub_folder, est_miner.name, log_folder, 'res.log'), mode='w')
    #logger = logging.getLogger(est_miner.name)
    #logger.addHandler(file_handler)
    #logger.setLevel(logging.INFO)
    log = xes_importer.apply(os.path.join(folder,log_file_name))
    net, im, fm, stat_logger = est_miner.apply(log, parameters=parameters)
    #evaluate_net(log, net, im, fm, os.path.join(folder, tau_sub_folder, est_miner.name, result_folder))  TODO my
    #gviz = apply(net, initial_marking=im, final_marking=fm)
    #print("EstMiner Name",est_miner.name)
    #save(gviz, os.path.join(folder,tau_sub_folder,est_miner.name,"petri_net.png"))
    #create_statistic(stat_logger, os.path.join(folder, tau_sub_folder, est_miner.name, charts_folder))
    #stat_logger.to_file(os.path.join(folder, tau_sub_folder, est_miner.name, 'stat_logger.StatLogger'))
    return stat_logger,net,im,fm

'''def create_statistic(stat_logger, path):             TODO maybe reactivate later, when comparing modified eSTMiner with original
    # write to file
    # charts
    charts.plot_runtimes(stat_logger, os.path.join(path, 'runtimes.pdf'))
    charts.plot_runtimes(stat_logger, os.path.join(path, 'runtimes.png'))
    charts.plot_pruned_places(stat_logger, os.path.join(path, 'cutoffs.pdf'))
    charts.plot_pruned_places(stat_logger, os.path.join(path, 'cutoffs.png'))'''

def construct_est_miners():
    est_miners = list()
    est_miner_director = EstMinerDirector()
    standard_est_miner_builder = StandardEstMinerBuilder()
    modif_standard_est_miner_builder = ModifiedStandardEstMinerBuilder()


    avg_first_occ_index_est_miner_builder = MaxCutoffsAverageFirstOccurrenceIndexEstMinerBuilder()


    """skip for better performance 
    max_cutoffs_abs_trace_freq_est_miner_builder = MaxCutoffsAbsFreqEstMinerBuilder()
    max_cutoffs_rel_trace_freq_est_miner_builder = MaxCutoffsRelTraceFreqEstMinerBuilder()
    max_cutoffs_abs_trace_freq_restricted_blue_edges_est_miner_builder = RestrictBlueEdgesAndMaxCutoffsAbsTraceFreqEstMinerBuilder()
    #alpha_miner_refinment_search_est_miner_builder = AlphaMinerRefinementSearchEstMinerBuilder()
    max_underfed_avg_trace_occ_est_miner_builder = MaxUnderfedAvgTraceOccEstMinerBuilder()
    max_underfed_avg_first_occ_index_est_miner_builder = MaxUnderfedAvgFirstOccIndexEstMinerBuilder()
    alternative_interesting_places_est_miner_builder = AlternativeInterestingPlacesEstMinerBuilder()
    restrict_num_in_out_trans_est_miner_builder = RestrictNumInAndOutTransitionsEstMinerBuilder()
    #important_traces_est_miner_builder = ImportantTracesEstMinerBuilder()                                          TODO Removed for compatibility
    #reduce_complexity_est_miner_builder = PrePruningAndReduceComplexityPostProcessingEstMinerBuilder()             TODO Removed for compatibility
    #anti_self_loops_interesting_places_est_miner_builder = IntersetingPlacesAntiSelfLoopsEstMinerBuilder()         TODO Removed for compatibility
    #colored_dfg_est_miner_builder = ColoredDfgEstMinerBuilder()                                                    TODO Removed for compatibility
    avg_first_occurence_index_est_miner_builder = MaxCutoffsAverageFirstOccurrenceIndexEstMinerBuilder()
    avg_trace_occ_est_miner_builder = MaxCutoffsAverageTraceOccurrenceEstMinerBuilder()
    abs_trace_freq_est_miner_builder = MaxCutoffsAbsoluteTraceFrequencyEstMinerBuilder()
    abs_activity_freq_est_miner_builder = MaxCutoffsAbsoluteActivityFrequencyEstMinerBuilder()
    interesting_places_est_miner_builder = InterestingPlacesEstMinerBuilder()

    """
    
    est_miner_director.construct(modif_standard_est_miner_builder)
    #est_miner_director.construct(standard_est_miner_builder)  TODO Removed for speed
    est_miner_director.construct(avg_first_occ_index_est_miner_builder)
    
    """
    est_miner_director.construct(interesting_places_est_miner_builder)
    est_miner_director.construct(max_cutoffs_abs_trace_freq_est_miner_builder)
    est_miner_director.construct(max_cutoffs_rel_trace_freq_est_miner_builder)
    est_miner_director.construct(max_cutoffs_abs_trace_freq_restricted_blue_edges_est_miner_builder)
    #est_miner_director.construct(alpha_miner_refinment_search_est_miner_builder)
    est_miner_director.construct(max_underfed_avg_trace_occ_est_miner_builder)
    est_miner_director.construct(max_underfed_avg_first_occ_index_est_miner_builder)
    est_miner_director.construct(alternative_interesting_places_est_miner_builder)
    est_miner_director.construct(restrict_num_in_out_trans_est_miner_builder)
    #est_miner_director.construct(important_traces_est_miner_builder)                    TODO Removed for compatibility
    #est_miner_director.construct(reduce_complexity_est_miner_builder)                   TODO Removed for compatibility
    #est_miner_director.construct(anti_self_loops_interesting_places_est_miner_builder)  TODO Removed for compatibility
    #est_miner_director.construct(colored_dfg_est_miner_builder)                         TODO Removed for compatibility
    est_miner_director.construct(avg_first_occurence_index_est_miner_builder)
    est_miner_director.construct(avg_trace_occ_est_miner_builder)
    est_miner_director.construct(abs_trace_freq_est_miner_builder)
    est_miner_director.construct(abs_activity_freq_est_miner_builder)
    """


    #est_miners.append(standard_est_miner_builder.est_miner)  TODO Removed for speed
    #est_miners.append(avg_first_occ_index_est_miner_builder.est_miner)
    
    
    est_miners.append(modif_standard_est_miner_builder.est_miner) #REMOVED because other execution is faster for experiment

    #est_miners.append(interesting_places_est_miner_builder.est_miner)
    #est_miners.append(avg_first_occurence_index_est_miner_builder.est_miner)
    #est_miners.append(avg_trace_occ_est_miner_builder.est_miner)
    #est_miners.append(abs_trace_freq_est_miner_builder.est_miner)
    #est_miners.append(abs_activity_freq_est_miner_builder.est_miner)
    #est_miners.append(max_cutoffs_abs_trace_freq_est_miner_builder.est_miner)
    #est_miners.append(max_cutoffs_rel_trace_freq_est_miner_builder.est_miner)
    #est_miners.append(max_cutoffs_abs_trace_freq_restricted_blue_edges_est_miner_builder.est_miner)
    #est_miners.append(max_cutoffs_rel_trace_freq_heuristic_pruning_est_miner_builder.est_miner)
    #est_miners.append(alpha_miner_refinment_search_est_miner_builder.est_miner)
    #est_miners.append(max_underfed_avg_trace_occ_est_miner_builder.est_miner)
    #est_miners.append(max_underfed_avg_first_occ_index_est_miner_builder.est_miner)
    #est_miners.append(interest_places_pre_pruning_est_miner_builder.est_miner)
    #est_miners.append(alternative_interesting_places_est_miner_builder.est_miner)
    #est_miners.append(restrict_num_in_out_trans_est_miner_builder.est_miner)
    #est_miners.append(important_traces_est_miner_builder.est_miner)
    #est_miners.append(reduce_complexity_est_miner_builder.est_miner)
    #est_miners.append(anti_self_loops_interesting_places_est_miner_builder.est_miner)
    #est_miners.append(colored_dfg_est_miner_builder.est_miner)

    return est_miners

'''def create_dataset_charts(stat_loggers, path):           TODO probably not needed
    # charts
    charts.plot_runtime_comparison(stat_loggers, os.path.join(path, charts_folder, 'runtime_comp.pdf'))
    charts.plot_runtime_comparison(stat_loggers, os.path.join(path, charts_folder, 'runtime_comp.png'))'''

'''def save_stats_to_file(stat_logger, path):               TODO when comparing to modified estMiner and original
    if not os.path.exists(path):
        os.makedirs(path)
    column_names = [
        'MinerName', 
        'AlgoRunTime(s)', 
        'SearchRunTime(s)',
        'PostProcessingRunTime(s)',
        'PrunedPlaces'
    ]


    row = []
    row.append(stat_logger.est_miner_name)
    row.append(stat_logger.algo_runtime(unit='s'))
    row.append(stat_logger.search_runtime(unit='s'))
    row.append(stat_logger.post_processing_runtime(unit='s'))
    row.append(stat_logger.total_pruned_places())
    
    if not os.path.isfile(os.path.join(path, statistics_file_name)):
        with open(os.path.join(path, statistics_file_name), 'w') as file:
            writer = csv.writer(file)
            writer.writerow(column_names)
        file.close()

    with open(os.path.join(path, 'statistics.csv'), 'a') as file:
        writer = csv.writer(file)
        writer.writerow(row)
    file.close()'''

def check_possible_partition(net,partition):
    itemsets = []
    for place in partition:
        itemsets.append(set([arc.source.name for arc in place.in_arcs]+[arc.target.name for arc in place.out_arcs]))
    #print(itemsets)

    G = nx.Graph()
    for i, s in enumerate(itemsets):
        G.add_node(i, set=s)

    for i in range(len(itemsets)):
        for j in range(i + 1, len(itemsets)):
            if itemsets[i].intersection(itemsets[j]):  # Check for intersection
                G.add_edge(i, j)

    unified_sets = [set().union(*(G.nodes[node]['set'] for node in component)) for component in nx.connected_components(G)]

    rest_places = [place for place in net.places if place not in partition]
    rest_placesv2 = [place for place in rest_places if place.name[0]=='(']
    rest_placesv3 = [set([arc.source.name for arc in place.in_arcs]+[arc.target.name for arc in place.out_arcs]) for place in rest_placesv2]

    for place_trans in rest_placesv3:
        for part in unified_sets:
            if place_trans.issubset(part):
                #print("Error",place_trans,part)
                return False
    return True

def different_partition_generation(net):
    places = net.places
    placesv2 = [place for place in places if place.name[0]=='(']
    placesv3 = [place for place in placesv2 if not '[start>' in [arc.source.name for arc in place.in_arcs] and not '[end]' in [arc.target.name for arc in place.out_arcs]]
    placesv3.sort(key=lambda x: x.name)
    print("pv3 test",placesv3,net.places)
    possible_partitions = chain.from_iterable(combinations(placesv3, r) for r in range(len(placesv3) + 1))

    print("Possible Partitions amount",(2**len(placesv3)))

    work_number = 0
    for partition in possible_partitions:
        if check_possible_partition(net,partition):
            yield map(lambda x : x.name,partition)
        work_number += 1
        if work_number % 100000 == 0:
            print(work_number)  

def generate_1placeless_nets(net):
    test = 0


def execute_experiments():
    taus = [0.4]
    splits = [
    {},
    #{1:["Accepted","Completed"],2:["Queued"]},
    #{1:["Accepted","Queued"],2:["Completed"]},
    #{1:["Completed","Queued"],2:["Accepted"]}
    #{1:['A_SUBMITTED', 'A_PARTLYSUBMITTED', 'A_PREACCEPTED', 'W_Completeren aanvraag', 'A_ACCEPTED', 'O_SELECTED', 'A_FINALIZED', 'O_CREATED'],2:['O_SENT', 'W_Nabellen offertes', 'O_SENT_BACK', 'W_Valideren aanvraag', 'A_REGISTERED', 'A_APPROVED', 'O_ACCEPTED', 'A_ACTIVATED', 'O_CANCELLED', 'W_Wijzigen contractgegevens', 'A_DECLINED', 'A_CANCELLED', 'W_Afhandelen leads', 'O_DECLINED', 'W_Nabellen incomplete dossiers', 'W_Beoordelen fraude']},
    #{1:['A_SUBMITTED', 'A_PARTLYSUBMITTED', 'A_PREACCEPTED', 'W_Completeren aanvraag', 'A_ACCEPTED', 'O_SELECTED', 'A_FINALIZED', 'O_CREATED', 'O_SENT', 'W_Nabellen offertes', 'O_SENT_BACK', 'W_Valideren aanvraag', 'A_REGISTERED', 'A_APPROVED'],2:[ 'O_ACCEPTED', 'A_ACTIVATED', 'O_CANCELLED', 'W_Wijzigen contractgegevens', 'A_DECLINED', 'A_CANCELLED', 'W_Afhandelen leads', 'O_DECLINED', 'W_Nabellen incomplete dossiers', 'W_Beoordelen fraude']},
    #{1:['A_SUBMITTED', 'A_PARTLYSUBMITTED', 'A_PREACCEPTED', 'W_Completeren aanvraag', 'A_ACCEPTED', 'O_SELECTED', 'A_FINALIZED', 'O_CREATED', 'O_SENT', 'W_Nabellen offertes', 'O_SENT_BACK', 'W_Valideren aanvraag', 'A_REGISTERED', 'A_APPROVED', 'O_ACCEPTED', 'A_ACTIVATED', 'O_CANCELLED', 'W_Wijzigen contractgegevens', 'A_DECLINED', 'A_CANCELLED'],2:[ 'W_Afhandelen leads', 'O_DECLINED', 'W_Nabellen incomplete dossiers', 'W_Beoordelen fraude']},
    ]
    '''splits = [
        {},
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
    ]'''
    for split in splits:
        for tau in taus:
            est_miners = construct_est_miners()
            parameters = dict()
            parameters['key']   = 'concept:name'
            parameters['tau']   = tau
            parameters['split'] = split
            for i in range(0, len(data_set_paths)):
                stat_loggers = dict()
                tau_sub_folder = tau_folder.format(tau=parameters['tau'])
                split_string = str(split)
                if len(split_string) > 50:
                    split_string = str(len(split[1]))
                for est_miner in est_miners:
                    stat_logger,net,im,fm = execute_miner(est_miner, parameters, data_set_paths[i], data_set_file_names[i],split_string)  
                    pnml_exporter.export_net(net,im,os.path.join(data_set_paths[i],split_string, tau_sub_folder, 'petri_net.pnml'),fm)
                    gviz = apply(net, initial_marking=im, final_marking=fm)
                    save(gviz, os.path.join(data_set_paths[i],split_string,tau_sub_folder,"petri_net.png"))
                '''
                stat_loggers[est_miner.name] = list()
                long_net = 0
                for j in range(NUM_RUNS):
                    stat_logger,net,im,fm = execute_miner(est_miner, parameters, data_set_paths[i], data_set_file_names[i])  
                    pnml_exporter.export_net(net,im,os.path.join(data_set_paths[i], tau_sub_folder,est_miner.name, 'petri_net.pnml'),fm)
                    long_net = net
                partitions = different_partition_generation(long_net)
                iter = 0
                for part in partitions:
                    if not os.path.exists(os.path.join(data_set_paths[i], tau_sub_folder, "ModiTest",str(iter))):
                        os.makedirs(os.path.join(data_set_paths[i], tau_sub_folder, "ModiTest", str(iter)))
                    replaces = {place for place in long_net.places if place.name not in part}
                    rearcs = {arc for arc in long_net.arcs if not(arc.source.name in part and arc.target.name in part)}  
                    mod_net = petri.petrinet.PetriNet(places=replaces, arcs=rearcs, transitions=long_net.transitions)
                    pnml_exporter.export_net(net,im,os.path.join(data_set_paths[i], tau_sub_folder,"ModiTest",str(iter), 'petri_net.pnml'),fm)
                    
                    iter += 1
                
                    
                    #save_stats_to_file(stat_logger, os.path.join(data_set_paths[i], tau_sub_folder, 'stats'))  TODO my
                    #stat_loggers[est_miner.name].append(stat_logger)
            #create_dataset_charts(stat_loggers, os.path.join(data_set_paths[i], tau_sub_folder))
            #save_stats_to_file(stat_loggers, os.path.join(data_set_paths[i], tau_sub_folder, 'stats'))
            '''

            ''' comparison to alpha and inductive TODO when comparing to other miners?
            if not os.path.exists(os.path.join(data_set_paths[i], tau_sub_folder, 'INDUCTIVE', result_folder)):
                os.makedirs(os.path.join(data_set_paths[i], tau_sub_folder, 'INDUCTIVE', result_folder))
            if not os.path.exists(os.path.join(data_set_paths[i], tau_sub_folder, 'ALPHA', result_folder)):
                os.makedirs(os.path.join(data_set_paths[i], tau_sub_folder, 'ALPHA', result_folder))
            print(os.path.join(data_set_paths[i],data_set_file_names[i]))    
            log = xes_importer.import_log(os.path.join(data_set_paths[i],data_set_file_names[i])) 
            #log = variants_filter.apply_auto_filter(log, parameters={'decreasingFactor': 0.9})
            start_time = time.time()
            net, initial_marking, final_marking = inductive_miner.apply(log, variant='imdfa')
            end_time = time.time()
            print('Inductive:')
            print(end_time - start_time)
            gviz = apply(net, initial_marking=initial_marking, final_marking=final_marking)
            save(gviz, os.path.join(data_set_paths[i], tau_sub_folder, 'INDUCTIVE', result_folder, 'net.png'))
            evaluate_net(log, net, initial_marking, final_marking,  
                os.path.join(data_set_paths[i], tau_sub_folder, 'INDUCTIVE', result_folder)
            ) 
            print('Alpha')
            log = xes_importer.import_log(os.path.join(data_set_paths[i],data_set_file_names[i])) 
            net, initial_marking, final_marking = alpha_miner.apply(log)
            gviz = apply(net, initial_marking=initial_marking, final_marking=final_marking)
            save(gviz, os.path.join(data_set_paths[i], tau_sub_folder, 'ALPHA', 'net.png'))
            #evaluate_net(log, net, initial_marking, final_marking, os.path.join(data_set_paths[i], tau_sub_folder, 'ALPHA', result_folder))  
            '''
            

if __name__ == "__main__":
    execute_experiments()







