from __future__ import annotations

import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ..services.image_service import generate_image_result


router = APIRouter(prefix="/api/images", tags=["image"])
logger = logging.getLogger(__name__)


class ImageRequest(BaseModel):
    prompt: str
    style: str | None = None
    aspect_ratio: str | None = None


@router.post("")
def generate_image(payload: ImageRequest):
    prompt = (payload.prompt or "").strip()
    logger.info(
        "Image endpoint request prompt=%s style=%s aspect_ratio=%s",
        prompt,
        payload.style,
        payload.aspect_ratio,
    )

    if not prompt:
        return JSONResponse(
            status_code=400,
            content={
                "type": "error",
                "content": "Image prompt is required.",
                "actions": ["Retry"],
                "meta": {},
            },
        )

    try:
        response = generate_image_result(prompt, payload.style, payload.aspect_ratio)
        logger.info("Image endpoint response=%s", response)
        return response
    except Exception as error:
        logger.exception("image generation failed")
        return JSONResponse(
            status_code=500,
            content={
                "type": "error",
                "content": "Something went wrong. Try again.",
                "actions": ["Retry"],
                "meta": {
                    "detail": str(error),
                },
            },
        )