import json
from pathlib import Path

from pydantic import TypeAdapter

from mtg_scanner.scryfall_data.model import ScryfallCard


def read_bulk_file(
    file: Path = Path(__file__).parent / "bulk_data/bulk_data.json",
) -> list[ScryfallCard]:
    with open(file, "r", encoding="utf-8") as f:
        data = json.load(f)

    return TypeAdapter(list[ScryfallCard]).validate_python(data)
