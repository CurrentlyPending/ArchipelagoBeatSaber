from dataclasses import dataclass
import os
from typing import TYPE_CHECKING, Dict, List, Optional, cast
import zipfile
from BaseClasses import Location
from worlds.Files import APPlayerContainer

class BeatSaberContainer(APPlayerContainer):
    """
    Responsible for generating the dynamic bplist files for the Beat Saber multiworld
    """
    game: Optional[str] = "Beat Saber"
    patch_file_ending = ".apbs"

    def __init__(self, patch_data: Dict[str, str], base_path: str = "", output_directory: str = "",
                 player: Optional[int] = None, player_name: str = "", server: str = ""):
        self.patch_data = patch_data
        self.file_path = base_path
        container_path = os.path.join(output_directory, base_path + ".apbs")
        super().__init__(container_path, player, player_name, server)

    def write_contents(self, opened_zipfile: zipfile.ZipFile) -> None:
        for filename, content in self.patch_data.items():
            opened_zipfile.writestr(filename, content)
        super().write_contents(opened_zipfile)