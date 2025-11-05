-- PostgreSQL initialization script for Telegram Chat Analyzer
-- This script sets up the pgvector extension and creates necessary databases

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create the chat_embeddings table (matches Supabase schema)
CREATE TABLE IF NOT EXISTS chat_embeddings (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    embedding vector(1536), -- Adjust dimension based on your model
    metadata JSONB DEFAULT '{}',
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    chunk_index INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS chat_embeddings_embedding_idx
ON chat_embeddings USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

CREATE INDEX IF NOT EXISTS chat_embeddings_metadata_idx
ON chat_embeddings USING gin (metadata);

CREATE INDEX IF NOT EXISTS chat_embeddings_created_at_idx
ON chat_embeddings (created_at);

-- Create a function for cosine similarity search
CREATE OR REPLACE FUNCTION cosine_similarity(a vector, b vector)
RETURNS float
LANGUAGE sql IMMUTABLE PARALLEL SAFE
AS $$
    SELECT 1 - (a <=> b)
$$;

-- Grant permissions to the tguser
GRANT ALL PRIVILEGES ON DATABASE tg_analyzer TO tguser;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO tguser;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO tguser;

-- Ensure future tables are accessible
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO tguser;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO tguser;

