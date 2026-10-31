from pathlib import Path

from fastapi.templating import Jinja2Templates

from camperlog.labels import status_label

TEMPLATES_DIR = Path(__file__).parent / "templates"

templates = Jinja2Templates(directory=TEMPLATES_DIR)
templates.env.globals["status_label"] = status_label
