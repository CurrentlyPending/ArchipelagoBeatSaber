import typing

def generate_campain_layout(options, random, node_connections: typing.Dict[int, typing.Set[int]], node_layers: typing.Dict[int, typing.Set[int]]):
    # First, generate the campaign layout
    ## Step 1: Generate layers
    """
    node_layers[0] = []
    cur_layer = 0
    cur_track = 0
    while options.num_tracks - cur_track > 0:
        # How many tracks to utilize for this layer,
        # at least 1 and up to min(remaining locations, 4)
        # TODO: Also generate gates at some point?
        count = random.randint(1, min(options.num_tracks - cur_track, 4))
        node_layers[cur_layer] = list(range(cur_track,cur_track+count))
        cur_track += count
        cur_layer = max(node_layers.keys()) + 1
    ## Step 2: Generate connections
    nodes_occupied = []
    for cur_layer in range(len(node_layers)-1):
        exist_next_layer_conn = False
        for cur_node in node_layers[cur_layer]:
            node_connections[cur_node] = []
            if random.randint(1,3) >= 2: # 2/3 chance of a connection
                target_node = random.choice(node_layers[cur_layer+1])
                node_connections[cur_node].append(target_node)
                nodes_occupied.append(target_node)
                exist_next_layer_conn = True
        if not exist_next_layer_conn:
            # Unlucky, current layer has no connection to next. Choose one explicitly
            target_node = random.choice(node_layers[cur_layer+1])
            node_connections[random.choice(node_layers[cur_layer])] = [target_node]
            nodes_occupied.append(target_node)
    # Create empty connections for last layer
    for cur_node in node_layers[cur_layer+1]:
        node_connections[cur_node] = []
    # Multiple nodes cannot be unlocked at the start, so all without dependencies so far are assigned root as dependency
    for i in range(options.num_tracks):
        if i not in nodes_occupied and i != 0:
            node_connections[0].append(i)
    """
    return node_connections, node_layers