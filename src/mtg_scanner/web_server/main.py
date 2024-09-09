from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

SRC_ROOT_DIR = Path(__file__).parent
STATIC_DIR = SRC_ROOT_DIR / "static"

app = FastAPI()

app.mount(
    "/static",
    StaticFiles(directory=STATIC_DIR, check_dir=True),
    name="static",
)


templates = Jinja2Templates(directory=STATIC_DIR / "templates")


@app.get("/", response_class=HTMLResponse)
async def card_list(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request=request, name="card_list.html")
