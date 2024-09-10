import uuid
from datetime import datetime, timezone

from sqlalchemy import UUID, DateTime, Enum, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def build_default_dt_now() -> Mapped[datetime]:
    return mapped_column(
        DateTime, nullable=False, default=datetime.now().astimezone(timezone.utc)
    )


class Base(DeclarativeBase):
    """
    Base class for all models.
    """


class CardRarity(Enum):
    """
    MTG Card rarity
    """

    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    MYTHIC = "mythic"


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
        Integer, primary_key=True, nullable=False, autoincrement=True, unique=True
    )
    # external_card_id: Mapped[str] = mapped_column(
    #     UUID, nullable=False, unique=True, default=uuid.uuid4()
    # )
    name: Mapped[str] = mapped_column(String, nullable=False)
    # colors: Mapped[list[CardColor]] = mapped_column(CardColor, nullable=False) # TODO: figure out how to represent list of colours here
    mana_cost: Mapped[str | None] = mapped_column(String(255), nullable=True)
    rarity: Mapped[CardRarity] = mapped_column(String(25), nullable=False)
    power: Mapped[int | None]
    toughness: Mapped[int | None]
    type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    set_code: Mapped[str | None] = mapped_column(String(3), nullable=True)
    scryfall_id: Mapped[str | None] = mapped_column(String, nullable=True, unique=True)
    scryfall_uri: Mapped[str | None] = mapped_column(String, nullable=True, unique=True)
    card_art_uri: Mapped[str | None]
    created_at: Mapped[datetime] = build_default_dt_now()
    updated_at: Mapped[datetime] = build_default_dt_now()
    deleted_at: Mapped[datetime | None]


# class Config(Base):
#     """
#     Configuration
#     """

#     __tablename__ = "config"

#     config_id: Mapped[int] = mapped_column(
#         Integer, primary_key=True, nullable=False, autoincrement=True
#     )
#     key: Mapped[str] = mapped_column(String, nullable=False)
#     value: Mapped[str] = mapped_column(String, nullable=False)
#     created_at: Mapped[datetime] = build_default_dt_now()
#     updated_at: Mapped[datetime] = build_default_dt_now()
#     deleted_at: Mapped[datetime | None]
