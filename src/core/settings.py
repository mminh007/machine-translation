from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr, Field
from schema.models import OpenAIModelName

class Settings(BaseSettings):
    """
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        validate_assignment=True,
    )
    NGROK_TOKEN: SecretStr | None = None
    
    # API Keys for various LLM providers
    VLLM_API_KEY: SecretStr | None = None
    OPENAI_API_KEY: SecretStr | None = None
    DEEPSEEK_API_KEY: SecretStr | None = None
    HUGGINGFACE_API_KEY: SecretStr | None = None

     # Azure OpenAI Settings
    AZURE_OPENAI_API_KEY: SecretStr | None = None
    AZURE_OPENAI_ENDPOINT: str | None = None
    AZURE_OPENAI_API_VERSION: str = "2024-02-15-preview"
    AZURE_OPENAI_DEPLOYMENT_MAP: dict[str, str] = Field(
        default_factory=dict, description="Map of model names to Azure deployment IDs"
    )
    # PostgreSQL Configuration
    POSTGRES_USER: str | None = None
    POSTGRES_PASSWORD: SecretStr | None = None
    POSTGRES_HOST: str | None = None
    POSTGRES_PORT: int | None = None
    POSTGRES_DB: str | None = None

    DEFAULT_MODEL: OpenAIModelName = OpenAIModelName.GPT_4O_MINI

settings = Settings()