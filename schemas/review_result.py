from pydantic import BaseModel

class ReviewResult(BaseModel):
    verdict: bool
    feedback: str