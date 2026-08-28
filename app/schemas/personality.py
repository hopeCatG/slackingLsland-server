from pydantic import BaseModel


class AnswerRequest(BaseModel):
    optionId: int
