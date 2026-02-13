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
progression_table = {
    "Progressive Song Unlock": BSItemData(1, ItemClassification.progression)
}

item_data_table = {
    **progression_table,
    **filler_table,
    "Victory": BSItemData(2, ItemClassification.progression_skip_balancing)
}

item_table = {name: data.code for name, data in item_data_table.items() if data.code is not None}
