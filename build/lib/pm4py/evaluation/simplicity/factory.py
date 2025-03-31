from pm4py.evaluation.simplicity.versions import arc_degree
from pm4py.evaluation.simplicity.versions import avg_degree
from pm4py.evaluation.simplicity.versions import num_edges

SIMPLICITY_ARC_DEGREE = "arc_degree"
SIMPLICITY_AVG_DEGREE = "avg_degree"
SIMPLICITY_NUM_EDGES  = "num_edges"
VERSIONS = {
        SIMPLICITY_ARC_DEGREE: arc_degree.apply, 
        SIMPLICITY_AVG_DEGREE: avg_degree.apply,
        SIMPLICITY_NUM_EDGES:  num_edges.apply,
    }

def apply(petri_net, parameters=None, variant="arc_degree"):
    return VERSIONS[variant](petri_net, parameters=parameters)

