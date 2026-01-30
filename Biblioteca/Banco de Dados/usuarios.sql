-- Script SQL para criar a tabela de usuários no Supabase
-- Execute este script no SQL Editor do Supabase

-- Tabela de usuários para autenticação
CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    senha_hash VARCHAR(255) NOT NULL,
    nome VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'user' CHECK (role IN ('user', 'admin', 'moderator')),
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índice para melhorar performance de busca por email
CREATE INDEX IF NOT EXISTS idx_usuarios_email ON usuarios(email);

-- Índice para busca por role
CREATE INDEX IF NOT EXISTS idx_usuarios_role ON usuarios(role);

-- Trigger para atualizar o campo atualizado_em automaticamente
CREATE OR REPLACE FUNCTION atualizar_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.atualizado_em = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_atualizar_usuarios
BEFORE UPDATE ON usuarios
FOR EACH ROW
EXECUTE FUNCTION atualizar_timestamp();

-- Inserir um usuário admin padrão (senha: admin123)
-- Hash gerado com bcrypt rounds=10
INSERT INTO usuarios (email, senha_hash, nome, role)
VALUES (
    'admin@biblioteca.com',
    '$2a$10$rO8WZpNvX9qQ3mQGqXkWfO8HS2F7hNa8O7V8kZ3rT6vH5wW1qH0Oa',
    'Administrador',
    'admin'
) ON CONFLICT (email) DO NOTHING;

-- Comentários na tabela
COMMENT ON TABLE usuarios IS 'Tabela de usuários do sistema de biblioteca';
COMMENT ON COLUMN usuarios.email IS 'Email único do usuário';
COMMENT ON COLUMN usuarios.senha_hash IS 'Hash bcrypt da senha do usuário';
COMMENT ON COLUMN usuarios.nome IS 'Nome completo do usuário';
COMMENT ON COLUMN usuarios.role IS 'Papel do usuário: user, admin ou moderator';
