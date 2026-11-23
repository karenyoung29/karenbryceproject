import json
import os
import sys
from pathlib import Path

from dotenv import find_dotenv, load_dotenv
from google import genai
from google.genai import errors, types
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Config — change the model name here only.
# Check it's current at https://ai.google.dev/gemini-api/docs/models
# and that it says "Free of charge" at https://ai.google.dev/gemini-api/docs/pricing
# ---------------------------------------------------------------------------
MODEL_NAME = "gemini-3.5-flash"

MAX_TAGS = 6

PROMPT = """Look at this image and describe its mood and aesthetic.
Return 3 to 6 short tags that would work as music tags on Last.fm
(moods like "melancholic" or "chill", or genres like "dream pop" or "lo-fi").
Respond only with JSON: {"tags": ["tag1", "tag2", ...]}"""

# File extension -> MIME type that Gemini expects
SUPPORTED_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}


# Structured output schema: Gemini must return {"tags": [str, ...]}
class TagsResponse(BaseModel):
    tags: list[str]


# ---------------------------------------------------------------------------
# .env / API key
# ---------------------------------------------------------------------------
def load_api_key() -> str:
    """Find .env in the current folder or any parent; ask for a path if not found."""
    print("Looking for .env file...")
    env_path = find_dotenv(usecwd=True)  # searches cwd, then each parent folder

    if not env_path:
        print("No .env file found in this folder or its parent folders.")
        env_path = input("Enter the path to your .env file: ").strip().strip('"')
        if not Path(env_path).is_file():
            raise FileNotFoundError(f".env file not found at: {env_path}")

    load_dotenv(env_path)
    print(f"Loaded .env from: {env_path}")

    api_key = os.getenv("GeminiKey")
    if not api_key:
        raise ValueError(
            f"GeminiKey is missing or empty in {env_path}. "
            "Add a line like: GeminiKey=your_api_key_here"
        )
    return api_key


# ---------------------------------------------------------------------------
# Image loading
# ---------------------------------------------------------------------------
def load_image(image_path: str) -> tuple[bytes, str]:
    """Return (image bytes, MIME type). Raises clear errors for bad input."""
    path = Path(image_path)

    if not path.is_file():
        raise FileNotFoundError(f"Image file not found: {path}")

    mime_type = SUPPORTED_TYPES.get(path.suffix.lower())
    if mime_type is None:
        raise ValueError(
            f"Unsupported file type '{path.suffix}'. "
            f"Use one of: {', '.join(sorted(SUPPORTED_TYPES))}"
        )

    print(f"Reading image: {path.name} ({mime_type})")
    return path.read_bytes(), mime_type


# ---------------------------------------------------------------------------
# Tag cleanup
# ---------------------------------------------------------------------------
def clean_tags(raw_tags: list[str]) -> list[str]:
    """Lowercase, trim, drop empties and duplicates (keeping order), cap at MAX_TAGS."""
    cleaned = []
    seen = set()
    for tag in raw_tags:
        tag = " ".join(str(tag).lower().split())  # trims and collapses inner spaces
        if tag and tag not in seen:
            seen.add(tag)
            cleaned.append(tag)
    return cleaned[:MAX_TAGS]


# ---------------------------------------------------------------------------
# Gemini call
# ---------------------------------------------------------------------------
def get_image_tags(image_path: str) -> dict:
    api_key = load_api_key()
    image_bytes, mime_type = load_image(image_path)

    client = genai.Client(api_key=api_key)

    print(f"Sending image to Gemini ({MODEL_NAME})...")
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                PROMPT,
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=TagsResponse,
            ),
        )
    except errors.ClientError as e:
        # 4xx errors: our request or our quota
        if e.code == 429:
            raise RuntimeError(
                "Rate limit hit (429). The free tier limits requests per minute "
                "and per day. Wait a minute and try again, or check your limits at "
                "https://aistudio.google.com/ (Usage / Rate limits)."
            ) from e
        if e.code == 404:
            raise RuntimeError(
                f"Model '{MODEL_NAME}' was not found (404). It may have been renamed "
                "or retired. Update MODEL_NAME at the top of this file."
            ) from e
        if e.code in (400, 403) and "API key" in str(e):
            raise RuntimeError("Gemini rejected the API key. Check GeminiKey in your .env.") from e
        raise RuntimeError(f"Gemini request failed ({e.code}): {e.message}") from e
    except errors.ServerError as e:
        raise RuntimeError(
            f"Gemini server error ({e.code}). This is on Google's side; try again shortly."
        ) from e

    print("Response received. Cleaning up tags...")

    # response.parsed is a TagsResponse when a Pydantic schema is used;
    # fall back to parsing the raw text just in case.
    parsed = response.parsed
    if parsed is None:
        parsed = TagsResponse.model_validate_json(response.text)

    return {"tags": clean_tags(parsed.tags)}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python gemini_image_tags.py path/to/image.jpg")
        sys.exit(1)

    try:
        result = get_image_tags(sys.argv[1])
    except (FileNotFoundError, ValueError, RuntimeError) as e:
        print(f"Error: {e}")
        sys.exit(1)

    print("Done!\n")
    print(json.dumps(result, indent=2))
