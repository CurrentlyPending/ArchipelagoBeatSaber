from typing import NamedTuple
from BaseClasses import Item, ItemClassification

class BSItem(Item):
    game: str = "Beat Saber"

class BSItemData(NamedTuple):
    code: int | None = None
    classification: ItemClassification = ItemClassification.progression

filler_table = {
    "Nothing": BSItemData(0, ItemClassification.filler)
}

item_data_table = {
    "Progressive Song Unlock": BSItemData(1, ItemClassification.progression),
    **filler_table
}

item_table = {name: data.code for name, data in item_data_table.items() if data.code is not None}
