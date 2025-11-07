"""
Pydantic models for configuration and data structures
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class TextEntity(BaseModel):
    """Text entity (link, mention, hashtag, etc.)"""

    type: str
    text: str
    href: Optional[str] = None
    user_id: Optional[str] = None


class Reaction(BaseModel):
    """Message reaction"""

    type: str = "emoji"
    emoji: Optional[str] = None
    count: int = 0
    recent: List[Dict[str, Any]] = Field(default_factory=list)


class Message(BaseModel):
    """Telegram message"""

    id: int
    type: str
    date: Optional[datetime] = None
    date_unixtime: Optional[int] = None
    edited: Optional[datetime] = None
    edited_unixtime: Optional[int] = None
    from_user: Optional[str] = None
    from_id: Optional[str] = None
    reply_to_message_id: Optional[int] = None
    text: str = ""
    text_entities: List[TextEntity] = Field(default_factory=list)
    reactions: List[Reaction] = Field(default_factory=list)
    forwarded_from: Optional[str] = None
    via_bot: Optional[str] = None

    # Media fields
    media_type: Optional[str] = None
    mime_type: Optional[str] = None
    duration_seconds: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    file: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    thumbnail: Optional[str] = None
    thumbnail_file_size: Optional[int] = None
    photo: Optional[str] = None

    # Contact fields
    contact_information: Optional[Dict[str, Any]] = None
    contact_vcard: Optional[str] = None

    # Location fields
    location_information: Optional[Dict[str, Any]] = None
    live_location_period_seconds: Optional[int] = None
    live_location_last_update_date: Optional[datetime] = None
    live_location_last_update_date_unixtime: Optional[int] = None

    # Poll fields
    poll: Optional[Dict[str, Any]] = None

    # Music fields
    performer: Optional[str] = None
    title: Optional[str] = None


class ChatInfo(BaseModel):
    """Telegram chat information"""

    name: str
    type: str
    id: str
    messages: List[Message] = Field(default_factory=list)
    source_file: str = ""


class ConfigSettings(BaseModel):
    """Application configuration settings"""

    # LLM API Keys
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None

    # Ollama settings
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama2"

    # Vector Database
    supabase_url: Optional[str] = None
    supabase_key: Optional[str] = None
    supabase_service_key: Optional[str] = None

    # Default Settings
    default_cleaning_approach: str = "privacy"
    default_cleaning_level: int = 2
    default_llm_provider: str = "openai"
    default_llm_model: str = "gpt-4"
    default_embedding_model: str = "text-embedding-3-small"

    # Data Directories
    data_dir: str = "data"
    input_dir: str = "input"
    output_dir: str = "output"
    analysis_dir: str = "analysis"
    vectors_dir: str = "vectors"

    # Processing Settings
    max_file_size_mb: int = 100
    text_chunk_size: int = 1000
    text_chunk_overlap: int = 200
    vector_batch_size: int = 100

    # Web Settings
    web_host: str = "0.0.0.0"
    web_port: int = 8000
    enable_cors: bool = True
    cors_origins: str = (
        "http://localhost:3000,http://localhost:8000"  # Comma-separated list
    )

    # Logging
    log_level: str = "INFO"
    log_file: Optional[str] = None
    enable_file_watch: bool = False
    watch_interval: int = 5


class LLMConfig(BaseModel):
    """LLM provider configuration"""

    provider: str
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    extra_params: Dict[str, Any] = Field(default_factory=dict)


class VectorConfig(BaseModel):
    """Vector database configuration"""

    provider: str = "supabase"
    url: Optional[str] = None
    api_key: Optional[str] = None
    table_name: str = "chat_embeddings"
    embedding_model: str = "text-embedding-3-small"
    chunk_size: int = 1000
    chunk_overlap: int = 200


class ProcessingResult(BaseModel):
    """Result of processing operations"""

    success: bool
    input_file: str
    output_file: Optional[str] = None
    message_count: int = 0
    processing_time: float = 0.0
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BatchProcessingResult(BaseModel):
    """Result of batch processing"""

    total_files: int = 0
    successful_files: int = 0
    failed_files: int = 0
    results: List[ProcessingResult] = Field(default_factory=list)
    total_processing_time: float = 0.0
