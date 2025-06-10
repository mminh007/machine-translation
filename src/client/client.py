from typing import Any
import httpx
from schema.base import UserInput, StreamInput, ChatHistoryInput, ChatHistory, ChatMessage
import json
from logs.logger_factory import get_logger
import traceback

logger = get_logger("Client", "client.log")

class AgentClientError(Exception):
    pass


class AgentClient:
    """
    Client for interacting with the Agent API.
    """

    def __init__(self, base_url: str = "http://0.0.0.0:8000"):
        self.base_url = base_url
        self.agent = None
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
    
    def _parse_stream_line(self, line: str) -> ChatMessage | str | None:
        line = line.strip()
        if line.startswith("data: "):
            data = line[6:]
            if data == "[DONE]":
                return None
            try:
                parsed = json.loads(data)

            except Exception as e:
                tb = traceback.format_exc()
                logger.error(f"❌ JSON parsing error in stream: {e}\nRaw line: {data}\n{tb}")
                raise Exception(f"Error JSON parsing message from server: {e}")
            
            match parsed["type"]:
                case "message":
                    # Convert the JSON formatted message to an AnyMessage
                    try:
                        return ChatMessage.model_validate(parsed["content"])
                    except Exception as e:
                        tb = traceback.format_exc()
                        logger.error(f"❌ Invalid ChatMessage format: {e}\n{tb}")
                        raise Exception(f"Server returned invalid message: {e}")
                    
                case "token":
                    # Yield the str token directly
                    logger.info(f"🔸 Parsed token: {parsed['content']}")
                    token = parsed["content"]
                    if token.strip() == "":  
                        return None
                    return token
                
                case "error":
                    error_msg = "Error: " + parsed["content"]
                    return ChatMessage(type="ai", content=error_msg)
        return None
    
    async def ainvoke(
            self,
            message: str,
            model: str,
            thread_id: str | None = None,
            user_id: str | None = None,
            agent_config: dict[str, Any] | None = None,
    ):
        request = UserInput(message=message, thread_id=thread_id, user_id = user_id, agent_config=agent_config)
        if model:
            request.model = model
            
        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, read=60.0)) as client:
            try:
                logger.info(f"📤 Sending /chat/invoke request | thread_id={thread_id}")
                response = await client.post(
                    f"{self.base_url}/chat/invoke",
                    headers=self.headers,
                    json=request.model_dump(),
                )
                if response.status_code == 200:
                    return response.json()
                
                else:
                    error_body = await response.aread()
                    tb = traceback.format_exc()
                    logger.error(f"❌ /chat/invoke failed: {response.status_code} - {error_body.decode('utf-8')}\n{tb}")
                    raise Exception(f"Error: {response.status_code} - {response.text}")
                
            except httpx.RequestError as e:
                tb = traceback.format_exc()
                logger.error(f"🔥 Request error in ainvoke(): {e}\n{tb}")
                raise Exception(f"Request failed: {e}")


    async def astream(
            self,
            message: str,
            model: str,
            thread_id: str | None = None,
            user_id: str | None = None,
            agent_config: dict[str, Any] | None = None,
            stream_tokens: bool = True,
    ):
        request = StreamInput(message=message, stream_tokens=stream_tokens, thread_id=thread_id, user_id = user_id, agent_config=agent_config)
        if model:
            request.model = model

        async with httpx.AsyncClient() as client:
            try:
                logger.info(f"📡 Streaming /chat/stream request | thread_id={thread_id}")
                async with client.stream(
                    "POST",
                    f"{self.base_url}/chat/stream",
                    headers=self.headers,
                    json=request.model_dump(),
                ) as response:
                    if response.status_code == 200:
                        async for line in response.aiter_lines():
                            logger.debug(f"🧪 Raw stream line: {line!r}")
                            if line.strip():
                                
                                parsed = self._parse_stream_line(line)
                                logger.info(f"🔸 Parsed stream content: {parsed}")
                                if parsed is None:
                                    break
                                yield parsed
                    else:
                        error_body = await response.aread()
                        tb = traceback.format_exc()
                        logger.error(f"❌ /chat/stream failed: {response.status_code} - {error_body.decode('utf-8')}\n{tb}")
                        raise Exception(f"Error: {response.status_code} - {error_body.decode('utf-8')}")
                    
            except httpx.RequestError as e:
                tb = traceback.format_exc()
                logger.error(f"🔥 Request error in astream(): {e}\n{tb}")
                raise Exception(f"Request failed: {e}")
    
    def get_history(self, thread_id: str) -> ChatHistory:
        """
        Get chat history.

        Args:
            thread_id (str, optional): Thread ID for identifying a conversation
        """
        request = ChatHistoryInput(thread_id=thread_id)
        try:
            logger.info(f"📄 Fetching /history | thread_id={thread_id}")
            response = httpx.post(
                f"{self.base_url}/history",
                json=request.model_dump(),
                headers=self._headers,
                timeout=self.timeout,
            )
            response.raise_for_status()

        except httpx.HTTPError as e:
            tb = traceback.format_exc()
            logger.error(f"❌ get_history() failed: {e}\n{tb}")
            raise AgentClientError(f"Error: {e}")

        try:
            return ChatHistory.model_validate(response.json())
        except Exception as e:
            tb = traceback.format_exc()
            logger.error(f"❌ Invalid response format in get_history(): {e}\n{tb}")
            raise AgentClientError("Invalid history response format.")