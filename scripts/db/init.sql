-- Local database initialisation. Schemas follow the spec's separation of concerns.
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE SCHEMA IF NOT EXISTS ops;        -- operational + audit tables (Section 15)
CREATE SCHEMA IF NOT EXISTS knowledge;  -- shared knowledge base (Section 18.16)
