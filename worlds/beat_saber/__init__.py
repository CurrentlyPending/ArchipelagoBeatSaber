import typing
import os, json
import zipfile

import requests
from .Items import item_table, item_data_table, BSItem
from .Locations import location_table, BSLocation
from .CampainLayout import generate_campain_layout
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

    node_layers: typing.Dict[int, typing.Set[int]]
    node_connections: typing.Dict[int, typing.Set[int]]

    songshuffle: list

    music_map: typing.Dict[int,int]

    options_dataclass = BSOptions

    campaign_name: str
    keystr_to_node: typing.Dict[str,int] = {}
    node_to_keystr: typing.Dict[int,str] = {}
    processed_songs = {}

    def create_regions(self):
        create_regions(self.multiworld, self.player)

    def set_rules(self):
        set_rules(self.multiworld, self.options, self.player, self.node_connections, self.node_layers)

    def create_item(self, name: str) -> Item:
        return BSItem(name, item_data_table[name].classification, item_data_table[name].code, self.player)

    def generate_early(self):
        self.node_connections = {}
        self.node_layers = {}
        generate_campain_layout(self.options, self.multiworld.random, self.node_connections, self.node_layers)

        for name, data in self.options.songs.items():
            keystr = data["levelid"] + "_" + data["characteristic"] + "_" + str(data["difficulty"])
            self.processed_songs[keystr] = data

    def create_items(self):
        songUnlocks = []
        for i in range(1,self.options.num_tracks):
            if not i in list(self.node_connections[0]):
                songUnlocks.append(self.create_item("Song " + str(i).zfill(2)))
        #TODO: nice filler items
        filler = [Item("Nothing", ItemClassification.filler, -1, self.player) for i in range(self.options.num_tracks - len(songUnlocks))]
        self.multiworld.itempool += songUnlocks + filler

    def generate_basic(self):
        self.campaign_name = f"AP Campaign, Seed {self.multiworld.seed_name}"
        self.songshuffle = list(self.processed_songs.keys())
        self.multiworld.random.shuffle(self.songshuffle)
        for i in range(self.options.num_tracks):
            self.keystr_to_node[list(self.processed_songs)[i]] = i
            self.node_to_keystr[i] = list(self.processed_songs)[i]
        for i in range(self.options.num_tracks, 50):
            self.multiworld.get_location("Node " + f"{i}".zfill(2), self.player).place_locked_item(Item("Nothing", ItemClassification.filler, -1, self.player))

    def fill_slot_data(self):
        return {
            "DeathLink": self.options.death_link.value,
            "node_to_keystr": self.node_to_keystr,
            "keystr_to_node": self.keystr_to_node,
            "campaign_name": self.campaign_name,
            "start_songs": [self.node_to_keystr[0]] + [self.node_to_keystr[i] for i in self.node_connections[0]]
        }
    
    def generate_output(self, output_directory: str):
        # Generate .bplist playlist format
        playlist = {
            "playlistTitle": self.campaign_name,
            "playlistAuthor": "Archipelago",
            "image": "",
            "customData": {
                "syncURL": "",
                "unlocked_nodes": [0] + list(self.node_connections[0])  # Start with node 0 and its direct connections
            },
            "songs": []
        }
        
        # Count difficulties per levelid
        difficulty_count = {}
        for song_keystr, song_data in self.processed_songs.items():
            levelid = song_data["levelid"]
            difficulty_count[levelid] = difficulty_count.get(levelid, 0) + 1
        
        # Create song list with sorting key
        songs_by_layer = []
        for layer in sorted(self.node_layers.keys()):
            for node_id in self.node_layers[layer]:
                song_keystr = self.node_to_keystr[node_id]
                song_data = self.processed_songs[song_keystr]
                levelid = song_data["levelid"]
                
                songs_by_layer.append({
                    "node_id": node_id,
                    "song_keystr": song_keystr,
                    "levelid": levelid,
                    "difficulty_count": difficulty_count[levelid]
                })
        
        # Sort by difficulty count (ascending or descending)
        songs_by_layer.sort(key=lambda x: x["difficulty_count"], reverse=False)
        
        # Add songs to playlist in sorted order
        for song in songs_by_layer:
            levelid = song["levelid"]
            
            # Fetch hash and name from BeatSaver API
            song_hash = levelid
            song_name = levelid
            try:
                response = requests.get(f"https://api.beatsaver.com/maps/id/{levelid}")
                if response.status_code == 200:
                    beatsaver_data = response.json()
                    song_hash = beatsaver_data.get("versions", [{}])[0].get("hash", levelid)
                    song_name = beatsaver_data.get("metadata", {}).get("songName", levelid)
            except:
                pass
            
            playlist["songs"].append({
                "key": levelid,
                "hash": song_hash,
                "songName": song_name
            })
        
        # Write playlist file
        file_path = f"{self.multiworld.get_out_file_name_base(self.player)}.bplist"
        with open(file_path, "w") as f:
            json.dump(playlist, f, indent=4)
        

        # Template for info.json
        info_json = {
            "name": self.campaign_name,
            "desc": "Generated on APWorld, version idk",
            "bigDesc": "TODO dump settings, other players maybe?",
            "allUnlocked": False,
            "mapPositions": [ ],
            "mapHeight": 1200,
            "backgroundAlpha": 0.9,
            "lightColor": {
                "r": 0.0,
                "g": 0.443137258,
                "b": 0.9843137
            }
        }

        # Nodes
        nodes_json = {}
        node_distance_horizontal = 60
        for layer in range(len(self.node_layers)):
            layer_width = len(self.node_layers[layer]) * node_distance_horizontal
            layer_start = -0.5 * layer_width # Center around 0, start from left, increment to right
            for i in range(len(self.node_layers[layer])):
                loc_id = self.node_layers[layer][i]
                # Write meta info to info.json
                locname = f"Track{loc_id}"
                node_meta_info = {
                    "childNodes": self.node_connections[loc_id],
                    "x":  layer_start + node_distance_horizontal * i,
                    "y": layer*80,
                    "scale": 0.9,
                    "letterPortion": locname,
                    "numberPortion": -1
                }
                info_json["mapPositions"].append(node_meta_info)

                # Write node info
                node_json = {
                    "name": locname,
                    "songid": self.processed_songs[self.node_to_keystr[loc_id]]["levelid"],
                    "characteristic": self.processed_songs[self.node_to_keystr[loc_id]]["characteristic"],
                    "difficulty": self.processed_songs[self.node_to_keystr[loc_id]]["difficulty"],
                    "modifiers": {
                        "fastNotes": False,
                        "songSpeed": 0,
                        "noBombs": False,
                        "disappearingArrows": False,
                        "strictAngles": False,
                        "noObstacles": False,
                        "batteryEnergy": False,
                        "failOnSaberClash": False,
                        "instaFail": False,
                        "noFail": False,
                        "noArrows": False,
                        "ghostNotes": False,
                        "energyType": 0,
                        "enabledObstacleType": 0,
                        "speedMul": 1.0
                    },
                    "requirements": [],
                    "externalModifiers": {},
                    "challengeInfo": None,
                    "unlockableItems": [],
                    "unlockMap": False
                }
                nodes_json[self.node_layers[layer][i]] = node_json
        # Write zipfile
        folder_prefix = f"AP_{self.multiworld.seed_name}"
        file_path = f"{self.multiworld.get_out_file_name_base(self.player)}.zip"
        with zipfile.ZipFile(file_path, mode="w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
            zf.writestr(f"{folder_prefix}/info.json", json.dumps(info_json))
            def load_data(name: str):
                import pkgutil
                data = pkgutil.get_data(__name__, "data/" + name)
                return data
            coverimg = load_data("cover.png")
            #bkgimg = load_data("map background.png")
            zf.writestr(f"{folder_prefix}/cover.png", coverimg)
            #zf.writestr(f"{folder_prefix}/map background.png", bkgimg)
            for i in range(self.options.num_tracks):
                zf.writestr(f"{folder_prefix}/{i}.json", json.dumps(nodes_json[i]))
