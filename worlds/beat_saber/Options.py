import typing
from dataclasses import dataclass
from Options import Option, DeathLink, Range, OptionDict, PerGameCommonOptions
from schema import Schema, And, Or, Use, Optional, SchemaError

class NumTracks(Range):
    """Amount of Tracks to require"""
    display_name = "Number of Tracks"
    range_start = 5 # Require 5 at minimum to ensure > 1 layer
    range_end = 50
    default = 6

#TODO: Items for starting map type (Onesaber, etc)
default_songs = {
    "XG - HYPNOTIZE": {
        "levelid": "4e0e1",
        "difficulty": 4,
        "characteristic": "Standard",
        "is_official": False
    },
    "lapix - Aura (feat. Luschel)": {
        "levelid": "4e1cd",
        "difficulty": 4,
        "characteristic": "Standard",
        "is_official": False
    },
    "[GD Mash Pack] MDK - Dash (V3 Lights)": {
        "levelid": "42e3a",
        "difficulty": 4,
        "characteristic": "Standard",
        "is_official": False
    },
    "100 Bills": {
        "levelid": "100Bills",
        "difficulty": 2,
        "characteristic": "Standard",
        "is_official": True
    },
    "Touch Tone Telephone": {
        "levelid": "352e9",
        "difficulty": 4,
        "characteristic": "Standard",
        "is_official": False
    },
    "[DITR7] Kairikibear- Darling Dance": {
        "levelid": "4941b",
        "difficulty": 4,
        "characteristic": "Standard",
        "is_official": False
    }
    # "Angel Voices": {
    #     "levelid": "AngelVoices",
    #     "difficulty": 3,
    #     "characteristic": "Standard",
    #     "is_official": True
    # },
}

class Songs(OptionDict):
    """
    Songs that may occur in the custom campaign generated.
    
    For custom maps:
    - Specify the levelid from beatsaver (in the url, /maps/<id>)
    - Set is_official to False
    
    For official Beat Saber maps:
    - Use the levelID (e.g., "100Bills", "AngelVoices", etc. Typically just the song name in PascalCase and no special characters)
    - Set is_official to True
    
    All songs need difficulty (0-4) and characteristic (usually "Standard")
    Currently, difficulty and characteristic are not utilized for anything, but they are required for future compatibility with potential logic that may want to differentiate between them.
    """
    display_name = "Songs"
    default = default_songs
    schema = Schema({
        str: {
            "levelid": str,
            "difficulty": And(Use(int), lambda n: 0 <= n <= 4),
            "characteristic": And(Use(str), lambda s: s in ("Standard", "OneSaber", "NoArrows", "90Degree", "360Degree", "Lightshow", "Lawless")),
            Optional("is_official", default=False): bool
        }
    })


@dataclass
class BSOptions(PerGameCommonOptions):
    num_tracks: NumTracks
    death_link: DeathLink
    songs: Songs