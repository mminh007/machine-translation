from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage, SystemMessage
from schema.base import ChatMessage

def convert_message_content_to_string(content: str | list[str | dict]) -> str:
    if isinstance(content, str):
        return content
    text: list[str] = []
    for content_item in content:
        if isinstance(content_item, str):
            text.append(content_item)
            continue
        if content_item["type"] == "text":
            text.append(content_item["text"])
    return "".join(text)


def langchain_to_chat_message(message: BaseMessage) -> ChatMessage:
    """Convert a LangChain message into an internal ChatMessage."""
    content_str = convert_message_content_to_string(message.content)
    
    match message:
        case HumanMessage():
            return ChatMessage(type="human", content=content_str)
        case AIMessage():
            return ChatMessage(type="ai", content=content_str)
        case ToolMessage():
            return ChatMessage(type="tool", content=content_str)
        case SystemMessage():
            return ChatMessage(type="system", content=content_str)
        case _:
            raise ValueError(f"Unsupported message type: {type(message)}")


