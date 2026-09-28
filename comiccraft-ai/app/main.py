from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routes import router


BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"


app = FastAPI(
    title="ComicCraft - AI Comic Story Creator",
    description=(
        "Generate personalized five-panel AI comics using "
        "Gemini and Hugging Face image generation."
    ),
    version="1.0.0",
)


app.mount(
    "/static",
    StaticFiles(directory=STATIC_DIR),
    name="static",
)


app.include_router(router)