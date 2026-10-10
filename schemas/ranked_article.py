from pydantic import BaseModel


class RankedArticle(BaseModel):
    title: str
    summary: str
    url: str
