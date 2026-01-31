import typing
from ..generic.Rules import add_rule

def set_rules(multiworld, options, player):
    """
    Set up rules for progressive song unlocking.
    
    With progressive items, the logic is simple:
    - Each location requires a certain number of "Progressive Song Unlock" items
    - Node 0 is always accessible (free)
    - Node N requires N "Progressive Song Unlock" items
    """
    
    for node_id in range(options.num_tracks):
        location = multiworld.get_location(f"Node {node_id:02d}", player)
        
        # Node 0 is always accessible (starting song)
        if node_id == 0:
            continue
        
        # Node N requires N progressive items
        # This means: node 1 needs 1 item, node 2 needs 2 items, etc.
        required_count = node_id
        
        # Use add_rule to set the access requirement
        add_rule(
            location,
            lambda state, count=required_count: state.has("Progressive Song Unlock", player, count)
        )
    
    # Completion condition: have all progressive items (or reach all locations)
    multiworld.completion_condition[player] = lambda state: state.has("Progressive Song Unlock", player, options.num_tracks - 1)