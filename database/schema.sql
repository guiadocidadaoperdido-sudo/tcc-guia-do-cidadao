-- Script de criação do banco do Guia do Cidadão Perdido (Apêndice B do TCC).
-- Uso: psql -U postgres -d guia_cidadao -f database/schema.sql
-- Também é possível criar as tabelas com: flask --app run criar-banco

CREATE TABLE administrador (
    id          SERIAL PRIMARY KEY,
    nome        VARCHAR(100) NOT NULL,
    email       VARCHAR(150) NOT NULL UNIQUE,
    senha_hash  VARCHAR(255) NOT NULL,
    criado_em   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE categoria (
    id         SERIAL PRIMARY KEY,
    nome       VARCHAR(80) NOT NULL,
    slug       VARCHAR(80) NOT NULL UNIQUE,
    descricao  TEXT
);

CREATE TABLE conteudo (
    id               SERIAL PRIMARY KEY,
    categoria_id     INTEGER NOT NULL REFERENCES categoria (id),
    administrador_id INTEGER REFERENCES administrador (id)
                     ON DELETE SET NULL,
    titulo           VARCHAR(150) NOT NULL,
    slug             VARCHAR(150) NOT NULL UNIQUE,
    resumo           VARCHAR(300) NOT NULL,
    o_que_e          TEXT NOT NULL,
    quem_tem_direito TEXT,
    documentos       TEXT,
    como_solicitar   TEXT,
    alerta_golpes    TEXT,
    publicado        BOOLEAN NOT NULL DEFAULT FALSE,
    criado_em        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE fonte_oficial (
    id           SERIAL PRIMARY KEY,
    conteudo_id  INTEGER NOT NULL REFERENCES conteudo (id)
                 ON DELETE CASCADE,
    orgao        VARCHAR(120) NOT NULL,
    titulo       VARCHAR(150) NOT NULL,
    url          VARCHAR(500) NOT NULL
);

CREATE TABLE avaliacao (
    id           SERIAL PRIMARY KEY,
    conteudo_id  INTEGER NOT NULL REFERENCES conteudo (id)
                 ON DELETE CASCADE,
    util         BOOLEAN NOT NULL,
    comentario   VARCHAR(500),
    criado_em    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- índice usado na busca em português (RF03)
CREATE INDEX idx_conteudo_busca ON conteudo USING GIN (
    to_tsvector('portuguese', titulo || ' ' || resumo || ' ' || o_que_e)
);
