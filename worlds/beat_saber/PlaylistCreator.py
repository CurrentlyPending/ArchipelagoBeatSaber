import time

import requests
import json
import random
from pathlib import Path
import os
from .BeatmapMasterList import BeatLeaderRankedMaps
from enum import IntFlag

class MapTypes(IntFlag):
    None_ = 0
    Acc = 1
    Tech = 2
    Midspeed = 4
    Speed = 8
    Fitbeat = 16
    Linear = 32
    BombReset = 64

class PlaylistCreator:
    @staticmethod
    def create_preset_playlist(world, player):
        print("Generating preset progression")
        # Preset progression with no randomization

        """Process songs and set up node connections"""
        world.node_connections = {}
        
        # First pass: fetch actual difficulty counts from BeatSaver
        difficulty_count = {}
        levelids_to_fetch = set()
        hash_list = {}
        for name, data in world.options.songs.items():
            levelid = str(data["levelid"])
            is_official = data.get("is_official", False)
            
            if not is_official:
                levelids_to_fetch.add(levelid)
            else:
                # For official maps, we can't query BeatSaver
                # Most official songs have 5 difficulties (Easy, Normal, Hard, Expert, Expert+)
                difficulty_count[levelid] = 5
        
        # Fetch difficulty counts from BeatSaver
        for levelid in levelids_to_fetch:
            try:
                response = requests.get(f"https://api.beatsaver.com/maps/id/{levelid}", timeout=5)
                if response.status_code == 200:
                    beatsaver_data = response.json()
                    # Count total difficulties across all characteristics
                    total_diffs = 0
                    versions = beatsaver_data.get("versions", [])
                    if versions:
                        diffs = versions[0].get("diffs", [])
                        hash_list[levelid] = versions[0].get("hash")
                        total_diffs = len(diffs)
                    difficulty_count[levelid] = total_diffs if total_diffs > 0 else 1
                    print("Total difficulties for " + levelid + ": " + str(difficulty_count[levelid]))
                else:
                    print(f"Warning: Could not fetch difficulty count for {levelid}, defaulting to 1")
                    difficulty_count[levelid] = 1
            except Exception as e:
                print(f"Warning: Error fetching BeatSaver data for {levelid}: {e}")
                if(is_official):
                    difficulty_count[levelid] = 5
                    print("Assuming 5 difficulties for official map " + levelid)
                else:
                    print("Defaulting to 1 difficulty for " + levelid)
                    difficulty_count[levelid] = 1
        
        # Second pass: create song list with correct difficulty counts
        song_list = []
        for name, data in world.options.songs.items():
            levelid = str(data["levelid"])
            song_list.append({
                'name': name,
                'data': data,
                'levelid': levelid,
                'hash': hash_list.get(levelid),
                'difficulty_count': difficulty_count.get(levelid, 1)
            })
        
        # Sort songs by difficulty count (ascending - easiest/simplest first)
        song_list.sort(key=lambda x: x['difficulty_count'])
        
        # Debug: print the sorted order
        print("Songs sorted by difficulty count:")
        for i, song in enumerate(song_list[:world.options.num_tracks]):
            print(f"  Node {i}: {song['name']} (levelid: {song['levelid']}, {song['difficulty_count']} difficulties)")
        
        # Take only the number of tracks we need
        song_list = song_list[:world.options.num_tracks]
        
        # Store sorted songs for later use in generate_basic
        world.sorted_songs = song_list
        
        # Initialize all nodes with empty connections
        for i in range(world.options.num_tracks):
            world.node_connections[i] = []
        
        # Simple connection structure: each song unlocks the next
        # Node 0 is always unlocked (root)
        for i in range(world.options.num_tracks - 1):
            world.node_connections[i].append(i + 1)
    
    @staticmethod
    def create_randomized_playlist(world, player):
        print("Generating randomized progression")
        speed_song_list = []
        tech_song_list = []
        midspeed_song_list = []
        acc_song_list = []
        world.speed_node_connections = {}
        world.tech_node_connections = {}
        world.midspeed_node_connections = {}
        world.acc_node_connections = {}

        # Get the data directory - same logic as BeatmapMasterList.save_to_json
        current_dir = os.path.dirname(os.path.abspath(__file__))
        repo_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
        file_path = os.path.join(repo_root, "data", "ranked_maps.json")

        if not os.path.exists(file_path):
            BeatLeaderRankedMaps.run()
            time.sleep(3)  # Small delay to ensure file is written before we try to read it
        with open(file_path, "r", encoding="utf-8") as f:
            ranked_maps = json.load(f)
        category_count = [0, 0, 0, 0]  # [speed, tech, midspeed, acc]
        categories_filled = False
        counter = 0

        RELEVANT_MASK = (
            MapTypes.Acc
            | MapTypes.Tech
            | MapTypes.Midspeed
            | MapTypes.Speed
        )

        while not categories_filled:
            random_song = random.choice(ranked_maps)

            world.speed_node_connections[counter] = []
            world.tech_node_connections[counter] = []
            world.midspeed_node_connections[counter] = []
            world.acc_node_connections[counter] = []
            
            # Determine the highest difficulty available for the song to check its tag. Temporary hack before the API provides a more reliable way to get this info.
            if "ExpertPlus" in random_song["star_ratings"]:
                difficulty_to_check = random_song["star_ratings"]["ExpertPlus"]

            elif "Expert" in random_song["star_ratings"]:
                difficulty_to_check = random_song["star_ratings"]["Expert"]

            elif "Hard" in random_song["star_ratings"]:
                difficulty_to_check = random_song["star_ratings"]["Hard"]

            elif "Normal" in random_song["star_ratings"]:
                difficulty_to_check = random_song["star_ratings"]["Normal"]

            else:
                difficulty_to_check = random_song["star_ratings"]["Easy"]
            
            
            map_type = difficulty_to_check["map_type"] & RELEVANT_MASK
            if world.options.max_stars is not None and difficulty_to_check["stars"] <= world.options.max_stars:
                
                match map_type:
                    case MapTypes.Speed:
                        if category_count[0] < world.speed_count:
                            speed_song_list.append(random_song)
                            category_count[0] += 1
                            print("Speed count: " + str(category_count[0]))

                    case MapTypes.Tech:
                        if category_count[1] < world.tech_count:
                            tech_song_list.append(random_song)
                            category_count[1] += 1
                            print("Tech count: " + str(category_count[1]))

                    case MapTypes.Acc:
                        if category_count[3] < world.acc_count:
                            acc_song_list.append(random_song)
                            category_count[3] += 1
                            print("Acc count: " + str(category_count[3]))
                    
                    case MapTypes.Midspeed:
                        if category_count[2] < world.midspeed_count:
                            midspeed_song_list.append(random_song)
                            category_count[2] += 1
                            print("Midspeed count: " + str(category_count[2]))
                    case _:
                        if category_count[2] < world.midspeed_count:
                            print(f"Warning: Song '{random_song['map_name']}' has unrecognized map type {map_type}, adding to midspeed.")
                            midspeed_song_list.append(random_song)
                            category_count[2] += 1
                counter += 1

            if sum(category_count) >= world.options.num_tracks:
                categories_filled = True
        
        # -1 because the final song shouldnt unlock anything
        if world.speed_count > 0:
            for i in range(world.speed_count - 1):
                world.speed_node_connections[i].append(i + 1)

        if world.tech_count > 0:
            for i in range(world.tech_count - 1):
                print("i value: " + str(i))
                world.tech_node_connections[i].append(i + 1)

        if world.midspeed_count > 0:
            for i in range(world.midspeed_count - 1):
                print("i value: " + str(i))
                world.midspeed_node_connections[i].append(i + 1)

        if world.acc_count > 0:
            for i in range(world.acc_count - 1):
                print("i value: " + str(i))
                world.acc_node_connections[i].append(i + 1)

        # Store category song lists on world for location name generation in generate_early
        world.speed_songs = speed_song_list
        world.tech_songs = tech_song_list
        world.midspeed_songs = midspeed_song_list
        world.acc_songs = acc_song_list