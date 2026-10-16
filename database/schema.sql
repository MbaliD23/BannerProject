CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS websites (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  key VARCHAR(80) UNIQUE NOT NULL,
  name VARCHAR(150) NOT NULL,
  url TEXT NOT NULL,
  enabled BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS capture_runs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  website_id UUID NOT NULL REFERENCES websites(id),
  started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  finished_at TIMESTAMPTZ,
  status VARCHAR(30) NOT NULL DEFAULT 'running',
  banners_found INTEGER NOT NULL DEFAULT 0,
  error_message TEXT,
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS banners (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  capture_run_id UUID NOT NULL REFERENCES capture_runs(id),
  website_id UUID NOT NULL REFERENCES websites(id),
  captured_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  position INTEGER NOT NULL,
  unique_identifier VARCHAR(160) NOT NULL,
  content_hash VARCHAR(64) NOT NULL,
  perceptual_hash VARCHAR(32),
  image_path TEXT NOT NULL,
  image_data BYTEA,
  source_image_url TEXT,
  clickthrough_url TEXT,
  ocr_text TEXT NOT NULL DEFAULT '',
  headline TEXT,
  subheadline TEXT,
  cta_text VARCHAR(160),
  terms_reference TEXT,
  detected_brands JSONB NOT NULL DEFAULT '[]'::jsonb,
  social_platforms JSONB NOT NULL DEFAULT '[]'::jsonb,
  promotional_keywords JSONB NOT NULL DEFAULT '[]'::jsonb,
  primary_colours JSONB NOT NULL DEFAULT '[]'::jsonb,
  visual_flags JSONB NOT NULL DEFAULT '{}'::jsonb,
  automated_description TEXT,
  is_new BOOLEAN NOT NULL DEFAULT TRUE,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  raw_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  UNIQUE (capture_run_id, position, content_hash)
);
CREATE INDEX IF NOT EXISTS ix_banners_captured_source ON banners(captured_at, website_id);
CREATE INDEX IF NOT EXISTS ix_banners_content_hash ON banners(content_hash);

CREATE TABLE IF NOT EXISTS banner_categories (
  id BIGSERIAL PRIMARY KEY,
  banner_id UUID NOT NULL REFERENCES banners(id) ON DELETE CASCADE,
  category VARCHAR(100) NOT NULL,
  confidence NUMERIC(5,4) NOT NULL DEFAULT 1,
  rule_version VARCHAR(40) NOT NULL DEFAULT 'v1'
);

CREATE TABLE IF NOT EXISTS monetary_values (
  id BIGSERIAL PRIMARY KEY,
  banner_id UUID NOT NULL REFERENCES banners(id) ON DELETE CASCADE,
  raw_text VARCHAR(100) NOT NULL,
  currency VARCHAR(3) NOT NULL DEFAULT 'ZAR',
  amount NUMERIC(18,2) NOT NULL
);

CREATE TABLE IF NOT EXISTS detected_dates (
  id BIGSERIAL PRIMARY KEY,
  banner_id UUID NOT NULL REFERENCES banners(id) ON DELETE CASCADE,
  raw_text VARCHAR(150) NOT NULL,
  date_type VARCHAR(40) NOT NULL DEFAULT 'unspecified',
  parsed_date DATE
);

CREATE TABLE IF NOT EXISTS scheduler_settings (
  key VARCHAR(80) PRIMARY KEY,
  value TEXT NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

