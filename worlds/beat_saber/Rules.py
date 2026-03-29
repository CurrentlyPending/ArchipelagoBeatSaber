from ..generic.Rules import add_rule
from .Options import GameMode


def set_rules(world, options, player):
    """
    Set up rules for progressive song unlocking.

    Locations are grouped by song: each song has one or more grade locations
    (e.g. "Song (ExpertPlus) - C", "- B", "- A" for accuracy mode, or just
    "Song (ExpertPlus)" for pass mode). All grade locations for the same song
    share the same progressive-unlock requirement — they're parallel checks for
    the same underlying song unlock.

    Index 0 in each group list is the first/free song; no rule is added for it.
    """
    rule_count = 0
    
    if options.game_mode in (GameMode.option_randomizedAccuracy, GameMode.option_randomizedPass):
        for category_name, song_groups in [
            ("Speed", world.speed_song_location_groups),
            ("Tech", world.tech_song_location_groups),
            ("Midspeed", world.midspeed_song_location_groups),
            ("Acc", world.acc_song_location_groups),
        ]:
            print(f"\n{category_name}: {len(song_groups)} songs")
            for node_id, song_locs in enumerate(song_groups):
                print(f"  Song {node_id}: {len(song_locs)} locations (free={node_id==0})")
                rule_count += len(song_locs) if node_id > 0 else 0
    
    print(f"\nTotal locations with rules: {rule_count}")
    
    if options.game_mode in (GameMode.option_presetPass, GameMode.option_presetAccuracy):
        for node_id, song_locs in enumerate(world.preset_song_location_groups):
            if node_id == 0:
                continue
            for loc_name in song_locs:
                if options.lock_goal_map and loc_name == world.goal_location_name:
                    add_rule(
                        world.multiworld.get_location(loc_name, player),
                        lambda state: state.has("Bloq Key", player, options.bloq_keys_required.value)
                    )
                    print(f"Added rule for {loc_name}: requires {options.bloq_keys_required.value} Bloq Key(s)")
                else:
                    add_rule(
                        world.multiworld.get_location(loc_name, player),
                        lambda state, count=node_id: state.has("Progressive Song Unlock", player, count)
                    )

    elif options.game_mode in (GameMode.option_randomizedAccuracy, GameMode.option_randomizedPass):
        _set_category_rules(world, player, world.speed_song_location_groups, "Progressive Speed Unlock", options)
        _set_category_rules(world, player, world.tech_song_location_groups, "Progressive Tech Unlock", options)
        _set_category_rules(world, player, world.midspeed_song_location_groups, "Progressive Midspeed Unlock", options)
        _set_category_rules(world, player, world.acc_song_location_groups, "Progressive Accuracy Unlock", options)


def _set_category_rules(world, player, song_location_groups, unlock_item, options):
    """Apply progressive unlock rules to one category's grouped location list."""
    for node_id, song_locs in enumerate(song_location_groups):
        if node_id == 0:
            continue
        for loc_name in song_locs:
            location = world.multiworld.get_location(loc_name, player)

            # The goal location (highest grade of the goal song) also requires Bloq Keys
            if options.lock_goal_map and loc_name == world.goal_location_name:
                add_rule(
                    location,
                    lambda state: state.has("Bloq Key", player, options.bloq_keys_required.value)
                )
                print(f"Added rule for {loc_name}: requires {options.bloq_keys_required.value} Bloq Key(s)")
            else:
                add_rule(
                    location,
                    lambda state, count=node_id: state.has(unlock_item, player, count)
                )
