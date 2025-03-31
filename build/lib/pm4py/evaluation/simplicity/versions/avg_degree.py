def apply(petri_net, parameters=None):
    """
    Measures the average in-degree and average out-degree for places
    and transitions within the given net.
    Parameters
    -----------
    petri_net
        Petri net
    parameters
        Possible parameters of the algorithm

    Returns
    -----------
    avg_<node_type>_in_degree
        Average in degree of each node (place or transition) in the net
    avg_<node_type>_out_degree
        Average out degree of each node (place or transition) in the net
    """
    avg_transition_in_degree  = 0.0
    avg_transition_out_degree = 0.0
    avg_place_in_degree  = 0.0
    avg_place_out_degree = 0.0

    for transition in petri_net.transitions:
        avg_transition_in_degree  += len(transition.in_arcs)
        avg_transition_out_degree += len(transition.out_arcs)
    avg_transition_in_degree  = avg_transition_in_degree  / len(petri_net.transitions)
    avg_transition_out_degree = avg_transition_out_degree / len(petri_net.transitions)

    for place in petri_net.places:
        avg_place_in_degree  += len(place.in_arcs)
        avg_place_out_degree += len(place.out_arcs)
    avg_place_in_degree  = avg_place_in_degree  / len(petri_net.places)
    avg_place_out_degree = avg_place_out_degree / len(petri_net.places)

    return avg_transition_in_degree, avg_transition_out_degree, avg_place_in_degree, avg_place_out_degree

