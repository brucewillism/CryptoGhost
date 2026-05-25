-- ============================================================
-- CryptoGhost — Passo 1: execute conectado ao banco "postgres"
-- ============================================================

CREATE DATABASE cryptoghost OWNER bruce;

-- Se já existir, ignore o erro e vá para o Passo 2

-- ============================================================
-- Passo 2: abra Query Tool no banco "cryptoghost" e execute:
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS vector;

GRANT ALL ON SCHEMA public TO bruce;

COMMENT ON DATABASE cryptoghost IS 'CryptoGhost - Intelligence Platform';
