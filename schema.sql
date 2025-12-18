-- ============================================================
-- DATABASE SETUP
-- ============================================================

-- Enable UUID generator (standard in Supabase)
CREATE EXTENSION IF NOT EXISTS "pgcrypto";


-- ============================================================
-- ENUM TYPES
-- ============================================================

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'role_type') THEN
        CREATE TYPE role_type AS ENUM (
            'founder',
            'user',
            'accelerator_manager'
        );
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'service_status') THEN
        CREATE TYPE service_status AS ENUM (
            'active',
            'paused',
            'archived'
        );
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'deal_status') THEN
        CREATE TYPE deal_status AS ENUM (
            'proposed',
            'accepted',
            'in_progress',
            'delivered',
            'completed',
            'cancelled'
        );
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'contract_status') THEN
        CREATE TYPE contract_status AS ENUM (
            'draft',
            'pending',
            'active',
            'completed',
            'void'
        );
    END IF;
END
$$;


-- ============================================================
-- PROFILE
-- ============================================================

CREATE TABLE IF NOT EXISTS public.profile (
    user_id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_name            TEXT NOT NULL,
    email                TEXT NOT NULL,
    role                 role_type NOT NULL,
    location             TEXT,
    profile_picture_url  TEXT,
    job_description      TEXT,
    company_name         TEXT,
    verified             BOOLEAN DEFAULT FALSE,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS profile_email_uidx
    ON public.profile (LOWER(email));


-- ============================================================
-- SERVICE
-- ============================================================

CREATE TABLE IF NOT EXISTS public.service (
    service_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id              UUID NOT NULL
                           REFERENCES public.profile(user_id)
                           ON DELETE CASCADE,
    title                TEXT NOT NULL,
    description          TEXT NOT NULL,
    category             TEXT NOT NULL,
    is_offered            BOOLEAN NOT NULL,
    estimated_time_min   INTEGER,
    value_estimate       NUMERIC,
    availability         JSONB,
    status               service_status NOT NULL DEFAULT 'active',
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS service_user_id_idx
    ON public.service (user_id);


-- ============================================================
-- BARTER DEAL
-- ============================================================

CREATE TABLE IF NOT EXISTS public.barterdeal (
    deal_id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_a_id            UUID NOT NULL
                           REFERENCES public.profile(user_id)
                           ON DELETE RESTRICT,
    user_b_id            UUID NOT NULL
                           REFERENCES public.profile(user_id)
                           ON DELETE RESTRICT,
    service_a_id         UUID NOT NULL
                           REFERENCES public.service(service_id)
                           ON DELETE RESTRICT,
    service_b_id         UUID NOT NULL
                           REFERENCES public.service(service_id)
                           ON DELETE RESTRICT,
    status               deal_status NOT NULL DEFAULT 'proposed',
    start_date           DATE,
    end_date             DATE,
    ratio_a_to_b         NUMERIC,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS barterdeal_users_idx
    ON public.barterdeal (user_a_id, user_b_id);

CREATE INDEX IF NOT EXISTS barterdeal_services_idx
    ON public.barterdeal (service_a_id, service_b_id);


-- ============================================================
-- CONTRACT
-- ============================================================

CREATE TABLE IF NOT EXISTS public.contract (
    contract_id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    deal_id                  UUID NOT NULL
                               REFERENCES public.barterdeal(deal_id)
                               ON DELETE CASCADE,
    signed_by_initiator      BOOLEAN DEFAULT FALSE,
    signed_by_counterparty   BOOLEAN DEFAULT FALSE,
    signed_at_initiator      TIMESTAMPTZ,
    signed_at_counterparty   TIMESTAMPTZ,
    status                   contract_status NOT NULL DEFAULT 'draft',
    created_at               TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS contract_deal_id_idx
    ON public.contract (deal_id);


-- ============================================================
-- REVIEW
-- ============================================================

CREATE TABLE IF NOT EXISTS public.review (
    review_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    deal_id              UUID NOT NULL
                           REFERENCES public.barterdeal(deal_id)
                           ON DELETE CASCADE,
    reviewer_id          UUID NOT NULL
                           REFERENCES public.profile(user_id)
                           ON DELETE RESTRICT,
    reviewed_user_id     UUID NOT NULL
                           REFERENCES public.profile(user_id)
                           ON DELETE RESTRICT,
    rating               SMALLINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment              TEXT,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS review_deal_idx
    ON public.review (deal_id);

CREATE INDEX IF NOT EXISTS review_users_idx
    ON public.review (reviewer_id, reviewed_user_id);


-- ============================================================
-- UPDATED_AT TRIGGERS
-- ============================================================

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'profile_set_updated_at') THEN
        CREATE TRIGGER profile_set_updated_at
        BEFORE UPDATE ON public.profile
        FOR EACH ROW
        EXECUTE PROCEDURE set_updated_at();
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'service_set_updated_at') THEN
        CREATE TRIGGER service_set_updated_at
        BEFORE UPDATE ON public.service
        FOR EACH ROW
        EXECUTE PROCEDURE set_updated_at();
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'barterdeal_set_updated_at') THEN
        CREATE TRIGGER barterdeal_set_updated_at
        BEFORE UPDATE ON public.barterdeal
        FOR EACH ROW
        EXECUTE PROCEDURE set_updated_at();
    END IF;
END;
$$;

