import os
import sys

# In a real scenario, this would use a psycopg2 connection to execute DDL, 
# or use the Supabase CLI. Since the supabase-py client (REST) cannot execute 
# raw DDL schema creation, this script provides the necessary SQL to run in 
# the Supabase Dashboard SQL Editor.

SCHEMA_SQL = """
-- Append-only audit log
CREATE TABLE IF NOT EXISTS audit_log (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sequence     SERIAL UNIQUE,
    action_type  TEXT NOT NULL,
    actor        TEXT NOT NULL,
    target_type  TEXT,
    target_id    TEXT,
    result       TEXT,
    metadata     JSONB,
    timestamp    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    entry_hash   TEXT NOT NULL,
    previous_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tenders (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title        TEXT NOT NULL,
    file_path    TEXT NOT NULL,
    status       TEXT NOT NULL DEFAULT 'processing',
    created_at   TIMESTAMPTZ DEFAULT NOW(),
    locked_at    TIMESTAMPTZ,
    locked_by    TEXT
);

CREATE TABLE IF NOT EXISTS criteria (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tender_id            UUID REFERENCES tenders(id),
    criterion_code       TEXT NOT NULL,
    text                 TEXT NOT NULL,
    category             TEXT NOT NULL,
    mandatory            BOOLEAN NOT NULL,
    mandatory_confidence TEXT NOT NULL DEFAULT 'high',
    threshold_value      NUMERIC,
    threshold_unit       TEXT,
    threshold_period     TEXT,
    threshold_comparison TEXT,
    evidence_documents   TEXT[],
    source_clause        TEXT,
    approved_by          TEXT,
    approved_at          TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS bidders (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tender_id  UUID REFERENCES tenders(id),
    name       TEXT NOT NULL,
    status     TEXT NOT NULL DEFAULT 'pending'
);

CREATE TABLE IF NOT EXISTS extractions (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    criterion_id            UUID REFERENCES criteria(id),
    bidder_id               UUID REFERENCES bidders(id),
    value_found             BOOLEAN NOT NULL,
    not_found_reason        TEXT,
    extracted_value         TEXT,
    extracted_value_numeric NUMERIC,
    source_document         TEXT,
    source_page             INTEGER,
    source_excerpt          TEXT,
    ocr_quality             TEXT,
    extraction_confidence   NUMERIC,
    created_at              TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS verdicts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    criterion_id    UUID REFERENCES criteria(id),
    bidder_id       UUID REFERENCES bidders(id),
    extraction_id   UUID REFERENCES extractions(id),
    status          TEXT NOT NULL,
    reason          TEXT NOT NULL,
    overridden_by   TEXT,
    override_action TEXT,
    override_reason TEXT,
    overridden_at   TIMESTAMPTZ,
    computed_at     TIMESTAMPTZ DEFAULT NOW()
);
"""

if __name__ == "__main__":
    print("To initialize the database, please run the following SQL script in your Supabase SQL Editor:")
    print("-----------------------------------------------------------------------------------------")
    print(SCHEMA_SQL)
    print("-----------------------------------------------------------------------------------------")
    print("Note: The supabase-py client uses the REST API and cannot execute raw DDL statements.")
