# Configuration for the LLM Agent
import os
from typing import Optional


class LLMConfig:
    """Configuration class for LLM settings."""

    # Default model settings
    DEFAULT_MODEL = "gpt-4o-mini"
    DEFAULT_TEMPERATURE = 0.7
    DEFAULT_MAX_TOKENS = None

    # Available models
    AVAILABLE_MODELS = [
        "gpt-4",
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4-turbo-preview",
        "gpt-3.5-turbo",
        "gpt-3.5-turbo-16k",
    ]

    @staticmethod
    def get_api_key() -> Optional[str]:
        """Get the OpenAI API key from environment variables."""
        return os.getenv("OPENAI_API_KEY")

    @staticmethod
    def validate_model(model: str) -> bool:
        """Validate if the model is available."""
        return model in LLMConfig.AVAILABLE_MODELS

    @staticmethod
    def validate_temperature(temperature: float) -> bool:
        """Validate temperature is in valid range."""
        return 0.0 <= temperature <= 2.0
