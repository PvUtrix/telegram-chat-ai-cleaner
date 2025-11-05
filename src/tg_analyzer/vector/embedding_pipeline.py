"""
Embedding pipeline for processing text into vectors
"""

import logging
from typing import Dict, Any, List, Optional, Callable
import asyncio
from dataclasses import dataclass
from enum import Enum

from ..config.config_manager import ConfigManager
from ..llm.llm_manager import LLMManager
from .supabase_client import SupabaseClient
from ..constants import (
    MIN_WORD_BOUNDARY_RATIO,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_CHUNK_OVERLAP,
    CHARS_PER_TOKEN_ESTIMATE
)


logger = logging.getLogger(__name__)


class ChunkingStrategy(Enum):
    """Text chunking strategies"""
    FIXED_SIZE = "fixed_size"
    SENTENCE = "sentence"
    PARAGRAPH = "paragraph"
    OVERLAP = "overlap"


@dataclass
class TextChunk:
    """Represents a chunk of text with metadata"""
    text: str
    start_pos: int
    end_pos: int
    chunk_index: int
    metadata: Dict[str, Any]


@dataclass
class EmbeddingResult:
    """Result of embedding generation"""
    chunks: List[TextChunk]
    vectors: List[List[float]]
    provider: str
    model: str
    total_tokens: int
    processing_time: float


