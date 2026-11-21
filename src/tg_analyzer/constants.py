"""
Application-wide constants for Telegram Chat Analyzer
"""

# Text processing constants
REPLY_TEXT_PREVIEW_LENGTH = 50
MIN_WORD_BOUNDARY_RATIO = 0.5
CHARS_PER_TOKEN_ESTIMATE = 4

# API batch sizes
OPENAI_EMBEDDING_BATCH_SIZE = 100
DEFAULT_VECTOR_BATCH_SIZE = 100

# File size limits
MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024  # 100 MB

# Text chunking
DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 200

# Hash lengths for anonymization
ANONYMIZED_USER_ID_LENGTH = 12

# Retry configuration
API_RETRY_MAX_ATTEMPTS = 4
API_RETRY_BASE_DELAY = 2  # seconds
API_RETRY_MAX_DELAY = 16  # seconds

# Rate limiting
DEFAULT_RATE_LIMIT_CALLS = 60  # calls per minute
DEFAULT_RATE_LIMIT_PERIOD = 60  # seconds

# Web server defaults
DEFAULT_WEB_HOST = "0.0.0.0"
DEFAULT_WEB_PORT = 8000

# Logging
DEFAULT_LOG_LEVEL = "INFO"

# Model pricing (per 1K tokens, as of 2024)
MODEL_PRICING = {
    "gpt-4": {"input": 0.03, "output": 0.06},
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    "gpt-4-turbo-preview": {"input": 0.01, "output": 0.03},
    "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
}

# Model context lengths
MODEL_CONTEXT_LENGTHS = {
    "gpt-4": 8192,
    "gpt-4-32k": 32768,
    "gpt-4-turbo": 128000,
    "gpt-4-turbo-preview": 128000,
    "gpt-3.5-turbo": 4096,
    "gpt-3.5-turbo-16k": 16384,
}

# Valid configuration values
VALID_CLEANING_APPROACHES = ["privacy", "size", "context"]
VALID_CLEANING_LEVELS = [1, 2, 3]
VALID_OUTPUT_FORMATS = ["text", "json", "markdown", "csv"]
VALID_LLM_PROVIDERS = ["openai", "anthropic", "google", "groq", "ollama", "openrouter"]
