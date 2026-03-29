import typing
from dataclasses import dataclass
from Options import Choice, DefaultOnToggle, DeathLink, Range, OptionDict, PerGameCommonOptions, Toggle
from schema import Schema, And, Or, Use, Optional, SchemaError

class NumTracks(Range):
    """Amount of Tracks to require"""
    display_name = "Number of Tracks"
    range_start = 5 
    range_end = 100
    default = 6

class GameMode(Choice):
    """Game mode to generate for (RANDOMIZED PP IS NOT YET IMPLEMENTED, PLEASE TEST OTHER MODES FIRST AND REPORT ANY ISSUES YOU FIND!)

    randomizedPP: Randomly generates a list of ranked songs, separated by style (Speed, Tech, etc). 
        Checks are gated behind dynamic pp thresholds (one check every X pp, with X going down as you get more checks). 
        Your pp is weighted on both a map curve and a pool curve, meaning as you clear more maps, 
        the amount of pp you get every new clear goes down. Works with OST and DLC maps (thanks to BeatLeader).
        Win condition: Pass a certain pp threshold (e.g., 1000pp).
        This is the recommended mode, as it provides a more balanced experience.

    randomizedAccuracy: Randomly generates a list of curated/ranked songs, separated by style (Speed, Tech, etc).
        Checks are gated behind per-difficulty accuracy thresholds (e.g getting A or above on Expert+, an S on Expert, etc).
        Maximum difficulty for songs is based on selected star rating, and the difficulty to play each map is always the highest available.
        Win condition: A random 'goal map' is selected as the hardest map from the randomly generated pool, and you need to meet the accuracy threshold on that map to win.
        The goal map is locked until you have a certain number of Bloq Keys (10 by default).

    randomizedPass: Randomly generates a list of curated/ranked songs, separated by style (Speed, Tech, etc).
        Similar to randomizedAccuracy, but checks are gated behind simply passing the song at each difficulty.
        Win condition: Same as randomizedAccuracy, but you just need to pass the goal map instead of meeting an accuracy threshold.
        Can lead to similarly unbalanced experiences as randomizedAccuracy,
        but is more accessible for players who may struggle with accing certain songs/difficulties but can still pass them.

    presetAccuracy:Uses the preset song list under the "Songs" option, and gates checks behind accuracy thresholds (e.g getting A or above on Expert+, an S on Expert, etc).
        Win condition: can either be a preselected goal map, or just pass the hardest accuracy threshold of your final map.

    presetPass: Uses the preset song list under the "Songs" option, and gates checks behind simply passing the song at each difficulty.
        Win condition: can either be a preselected goal map, or just pass the final song in the playlist. (currently only the latter is implemented)
    """
    display_name = "Game Mode"
    option_randomizedPP = 0
    option_randomizedAccuracy = 1
    option_randomizedPass = 2
    option_presetAccuracy = 3
    option_presetPass = 4
    default = option_randomizedAccuracy

class MaxStars(Range):
    """Maximum star rating for maps to be included in the pool, if using randomized map pools.
    Some reference points, for those unfamiliar with star ratings:
    Beat Saber Normal is 2.25 stars
    Country Rounds Hard is 3.3 stars
    Crab Rave Expert is 6.7 stars
    $100 Bills Expert+ is 8.2 stars
    Ghost Expert+ on the Camellia OST is 11.3 stars
    Power of the Saber Blade Expert+ is 12.6 stars
    Ov Sacrament Expert+ is 12.9 stars
    The highest rated map on BeatLeader as of February 2025 is Unwelcome School at 15.9 stars"""
    display_name = "Max Stars"
    range_start = 1
    range_end = 16
    default = 10

class GoalPP(Range):
    """PP threshold required to win. Only applicable for randomizedPP mode."""
    display_name = "Goal PP"
    range_start = 100
    range_end = 10000
    default = 1000

class LockGoalMap(DefaultOnToggle):
    """Whether the goal map is locked until you have a certain number of Bloq Keys. Only applicable for randomizedAccuracy and randomizedPass modes."""
    display_name = "Lock Goal Map"

class BloqKeysRequired(Range):
    """Number of Bloq Keys required to unlock the goal map if lockGoalMap is enabled."""
    display_name = "Bloq Keys Required to Unlock Goal Map"
    range_start = 1
    range_end = 100
    default = 10

class ExtraBloqKeys(Range):
    """Extra Bloq Keys added to the item pool. Only applicable for randomizedAccuracy and randomizedPass modes."""
    display_name = "Extra Bloq Keys"
    range_start = 0
    range_end = 100
    default = 5

class FormulaSanity(Toggle):
    """Not currently implemented. Your base pp formula is downgraded. Adds pp formula improvements into the item pool. Only works with randomizedPP."""
    display_name = "Formula Sanity"

class SongSorting(Choice):
    """The order in which you unlock songs in each playlist. Currently only difficulty count is implemented for preset lists. Difficulty count means single difficulties go first and full spread maps go last. Difficulty sorting is ascending by default (easiest to hardest). Descending would be the opposite (hardest maps go first)"""
    display_name = "Song Sorting"
    option_randomize = 0
    option_difficulty = 1
    option_difficulty_descending = 2
    option_difficulty_count = 3
    default = option_difficulty

class MapTypeWeighting(Choice):
    """How commonly each type of map (speed, midspeed, tech, acc) appears in the pool. All modes are randomized, only the weighting of each type is changed.
    If you set your max stars very low (<7), you may need to pick acc_exclusive, as maps do not get tagged other categories (especially speed) unless they have enough stars."""
    display_name = "Map Type Weighting"
    option_equal_weight = 0
    option_randomize_weight = 1
    option_speed_exclusive = 2
    option_tech_exclusive = 3
    option_midspeed_exclusive = 4
    option_acc_exclusive = 5
    default = option_equal_weight

class ExtraUnlocks(Range):
    """Amount of additional song unlock items to generate, along with the necessary (one per track)"""
    display_name = "Extra Unlocks"
    range_start = 0
    range_end = 50
    default = 5


class AccuracyThreshold(Choice):
    """Maximum accuracy grade required to check locations in accuracy modes (presetAccuracy, randomizedAccuracy).
    Every accuracy below the selected one also counts as a check (e.g if you select B, then both $100 Bills Expert (B) and $100 Bills Expert (C) would count as checks)
    Has no effect in pass or PP modes. The grade is shown in each location name so you always know what's required."""
    display_name = "Accuracy Threshold"
    option_C = 0
    option_B = 1
    option_A = 2
    option_S = 3
    option_SS = 4
    default = option_A  # A
    
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
    Songs that may occur in the custom playlist if a preset game mode is selected. Ignored otherwise.
    
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
    game_mode: GameMode
    death_link: DeathLink
    songs: Songs
    max_stars: MaxStars
    goal_pp: GoalPP
    lock_goal_map: LockGoalMap
    bloq_keys_required: BloqKeysRequired
    extra_bloq_keys: ExtraBloqKeys
    formula_sanity: FormulaSanity
    song_sorting: SongSorting
    map_type_weighting: MapTypeWeighting
    extra_unlocks: ExtraUnlocks
    accuracy_threshold: AccuracyThreshold