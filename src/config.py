"""Application configuration managed through Pydantic BaseSettings."""

from typing import List, Union

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Pipeline configuration settings loaded from environment or .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # MongoDB Settings
    mongodb_uri: str = Field(
        default="mongodb://root:example@localhost:27017",
        description="MongoDB connection URI string",
    )
    database_name: str = Field(
        default="ner_chatbot",
        description="Target database name in MongoDB",
    )

    # Xberg OCR Extraction Service Settings
    xberg_api_url: str = Field(
        default="http://localhost:8000",
        description="Base URL for the containerized Xberg HTTP REST API",
    )
    xberg_ocr_language: str = Field(
        default="eng",
        description="Default language code for OCR processing",
    )

    # GLiNER Entity Recognition Settings
    gliner_model_name: str = Field(
        default="knowledgator/gliner-multitask-large-v0.5",
        description="Hugging Face model identifier or local path for GLiNER",
    )
    ner_labels: Union[List[str], str] = Field(
        default_factory=lambda: [
            "Person",
            "Organization",
            "Location",
            "Date",
            "Event",
        ],
        description="List of target entity recognition classification labels",
    )
    ner_threshold: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Confidence score threshold for entity predictions",
    )

    @field_validator("ner_labels")
    @classmethod
    def parse_labels(cls, value: Union[str, List[str]]) -> List[str]:
        """Support comma-separated string inputs for labels from environment variables."""
        if isinstance(value, str):
            return [label.strip() for label in value.split(",") if label.strip()]
        return value


settings = Settings()
