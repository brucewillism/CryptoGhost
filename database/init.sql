-- CryptoGhost - Inicialização do PostgreSQL
-- Extensões e configurações base

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS vector;

COMMENT ON DATABASE cryptoghost IS 'CryptoGhost - Intelligence Platform (uso pessoal/familiar)';
