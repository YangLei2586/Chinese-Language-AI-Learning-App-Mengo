from functools import lru_cache
from typing import Literal
from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="MENGO_", extra="ignore")
    app_env: Literal["local", "test", "production"] = "local"
    demo_mode: bool = True
    database_url: str = "sqlite:///./mengo.db"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8081,http://127.0.0.1:8081"
    ai_provider_mode: Literal["mock", "live"] = "mock"
    # Selection defaults are documented production recommendations; mock mode ignores them.
    llm_provider: Literal["openai", "anthropic", "google-gemini", "aws-bedrock"] = "openai"
    stt_provider: Literal["deepgram", "openai", "google-cloud", "aws-transcribe"] = "deepgram"
    tts_provider: Literal["elevenlabs", "openai", "google-cloud", "amazon-polly"] = "elevenlabs"
    llm_model: str = "gpt-4.1-mini"
    stt_model: str = "nova-3"
    tts_model: str = "eleven_multilingual_v2"
    tts_voice_id: str | None = None
    posthog_api_key: str | None = None
    posthog_host: str | None = None
    openai_api_key: str | None = Field(default=None, validation_alias=AliasChoices("MENGO_OPENAI_API_KEY", "OPENAI_API_KEY"))
    anthropic_api_key: str | None = Field(default=None, validation_alias=AliasChoices("MENGO_ANTHROPIC_API_KEY", "ANTHROPIC_API_KEY"))
    google_api_key: str | None = Field(default=None, validation_alias=AliasChoices("MENGO_GOOGLE_API_KEY", "GOOGLE_API_KEY"))
    deepgram_api_key: str | None = Field(default=None, validation_alias=AliasChoices("MENGO_DEEPGRAM_API_KEY", "DEEPGRAM_API_KEY"))
    elevenlabs_api_key: str | None = Field(default=None, validation_alias=AliasChoices("MENGO_ELEVENLABS_API_KEY", "ELEVENLABS_API_KEY"))
    google_application_credentials: str | None = Field(default=None, validation_alias=AliasChoices("MENGO_GOOGLE_APPLICATION_CREDENTIALS", "GOOGLE_APPLICATION_CREDENTIALS"))
    aws_region: str | None = Field(default=None, validation_alias=AliasChoices("MENGO_AWS_REGION", "AWS_REGION"))
    aws_iam_auth_enabled: bool = False
    bedrock_model_id: str | None = None
    rate_limit_per_minute: int = 120
    @property
    def allowed_origins(self): return [x.strip() for x in self.cors_origins.split(",") if x.strip()]
@lru_cache
def get_settings() -> Settings: return Settings()
