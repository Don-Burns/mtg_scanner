import logging.config
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import mtg_scanner.db as db
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


def get_db():
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
async def card_list(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request=request, name="card_list.tmpl.html")


@app.post("/sync_scryfall_data")
def sync_db_scryfall(orm: db.OrmSession = Depends(get_db)):
    logger.info("Syncing Scryfall data")
    cards = bulk_data.read_bulk_file(SCRYFALL_BULK_DATA_PATH)
    logger.info("Read %s cards from Scryfall bulk data", len(cards))
    populate_cards_from_scryfall_data(
        cards=cards, orm=orm, image_dir=SCRYFALL_IMAGE_DIR
    )
    logger.info("Synced Scryfall data")
