from pydantic import BaseModel


class RankedArticle(BaseModel):
    title: str
    url: str
    summary: str
