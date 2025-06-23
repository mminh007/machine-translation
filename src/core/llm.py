from functools import cache
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from logs.logger_factory import get_logger
from schema.llamaCpp import ChatLlamaCpp
import traceback

logger = get_logger("llm", "llm.log")

from core.settings import settings
from schema.models import (
    AllModelEnum,
    OpenAIModelName,
    DeepseekModelName,
    AzureOpenAIModelName,
    LocalvLLMModelName,)


_MODEL_MAP: dict[AllModelEnum, type] = {
    OpenAIModelName.GPT_4O_MINI: "gpt-4o-mini",
    OpenAIModelName.GPT_4O: "gpt-4o",
    AzureOpenAIModelName.AZURE_GPT_4O_MINI: settings.AZURE_OPENAI_DEPLOYMENT_MAP.get(
        "gpt-4o-mini", ""
    ),
    AzureOpenAIModelName.AZURE_GPT_4O: settings.AZURE_OPENAI_DEPLOYMENT_MAP.get("gpt-4o", ""),
    DeepseekModelName.DEEPSEEK_CHAT: "deepseek-chat",

    LocalvLLMModelName.MISTRAL_7B: "mistral-7b",
    LocalvLLMModelName.LLAMA_3_8B: "llama-3-8b",
    LocalvLLMModelName.LLAMA_3_34B: "llama-3-34b",
    LocalvLLMModelName.LLAMA_32_3B_INSTRUCT: "llama-32-3B-instruct",
    LocalvLLMModelName.LLAMA_32_1B_INSTRUCT: "llama-32-1B-instruct",
    LocalvLLMModelName.LLAMA_CPP_7B: "llama-cpp-7b"
}

@cache
def get_model(model_name: str | AllModelEnum):
    """
    Get the model class based on the model name. Supports string or Enum.
    Logs error and returns None if not found.
    """
    try:
        if isinstance(model_name, str):
            # Try to convert string to proper Enum
            for enum_class in (OpenAIModelName,
                               AzureOpenAIModelName,
                               DeepseekModelName,
                               LocalvLLMModelName):
                try:
                    model_name = enum_class(model_name)
                    break
                except ValueError:
                    continue
            else:
                logger.error(f"❌ Unknown model name string: {model_name}")
                return None

        logger.debug(f"🔍 Resolved model enum: {model_name}")

        api_model_name = _MODEL_MAP.get(model_name)
        if not api_model_name:
            logger.error(f"❌ No API model found for {model_name}")
            return None

        if model_name in OpenAIModelName:
            return ChatOpenAI(model=api_model_name, temperature=0.5, streaming=True)

        if model_name in AzureOpenAIModelName:
            if not settings.AZURE_OPENAI_API_KEY or not settings.AZURE_OPENAI_ENDPOINT:
                logger.error("Azure OpenAI API key or endpoint missing.")
                return None

            return AzureChatOpenAI(
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                deployment_name=api_model_name,
                api_version=settings.AZURE_OPENAI_API_VERSION,
                temperature=0.5,
                streaming=True,
                timeout=60,
                max_retries=3,
            )

        if model_name in DeepseekModelName:
            return ChatOpenAI(
                model=api_model_name,
                temperature=0.5,
                streaming=True,
                openai_api_base="https://api.deepseek.com",
                openai_api_key=settings.DEEPSEEK_API_KEY,
            )

        # if model_name in HuggingFaceModelName:
        #     llm = HuggingFaceEndpoint(
        #         model=api_model_name,
        #         token=settings.HUGGINGFACE_API_KEY,
        #         temperature=0.5,
        #         max_new_tokens=512,
        #         top_p=0.95,
        #         top_k=40,
        #         repetition_penalty=1.2,
        #         stop=["\n", "\n\n"])
            
        #     return ChatHuggingFace(llm=llm)

        if model_name in LocalvLLMModelName:
            return ChatOpenAI(
                model=api_model_name,
                temperature=0.5,
                streaming=True,
                openai_api_base="http://vllm:8001/v1",
                openai_api_key=settings.VLLM_API_KEY,
            )
        
    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"🔥 Failed to load model {model_name}: {e}\n{tb}")
        return None