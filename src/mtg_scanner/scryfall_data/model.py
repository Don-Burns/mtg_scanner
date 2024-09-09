from datetime import datetime
from enum import Enum

from pydantic import UUID4, BaseModel, Field


class Rarity(Enum):
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    MYTHIC = "mythic"
    BONUS = "bonus"
    SPECIAL = "special"


class Color(Enum):
    """
    MTG Card color
    """

    W = "W"
    U = "U"
    B = "B"
    R = "R"
    G = "G"


class CardImgUris(BaseModel):
    """
    Docs: https://scryfall.com/docs/api/images
    """

    art_crop: str
    border_crop: str
    large: str
    normal: str
    png: str
    small: str


class CardFace(BaseModel):
    """
    Docs: https://scryfall.com/docs/api/cards#card-face-objects
    """

    artist: str | None = None
    artist_id: str | None = None
    cmc: float | None = None
    color_indicator: list[Color] | None = None
    colors: list[Color] | None = None
    defense: str | None = None
    flavor_text: str | None = None
    illustration_id: UUID4 | None = None
    image_uris: CardImgUris | None = None
    layout: str | None = None
    loyalty: str | None = None
    mana_cost: str
    name: str
    object_: str = Field(alias="object")
    oracle_id: UUID4 | None = None
    oracle_text: str | None = None
    power: str | None = None
    printed_name: str | None = None
    printed_text: str | None = None
    printed_type_line: str | None = None
    toughness: str | None = None
    type_line: str | None = None
    watermark: str | None = None


class ScryfallCard(BaseModel):
    """
    Model for an entry in the Scryfall bulk data file
    Docs on card object: https://scryfall.com/docs/api/cards
    """

    # Core Card Fields
    arena_id: int | None = None
    id: str
    lang: str
    mtgo_id: int | None = None
    mtgo_foil_id: int | None = None
    multiverse_ids: list[int] | None = None
    tcgplayer_id: int | None = None
    tcgplayer_etched_id: int | None = None
    object_: str = Field(alias="object")
    layout: str
    oracle_id: UUID4 | None = None
    prints_search_uri: str
    rulings_uri: str
    scryfall_uri: str
    uri: str
    # Gameplay Fields
    all_parts: list[object] | None = None
    card_faces: list[CardFace] | None = None
    cmc: float | None = None
    color_identity: list[Color]
    color_indicator: list[Color] | None = None
    colors: list[Color] | None = None
    defense: str | None = None
    edhrec_rank: int | None = None
    hand_modifier: str | None = None
    keywords: list[str] | None = None
    legalities: dict[str, str]
    life_modifier: str | None = None
    loyalty: str | None = None
    mana_cost: str | None = None
    name: str
    oracle_text: str | None = None
    penny_rank: int | None = None
    power: str | None = None
    procuced_mana: list[Color] | None = None
    reserved: bool
    toughness: str | None = None
    type_line: str | None = None
    # Print Fields
    artist: str | None = None
    artist_ids: list[UUID4] | None = None
    attraction_lights: list[int] | None = None
    booster: bool
    border_color: str
    card_back_id: UUID4 | None = None
    collector_number: str
    content_warning: bool | None = None
    digital: bool
    finishes: list[str] | None = None
    flavour_name: str | None = None
    flavour_text: str | None = None
    frame_effects: list[str] | None = None
    frame: str
    full_art: bool
    games: list[str]
    highres_image: bool
    illustration_id: UUID4 | None = None
    image_status: str
    image_uris: CardImgUris | None = None
    oversized: bool
    prices: dict[str, object]
    printed_name: str | None = None
    printed_text: str | None = None
    printed_type_line: str | None = None
    promo: bool
    promo_types: list[str] | None = None
    purchase_uris: dict[str, object] | None = None
    rarity: Rarity
    related_uris: dict[str, object]
    released_at: datetime
    reprint: bool
    scryfall_set_uri: str
    set_name: str
    set_search_uri: str
    set_type: str
    set: str
    set_id: UUID4
    story_spotlight: bool
    textless: bool
    variation: bool
    variation_of: UUID4 | None = None
    security_stamp: str | None = None
    watermark: str | None = None
    preview_previewed_at: datetime | None = Field(
        alias="preview.previewed_at", default=None
    )
    preview_source_uri: str | None = Field(alias="preview.source_uri", default=None)
    preview_source: str | None = Field(alias="preview.source", default=None)
