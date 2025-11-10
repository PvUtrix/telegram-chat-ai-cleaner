"""
Supabase vector database client with pgvector support
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

try:
    from supabase import create_client, Client
except ImportError:
    create_client = None
    Client = None

from ..config.config_manager import ConfigManager


logger = logging.getLogger(__name__)


class SupabaseClient:
    """Supabase client for vector storage and retrieval"""

    def __init__(self, config: ConfigManager):
        """
        Initialize Supabase client

        Args:
            config: Configuration manager
        """
        self.config = config
        self._client: Optional[Client] = None
        self._table_name = config.get("supabase_table_name", "chat_embeddings")

    def _get_client(self) -> Client:
        """Get or create Supabase client"""
        if self._client is None:
            if create_client is None:
                raise ImportError(
                    "supabase package is required for vector database operations"
                )

            url = self.config.get("supabase_url")
            key = self.config.get("supabase_key")

            if not url or not key:
                raise ValueError("Supabase URL and key must be configured")

            self._client = create_client(url, key)

        return self._client

    async def store_embeddings(
        self,
        vectors: List[List[float]],
        texts: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None,
        provider: str = "openai",
        model: str = "text-embedding-3-small",
    ) -> Dict[str, Any]:
        """
        Store embeddings in Supabase vector database

        Args:
            vectors: List of embedding vectors
            texts: Original text chunks
            metadata: Metadata for each vector
            provider: Embedding provider used
            model: Embedding model used

        Returns:
            Storage result with IDs and statistics
        """
        client = self._get_client()

        if len(vectors) != len(texts):
            raise ValueError("Vectors and texts lists must have the same length")

        if metadata and len(metadata) != len(vectors):
            raise ValueError("Metadata list must match vectors list length")

        # Prepare data for insertion
        records = []
        for i, (vector, text) in enumerate(zip(vectors, texts)):
            record = {
                "content": text,
                "embedding": vector,
                "metadata": metadata[i] if metadata else {},
                "provider": provider,
                "model": model,
                "created_at": datetime.now().isoformat(),
                "chunk_index": i,
            }
            records.append(record)

        try:
            # Insert in batches to avoid payload size limits
            batch_size = 100
            inserted_ids = []

            for i in range(0, len(records), batch_size):
                batch = records[i : i + batch_size]
                response = client.table(self._table_name).insert(batch).execute()
                batch_ids = [record["id"] for record in response.data]
                inserted_ids.extend(batch_ids)
                logger.info(f"Inserted batch of {len(batch)} vectors")

            result = {
                "success": True,
                "inserted_count": len(inserted_ids),
                "ids": inserted_ids,
                "provider": provider,
                "model": model,
            }

            logger.info(f"Successfully stored {len(inserted_ids)} vectors in Supabase")
            return result

        except Exception as e:
            logger.error(f"Failed to store embeddings: {e}")
            raise

    async def search_similar(
        self,
        query_embedding: List[float],
        limit: int = 10,
        metadata_filter: Optional[Dict[str, Any]] = None,
        similarity_threshold: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors using cosine similarity

        Args:
            query_embedding: Query embedding vector
            limit: Maximum number of results
            metadata_filter: Filter by metadata fields
            similarity_threshold: Minimum similarity score (0.0 to 1.0)

        Returns:
            List of similar documents with similarity scores
        """
        client = self._get_client()

        try:
            # Build the query
            query = client.table(self._table_name).select(
                "id, content, metadata, provider, model, created_at"
            )

            # Apply metadata filters
            if metadata_filter:
                for key, value in metadata_filter.items():
                    # Use JSON path queries for metadata filtering
                    query = query.filter(f"metadata->>{key}", "eq", value)

            # Execute similarity search using pgvector
            # Note: This requires the pgvector extension and proper indexing
            query_str = f"""
            SELECT id, content, metadata, provider, model, created_at,
                   1 - (embedding <=> '{query_embedding}') as similarity
            FROM {self._table_name}
            WHERE 1 - (embedding <=> '{query_embedding}') > {similarity_threshold}
            ORDER BY embedding <=> '{query_embedding}'
            LIMIT {limit}
            """

            response = client.rpc("execute_sql", {"query": query_str}).execute()

            results = []
            for row in response.data:
                result = {
                    "id": row["id"],
                    "content": row["content"],
                    "metadata": row["metadata"],
                    "provider": row["provider"],
                    "model": row["model"],
                    "created_at": row["created_at"],
                    "similarity": float(row["similarity"]),
                }
                results.append(result)

            logger.info(f"Found {len(results)} similar documents")
            return results

        except Exception as e:
            logger.error(f"Similarity search failed: {e}")
            raise

    async def delete_by_metadata(self, metadata_filter: Dict[str, Any]) -> int:
        """
        Delete vectors by metadata filter

        Args:
            metadata_filter: Metadata fields to filter by

        Returns:
            Number of deleted records
        """
        client = self._get_client()

        try:
            query = client.table(self._table_name)

            # Apply metadata filters
            for key, value in metadata_filter.items():
                query = query.filter(f"metadata->>{key}", "eq", value)

            # Delete matching records
            response = query.delete().execute()

            deleted_count = len(response.data)
            logger.info(f"Deleted {deleted_count} vectors matching filter")
            return deleted_count

        except Exception as e:
            logger.error(f"Failed to delete vectors: {e}")
            raise

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get database statistics

        Returns:
            Statistics about stored vectors
        """
        client = self._get_client()

        try:
            # Get total count
            count_response = (
                client.table(self._table_name).select("id", count="exact").execute()
            )
            total_count = count_response.count

            # Get provider breakdown
            provider_query = f"""
            SELECT provider, COUNT(*) as count
            FROM {self._table_name}
            GROUP BY provider
            """
            provider_response = client.rpc(
                "execute_sql", {"query": provider_query}
            ).execute()

            providers = {}
            for row in provider_response.data:
                providers[row["provider"]] = row["count"]

            # Get recent additions (last 24 hours)
            recent_query = f"""
            SELECT COUNT(*) as count
            FROM {self._table_name}
            WHERE created_at > NOW() - INTERVAL '24 hours'
            """
            recent_response = client.rpc(
                "execute_sql", {"query": recent_query}
            ).execute()
            recent_count = (
                recent_response.data[0]["count"] if recent_response.data else 0
            )

            return {
                "total_vectors": total_count,
                "providers": providers,
                "recent_additions_24h": recent_count,
                "table_name": self._table_name,
            }

        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            raise

    async def create_table_if_not_exists(self):
        """
        Create the embeddings table if it doesn't exist

        Note: This requires appropriate database permissions
        """
        client = self._get_client()

        try:
            # Check if pgvector extension exists and create table
            create_table_query = f"""
            -- Enable pgvector extension (requires superuser)
            CREATE EXTENSION IF NOT EXISTS vector;

            -- Create embeddings table
            CREATE TABLE IF NOT EXISTS {self._table_name} (
                id SERIAL PRIMARY KEY,
                content TEXT NOT NULL,
                embedding vector(1536), -- Adjust dimension based on your model
                metadata JSONB DEFAULT '{{}}',
                provider TEXT NOT NULL,
                model TEXT NOT NULL,
                chunk_index INTEGER DEFAULT 0,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );

            -- Create vector similarity index (IVFFlat for smaller datasets)
            CREATE INDEX IF NOT EXISTS {self._table_name}_embedding_idx
            ON {self._table_name} USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100);

            -- Create metadata index for faster filtering
            CREATE INDEX IF NOT EXISTS {self._table_name}_metadata_idx
            ON {self._table_name} USING gin (metadata);
            """

            # Execute table creation
            client.rpc("execute_sql", {"query": create_table_query}).execute()

            logger.info(f"Created/verified table: {self._table_name}")

        except Exception as e:
            logger.error(f"Failed to create table: {e}")
            logger.info(
                "Note: Table creation requires appropriate database permissions"
            )
            logger.info("You may need to create the table manually or ask your DBA")
            raise

    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on the vector database

        Returns:
            Health status information
        """
        try:
            client = self._get_client()

            # Simple query to test connection
            response = (
                client.table(self._table_name)
                .select("id", count="exact")
                .limit(1)
                .execute()
            )

            return {
                "status": "healthy",
                "table_exists": True,
                "total_records": response.count,
                "connection": "ok",
            }

        except Exception as e:
            return {"status": "unhealthy", "error": str(e), "connection": "failed"}