class EmbeddingPipeline:
    """Pipeline for processing text into embeddings"""

    def __init__(self, config: ConfigManager, llm_manager: Optional[LLMManager] = None):
        """
        Initialize embedding pipeline

        Args:
            config: Configuration manager
            llm_manager: Optional LLM manager (created if not provided)
        """
        self.config = config
        self.llm_manager = llm_manager or LLMManager(config)
        self.vector_client = SupabaseClient(config)

    def chunk_text(
        self,
        text: str,
        strategy: ChunkingStrategy = ChunkingStrategy.OVERLAP,
        chunk_size: Optional[int] = None,
        overlap: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[TextChunk]:
        """
        Split text into chunks for embedding

        Args:
            text: Input text to chunk
            strategy: Chunking strategy
            chunk_size: Maximum chunk size in characters
            overlap: Overlap between chunks in characters
            metadata: Additional metadata for chunks

        Returns:
            List of text chunks
        """
        chunk_size = chunk_size or self.config.get('text_chunk_size', 1000)
        overlap = overlap or self.config.get('text_chunk_overlap', 200)
        metadata = metadata or {}

        if strategy == ChunkingStrategy.FIXED_SIZE:
            return self._chunk_fixed_size(text, chunk_size, metadata)
        elif strategy == ChunkingStrategy.OVERLAP:
            return self._chunk_with_overlap(text, chunk_size, overlap, metadata)
        elif strategy == ChunkingStrategy.SENTENCE:
            return self._chunk_by_sentence(text, chunk_size, metadata)
        elif strategy == ChunkingStrategy.PARAGRAPH:
            return self._chunk_by_paragraph(text, chunk_size, metadata)
        else:
            raise ValueError(f"Unsupported chunking strategy: {strategy}")

    def _chunk_fixed_size(self, text: str, chunk_size: int, metadata: Dict[str, Any]) -> List[TextChunk]:
        """Split text into fixed-size chunks"""
        chunks = []
        start_pos = 0
        chunk_index = 0

        while start_pos < len(text):
            end_pos = min(start_pos + chunk_size, len(text))
            chunk_text = text[start_pos:end_pos]

            # Try to break at word boundary
            if end_pos < len(text) and not text[end_pos].isspace():
                last_space = chunk_text.rfind(' ')
                min_chunk_size = int(chunk_size * MIN_WORD_BOUNDARY_RATIO)  # Don't break too early
                if last_space > min_chunk_size:
                    end_pos = start_pos + last_space
                    chunk_text = text[start_pos:end_pos]

            chunk = TextChunk(
                text=chunk_text.strip(),
                start_pos=start_pos,
                end_pos=end_pos,
                chunk_index=chunk_index,
                metadata={**metadata, "chunking_strategy": "fixed_size"}
            )
            chunks.append(chunk)

            start_pos = end_pos
            chunk_index += 1

        return chunks

    def _chunk_with_overlap(self, text: str, chunk_size: int, overlap: int, metadata: Dict[str, Any]) -> List[TextChunk]:
        """Split text into overlapping chunks"""
        chunks = []
        start_pos = 0
        chunk_index = 0

        while start_pos < len(text):
            end_pos = min(start_pos + chunk_size, len(text))
            chunk_text = text[start_pos:end_pos]

            # Try to break at word boundary
            if end_pos < len(text) and not text[end_pos].isspace():
                last_space = chunk_text.rfind(' ')
                min_chunk_size = int(chunk_size * MIN_WORD_BOUNDARY_RATIO)
                if last_space > min_chunk_size:
                    end_pos = start_pos + last_space
                    chunk_text = text[start_pos:end_pos]

            chunk = TextChunk(
                text=chunk_text.strip(),
                start_pos=start_pos,
                end_pos=end_pos,
                chunk_index=chunk_index,
                metadata={**metadata, "chunking_strategy": "overlap"}
            )
            chunks.append(chunk)

            # Move start position with overlap
            start_pos = max(start_pos + chunk_size - overlap, end_pos)
            chunk_index += 1

        return chunks

    def _chunk_by_sentence(self, text: str, max_chunk_size: int, metadata: Dict[str, Any]) -> List[TextChunk]:
        """Split text by sentences, combining as needed to reach max_chunk_size"""
        import re

        # Split by sentence endings
        sentence_pattern = r'(?<=[.!?])\s+'
        sentences = re.split(sentence_pattern, text)

        chunks = []
        current_chunk = []
        current_length = 0
        start_pos = 0
        chunk_index = 0

        for sentence in sentences:
            sentence_length = len(sentence)

            # If adding this sentence would exceed chunk size, save current chunk
            if current_length + sentence_length > max_chunk_size and current_chunk:
                chunk_text = ' '.join(current_chunk)
                end_pos = start_pos + len(chunk_text)

                chunk = TextChunk(
                    text=chunk_text.strip(),
                    start_pos=start_pos,
                    end_pos=end_pos,
                    chunk_index=chunk_index,
                    metadata={**metadata, "chunking_strategy": "sentence"}
                )
                chunks.append(chunk)

                start_pos = end_pos
                current_chunk = []
                current_length = 0
                chunk_index += 1

            current_chunk.append(sentence)
            current_length += sentence_length

        # Add remaining sentences
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunk = TextChunk(
                text=chunk_text.strip(),
                start_pos=start_pos,
                end_pos=start_pos + len(chunk_text),
                chunk_index=chunk_index,
                metadata={**metadata, "chunking_strategy": "sentence"}
            )
            chunks.append(chunk)

        return chunks

    def _chunk_by_paragraph(self, text: str, max_chunk_size: int, metadata: Dict[str, Any]) -> List[TextChunk]:
        """Split text by paragraphs"""
        # Split by double newlines (paragraph breaks)
        paragraphs = text.split('\n\n')

        chunks = []
        current_chunk = []
        current_length = 0
        start_pos = 0
        chunk_index = 0

        for paragraph in paragraphs:
            paragraph_length = len(paragraph)

            # If adding this paragraph would exceed chunk size, save current chunk
            if current_length + paragraph_length > max_chunk_size and current_chunk:
                chunk_text = '\n\n'.join(current_chunk)
                end_pos = start_pos + len(chunk_text)

                chunk = TextChunk(
                    text=chunk_text.strip(),
                    start_pos=start_pos,
                    end_pos=end_pos,
                    chunk_index=chunk_index,
                    metadata={**metadata, "chunking_strategy": "paragraph"}
                )
                chunks.append(chunk)

                start_pos = end_pos
                current_chunk = []
                current_length = 0
                chunk_index += 1

            current_chunk.append(paragraph)
            current_length += paragraph_length + 2  # +2 for \n\n

        # Add remaining paragraphs
        if current_chunk:
            chunk_text = '\n\n'.join(current_chunk)
            chunk = TextChunk(
                text=chunk_text.strip(),
                start_pos=start_pos,
                end_pos=start_pos + len(chunk_text),
                chunk_index=chunk_index,
                metadata={**metadata, "chunking_strategy": "paragraph"}
            )
            chunks.append(chunk)

        return chunks

    async def generate_embeddings(
        self,
        chunks: List[TextChunk],
        provider: Optional[str] = None,
        model: Optional[str] = None,
        batch_size: int = 100,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> EmbeddingResult:
        """
        Generate embeddings for text chunks

        Args:
            chunks: List of text chunks
            provider: Embedding provider
            model: Embedding model
            batch_size: Batch size for processing
            progress_callback: Callback for progress updates

        Returns:
            Embedding result with vectors and metadata
        """
        import time
        start_time = time.time()

        provider = provider or self.config.get('default_embedding_provider', 'openai')
        model = model or self.config.get('default_embedding_model', 'text-embedding-3-small')

        texts = [chunk.text for chunk in chunks]
        all_vectors = []
        total_tokens = 0

        # Process in batches
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]

            try:
                # Generate embeddings for batch
                batch_vectors = await self.llm_manager._get_provider(provider).get_embeddings(
                    batch_texts, model=model
                )
                all_vectors.extend(batch_vectors)

                # Estimate tokens (rough approximation)
                batch_tokens = sum(len(text) // CHARS_PER_TOKEN_ESTIMATE for text in batch_texts)
                total_tokens += batch_tokens

                if progress_callback:
                    progress_callback(i + len(batch_texts), len(texts))

                logger.info(f"Processed batch {i // batch_size + 1}: {len(batch_texts)} chunks")

            except Exception as e:
                logger.error(f"Failed to generate embeddings for batch {i // batch_size + 1}: {e}")
                raise

        processing_time = time.time() - start_time

        return EmbeddingResult(
            chunks=chunks,
            vectors=all_vectors,
            provider=provider,
            model=model,
            total_tokens=total_tokens,
            processing_time=processing_time
        )

    async def process_and_store(
        self,
        text: str,
        source_metadata: Optional[Dict[str, Any]] = None,
        chunking_strategy: ChunkingStrategy = ChunkingStrategy.OVERLAP,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        progress_callback: Optional[Callable[[str, int, int], None]] = None
    ) -> Dict[str, Any]:
        """
        Complete pipeline: chunk text, generate embeddings, store in vector DB

        Args:
            text: Input text to process
            source_metadata: Metadata about the source text
            chunking_strategy: Text chunking strategy
            provider: Embedding provider
            model: Embedding model
            progress_callback: Progress callback function

        Returns:
            Processing result with statistics
        """
        source_metadata = source_metadata or {}

        # Step 1: Chunk text
        if progress_callback:
            progress_callback("chunking", 0, 1)

        chunks = self.chunk_text(
            text=text,
            strategy=chunking_strategy,
            metadata=source_metadata
        )

        if progress_callback:
            progress_callback("chunking", 1, 1)

        logger.info(f"Created {len(chunks)} chunks from {len(text)} characters")

        # Step 2: Generate embeddings
        if progress_callback:
            progress_callback("embedding", 0, len(chunks))

        def embedding_progress(current, total):
            if progress_callback:
                progress_callback("embedding", current, total)

        embedding_result = await self.generate_embeddings(
            chunks=chunks,
            provider=provider,
            model=model,
            progress_callback=embedding_progress
        )

        # Step 3: Store in vector database
        if progress_callback:
            progress_callback("storing", 0, 1)

        # Prepare metadata for each chunk
        chunk_metadata = []
        for chunk in chunks:
            metadata = {
                **chunk.metadata,
                "start_pos": chunk.start_pos,
                "end_pos": chunk.end_pos,
                "chunk_index": chunk.chunk_index,
                "source_length": len(text)
            }
            chunk_metadata.append(metadata)

        storage_result = await self.vector_client.store_embeddings(
            vectors=embedding_result.vectors,
            texts=[chunk.text for chunk in chunks],
            metadata=chunk_metadata,
            provider=embedding_result.provider,
            model=embedding_result.model
        )

        if progress_callback:
            progress_callback("storing", 1, 1)

        # Combine results
        result = {
            "chunks_created": len(chunks),
            "vectors_stored": storage_result["inserted_count"],
            "provider": embedding_result.provider,
            "model": embedding_result.model,
            "total_tokens": embedding_result.total_tokens,
            "processing_time": embedding_result.processing_time,
            "chunking_strategy": chunking_strategy.value,
            "source_metadata": source_metadata,
            "storage_ids": storage_result["ids"]
        }

        logger.info(f"Pipeline completed: {len(chunks)} chunks, {storage_result['inserted_count']} vectors stored")
        return result

    async def search_similar(
        self,
        query: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        limit: int = 10,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar content using vector similarity

        Args:
            query: Search query
            provider: Embedding provider for query
            model: Embedding model for query
            limit: Maximum results
            metadata_filter: Filter by metadata

        Returns:
            Similar content with scores
        """
        provider = provider or self.config.get('default_embedding_provider', 'openai')
        model = model or self.config.get('default_embedding_model', 'text-embedding-3-small')

        # Generate embedding for query
        query_provider = self.llm_manager._get_provider(provider)
        query_embedding = await query_provider.get_embeddings([query], model=model)
        query_vector = query_embedding[0]

        # Search vector database
        results = await self.vector_client.search_similar(
            query_embedding=query_vector,
            limit=limit,
            metadata_filter=metadata_filter
        )

        return results

