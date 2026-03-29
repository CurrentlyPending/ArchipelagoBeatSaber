import os
from random import Random, random
import typing
import json
import requests
import math

import worlds
from .PlaylistCreator import PlaylistCreator
from .Items import item_table, item_data_table, BSItem
from .Locations import BSLocation, location_name_to_id, id_to_location_name, ACCURACY_GRADES, get_highest_diff_idx, make_preset_mnemonic_name, make_randomized_mnemonic_name
from .Options import BSOptions, GameMode, MapTypeWeighting
from .Rules import set_rules
from .Regions import create_regions
from BaseClasses import Item, ItemClassification, Tutorial, Region
from ..AutoWorld import World, WebWorld
from .Container import BeatSaberContainer
from .PlaylistOutput import generate_randomized_output, generate_preset_output

class BSWeb(WebWorld):
    tutorials = [Tutorial(
        "Multiworld Setup Guide",
        "A guide to setting up Beat Saber for Multiworld.",
        "English",
        "setup_en.md",
        "setup/en",
        ["currentlypending"]
    )]

class BSWorld(World):
    """
     bloks
    """ #Lifted from Store Page

    game: str = "Beat Saber"
    topology_present = False
    web = BSWeb()

    item_name_to_id = item_table
    location_name_to_id = Locations.location_name_to_id

    # Only need connections for unlock logic, not layers
    node_connections: typing.Dict[int, typing.List[int]]

    speed_node_connections: typing.Dict[int, typing.List[int]]
    tech_node_connections: typing.Dict[int, typing.List[int]]
    midspeed_node_connections: typing.Dict[int, typing.List[int]]
    acc_node_connections: typing.Dict[int, typing.List[int]]

    options_dataclass = BSOptions

    campaign_name: str

    # Per-instance song data (NOT class-level defaults to avoid sharing across instances)
    processed_songs: typing.Dict[str, dict]
    node_to_song: typing.Dict[int, dict]
    sorted_songs: typing.List[dict]
    # Which songs are unlocked by default. For preset modes this is always just node 0; for randomized modes this can be multiple nodes across categories depending on settings.
    unlocked_nodes: typing.List[int] = []

    # Category song lists (randomized modes)
    speed_songs: typing.List[dict]
    tech_songs: typing.List[dict]
    midspeed_songs: typing.List[dict]
    acc_songs: typing.List[dict]

    # Locations grouped by song position: groups[song_index] = [grade_loc_name, ...]
    # Pass modes have one entry per song; accuracy modes have one per grade up to the threshold.
    # Randomized pp uses a different location method entirely.
    preset_song_location_groups: typing.List[typing.List[str]]
    speed_song_location_groups: typing.List[typing.List[str]]
    tech_song_location_groups: typing.List[typing.List[str]]
    midspeed_song_location_groups: typing.List[typing.List[str]]
    acc_song_location_groups: typing.List[typing.List[str]]

    # The location that holds the Victory item
    goal_location_name: str

    def create_regions(self):
        create_regions(self, self.player)

    def set_rules(self):
        set_rules(self, self.options, self.player)

    def create_item(self, name: str) -> Item:
        return BSItem(name, item_data_table[name].classification, item_data_table[name].code, self.player)

    def generate_early(self):
        # Initialize per-instance state
        self.location_name_to_id = location_name_to_id
        self.id_to_location_name = id_to_location_name
        self.location_name_to_mnemonic = {}  # Maps server-friendly generic names to client-friendly mnemonic names
        self.node_to_song = {}
        self.processed_songs = {}
        self.sorted_songs = []

        self.preset_song_location_groups = []
        self.speed_song_location_groups = []
        self.tech_song_location_groups = []
        self.midspeed_song_location_groups = []
        self.acc_song_location_groups = []

        self.goal_location_name = ""

        self.randomized_game_mode = self.options.game_mode == GameMode.option_randomizedPP or self.options.game_mode == GameMode.option_randomizedAccuracy or self.options.game_mode == GameMode.option_randomizedPass

        if self.randomized_game_mode:
            print("Generating randomized PP progression")

            speed_weight = tech_weight = midspeed_weight = acc_weight = 0
            match self.options.map_type_weighting:
                case MapTypeWeighting.option_equal_weight:
                    speed_weight = tech_weight = midspeed_weight = acc_weight = 1
                case MapTypeWeighting.option_randomize_weight:
                    speed_weight = math.ceil(random.random() * 3)
                    tech_weight = math.ceil(random.random() * 3)
                    midspeed_weight = math.ceil(random.random() * 3)
                    acc_weight = math.ceil(random.random() * 3)
                case MapTypeWeighting.option_speed_exclusive:
                    speed_weight = 1
                    tech_weight = midspeed_weight = acc_weight = 0
                case MapTypeWeighting.option_tech_exclusive:
                    tech_weight = 1
                    speed_weight = midspeed_weight = acc_weight = 0
                case MapTypeWeighting.option_midspeed_exclusive:
                    midspeed_weight = 1
                    speed_weight = tech_weight = acc_weight = 0
                case MapTypeWeighting.option_acc_exclusive:
                    acc_weight = 1
                    speed_weight = tech_weight = midspeed_weight = 0

            if self.options.max_stars < 11:
                print("Max stars under 11, removing speed maps from pool!")
                speed_weight = 0

            map_type_weights = [speed_weight, tech_weight, midspeed_weight, acc_weight]

            speed_count = tech_count = midspeed_count = acc_count = 0

            if not map_type_weights:
                map_type_weights = [1,1,1,1]
            population=["speed", "tech", "midspeed", "acc"]
            randomized_types = Random().choices(population, weights=map_type_weights, k=self.options.num_tracks)
            speed_count = randomized_types.count("speed")
            tech_count = randomized_types.count("tech")
            midspeed_count = randomized_types.count("midspeed")
            acc_count = randomized_types.count("acc")

            print(f"Selected map type distribution - Speed: {speed_count}, Tech: {tech_count}, Midspeed: {midspeed_count}, Acc: {acc_count}")
            self.speed_count = speed_count
            self.tech_count = tech_count
            self.midspeed_count = midspeed_count
            self.acc_count = acc_count

            # Not a pure function; defines new variables in the form of [type]_songs and [type]_node_connections on the world instance
            PlaylistCreator.create_randomized_playlist(self, self.player)

            is_accuracy = self.options.game_mode == GameMode.option_randomizedAccuracy
            # Grades to generate per song: all grades up to (and including) the threshold.
            # Pass mode uses a single None entry so mnemonic name omits the grade suffix.
            grades_to_use = ACCURACY_GRADES[:self.options.accuracy_threshold.value + 1] if is_accuracy else [None]
            num_grades = len(grades_to_use)

            # Speed: base ID 1000
            for i, song in enumerate(self.speed_songs):
                diff_idx = get_highest_diff_idx(song["star_ratings"])
                song_locs = []
                for grade in grades_to_use:
                    # Generic name for Archipelago server
                    if grade:
                        generic_name = f"[Speed] Song {i:02d} - {grade}"
                    else:
                        generic_name = f"[Speed] Song {i:02d}"
                    # Mnemonic name for client display
                    mnemonic_name = make_randomized_mnemonic_name("Speed", song["map_name"], diff_idx, grade)
                    song_locs.append(generic_name)
                    self.location_name_to_mnemonic[generic_name] = mnemonic_name
                self.speed_song_location_groups.append(song_locs)
                self.node_to_song[i] = {
                    'levelid': song['level_id'], 'difficulty': diff_idx,
                    'characteristic': 'Standard', 'name': song['map_name'], 'is_official': False, 'map_type': "speed", 'hash': song['hash']
                }
                self.unlocked_nodes.append(0) if i == 0 else None  # First speed song is always unlocked

            # Tech: base ID 2000
            for i, song in enumerate(self.tech_songs):
                diff_idx = get_highest_diff_idx(song["star_ratings"])
                song_locs = []
                for grade in grades_to_use:
                    # Generic name for Archipelago server
                    if grade:
                        generic_name = f"[Tech] Song {i:02d} - {grade}"
                    else:
                        generic_name = f"[Tech] Song {i:02d}"
                    # Mnemonic name for client display
                    mnemonic_name = make_randomized_mnemonic_name("Tech", song["map_name"], diff_idx, grade)
                    song_locs.append(generic_name)
                    self.location_name_to_mnemonic[generic_name] = mnemonic_name
                self.tech_song_location_groups.append(song_locs)
                self.node_to_song[speed_count + i] = {
                    'levelid': song['level_id'], 'difficulty': diff_idx,
                    'characteristic': 'Standard', 'name': song['map_name'], 'is_official': False, 'map_type': "tech", 'hash': song['hash']
                }
                self.unlocked_nodes.append(speed_count) if i == 0 else None  # First tech song unlocks with last speed song

            # Midspeed: base ID 3000
            for i, song in enumerate(self.midspeed_songs):
                diff_idx = get_highest_diff_idx(song["star_ratings"])
                song_locs = []
                for grade in grades_to_use:
                    # Generic name for Archipelago server
                    if grade:
                        generic_name = f"[Midspeed] Song {i:02d} - {grade}"
                    else:
                        generic_name = f"[Midspeed] Song {i:02d}"
                    # Mnemonic name for client display
                    mnemonic_name = make_randomized_mnemonic_name("Midspeed", song["map_name"], diff_idx, grade)
                    song_locs.append(generic_name)
                    self.location_name_to_mnemonic[generic_name] = mnemonic_name
                self.midspeed_song_location_groups.append(song_locs)
                self.node_to_song[speed_count + tech_count + i] = {
                    'levelid': song['level_id'], 'difficulty': diff_idx,
                    'characteristic': 'Standard', 'name': song['map_name'], 'is_official': False, 'map_type': "midspeed", 'hash': song['hash']
                }
                self.unlocked_nodes.append(speed_count + tech_count) if i == 0 else None  # First midspeed song unlocks with last tech song

            # Acc: base ID 4000
            for i, song in enumerate(self.acc_songs):
                diff_idx = get_highest_diff_idx(song["star_ratings"])
                song_locs = []
                for grade in grades_to_use:
                    # Generic name for Archipelago server
                    if grade:
                        generic_name = f"[Acc] Song {i:02d} - {grade}"
                    else:
                        generic_name = f"[Acc] Song {i:02d}"
                    # Mnemonic name for client display
                    mnemonic_name = make_randomized_mnemonic_name("Acc", song["map_name"], diff_idx, grade)
                    song_locs.append(generic_name)
                    self.location_name_to_mnemonic[generic_name] = mnemonic_name
                self.acc_song_location_groups.append(song_locs)
                self.node_to_song[speed_count + tech_count + midspeed_count + i] = {
                    'levelid': song['level_id'], 'difficulty': diff_idx,
                    'characteristic': 'Standard', 'name': song['map_name'], 'is_official': False, 'map_type': "acc", 'hash': song['hash']
                }
                self.unlocked_nodes.append(speed_count + tech_count + midspeed_count) if i == 0 else None  # First acc song unlocks with last midspeed song
                
            # Goal location = highest grade of last song in the largest category
            goal_groups = max(
                [self.speed_song_location_groups, self.tech_song_location_groups,
                    self.midspeed_song_location_groups, self.acc_song_location_groups],
                key=len
            )
            self.goal_location_name = goal_groups[-1][-1]

            # For each category that has gated songs, force at least one of its
            # progression unlock into sphere-0 (free) locations. Without this the fill
            # algorithm can consume all free slots with other items, leaving every
            # location of that category inaccessible — a deadlock it can't escape.
            early = self.multiworld.local_early_items[self.player]
            if self.speed_count > 1:
                early["Progressive Speed Unlock"] = 1
            if self.tech_count > 1:
                early["Progressive Tech Unlock"] = 1
            if self.midspeed_count > 1:
                early["Progressive Midspeed Unlock"] = 1
            if self.acc_count > 1:
                early["Progressive Accuracy Unlock"] = 1
            
            print(f"\nEarly items setting:")
            early = self.multiworld.local_early_items[self.player]
            for item_name, count in early.items():
                print(f"  {item_name}: {count}")

        else: # Preset modes
            print("Generating preset progression")
            PlaylistCreator.create_preset_playlist(self, self.player)

            is_accuracy = self.options.game_mode == GameMode.option_presetAccuracy
            grades_to_use = ACCURACY_GRADES[:self.options.accuracy_threshold.value + 1] if is_accuracy else [None]
            num_grades = len(grades_to_use)

            for i, song_info in enumerate(self.sorted_songs):
                song_name = song_info['name']
                difficulty = song_info['data']['difficulty']
                song_locs = []
                for grade in grades_to_use:
                    # Generic name for Archipelago server
                    if grade:
                        generic_name = f"Song {i:02d} - {grade}"
                    else:
                        generic_name = f"Song {i:02d}"
                    # Mnemonic name for client display
                    mnemonic_name = make_preset_mnemonic_name(song_name, difficulty, grade)
                    song_locs.append(generic_name)
                    self.location_name_to_mnemonic[generic_name] = mnemonic_name
                self.preset_song_location_groups.append(song_locs)
                self.node_to_song[i] = {**song_info['data'], 'name': song_name, 'hash': song_info['hash']}

            self.unlocked_nodes.append(0)  # First song is always unlocked
            # Goal location = highest grade of the last song
            self.goal_location_name = self.preset_song_location_groups[-1][-1]

    def create_items(self):
        """Create progressive song unlock items"""
        # Victory is pre-placed by generate_basic(), so the pool must fill exactly
        # (total_locations - 1) slots. We build core items (progression, required for logic)
        # and extra items (useful, nice-to-have) separately, then trim extras to fit.
        available_slots = len(self.location_name_to_mnemonic) - 1

        core_items = []
        extra_items = []

        if self.randomized_game_mode:
            print("Generating randomized progression items")
            extra_unlocks_category_count = self.options.extra_unlocks // 4
            remainder_extra_unlocks = self.options.extra_unlocks % 4

            core_items += [self.create_item("Progressive Speed Unlock") for i in range(max(0, self.speed_count - 1))]
            extra_items += [Item("Progressive Speed Unlock", ItemClassification.useful, 2, self.player) for i in range(extra_unlocks_category_count)]

            core_items += [self.create_item("Progressive Tech Unlock") for i in range(max(0, self.tech_count - 1))]
            extra_items += [Item("Progressive Tech Unlock", ItemClassification.useful, 4, self.player) for i in range(extra_unlocks_category_count)]
            print("tech count: " + str(self.tech_count))

            core_items += [self.create_item("Progressive Midspeed Unlock") for i in range(max(0, self.midspeed_count - 1))]
            extra_items += [Item("Progressive Midspeed Unlock", ItemClassification.useful, 5, self.player) for i in range(extra_unlocks_category_count  + (remainder_extra_unlocks if self.options.extra_unlocks > 0 else 0))]
            print("midspeed count: " + str(self.midspeed_count))

            core_items += [self.create_item("Progressive Accuracy Unlock") for i in range(max(0, self.acc_count - 1))]
            extra_items += [Item("Progressive Accuracy Unlock", ItemClassification.useful, 3, self.player) for i in range(extra_unlocks_category_count)]

            

        else: # Preset modes
            core_items += [
                Item("Progressive Song Unlock", ItemClassification.progression, 1, self.player)
                for i in range(self.options.num_tracks - 1)
            ]
            extra_items += [
                Item("Progressive Song Unlock", ItemClassification.useful, 2, self.player)
                for i in range(self.options.extra_unlocks)
            ]

        if self.options.game_mode.value != "option_randomizedpp" and self.options.lock_goal_map: # type: ignore
                core_items += [self.create_item("Bloq Key") for i in range(self.options.bloq_keys_required)]
                extra_items += [Item("Bloq Key", ItemClassification.useful, 6, self.player) for i in range(self.options.extra_bloq_keys)]
        # Trim extras if the core items already fill (or overflow) the available slots.
        extra_budget = max(0, available_slots - len(core_items))
        trimmed_extras = extra_items[:extra_budget]

        filler_count = available_slots - len(core_items) - len(trimmed_extras)
        filler = [Item("Nothing", ItemClassification.filler, -1, self.player) for i in range(filler_count)]

        self.multiworld.itempool += core_items + trimmed_extras + filler
        print(f"Pool: {len(core_items)} core + {len(trimmed_extras)} extras + {len(filler)} filler = {len(self.multiworld.itempool)} items for {available_slots} slots")

    def generate_basic(self):
        self.campaign_name = f"AP Campaign, Seed {self.multiworld.seed_name}"

        # Process song data from options (used for keystr generation)
        for name, data in self.options.songs.items():
            levelid = data["levelid"]
            is_official = data.get("is_official", False)
            if is_official:
                keystr = f"OST_{levelid}_{data['characteristic']}_{data['difficulty']}"
            else:
                keystr = f"{levelid}_{data['characteristic']}_{data['difficulty']}"
            self.processed_songs[keystr] = {**data, 'name': name}

        # Place Victory at the goal location
        self.multiworld.get_location(self.goal_location_name, self.player).place_locked_item(
            Item("Victory", ItemClassification.progression_skip_balancing, item_table["Victory"], self.player))

        self.multiworld.completion_condition[self.player] = lambda state: state.has("Victory", self.player)

    def fill_slot_data(self):
        """Send data to the client"""
        node_to_keystr = {}
        keystr_to_node = {}
        song_mapping = {}
        map_type_counts = [self.speed_count, self.tech_count, self.midspeed_count, self.acc_count] if self.randomized_game_mode else None

        is_accuracy = self.options.game_mode == GameMode.option_randomizedAccuracy or self.options.game_mode == GameMode.option_presetAccuracy
        grades_to_use = ACCURACY_GRADES[:self.options.accuracy_threshold.value + 1] if is_accuracy else [None]
        num_grades = len(grades_to_use) if grades_to_use else 1

        for node_id, song_data in self.node_to_song.items():
            is_official = song_data.get('is_official', False)
            if is_official:
                keystr = f"OST_{song_data['levelid']}_{song_data['characteristic']}_{song_data['difficulty']}"
            else:
                keystr = f"{song_data['levelid']}_{song_data['characteristic']}_{song_data['difficulty']}"
            node_to_keystr[node_id] = keystr
            keystr_to_node[keystr] = node_id
            song_mapping[node_id] = {
                'levelid': song_data['levelid'],
                'characteristic': song_data['characteristic'],
                'difficulty': song_data['difficulty'],
                'name': song_data['name'],
                'map_type': song_data['map_type'] if 'map_type' in song_data else "unknown",
                'is_official': song_data.get('is_official', False)
            }

        return {
            "DeathLink": self.options.death_link.value,
            "campaign_name": self.campaign_name,
            "songs": song_mapping,
            "node_to_keystr": node_to_keystr,
            "keystr_to_node": keystr_to_node,
            "start_songs": self.unlocked_nodes,
            "game_mode": self.options.game_mode.value,
            "map_type_counts": map_type_counts,
            "num_grades": num_grades,
            "location_name_to_mnemonic": self.location_name_to_mnemonic,
        }

    def generate_output(self, output_directory: str):
        if self.randomized_game_mode:
            generate_randomized_output(self, output_directory)
        else:
            generate_preset_output(self, output_directory)
        
