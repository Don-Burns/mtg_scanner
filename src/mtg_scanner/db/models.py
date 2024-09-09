from sqlalchemy import Engine, Enum, ForeignKey, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship

from mtg_scanner.db import logger


class Base(DeclarativeBase):
    """
    Base class for all models.
    """


class CardColor(Enum):
    """
    MTG Card color
    """

    WHITE = "white"
    BLUE = "blue"
    BLACK = "black"
    RED = "red"
    GREEN = "green"
    COLORLESS = "colorless"


class Card(Base):
    """
    MTG Card
    """

    __tablename__ = "card"

    card_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, nullable=False, autoincrement=True
    )
    external_card_id: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    # colors: Mapped[list[CardColor]] = mapped_column(CardColor, nullable=False) # TODO: figure out how to represent list of colours here
    mana_cost: Mapped[str] = mapped_column(String(255), nullable=False)
    power: Mapped[int | None]
    toughness: Mapped[int | None]
    set_code: Mapped[str | None] = mapped_column(String(3), nullable=True)
    scryfall_id: Mapped[str | None]
    scryfall_uri: Mapped[str | None]
    card_art_uri: Mapped[str | None]


def migrate(engine: None | Engine):
    if engine is None:
        logger.warning("Creating in-memory database as no engine was provided")
        engine = create_engine("sqlite:///:memory:")

    with Session(engine) as session:
        Base.metadata.create_all(engine)
