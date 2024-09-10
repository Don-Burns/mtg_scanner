import logging.config
from collections.abc import Generator
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import mtg_scanner.db as db
import mtg_scanner.db.models as db_models
import mtg_scanner.env as env
from mtg_scanner.db.sync_scryfall_data import populate_cards_from_scryfall_data
from mtg_scanner.scryfall_data import bulk_data
from mtg_scanner.web_server import logger

env.export_dot_env()
DB_URL = env.get_db_url()

SRC_ROOT_DIR = Path(__file__).parent
STATIC_DIR = SRC_ROOT_DIR / "static"
SCRYFALL_DATA_DIR = SRC_ROOT_DIR.parent / "scryfall_data"

SCRYFALL_BULK_DATA_PATH = SCRYFALL_DATA_DIR / "bulk_data" / "bulk_data.json"

SCRYFALL_IMAGE_DIR = SCRYFALL_DATA_DIR / "image_data"

engine = create_engine(
    DB_URL,
    connect_args={
        # only for SQLite (see:https://fastapi.tiangolo.com/tutorial/sql-databases/#create-the-sqlalchemy-engine)
        "check_same_thread": False
    },
)
SessionLocal = sessionmaker(autoflush=False, autocommit=False, bind=engine)


def get_db() -> Generator[db.OrmSession, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app = FastAPI()

app.mount(
    "/static",
    StaticFiles(directory=STATIC_DIR, check_dir=True),
    name="static",
)

app.mount("/images", StaticFiles(directory=SCRYFALL_IMAGE_DIR), name="images")

templates = Jinja2Templates(directory=STATIC_DIR / "templates")

# logging_config = {
#     "version": 1,
# "formatters": {
#     "default": {
#         "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
#     }
# },
#     "handlers": {
#         "console": {
#             "level": "DEBUG",
#             "class": "logging.StreamHandler",
#             # "formatter": "default",
#             "stream": "ext://sys.stderr",
#         }
#     },
#     "root": {"level": "DEBUG", "handlers": ["console"], "propagate": True},
# }

# logging.config.dictConfig(logging_config)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request=request, name="home.tmpl.html")


COL_MAP = {
    "W": "⚪",
    "U": "🔵",
    "B": "⚫",
    "R": "🔴",
    "G": "🟢",
}


class _CardListRow(BaseModel):
    name: str
    color_text: str
    color_symbol: str
    mana_value: str
    rarity: str
    type: str
    image_uri: str
    scryfall_uri: str

    @staticmethod
    def _color_text_to_symbol(text: str) -> str:
        """
        Map color text to color symbols removing any duplicates
        Will skip any characters not in COL_MAP

        Args:
            text (str): text to process

        Returns:
            str: symbol string

        Usage:
            ```python
            _CardListRow._color_text_to_symbol("{W}{U}{B}{R}{G}") -> "⚪🔵⚫🔴🟢"
            _CardListRow._color_text_to_symbol("UUB") -> "🔵⚫"
            _CardListRow._color_text_to_symbol("RW") -> "⚪🔴"
            ```
        """
        # sort by WUBRG with no duplicates
        sorted_colors = {sym: "WUBRG".index(char) for char, sym in COL_MAP.items()}
        return "".join(
            sorted(
                list({COL_MAP[c] for c in text.upper() if c in COL_MAP}),
                key=sorted_colors.__getitem__,
            )
        )

    @staticmethod
    def _filter_color_text(text: str) -> str:
        """
        Filter out any characters not in COL_MAP and remove any duplicates before sorting to WUBRG order

        Args:
            text (str): text to process

        Returns:
            str: sorted string

        Usage:
            ```python
            _CardListRow._color_text_to_symbol("WUBRG") -> "WUBRG"
            _CardListRow._color_text_to_symbol("UUB") -> "UB"
            _CardListRow._color_text_to_symbol("RW") -> "WR"
            ```
        """
        # sort by WUBRG with no duplicates
        return "".join(
            sorted(list({c for c in text.upper() if c in COL_MAP}), key="WUBRG".index)
        )

    @classmethod
    def model_validate_orm(cls, card: db_models.Card) -> "_CardListRow":
        return cls(
            name=card.name,
            color_text=(
                _CardListRow._filter_color_text(card.mana_cost)
                if card.mana_cost is not None
                else "N/a"
            ),
            color_symbol=(
                _CardListRow._color_text_to_symbol(card.mana_cost)
                if card.mana_cost is not None
                else "N/a"
            ),
            mana_value=card.mana_cost if card.mana_cost is not None else "0",
            rarity=str(card.rarity),
            type=card.type if card.type is not None else "N/a",
            image_uri=(
                card.card_art_uri.removeprefix("file:///home/donal/src/mtg_scanner")
                if card.card_art_uri
                else "https://via.placeholder.com/150"
            ),
            scryfall_uri=card.scryfall_uri or "#",
        )


@app.get("/card_list", response_class=HTMLResponse)
async def card_list(
    request: Request, orm: db.OrmSession = Depends(get_db)
) -> HTMLResponse:
    cards = (
        orm.query(db_models.Card)
        .order_by(db_models.Card.name)
        .where(db_models.Card.mana_cost.is_not(None))
        .where(db_models.Card.card_art_uri.is_not(None))
        .limit(100)
        .all()
    )
    return templates.TemplateResponse(
        request=request,
        name="card_list.tmpl.html",
        context={
            "cards": [
                _CardListRow.model_validate_orm(card).model_dump() for card in cards
            ]
        },
    )


@app.post("/sync_scryfall_data")
def sync_db_scryfall(request: Request, orm: db.OrmSession = Depends(get_db)) -> None:
    logger.info("Syncing Scryfall data")
    cards = bulk_data.read_bulk_file(SCRYFALL_BULK_DATA_PATH)
    logger.info("Read %s cards from Scryfall bulk data", len(cards))
    populate_cards_from_scryfall_data(
        cards=cards, orm=orm, image_dir=SCRYFALL_IMAGE_DIR
    )
    logger.info("Synced Scryfall data")
