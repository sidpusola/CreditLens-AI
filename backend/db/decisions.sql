-- CreditLens AI — officer decision columns
-- Run once in the Supabase SQL editor to persist underwriting decisions.

alter table public.assessments add column if not exists decision text;
alter table public.assessments add column if not exists decision_note text;
alter table public.assessments add column if not exists decided_at timestamptz;
