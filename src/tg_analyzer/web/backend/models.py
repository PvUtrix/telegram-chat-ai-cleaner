"""
Pydantic models for the web API
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class CleanRequest(BaseModel):
    """Request model for cleaning operations"""

    approach: str = Field(
        "privacy", description="Cleaning approach: privacy, size, or context"
    )
    level: int = Field(2, description="Cleaning level (1-3)", ge=1, le=3)
    output_format: str = Field(
        "text", description="Output format: text, json, markdown, csv"
    )


class AnalyzeRequest(BaseModel):
    """Request model for analysis operations"""

    text: str = Field(..., description="Text to analyze")
    prompt: Optional[str] = Field(None, description="Custom analysis prompt")
    template: Optional[str] = Field(None, description="Prompt template name")
    provider: Optional[str] = Field(None, description="LLM provider override")
    model: Optional[str] = Field(None, description="LLM model override")
    stream: bool = Field(False, description="Stream response")


class VectorizeRequest(BaseModel):
    """Request model for vectorization operations"""

    text: str = Field(..., description="Text to vectorize")
    provider: Optional[str] = Field(None, description="Embedding provider")
    model: Optional[str] = Field(None, description="Embedding model")
    chunk_strategy: str = Field("overlap", description="Text chunking strategy")
    chunk_size: Optional[int] = Field(None, description="Text chunk size")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class SearchRequest(BaseModel):
    """Request model for vector search operations"""

    query: str = Field(..., description="Search query")
    limit: int = Field(10, description="Maximum results", ge=1, le=100)
    provider: Optional[str] = Field(None, description="Embedding provider for query")
    metadata_filter: Optional[Dict[str, Any]] = Field(
        None, description="Metadata filter"
    )


class ConfigUpdate(BaseModel):
    """Request model for configuration updates"""

    key: str = Field(..., description="Configuration key")
    value: Any = Field(..., description="Configuration value")


class BatchProcessRequest(BaseModel):
    """Request model for batch processing operations"""

    approach: str = Field("privacy", description="Cleaning approach")
    level: int = Field(2, description="Cleaning level", ge=1, le=3)
    output_format: str = Field("text", description="Output format")


class FileInfo(BaseModel):
    """Model for file information"""

    name: str
    path: str
    size: Optional[int] = None
    modified: Optional[str] = None


class ProcessingResult(BaseModel):
    """Model for processing results"""

    success: bool
    input_file: str
    output_file: Optional[str] = None
    message_count: int = 0
    processing_time: float = 0.0
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class VectorResult(BaseModel):
    """Model for vectorization results"""

    chunks_created: int
    vectors_stored: int
    provider: str
    model: str
    total_tokens: int
    processing_time: float
    chunking_strategy: str


class SearchResult(BaseModel):
    """Model for search results"""

    id: str
    content: str
    metadata: Dict[str, Any]
    provider: str
    model: str
    similarity: float
    created_at: str


class APIResponse(BaseModel):
    """Generic API response model"""

    success: bool
    message: Optional[str] = None
    data: Optional[Any] = None
    errors: List[str] = Field(default_factory=list)


class HealthResponse(BaseModel):
    """Health check response"""

    status: str
    version: str
    config_loaded: bool
    analyzer_ready: bool
    database_connected: Optional[bool] = None
