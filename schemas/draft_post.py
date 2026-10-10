from pydantic import BaseModel


class DraftPost(BaseModel):
    hook: str   # opening headline line
    body: str   # supporting paragraph
    url: str    # article URL
