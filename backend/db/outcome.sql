-- CreditLens AI — actual repayment outcome for seeded historical precedents
-- Run once in the Supabase SQL editor. Needed for ml/seed_precedents.py.

alter table public.assessments add column if not exists outcome text;  -- 'Defaulted' | 'Repaid'
