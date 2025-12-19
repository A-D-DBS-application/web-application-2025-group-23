-- Enable UUID generator (usually on in Supabase)
create extension if not exists "pgcrypto";

-- === ENUMS ===
do $$
begin
  if not exists (select 1 from pg_type where typname = 'role_type') then
    create type role_type as enum ('founder', 'user', 'accelerator_manager');
  end if;

  if not exists (select 1 from pg_type where typname = 'service_status') then
    create type service_status as enum ('active', 'paused', 'archived');
  end if;

  if not exists (select 1 from pg_type where typname = 'deal_status') then
    create type deal_status as enum ('proposed', 'accepted', 'in_progress', 'delivered', 'completed', 'cancelled');
  end if;

  if not exists (select 1 from pg_type where typname = 'contract_status') then
    create type contract_status as enum ('draft', 'pending', 'active', 'completed', 'void');
  end if;
end$$;

-- =========================================
-- PROFILE
-- =========================================
create table if not exists public.profile (
  user_id            uuid primary key default gen_random_uuid(),
  user_name          text not null,
  email              text not null,
  role               role_type not null,
  location           text,
  profile_picture_url text,
  job_description    text,
  company_name       text,
  verified           boolean default false,
  created_at         timestamptz not null default now(),
  updated_at         timestamptz not null default now()
);

-- Handige uniqueness (optioneel, maar vaak gewenst)
create unique index if not exists profile_email_uidx on public.profile (lower(email));

-- =========================================
-- SERVICE
-- =========================================
create table if not exists public.service (
  service_id         uuid primary key default gen_random_uuid(),
  user_id            uuid not null references public.profile(user_id) on delete cascade,
  title              text not null,
  description        text not null,
  category           text not null,
  is_offered         boolean not null,                       -- true = offered, false = needed
  estimated_time_min integer,
  value_estimate     numeric,
  availability       jsonb,
  status             service_status not null default 'active',
  created_at         timestamptz not null default now(),
  updated_at         timestamptz not null default now()
);

create index if not exists service_user_id_idx on public.service(user_id);

-- =========================================
-- BARTERDEAL
-- =========================================
create table if not exists public.barterdeal (
  deal_id            uuid primary key default gen_random_uuid(),
  user_a_id          uuid not null references public.profile(user_id) on delete restrict,
  user_b_id          uuid not null references public.profile(user_id) on delete restrict,
  service_a_id       uuid not null references public.service(service_id) on delete restrict,
  service_b_id       uuid not null references public.service(service_id) on delete restrict,
  status             deal_status not null default 'proposed',
  start_date         date,
  end_date           date,
  ratio_a_to_b       numeric,
  created_at         timestamptz not null default now(),
  updated_at         timestamptz not null default now()
);

create index if not exists barterdeal_users_idx on public.barterdeal(user_a_id, user_b_id);
create index if not exists barterdeal_services_idx on public.barterdeal(service_a_id, service_b_id);

-- =========================================
-- CONTRACT
-- =========================================
create table if not exists public.contract (
  contract_id            uuid primary key default gen_random_uuid(),
  deal_id                uuid not null references public.barterdeal(deal_id) on delete cascade,
  signed_by_initiator    boolean default false,
  signed_by_counterparty boolean default false,
  signed_at_initiator    timestamptz,
  signed_at_counterparty timestamptz,
  status                 contract_status not null default 'draft',
  created_at             timestamptz not null default now()
);

create index if not exists contract_deal_id_idx on public.contract(deal_id);

-- =========================================
-- REVIEW
-- =========================================
create table if not exists public.review (
  review_id        uuid primary key default gen_random_uuid(),
  deal_id          uuid not null references public.barterdeal(deal_id) on delete cascade,
  reviewer_id      uuid not null references public.profile(user_id) on delete restrict,
  reviewed_user_id uuid not null references public.profile(user_id) on delete restrict,
  rating           smallint not null check (rating between 1 and 5),
  comment          text,
  created_at       timestamptz not null default now()
);

create index if not exists review_deal_idx on public.review(deal_id);
create index if not exists review_users_idx on public.review(reviewer_id, reviewed_user_id);

-- Optional: trigger to keep updated_at fresh
create or replace function set_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end $$;

do $$
begin
  if not exists (select 1 from pg_trigger where tgname = 'profile_set_updated_at') then
    create trigger profile_set_updated_at before update on public.profile
    for each row execute procedure set_updated_at();
  end if;

  if not exists (select 1 from pg_trigger where tgname = 'service_set_updated_at') then
    create trigger service_set_updated_at before update on public.service
    for each row execute procedure set_updated_at();
  end if;

  if not exists (select 1 from pg_trigger where tgname = 'barterdeal_set_updated_at') then
    create trigger barterdeal_set_updated_at before update on public.barterdeal
    for each row execute procedure set_updated_at();
  end if;
end $$;
