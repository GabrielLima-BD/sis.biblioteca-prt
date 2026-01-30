-- Script para adicionar a coluna de status na tabela de reservas
-- Execute no console SQL do Supabase

ALTER TABLE reservas
ADD COLUMN IF NOT EXISTS status VARCHAR(20) NOT NULL DEFAULT 'ativa';

-- Atualiza reservas existentes que não possuam status definido
UPDATE reservas
SET status = 'ativa'
WHERE status IS NULL;

-- Opcional: cria índice para acelerar filtros por status
do $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_indexes
        WHERE schemaname = 'public'
          AND tablename = 'reservas'
          AND indexname = 'idx_reservas_status'
    ) THEN
        CREATE INDEX idx_reservas_status ON reservas(status);
    END IF;
END$$;