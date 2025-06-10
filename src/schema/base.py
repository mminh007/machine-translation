from pydantic import BaseModel, Field
from typing import Any, Literal

class TextRequest(BaseModel):
    text: str
    src_lang: str
    tgt_lang: str
    model: str

class SpeechRequest(BaseModel):   
    audio: bytes

    
class BaseModelWrapper:
    """
    Base class for all models.
    """

    def __load_model__(self):
        raise NotImplementedError("load_model method not implemented.")
        
    def generate(self, request: TextRequest):
        
        raise NotImplementedError("Generate method not implemented.")

class UserInput(BaseModel):
    message: str
    thread_id: str | None
    user_id: str | None
    agent_config: dict[str, Any]
    model: str | None = None

class StreamInput(UserInput):
    stream_tokens: bool = Field(
        description="Whether to stream LLM tokens to the client.",
        default=True,
    )

class AgentInfo(BaseModel):
    """Info about an available agent."""

    key: str = Field(
        description="Agent key.",
        examples=["research_assistant"],
    )
    description: str = Field(
        description="Description of the agent.",
        examples=["A research assistant for generating research papers."],
    )

class ChatMessage(BaseModel):
    """Message in a chat."""

    type: Literal["human", "ai"] = Field(
        description="Role of the message.",
        examples=["human", "ai", "tool", "custom"],
    )
    content: str = Field(
        description="Content of the message.",
        examples=["Hello, world!"],
    )
    run_id: str | None = Field(
        description="Run ID of the message.",
        default=None,
        examples=["847c6285-8fc9-4560-a83f-4e6285809254"],
    )


class ChatHistoryInput(BaseModel):
    """Input for retrieving chat history."""

    thread_id: str = Field(
        description="Thread ID to persist and continue a multi-turn conversation.",
        examples=["847c6285-8fc9-4560-a83f-4e6285809254"],
    )

class ChatHistory(BaseModel):
    messages: list[ChatMessage]