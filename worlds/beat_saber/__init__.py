import typing
import json
import requests
from .Items import item_table, item_data_table, BSItem
from .Locations import location_table, BSLocation
from .Options import BSOptions
from .Rules import set_rules
from .Regions import create_regions
from BaseClasses import Item, ItemClassification, Tutorial
from ..AutoWorld import World, WebWorld

class BSWeb(WebWorld):
    tutorials = [Tutorial(
        "Multiworld Setup Guide",
        "A guide to setting up Beat Saber for Multiworld.",
        "English",
        "setup_en.md",
        "setup/en",
        ["N00byKing"]
    )]

class BSWorld(World):
    """ 
     bloks
    """ #Lifted from Store Page

    game: str = "Beat Saber"
    topology_present = False
    web = BSWeb()

    item_name_to_id = item_table
    location_name_to_id = location_table

    # Only need connections for unlock logic, not layers
    node_connections: typing.Dict[int, typing.List[int]]
    
    options_dataclass = BSOptions

    campaign_name: str
    processed_songs: typing.Dict[str, dict] = {}
    node_to_song: typing.Dict[int, dict] = {}  # Maps node ID directly to song data
    sorted_songs: typing.List[dict] = []  # Sorted list of songs by difficulty count

    def create_regions(self):
        create_regions(self.multiworld, self.player)

    def set_rules(self):
        # Simplified rules - you'll need to update Rules.py accordingly
        set_rules(self.multiworld, self.options, self.player)

    def create_item(self, name: str) -> Item:
        return BSItem(name, item_data_table[name].classification, item_data_table[name].code, self.player)

    def generate_early(self):
        """Process songs and set up node connections"""
        self.node_connections = {}
        
        # First pass: fetch actual difficulty counts from BeatSaver
        difficulty_count = {}
        levelids_to_fetch = set()
        
        for name, data in self.options.songs.items():
            levelid = data["levelid"]
            levelids_to_fetch.add(levelid)
        
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
                        total_diffs = len(diffs)
                    difficulty_count[levelid] = total_diffs if total_diffs > 0 else 1
                    print("Total difficulties for " + levelid + ": " + str(difficulty_count[levelid]))
                else:
                    print(f"Warning: Could not fetch difficulty count for {levelid}, defaulting to 1")
                    difficulty_count[levelid] = 1
            except Exception as e:
                print(f"Warning: Error fetching BeatSaver data for {levelid}: {e}, defaulting to 1")
                difficulty_count[levelid] = 1
        
        # Second pass: create song list with correct difficulty counts
        song_list = []
        for name, data in self.options.songs.items():
            levelid = data["levelid"]
            song_list.append({
                'name': name,
                'data': data,
                'levelid': levelid,
                'difficulty_count': difficulty_count.get(levelid, 1)
            })
        
        # Sort songs by difficulty count (ascending - easiest/simplest first)
        song_list.sort(key=lambda x: x['difficulty_count'])
        
        # Debug: print the sorted order
        print("Songs sorted by difficulty count:")
        for i, song in enumerate(song_list[:self.options.num_tracks]):
            print(f"  Node {i}: {song['name']} (levelid: {song['levelid']}, {song['difficulty_count']} difficulties)")
        
        # Take only the number of tracks we need
        song_list = song_list[:self.options.num_tracks]
        
        # Store sorted songs for later use in generate_basic
        self.sorted_songs = song_list
        
        # Initialize all nodes with empty connections
        for i in range(self.options.num_tracks):
            self.node_connections[i] = []
        
        # Simple connection structure: each song unlocks the next
        # Node 0 is always unlocked (root)
        for i in range(self.options.num_tracks - 1):
            self.node_connections[i].append(i + 1)
        
        # OR: Use your existing campaign layout logic if you want that structure
        # from .CampainLayout import generate_campain_layout
        # node_layers = {}
        # generate_campain_layout(self.options, self.multiworld.random, self.node_connections, node_layers)

    def create_items(self):
        """Create progressive song unlock items"""
        # Create one progressive item for each track (except node 0 which is free)
        progressive_items = [
            self.create_item("Progressive Song Unlock") 
            for i in range(self.options.num_tracks - 1)  # -1 because node 0 is free
        ]
        songUnlocks = progressive_items
        print(songUnlocks)
        filler = [Item("Nothing", ItemClassification.filler, -1, self.player) 
                  for i in range(self.options.num_tracks - len(songUnlocks))]
        self.multiworld.itempool += songUnlocks + filler
        print(self.multiworld.itempool)

    def generate_basic(self):
        """Map songs to nodes"""
        self.campaign_name = f"AP Campaign, Seed {self.multiworld.seed_name}"
        
        # Process song data from the pre-sorted list
        for name, data in self.options.songs.items():
            levelid = data["levelid"]
            keystr = f"{levelid}_{data['characteristic']}_{data['difficulty']}"
            self.processed_songs[keystr] = {
                **data,
                'name': name
            }
        
        # Assign songs to nodes in sorted order (already sorted by difficulty count in generate_early)
        for i, song_info in enumerate(self.sorted_songs):
            if i >= self.options.num_tracks:
                break
            self.node_to_song[i] = {
                **song_info['data'],
                'name': song_info['name']
            }
        
        # Lock unused location nodes
        for i in range(self.options.num_tracks, 50):
            self.multiworld.get_location("Node " + f"{i}".zfill(2), self.player).place_locked_item(
                Item("Nothing", ItemClassification.filler, -1, self.player))

    def fill_slot_data(self):
        """Send data to the client"""
        # Build keystr mapping: node_id -> "levelid_characteristic_difficulty"
        node_to_keystr = {}
        keystr_to_node = {}

        # Convert node_to_song to a simple format the client can use
        song_mapping = {}
        for node_id, song_data in self.node_to_song.items():
            keystr = f"{song_data['levelid']}_{song_data['characteristic']}_{song_data['difficulty']}"
            node_to_keystr[node_id] = keystr
            keystr_to_node[keystr] = node_id
            song_mapping[node_id] = {
                'levelid': song_data['levelid'],
                'characteristic': song_data['characteristic'],
                'difficulty': song_data['difficulty'],
                'name': song_data['name']
            }
        
        return {
            "DeathLink": self.options.death_link.value,
            "campaign_name": self.campaign_name,
            "songs": song_mapping,
            "node_to_keystr": node_to_keystr,  # {0: "43A2E_Standard_4", 1: "43A5D_Standard_4", ...}
            "keystr_to_node": keystr_to_node,  # {"43A2E_Standard_4": 0, "43A5D_Standard_4": 1, ...}
            "start_songs": [node_to_keystr[0]]  # Just the first song (node 0)
        }
    
    def generate_output(self, output_directory: str):
        """Generate only the .bplist playlist file"""
        
        # Build playlist
        playlist = {
            "playlistTitle": self.campaign_name,
            "playlistAuthor": "Archipelago",
            "image": "",
            "customData": {
                "syncURL": "",
                "unlocked_nodes": [0] + list(self.node_connections[0]),  # Initially unlocked nodes
                "node_connections": self.node_connections  # For client to track progression
            },
            "songs": []
        }
        
        # Add all songs to the playlist
        # The client will handle showing/hiding based on unlock state
        for node_id in sorted(self.node_to_song.keys()):
            song_data = self.node_to_song[node_id]
            levelid = song_data["levelid"]
            
            # Fetch BeatSaver metadata
            song_hash = levelid
            song_name = song_data.get('name', levelid)
            
            try:
                response = requests.get(f"https://api.beatsaver.com/maps/id/{levelid}", timeout=5)
                if response.status_code == 200:
                    beatsaver_data = response.json()
                    song_hash = beatsaver_data.get("versions", [{}])[0].get("hash", levelid)
                    api_song_name = beatsaver_data.get("metadata", {}).get("songName")
                    if api_song_name:
                        song_name = api_song_name
            except Exception as e:
                print(f"Warning: Could not fetch BeatSaver data for {levelid}: {e}")
            
            playlist["songs"].append({
                "key": levelid,
                "hash": song_hash,
                "songName": song_name,
                "node_id": node_id,  # Add node ID so client knows which unlock corresponds to which song
                "difficulties": [{
                    "characteristic": song_data["characteristic"],
                    "name": ["Easy", "Normal", "Hard", "Expert", "ExpertPlus"][song_data["difficulty"]]
                }]
            })
        
        # Write playlist file
        file_path = f"{self.multiworld.get_out_file_name_base(self.player)}.bplist"
        with open(file_path, "w") as f:
            json.dump(playlist, f, indent=2)
        
        print(f"Generated playlist: {file_path}")