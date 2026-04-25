from fastapi import APIRouter
import requests
from bs4 import BeautifulSoup


router = APIRouter()


@router.get("/preview")
def get_preview(url: str):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}

        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        def get_meta(property_name: str):
            tag = soup.find("meta", property=property_name)
            if tag and tag.get("content"):
                return tag["content"]

            tag = soup.find("meta", attrs={"name": property_name})
            if tag and tag.get("content"):
                return tag["content"]

            return None

        title = get_meta("og:title") or (soup.title.string.strip() if soup.title and soup.title.string else None)
        description = get_meta("og:description") or get_meta("description")
        image = get_meta("og:image")

        return {
            "title": title,
            "description": description,
            "image": image,
            "url": url,
        }
    except Exception:
        return {
            "title": url,
            "description": "Preview unavailable",
            "image": None,
            "url": url,
        }