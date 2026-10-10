import os
from typing import TypeVar

from google import genai
from google.genai import types
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

DEFAULT_MODEL = "gemini-flash-latest"


def _get_gemini_client() -> genai.Client:
    return genai.Client(api_key=os.environ["GEMINI_API_KEY"])


def generate_structured(prompt: str, schema: type[T]) -> T:
    """Send a prompt to Gemini and parse the JSON response into `schema`."""
    client = _get_gemini_client()
    response = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL", DEFAULT_MODEL),
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=schema,
        ),
    )
    if response.parsed is None:
        raise ValueError(f"Gemini returned no parseable output: {response.text!r}")
    return response.parsed
