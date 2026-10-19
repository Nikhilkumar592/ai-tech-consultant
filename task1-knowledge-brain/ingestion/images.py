"""Image downloading and vision-based analysis using Claude."""
from __future__ import annotations

import base64
import hashlib
import logging
from pathlib import Path

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


async def download_image(
    image_url: str,
    save_dir: Path | None = None,
) -> tuple[bytes | None, str]:
    """Download an image, return (bytes, local_path) or (None, "")."""
    save_dir = save_dir or settings.images_dir
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.get(
                image_url,
                headers={"User-Agent": "KnowledgeBrain/1.0 (educational project)"},
            )
            resp.raise_for_status()

            content_type = resp.headers.get("content-type", "")
            if not content_type.startswith("image/"):
                logger.warning(f"Not an image: {image_url} ({content_type})")
                return None, ""

            data = resp.content
            img_hash = hashlib.sha256(data).hexdigest()[:16]
            ext = _ext_from_content_type(content_type)
            filename = f"{img_hash}{ext}"
            local_path = save_dir / filename

            local_path.write_bytes(data)
            return data, str(local_path)

    except Exception as e:
        logger.warning(f"Failed to download image {image_url}: {e}")
        return None, ""


async def analyze_image_with_vision(
    image_data: bytes,
    image_url: str,
    surrounding_text: str = "",
    article_title: str = "",
) -> str:
    """Use Claude vision to describe the content of an image.

    Returns a text description of what the image shows.
    """
    if settings.mock_mode or not settings.has_anthropic_key:
        return _mock_image_description(image_url, surrounding_text, article_title)

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

        # Determine media type
        media_type = "image/png"
        if image_url.lower().endswith(".jpg") or image_url.lower().endswith(".jpeg"):
            media_type = "image/jpeg"
        elif image_url.lower().endswith(".gif"):
            media_type = "image/gif"
        elif image_url.lower().endswith(".webp"):
            media_type = "image/webp"

        b64_data = base64.b64encode(image_data).decode("utf-8")

        context_info = ""
        if article_title:
            context_info += f"This image is from a help article titled: '{article_title}'. "
        if surrounding_text:
            context_info += f"The surrounding text says: '{surrounding_text[:300]}'"

        message = client.messages.create(
            model=settings.claude_default_model,
            max_tokens=500,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": b64_data,
                            },
                        },
                        {
                            "type": "text",
                            "text": (
                                f"Describe what this screenshot shows from a software help center. "
                                f"Focus on: UI elements, settings, buttons, labels, menu items, "
                                f"and any visible configuration options. Be concise and factual. "
                                f"{context_info}"
                            ),
                        },
                    ],
                }
            ],
        )

        description = message.content[0].text
        logger.info(f"Vision analysis complete for {image_url}: {len(description)} chars")
        return description

    except Exception as e:
        logger.error(f"Vision analysis failed for {image_url}: {e}")
        return f"[Image analysis failed: {e}]"


def _mock_image_description(image_url: str, surrounding_text: str, article_title: str) -> str:
    """Generate a deterministic mock description for testing."""
    return (
        f"[Mock description] Screenshot from '{article_title}'. "
        f"Shows a software interface related to the article content. "
        f"Context: {surrounding_text[:100]}"
    )


def _ext_from_content_type(ct: str) -> str:
    """Map content-type to file extension."""
    mapping = {
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "image/gif": ".gif",
        "image/webp": ".webp",
        "image/svg+xml": ".svg",
    }
    for key, ext in mapping.items():
        if key in ct:
            return ext
    return ".png"
