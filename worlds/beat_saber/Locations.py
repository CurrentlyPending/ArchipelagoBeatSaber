from BaseClasses import Location
from .Options import BSOptions

class BSLocation(Location):
    game: str = "Beat Saber"

location_table = {"Node " + f"{i}".zfill(2) : i for i in range(50)}