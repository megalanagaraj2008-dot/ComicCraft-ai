import json
import re

from google import genai
from google.genai import types

from app.config import get_settings
from app.schemas import PromptRequest


def _extract_json(text: str):
    text = text.strip()

    if text.startswith("```"):
        text = re.sub(
            r"^```(?:json)?\s*",
            "",
            text,
        )

        text = re.sub(
            r"\s*```$",
            "",
            text,
        )

    match = re.search(
        r"\{.*\}|\[.*\]",
        text,
        re.S,
    )

    if not match:
        raise ValueError(
            "Gemini did not return valid JSON."
        )

    return json.loads(match.group(0))


def generate_outline(
    request: PromptRequest,
) -> list[dict]:

    settings = get_settings()

    if not settings.gemini_api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is missing. "
            "Add it to your .env file."
        )

    client = genai.Client(
        api_key=settings.gemini_api_key
    )

    prompt = f"""
Create a cohesive {settings.panels}-panel comic outline.

USER STORY:
{request.story_prompt}

MAIN CHARACTER:
{request.character_name}

SETTING:
{request.setting}

TONE:
{request.tone}

ART STYLE:
{request.art_style}

Return ONLY valid JSON.

Use exactly this structure:

{{
  "panels": [
    {{
      "panel_number": 1,
      "title": "Short panel title",
      "scene_description": "Detailed scene description",
      "image_prompt": "Detailed prompt for an image generation model"
    }}
  ]
}}

Requirements:

1. Generate exactly {settings.panels} panels.
2. Maintain the same main character throughout.
3. Give the story a clear beginning.
4. Develop the conflict or adventure.
5. Include a meaningful turning point.
6. End with a satisfying conclusion.
7. Make every image prompt visually detailed.
8. Do not put written text inside generated images.
9. Do not generate speech bubbles inside images.
10. Match the requested art style.
11. Match the requested tone.
"""

    response = client.models.generate_content(
        model=settings.gemini_flash_model,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.9,
            response_mime_type="application/json",
        ),
    )

    data = _extract_json(response.text)

    if isinstance(data, dict):
        panels = data.get("panels", [])
    else:
        panels = data

    if not isinstance(panels, list):
        raise ValueError(
            "Invalid panel data returned by Gemini."
        )

    if len(panels) != settings.panels:
        raise ValueError(
            f"Expected {settings.panels} panels, "
            f"but Gemini returned {len(panels)}."
        )

    return panels