import os
import requests
import json
import time

"""Creates a master list of cached ranked BeatLeader maps to pull from during random generation."""
class BeatLeaderRankedMaps:
    BASE_URL = "https://api.beatleader.com/maps"

    PAGE_SIZE = 100
    OUTPUT_FILE = "ranked_maps.json"

    # Default filter parameters (as observed)
    DEFAULT_PARAMS = {
        "type": "ranked",
        "date_from": 1577872242 # Jan 1, 2020, to prevent really old maps that were lowkey kinda stinky
    }

    @staticmethod
    def fetch_all_ranked_maps():
        all_maps = []
        page = 0

        session = requests.Session()

        while True:
            params = {
                "page": page,
                "count": BeatLeaderRankedMaps.PAGE_SIZE,
                **BeatLeaderRankedMaps.DEFAULT_PARAMS
            }

            response = session.get(
                BeatLeaderRankedMaps.BASE_URL,
                params=params,
                timeout=15
            )

            response.raise_for_status()

            data = response.json()
            maps = data.get("data", [])

            if not maps:
                break

            print(f"Fetched page {page}: {len(maps)} maps")

            all_maps.extend(maps)
            page += 1

            # basic rate-limit protection
            time.sleep(0.2)

        return all_maps

    @staticmethod
    def extract_fields(raw_maps):
        result = []

        for m in raw_maps:
            difficulties = {}

            for diff in m.get("difficulties", []):
                name = diff.get("difficultyName")
                stars = diff.get("stars")
                pass_stars = diff.get("passRating")
                acc_stars = diff.get("accRating")
                tech_stars = diff.get("techRating")
                map_type = diff.get("type")

                if name and stars is not None:
                    difficulties[name] = {
                        "stars": stars,
                        "pass_stars": pass_stars,
                        "acc_stars": acc_stars,
                        "tech_stars": tech_stars,
                        "map_type": map_type
                    }

            raw_id = m.get("id")

            # Remove all lowercase and uppercase x characters
            clean_id = None
            if isinstance(raw_id, str):
                clean_id = raw_id.replace("x", "").replace("X", "")

            entry = {
                "map_name": m.get("name"),
                "level_id": clean_id,
                "hash": m.get("hash"),
                "star_ratings": difficulties,
                "tags": m.get("tags", [])
            }

            result.append(entry)

        return result


    @staticmethod
    def save_to_json(data, filename=None):
        if filename is None:
            filename = BeatLeaderRankedMaps.OUTPUT_FILE

        # Get the data directory relative to this file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up to Archipelago root (3 levels when in apworld: beat_saber -> beat_saber.apworld -> custom_worlds -> Archipelago)
        repo_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
        data_dir = os.path.join(repo_root, "data")
        full_path = os.path.join(data_dir, filename)
        print("full path: " + full_path)

        with open(full_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @staticmethod
    def run(output_file=None):
        print("Fetching ranked maps...")

        raw_maps = BeatLeaderRankedMaps.fetch_all_ranked_maps()

        print(f"Total maps: {len(raw_maps)}")

        cleaned = BeatLeaderRankedMaps.extract_fields(raw_maps)

        BeatLeaderRankedMaps.save_to_json(cleaned, output_file)

        print("Done.")