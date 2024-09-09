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


@app.get("/items/{id_}", response_class=HTMLResponse)
async def read_item(request: Request, id_: str):
    return templates.TemplateResponse(
        request=request, name="item.html", context={"id": id_}
    )
