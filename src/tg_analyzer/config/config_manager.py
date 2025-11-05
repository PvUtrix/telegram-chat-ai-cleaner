"""
Configuration management for the Telegram Chat Analyzer
"""

import os
import logging
from typing import Dict, Any, Optional, Union
from pathlib import Path
from dotenv import load_dotenv

from .models import ConfigSettings


logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages application configuration from environment variables and .env files"""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager

        Args:
            config_path: Path to .env file (optional, will search automatically)
        """
        self.config_path = self._find_config_file(config_path)
        self._load_config()
        self._settings = self._parse_settings()

    def _find_config_file(self, config_path: Optional[str]) -> Optional[Path]:
        """Find configuration file"""
        if config_path:
            path = Path(config_path)
            if path.exists():
                return path

        # Search for .env in current and parent directories
        current_dir = Path.cwd()
        for parent in [current_dir] + list(current_dir.parents):
            env_file = parent / ".env"
            if env_file.exists():
                return env_file

        # Check for env.example as fallback
        env_example = current_dir / "env.example"
        if env_example.exists():
            logger.warning("Using env.example as config file. Consider copying to .env and setting your values.")
            return env_example

        logger.warning("No configuration file found. Using default settings.")
        return None

    def _load_config(self):
        """Load configuration from file"""
        if self.config_path:
            load_dotenv(self.config_path)

    def _parse_settings(self) -> ConfigSettings:
        """Parse environment variables into ConfigSettings"""
        return ConfigSettings(
            # LLM API Keys
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            groq_api_key=os.getenv("GROQ_API_KEY"),
            openrouter_api_key=os.getenv("OPENROUTER_API_KEY"),

            # Ollama settings
            ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            ollama_model=os.getenv("OLLAMA_MODEL", "llama2"),

            # Vector Database
            supabase_url=os.getenv("SUPABASE_URL"),
            supabase_key=os.getenv("SUPABASE_KEY"),
            supabase_service_key=os.getenv("SUPABASE_SERVICE_KEY"),

            # Default Settings
            default_cleaning_approach=os.getenv("DEFAULT_CLEANING_APPROACH", "privacy"),
            default_cleaning_level=int(os.getenv("DEFAULT_CLEANING_LEVEL", "2")),
            default_llm_provider=os.getenv("DEFAULT_LLM_PROVIDER", "openai"),
            default_llm_model=os.getenv("DEFAULT_LLM_MODEL", "gpt-4"),
            default_embedding_model=os.getenv("DEFAULT_EMBEDDING_MODEL", "text-embedding-3-small"),

            # Data Directories
            data_dir=os.getenv("DATA_DIR", "data"),
            input_dir=os.getenv("INPUT_DIR", "input"),
            output_dir=os.getenv("OUTPUT_DIR", "output"),
            analysis_dir=os.getenv("ANALYSIS_DIR", "analysis"),
            vectors_dir=os.getenv("VECTORS_DIR", "vectors"),

            # Processing Settings
            max_file_size_mb=int(os.getenv("MAX_FILE_SIZE_MB", "100")),
            text_chunk_size=int(os.getenv("TEXT_CHUNK_SIZE", "1000")),
            text_chunk_overlap=int(os.getenv("TEXT_CHUNK_OVERLAP", "200")),
            vector_batch_size=int(os.getenv("VECTOR_BATCH_SIZE", "100")),

            # Web Settings
            web_host=os.getenv("WEB_HOST", "0.0.0.0"),
            web_port=int(os.getenv("WEB_PORT", "8000")),
            enable_cors=os.getenv("ENABLE_CORS", "true").lower() == "true",
            cors_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8000"),

            # Logging
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            log_file=os.getenv("LOG_FILE"),
            enable_file_watch=os.getenv("ENABLE_FILE_WATCH", "false").lower() == "true",
            watch_interval=int(os.getenv("WATCH_INTERVAL", "5"))
        )

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value
        """
        return getattr(self._settings, key, default)

    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value (in-memory only)

        Args:
            key: Configuration key
            value: Value to set
        """
        if hasattr(self._settings, key):
            setattr(self._settings, key, value)
        else:
            logger.warning(f"Unknown configuration key: {key}")

    def get_all(self) -> Dict[str, Any]:
        """Get all configuration as dictionary"""
        return self._settings.model_dump()

    def save_to_env(self, env_path: Optional[str] = None) -> None:
        """
        Save current configuration to .env file

        WARNING: This saves API keys and other sensitive data as plain text.
        - Ensure file has restricted permissions (600)
        - Never commit .env files to version control
        - Use secrets management systems in production

        Args:
            env_path: Path to save .env file (optional)
        """
        if not env_path and self.config_path:
            env_path = str(self.config_path)
        elif not env_path:
            env_path = ".env"

        # Security warning
        logger.warning(
            "Saving sensitive data (API keys) to file. "
            "Ensure file permissions are restricted and file is not committed to git."
        )

        env_content = self._generate_env_content()

        # Write with restricted permissions
        import os
        import stat

        # Create/write file
        with open(env_path, 'w') as f:
            f.write(env_content)

        # Set file permissions to 600 (owner read/write only) on Unix-like systems
        try:
            os.chmod(env_path, stat.S_IRUSR | stat.S_IWUSR)
            logger.info(f"Configuration saved to: {env_path} (permissions: 600)")
        except (OSError, AttributeError) as e:
            # chmod may not work on Windows or with permission issues
            logger.warning(
                f"Could not set file permissions for {env_path}: {e}. "
                "Please manually restrict file access."
            )
            logger.info(f"Configuration saved to: {env_path}")

    def _generate_env_content(self) -> str:
        """Generate .env file content from current settings"""
        lines = [
            "# Telegram Chat Analyzer Configuration",
            "# Generated automatically - edit as needed",
            "",
            "# ======================================",
            "# LLM API Keys (required for analysis)",
            "# ======================================",
            "",
        ]

        # API Keys
        if self._settings.openai_api_key:
            lines.append(f"OPENAI_API_KEY={self._settings.openai_api_key}")
        else:
            lines.append("# OPENAI_API_KEY=sk-your-openai-api-key-here")

        if self._settings.anthropic_api_key:
            lines.append(f"ANTHROPIC_API_KEY={self._settings.anthropic_api_key}")
        else:
            lines.append("# ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key-here")

        if self._settings.google_api_key:
            lines.append(f"GOOGLE_API_KEY={self._settings.google_api_key}")
        else:
            lines.append("# GOOGLE_API_KEY=your-google-ai-api-key-here")

        if self._settings.groq_api_key:
            lines.append(f"GROQ_API_KEY={self._settings.groq_api_key}")
        else:
            lines.append("# GROQ_API_KEY=gsk_your-groq-api-key-here")

        if self._settings.openrouter_api_key:
            lines.append(f"OPENROUTER_API_KEY={self._settings.openrouter_api_key}")
        else:
            lines.append("# OPENROUTER_API_KEY=sk-or-your-openrouter-api-key-here")

        lines.extend([
            "",
            "# Ollama Configuration (for local models)",
            f"OLLAMA_BASE_URL={self._settings.ollama_base_url}",
            f"OLLAMA_MODEL={self._settings.ollama_model}",
            "",
            "# ======================================",
            "# Vector Database Configuration",
            "# ======================================",
            "",
        ])

        # Supabase
        if self._settings.supabase_url:
            lines.append(f"SUPABASE_URL={self._settings.supabase_url}")
        else:
            lines.append("# SUPABASE_URL=https://your-project.supabase.co")

        if self._settings.supabase_key:
            lines.append(f"SUPABASE_KEY={self._settings.supabase_key}")
        else:
            lines.append("# SUPABASE_KEY=your-supabase-anon-key-here")

        if self._settings.supabase_service_key:
            lines.append(f"SUPABASE_SERVICE_KEY={self._settings.supabase_service_key}")
        else:
            lines.append("# SUPABASE_SERVICE_KEY=your-supabase-service-key-here")

        lines.extend([
            "",
            "# ======================================",
            "# Default Settings",
            "# ======================================",
            "",
            f"DEFAULT_CLEANING_APPROACH={self._settings.default_cleaning_approach}",
            f"DEFAULT_CLEANING_LEVEL={self._settings.default_cleaning_level}",
            f"DEFAULT_LLM_PROVIDER={self._settings.default_llm_provider}",
            f"DEFAULT_LLM_MODEL={self._settings.default_llm_model}",
            f"DEFAULT_EMBEDDING_MODEL={self._settings.default_embedding_model}",
            "",
            "# ======================================",
            "# Data Directory Configuration",
            "# ======================================",
            "",
            f"DATA_DIR={self._settings.data_dir}",
            f"INPUT_DIR={self._settings.input_dir}",
            f"OUTPUT_DIR={self._settings.output_dir}",
            f"ANALYSIS_DIR={self._settings.analysis_dir}",
            f"VECTORS_DIR={self._settings.vectors_dir}",
            "",
            "# ======================================",
            "# Processing Configuration",
            "# ======================================",
            "",
            f"MAX_FILE_SIZE_MB={self._settings.max_file_size_mb}",
            f"TEXT_CHUNK_SIZE={self._settings.text_chunk_size}",
            f"TEXT_CHUNK_OVERLAP={self._settings.text_chunk_overlap}",
            f"VECTOR_BATCH_SIZE={self._settings.vector_batch_size}",
            "",
            "# ======================================",
            "# Web Interface Configuration",
            "# ======================================",
            "",
            f"WEB_HOST={self._settings.web_host}",
            f"WEB_PORT={self._settings.web_port}",
            f"ENABLE_CORS={str(self._settings.enable_cors).lower()}",
            f"CORS_ORIGINS={self._settings.cors_origins}",
            "",
            "# ======================================",
            "# Logging Configuration",
            "# ======================================",
            "",
            f"LOG_LEVEL={self._settings.log_level}",
        ])

        if self._settings.log_file:
            lines.append(f"LOG_FILE={self._settings.log_file}")

        lines.extend([
            f"ENABLE_FILE_WATCH={str(self._settings.enable_file_watch).lower()}",
            f"WATCH_INTERVAL={self._settings.watch_interval}",
        ])

        return "\n".join(lines)

    def validate_config(self) -> Dict[str, str]:
        """
        Validate configuration and return any issues

        Returns:
            Dictionary of validation issues (key -> error message)
        """
        issues = {}

        # Check required settings for different features
        if not any([
            self._settings.openai_api_key,
            self._settings.anthropic_api_key,
            self._settings.google_api_key,
            self._settings.groq_api_key,
            self._settings.openrouter_api_key
        ]):
            issues["llm"] = "No LLM API key configured. Analysis features will not work."

        if not self._settings.supabase_url or not self._settings.supabase_key:
            issues["vector"] = "Supabase configuration incomplete. Vector features will not work."

        # Validate cleaning settings
        valid_approaches = ["privacy", "size", "context"]
        if self._settings.default_cleaning_approach not in valid_approaches:
            issues["cleaning_approach"] = f"Invalid cleaning approach: {self._settings.default_cleaning_approach}. Must be one of {valid_approaches}"

        if not 1 <= self._settings.default_cleaning_level <= 3:
            issues["cleaning_level"] = f"Invalid cleaning level: {self._settings.default_cleaning_level}. Must be 1, 2, or 3"

        return issues

