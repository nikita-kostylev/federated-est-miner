def apply(petri_net, parameters=None):
    """
    Calculate the number of edges occurring in the Petri net.
    """
    edges = 0
    for transition in petri_net.transitions:
        edges += len(transition.in_arcs)
        edges += len(transition.out_arcs)
    return edges

