from __future__ import annotations

import base64
import logging

from openai import OpenAI

from ..config import get_settings


logger = logging.getLogger(__name__)

_ASPECT_RATIO_TO_SIZE = {
    "1:1": "1024x1024",
    "square": "1024x1024",
    "4:5": "1024x1536",
    "portrait": "1024x1536",
    "5:4": "1536x1024",
    "16:9": "1536x1024",
    "landscape": "1536x1024",
}


def resolve_image_size(aspect_ratio: str | None) -> str:
    normalized = str(aspect_ratio or "").strip().lower()
    return _ASPECT_RATIO_TO_SIZE.get(normalized, "1024x1024")


def build_image_prompt(prompt: str, style: str | None = None, aspect_ratio: str | None = None) -> str:
    parts = [str(prompt or "").strip()]

    if style:
        parts.append(f"Style: {str(style).strip()}")
    if aspect_ratio:
        parts.append(f"Aspect ratio: {str(aspect_ratio).strip()}")

    return "\n".join(part for part in parts if part)


def _extract_image_url(result: object) -> str | None:
    data = getattr(result, "data", None)
    if not data:
        return None

    first = data[0]
    url = getattr(first, "url", None)
    if isinstance(url, str) and url.strip():
        return url

    b64_json = getattr(first, "b64_json", None)
    if isinstance(b64_json, str) and b64_json.strip():
        return f"data:image/png;base64,{b64_json}"

    return None


def generate_image_result(prompt: str, style: str | None = None, aspect_ratio: str | None = None) -> dict[str, object]:
    cleaned_prompt = str(prompt or "").strip()
    if not cleaned_prompt:
        raise ValueError("Image prompt is required.")

    settings = get_settings()
    client = OpenAI(api_key=settings.openai_api_key)
    composed_prompt = build_image_prompt(cleaned_prompt, style, aspect_ratio)
    size = resolve_image_size(aspect_ratio)

    logger.info(
        "Image generation request prompt_length=%s style=%s aspect_ratio=%s size=%s",
        len(cleaned_prompt),
        style,
        aspect_ratio,
        size,
    )

    result = client.images.generate(
        model="gpt-image-1",
        prompt=composed_prompt,
        size=size,
    )

    image_url = _extract_image_url(result)
    if not image_url:
        raise ValueError("Image provider returned no image output.")

    logger.info("Image generation completed prompt_length=%s", len(cleaned_prompt))
    return {
        "type": "images",
        "content": "Generated image",
        "image_url": image_url,
        "actions": ["Regenerate", "Make variations"],
        "meta": {
            "prompt": cleaned_prompt,
            "style": style or "",
            "aspect_ratio": aspect_ratio or "1:1",
        },
    }