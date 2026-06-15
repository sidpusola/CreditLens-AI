-- CreditLens AI — Supabase schema
-- Run this in the Supabase SQL editor (Dashboard -> SQL -> New query) once.

create table if not exists public.assessments (
    id                       uuid primary key default gen_random_uuid(),
    created_at               timestamptz not null default now(),
    risk_score               double precision not null,
    default_probability      double precision not null,
    risk_category            text not null,
    confidence               double precision,
    top_risk_factors         jsonb not null default '[]'::jsonb,
    top_protective_factors   jsonb not null default '[]'::jsonb,
    inputs                   jsonb not null default '{}'::jsonb
);

-- Fast "most recent first" history queries
create index if not exists assessments_created_at_idx
    on public.assessments (created_at desc);

-- Row Level Security: enabled, with a permissive policy suitable for a single-user
-- portfolio/demo project. Tighten this (e.g. by auth.uid()) before any real multi-user use.
alter table public.assessments enable row level security;

drop policy if exists "allow all (demo)" on public.assessments;
create policy "allow all (demo)" on public.assessments
    for all using (true) with check (true);
