from pathlib import Path

from fastapi import (
    APIRouter,
    Form,
    HTTPException,
    Request,
)

from fastapi.responses import (
    HTMLResponse,
    JSONResponse,
    FileResponse,
)

from fastapi.templating import (
    Jinja2Templates,
)

from app.config import get_settings
from app.schemas import (
    ComicResponse,
    Panel,
    PromptRequest,
)

from app.services.gemini_flash import (
    generate_outline,
)

from app.services.gemini_pro import (
    generate_story,
)

from app.services.image_generator import (
    generate_image,
)

from app.services.layout_builder import (
    build_comic_layout,
)

from app.services.exporters import (
    save_pdf,
)


BASE_DIR = Path(
    __file__
).resolve().parent.parent


templates = Jinja2Templates(
    directory=str(
        BASE_DIR / "templates"
    )
)


router = APIRouter()


@router.get(
    "/",
    response_class=HTMLResponse,
)
async def home(request: Request):

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
        },
    )


def _generate(
    request_data: PromptRequest,
) -> ComicResponse:

    # 1. Generate five-panel outline
    outline = generate_outline(
        request_data
    )

    # 2. Generate narration/dialogue
    story = generate_story(
        request_data,
        outline,
    )

    # 3. Generate images
    image_paths = []

    for panel in outline:

        image_path = generate_image(
            panel["image_prompt"],
            int(panel["panel_number"]),
        )

        image_paths.append(
            image_path
        )

    # 4. Build layout
    layout = build_comic_layout(
        outline,
        story,
        image_paths,
    )

    # 5. Create title
    title = (
        f"{request_data.character_name}: "
        f"{request_data.story_prompt[:45]}"
    )

    # 6. Export PDF
    pdf_url = save_pdf(
        title,
        layout,
    )

    panels = [
        Panel(**item)
        for item in layout
    ]

    return ComicResponse(
        title=title,
        panels=panels,
        pdf_url=pdf_url,
    )


@router.post(
    "/generate",
    response_class=HTMLResponse,
)
async def generate_form(
    request: Request,

    story_prompt: str = Form(...),

    character_name: str = Form(...),

    setting: str = Form(...),

    tone: str = Form(...),

    art_style: str = Form(...),
):

    try:

        data = PromptRequest(
            story_prompt=story_prompt,
            character_name=character_name,
            setting=setting,
            tone=tone,
            art_style=art_style,
        )

        comic = _generate(data)

        return templates.TemplateResponse(
            "comic_preview.html",
            {
                "request": request,
                "comic": comic,
            },
        )

    except Exception as exc:

        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "error": str(exc),
            },
            status_code=500,
        )


@router.post(
    "/generate-comic/json",
    response_model=ComicResponse,
)
async def generate_json(
    data: PromptRequest,
):

    try:

        return _generate(data)

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc


@router.post("/test-image")
async def test_image(
    prompt: str = Form(...),
):

    try:

        path = generate_image(
            prompt,
            0,
        )

        return JSONResponse(
            {
                "image_url": path,
            }
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc


@router.get(
    "/export-success",
    response_class=HTMLResponse,
)
async def export_success(
    request: Request,
):

    return templates.TemplateResponse(
        "export_success.html",
        {
            "request": request,
        },
    )


@router.get("/health")
async def health():

    return {
        "status": "ok",
        "service": "ComicCraft",
    }


@router.get(
    "/download/{filename}"
)
async def download_pdf(
    filename: str,
):

    settings = get_settings()

    safe_name = Path(filename).name

    path = (
        settings.exports_dir
        / safe_name
    )

    if not path.exists():

        raise HTTPException(
            status_code=404,
            detail="PDF not found",
        )

    return FileResponse(
        path,
        media_type="application/pdf",
        filename=safe_name,
    )