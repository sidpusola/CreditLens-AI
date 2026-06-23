-- CreditLens AI — pgvector similarity search migration
-- Run this in the Supabase SQL editor AFTER schema.sql, once.
-- Then set ENABLE_VECTOR_SEARCH=true in your .env and restart the backend.

-- 1. Enable the pgvector extension
create extension if not exists vector;

-- 2. Add an embedding column (the model's 454-dim preprocessed feature vector)
alter table public.assessments
    add column if not exists embedding vector(454);

-- 3. NO approximate index at this scale.
--    An ivfflat index built before data exists has useless centroids and silently
--    returns 0 rows for many queries on small tables. Exact (sequential) search is
--    fast and always correct for up to tens of thousands of rows, which is plenty here.
--    If you previously created one, drop it:
--        DROP INDEX IF EXISTS assessments_embedding_idx;
--    (Only add an HNSW/ivfflat index once you have many thousands of rows, built AFTER seeding.)

-- 4. Similarity search function, callable via Supabase RPC.
--    Returns the closest historical assessments by cosine similarity.
create or replace function public.match_assessments(
    query_embedding vector(454),
    match_count int default 5
)
returns table (
    id uuid,
    created_at timestamptz,
    risk_score double precision,
    default_probability double precision,
    risk_category text,
    similarity float
)
language sql stable
as $$
    select
        a.id,
        a.created_at,
        a.risk_score,
        a.default_probability,
        a.risk_category,
        1 - (a.embedding <=> query_embedding) as similarity
    from public.assessments a
    where a.embedding is not null
    order by a.embedding <=> query_embedding
    limit match_count;
$$;
