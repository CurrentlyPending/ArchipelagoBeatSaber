from BaseClasses import Location


class BSLocation(Location):
    game: str = "Beat Saber"


DIFFICULTY_NAMES = ["Easy", "Normal", "Hard", "Expert", "ExpertPlus"]
ACCURACY_GRADES = ["C", "B", "A", "S", "SS"]


def get_highest_diff_idx(star_ratings: dict) -> int:
    """Return the 0-4 index of the highest available difficulty in a ranked map's star_ratings dict."""
    for diff_name in ["ExpertPlus", "Expert", "Hard", "Normal", "Easy"]:
        if diff_name in star_ratings:
            return DIFFICULTY_NAMES.index(diff_name)
    return 4  # fallback to ExpertPlus


def make_preset_mnemonic_name(song_name: str, difficulty: int, accuracy_grade: str = None) -> str:
    diff_name = DIFFICULTY_NAMES[difficulty]
    if accuracy_grade:
        return f"{song_name} ({diff_name}) - {accuracy_grade}"
    return f"{song_name} ({diff_name})"


def make_randomized_mnemonic_name(category: str, song_name: str, difficulty: int, accuracy_grade: str = None) -> str:
    diff_name = DIFFICULTY_NAMES[difficulty]
    if accuracy_grade:
        return f"[{category}] {song_name} ({diff_name}) - {accuracy_grade}"
    return f"[{category}] {song_name} ({diff_name})"

def generate_all_location_names():
    """Generate ~3k location names: 100 max songs, 4 categories, 6 variants per song (5 accuracy grades + 1 pass mode)."""
    names = {}
    
    # Randomized: base_id offsets per category
    for category, base_id in [("Speed", 1000), ("Tech", 2000), ("Midspeed", 3000), ("Acc", 4000)]:
        for song_idx in range(100):
            # Pass mode (no accuracy suffix)
            name = f"[{category}] Song {song_idx:02d}"
            names[name] = base_id + song_idx * 6
            
            # Accuracy modes
            for grade_idx, grade in enumerate(ACCURACY_GRADES):
                name = f"[{category}] Song {song_idx:02d} - {grade}"
                names[name] = base_id + song_idx * 6 + grade_idx + 1
    
    # Preset: no category prefix
    for song_idx in range(100):
        # Pass mode
        name = f"Song {song_idx:02d}"
        names[name] = song_idx * 6
        
        # Accuracy modes
        for grade_idx, grade in enumerate(ACCURACY_GRADES):
            name = f"Song {song_idx:02d} - {grade}"
            names[name] = song_idx * 6 + grade_idx + 1
    
    return names

location_name_to_id = generate_all_location_names()
id_to_location_name = {v: k for k, v in location_name_to_id.items()}
