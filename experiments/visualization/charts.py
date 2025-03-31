import numpy as np
import matplotlib.pyplot as plt
import os

from experiments.logging.logger import RuntimeStatisticsLogger

def plot_runtime_comparison(stat_loggers, path):
    algo_runtimes = list()
    for loggers in stat_loggers.values():
        runtime = 0
        for stat_logger in loggers:
            runtime += stat_logger.algo_runtime(unit='s')
        runtime = runtime / len(loggers)
        algo_runtimes.append(runtime)

    runtimes = tuple(algo_runtimes)
    ticks    = tuple(stat_loggers.keys())

    index = np.arange(len(runtimes))

    plt.bar(index, runtimes, align='center')
    plt.xlabel('Miner')
    plt.ylabel('Runtime (s)')
    plt.title('Runtimes')
    plt.xticks(index, ticks, rotation='vertical')
    plt.tight_layout()
    plt.savefig(path)
    plt.close()

def plot_runtimes(stat_logger, path):
    runtimes = (
        stat_logger.algo_runtime(unit='ms'), 
        stat_logger.search_runtime(unit='ms'),
    #    stat_logger.replay_runtime(unit='ms'),
        stat_logger.post_processing_runtime(unit='ms')
    )

    index = np.arange(len(runtimes))

    plt.bar(index, runtimes, align='center')
    plt.xlabel('Phase')
    plt.ylabel('Time (ms)')
    plt.title('Runtime by Phases')
    plt.xticks(index, ('Algo', 'Search', 'Post-Proc.'))

    plt.savefig(path)
    plt.close()

def plot_evaluation(fitness, precision, generalization, simplicity, path):
    stats = (
        fitness['log_fitness'],
        precision,
        generalization,
        simplicity
    )
    
    index = np.arange(len(stats))

    plt.bar(index, stats, align='center')
    plt.xlabel('Metric')
    plt.ylabel('Value')
    plt.title('Evaluation Metrics')
    plt.xticks(index, ('Fit.', 'Prec.', 'Gener.', 'Simpl.'))

    plt.savefig(path)
    plt.close()

def plot_pruned_places(stat_logger, path):
    blue_pruned_places  = stat_logger.num_pruned_blue_places()
    red_pruned_places   = stat_logger.num_pruned_red_places()
    total_pruned_places = stat_logger.total_pruned_places()

    pruned_places = (
        total_pruned_places,
        blue_pruned_places,
        red_pruned_places
    )

    index = np.arange(3)

    plt.bar(index, pruned_places, align='center')
    plt.xlabel('Edge Type')
    plt.ylabel('Number')
    plt.title('Pruned Places')
    plt.xticks(index, ('All', 'Blue', 'Red'))

    plt.savefig(os.path.join(path))
    plt.close()
