import json
import os
import requests
from .Container import BeatSaberContainer
import time

ap_image = "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"

def generate_randomized_output(world, output_directory):

    # Prepare sorted song list and pass into _generate_category_output for each category
    speed_playlist = _generate_category_output(world, "Speed", world.speed_songs, world.speed_node_connections)
    tech_playlist = _generate_category_output(world, "Tech", world.tech_songs, world.tech_node_connections)
    midspeed_playlist = _generate_category_output(world, "Midspeed", world.midspeed_songs, world.midspeed_node_connections)
    acc_playlist = _generate_category_output(world, "Acc", world.acc_songs, world.acc_node_connections)
    _patch_data = {
        f"Speed_{world.campaign_name}.bplist": json.dumps(speed_playlist, indent=2),
        f"Tech_{world.campaign_name}.bplist": json.dumps(tech_playlist, indent=2),
        f"Midspeed_{world.campaign_name}.bplist": json.dumps(midspeed_playlist, indent=2),
        f"Acc_{world.campaign_name}.bplist": json.dumps(acc_playlist, indent=2)
    }
    mod = BeatSaberContainer(
        patch_data=_patch_data,
        base_path=world.multiworld.get_out_file_name_base(world.player),
        output_directory=output_directory,
        player=world.player,
        player_name=world.multiworld.player_name[world.player]
    )
    mod.write()
    print(f"Generated playlists: {mod.file_path}")

def _generate_category_output(world, category_name, song_list, node_connections):
    playlist = {
        "playlistTitle": f"{category_name} - {world.campaign_name}",
        "playlistAuthor": "Archipelago",
        "image": "data:image/png;base64," + ap_image,
        "customData": {
            "syncURL": "",
            "unlocked_nodes": [0] + list(node_connections[0]),
            "node_connections": node_connections
        },
        "songs": []
    }
    for node_id, song_data in enumerate(song_list):
        print(f"Processing {category_name} node {node_id}")
        levelid = song_data["level_id"]
        song_name = song_data['map_name']
        song_hash = song_data['hash']

        """
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
        """
        playlist["songs"].append({
            "key": levelid,
            "hash": song_hash,
            "songName": song_name,
            "node_id": node_id
        })
    return playlist


def generate_preset_output(world, output_directory):
    playlist = {
            "playlistTitle": world.campaign_name,
            "playlistAuthor": "Archipelago",
            "image": "data:image/png;base64," + ap_image,
            "customData": {
                "syncURL": "",
                "unlocked_nodes": [0] + list(world.node_connections[0]),
                "node_connections": world.node_connections
            },
            "songs": []
        }
    

    for node_id in sorted(world.node_to_song.keys()):
        song_data = world.node_to_song[node_id]

        levelid = song_data["levelid"]
        song_hash = song_data['hash']
        song_name = song_data['name']

        playlist["songs"].append({
            "key": levelid,
            "hash": song_hash,
            "songName": song_name,
            "node_id": node_id,
            "difficulties": [{
                "characteristic": song_data["characteristic"],
                "name": ["Easy", "Normal", "Hard", "Expert", "ExpertPlus"][song_data["difficulty"]]
            }]
        })

    _patch_data = {
        world.campaign_name + ".bplist": json.dumps(playlist, indent=2)
    }

    mod = BeatSaberContainer(
        patch_data=_patch_data,
        base_path=world.multiworld.get_out_file_name_base(world.player),
        output_directory=output_directory,
        player=world.player,
        player_name=world.multiworld.player_name[world.player]
    )
    mod.write()
    print(f"Generated playlist: {mod.file_path}")