import os
from typing import TypeVar

from google import genai
from google.genai import types
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

DEFAULT_MODEL = "gemini-flash-lite-latest"


def _get_gemini_client() -> genai.Client:
    # Retry transient overload/rate-limit errors with exponential backoff.
    retry = types.HttpRetryOptions(
        attempts=5,
        initial_delay=5,
        max_delay=60,
        http_status_codes=[429, 500, 503, 504],
    )
    return genai.Client(
        api_key=os.environ["GEMINI_API_KEY"],
        http_options=types.HttpOptions(retry_options=retry),
    )


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
