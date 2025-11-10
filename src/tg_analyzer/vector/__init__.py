"""
Vector database and embedding functionality
"""

from .supabase_client import SupabaseClient
from .embedding_pipeline import EmbeddingPipeline, ChunkingStrategy

__all__ = ["SupabaseClient", "EmbeddingPipeline", "ChunkingStrategy"]
