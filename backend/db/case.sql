-- CreditLens AI — applicant case-file metadata
-- Run once in the Supabase SQL editor to persist case header details.

alter table public.assessments add column if not exists case_meta jsonb default '{}'::jsonb;
