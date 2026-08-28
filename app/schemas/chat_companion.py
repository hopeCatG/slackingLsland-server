from pydantic import BaseModel, Field


class CreateChatSessionRequest(BaseModel):
    topic: str = Field(min_length=1, max_length=100)
    mood: str = Field(min_length=1, max_length=50)
    eventDetail: str = Field(min_length=2, max_length=1000)


class SendChatMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=2000)
