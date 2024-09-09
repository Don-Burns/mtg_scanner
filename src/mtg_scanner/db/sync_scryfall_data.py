from pathlib import Path

from mtg_scanner.db import OrmSession, insert, logger
from mtg_scanner.db.models import Card
from mtg_scanner.scryfall_data.model import ScryfallCard


def populate_cards_from_scryfall_data(
    cards: list[ScryfallCard], orm: OrmSession, image_dir: Path
) -> None:
    logger.info("Populating cards from Scryfall data")
    orm.begin()
    while len(cards) > 0:
        card = cards.pop()
        statement = insert(Card).values(
            name=card.name,
            mana_cost=card.mana_cost,
            rarity=card.rarity.value,
            power=card.power,
            toughness=card.toughness,
            set_code=card.set,
            scryfall_id=card.id,
            scryfall_uri=card.uri,
            card_art_uri=(image_dir / f"{card.id}.png").as_uri(),
        )
        statement = statement.on_conflict_do_nothing(index_elements=[Card.scryfall_id])
        orm.execute(statement)
        if len(cards) % 100 == 0:
            # Commit every 100 cards
            orm.commit()
            orm.begin()
            logger.info("%s cards left to process", len(cards))
    orm.commit()
