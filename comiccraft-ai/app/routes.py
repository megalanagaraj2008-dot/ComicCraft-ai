from pathlib import Path

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent.parent

router = APIRouter()

templates = Jinja2Templates(
    directory=str(BASE_DIR / "templates")
)


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request
        }
    )


@router.post("/generate", response_class=HTMLResponse)
async def generate(
    request: Request,
    story_prompt: str = Form(...),
    character_name: str = Form(...),
    setting: str = Form(...),
    tone: str = Form(...),
    art_style: str = Form(...)
):
    # Temporary test response
    # We will connect Gemini + image generation after this works.

    return HTMLResponse(
        f"""
        <html>
        <head>
            <title>ComicCraft</title>
        </head>
        <body>
            <h1>🎨 ComicCraft</h1>

            <h2>Your comic request was received!</h2>

            <p><b>Story:</b> {story_prompt}</p>
            <p><b>Character:</b> {character_name}</p>
            <p><b>Setting:</b> {setting}</p>
            <p><b>Tone:</b> {tone}</p>
            <p><b>Art Style:</b> {art_style}</p>

            <hr>

            <p>✅ The /generate route is working.</p>

            <a href="/">Create another comic</a>
        </body>
        </html>
        """
    )


@router.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "ComicCraft"
    }