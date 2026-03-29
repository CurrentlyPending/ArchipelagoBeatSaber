from BaseClasses import Region
from .Locations import BSLocation, location_name_to_id



def create_regions(world, player):
    region = Region("Menu", player, world.multiworld, "Menu")

    # Add locations from the appropriate category groups
    if world.randomized_game_mode:
        for song_locs in [world.speed_song_location_groups, world.tech_song_location_groups,
                          world.midspeed_song_location_groups, world.acc_song_location_groups]:
            for location_name in song_locs:
                for loc_name in location_name:
                    loc = BSLocation(player, loc_name, location_name_to_id[loc_name], region)
                    region.locations.append(loc)
    else:
        for location_name in world.preset_song_location_groups:
            # Flatten the list of location lists (one list per song)
            for loc_name in location_name:
                loc = BSLocation(player, loc_name, location_name_to_id[loc_name], region)
                region.locations.append(loc)

    world.multiworld.regions.append(region)
