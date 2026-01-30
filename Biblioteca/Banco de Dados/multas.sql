-- ====================================================================
-- SCRIPT SQL PARA SISTEMA DE MULTAS
-- Sistema de Gerenciamento de Biblioteca
-- Data: 09/12/2025
-- ====================================================================

-- ====================================================================
-- 1. CRIAR TABELA DE MULTAS
-- ====================================================================

CREATE TABLE IF NOT EXISTS multas (
    id SERIAL PRIMARY KEY,
    cliente_id INTEGER NOT NULL,
    reserva_id INTEGER NOT NULL,
    valor DECIMAL(10, 2) NOT NULL CHECK (valor >= 0),
    data_multa DATE NOT NULL DEFAULT CURRENT_DATE,
    data_pagamento DATE,
    status VARCHAR(20) DEFAULT 'pendente' CHECK (status IN ('pendente', 'paga', 'cancelada')),
    observacoes TEXT,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT fk_multa_cliente FOREIGN KEY (cliente_id) REFERENCES cliente(id) ON DELETE CASCADE,
    CONSTRAINT fk_multa_reserva FOREIGN KEY (reserva_id) REFERENCES reservas(id) ON DELETE CASCADE,
    CONSTRAINT check_data_pagamento CHECK (data_pagamento IS NULL OR data_pagamento >= data_multa)
);

-- ====================================================================
-- 2. CRIAR ÍNDICES PARA PERFORMANCE
-- ====================================================================

-- Índice para busca por cliente (query mais comum)
CREATE INDEX IF NOT EXISTS idx_multas_cliente_id ON multas(cliente_id);

-- Índice para busca por reserva
CREATE INDEX IF NOT EXISTS idx_multas_reserva_id ON multas(reserva_id);

-- Índice para busca por status
CREATE INDEX IF NOT EXISTS idx_multas_status ON multas(status);

-- Índice para busca por data
CREATE INDEX IF NOT EXISTS idx_multas_data_multa ON multas(data_multa);

-- Índice composto para busca por cliente e status (otimização)
CREATE INDEX IF NOT EXISTS idx_multas_cliente_status ON multas(cliente_id, status);

-- ====================================================================
-- 3. TRIGGER PARA ATUALIZAR TIMESTAMP AUTOMATICAMENTE
-- ====================================================================

CREATE OR REPLACE FUNCTION atualizar_timestamp_multas()
RETURNS TRIGGER AS $$
BEGIN
    NEW.atualizado_em = CURRENT_TIMESTAMP;
    
    -- Se o status mudou para 'paga', atualizar data_pagamento
    IF NEW.status = 'paga' AND OLD.status != 'paga' AND NEW.data_pagamento IS NULL THEN
        NEW.data_pagamento = CURRENT_DATE;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_atualizar_multas
BEFORE UPDATE ON multas
FOR EACH ROW
EXECUTE FUNCTION atualizar_timestamp_multas();

-- ====================================================================
-- 4. FUNÇÃO PARA CALCULAR MULTA POR ATRASO
-- ====================================================================

CREATE OR REPLACE FUNCTION calcular_multa_atraso(
    p_data_prevista DATE,
    p_data_real DATE,
    p_valor_dia DECIMAL DEFAULT 2.50
)
RETURNS DECIMAL AS $$
DECLARE
    v_dias_atraso INTEGER;
    v_valor_multa DECIMAL;
BEGIN
    -- Calcular dias de atraso
    v_dias_atraso := GREATEST(0, p_data_real - p_data_prevista);
    
    -- Calcular valor da multa
    v_valor_multa := v_dias_atraso * p_valor_dia;
    
    RETURN v_valor_multa;
END;
$$ LANGUAGE plpgsql;

-- ====================================================================
-- 5. PROCEDURE PARA GERAR MULTA AUTOMÁTICA NA DEVOLUÇÃO
-- ====================================================================

CREATE OR REPLACE FUNCTION gerar_multa_automatica()
RETURNS TRIGGER AS $$
DECLARE
    v_dias_atraso INTEGER;
    v_valor_multa DECIMAL;
BEGIN
    -- Verificar se há atraso
    IF NEW.data_devolucao_real > NEW.data_devolucao_prevista THEN
        
        -- Calcular dias de atraso
        v_dias_atraso := NEW.data_devolucao_real - NEW.data_devolucao_prevista;
        
        -- Calcular multa (R$ 2,50 por dia)
        v_valor_multa := v_dias_atraso * 2.50;
        
        -- Inserir multa
        INSERT INTO multas (cliente_id, reserva_id, valor, data_multa, observacoes)
        VALUES (
            NEW.cliente_id,
            NEW.id,
            v_valor_multa,
            NEW.data_devolucao_real,
            FORMAT('Multa por %s dias de atraso na devolução', v_dias_atraso)
        );
        
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Criar trigger na tabela de reservas
CREATE TRIGGER trigger_gerar_multa_devolucao
AFTER UPDATE OF data_devolucao_real ON reservas
FOR EACH ROW
WHEN (NEW.data_devolucao_real IS NOT NULL AND OLD.data_devolucao_real IS NULL)
EXECUTE FUNCTION gerar_multa_automatica();

-- ====================================================================
-- 6. INSERIR DADOS DE TESTE
-- ====================================================================

-- Multas de teste (assumindo que já existem clientes e reservas)
INSERT INTO multas (cliente_id, reserva_id, valor, data_multa, status, observacoes) VALUES
-- Multas pendentes
(1, 1, 25.00, '2025-11-15', 'pendente', 'Multa por 10 dias de atraso'),
(2, 2, 12.50, '2025-11-20', 'pendente', 'Multa por 5 dias de atraso'),
(3, 3, 37.50, '2025-11-25', 'pendente', 'Multa por 15 dias de atraso'),
(4, 4, 20.00, '2025-11-28', 'pendente', 'Multa por 8 dias de atraso'),
(5, 5, 30.00, '2025-12-01', 'pendente', 'Multa por 12 dias de atraso'),
(1, 6, 15.00, '2025-12-03', 'pendente', 'Multa por 6 dias de atraso'),
(2, 7, 27.50, '2025-12-05', 'pendente', 'Multa por 11 dias de atraso'),

-- Multas pagas
(6, 8, 10.00, '2025-10-15', 'paga', 'Multa por 4 dias de atraso'),
(7, 9, 22.50, '2025-10-20', 'paga', 'Multa por 9 dias de atraso'),
(8, 10, 17.50, '2025-10-25', 'paga', 'Multa por 7 dias de atraso'),
(9, 11, 12.50, '2025-11-01', 'paga', 'Multa por 5 dias de atraso'),
(10, 12, 25.00, '2025-11-05', 'paga', 'Multa por 10 dias de atraso'),

-- Multas antigas (pagas há mais tempo)
(1, 13, 30.00, '2025-09-10', 'paga', 'Multa por 12 dias de atraso'),
(3, 14, 20.00, '2025-09-15', 'paga', 'Multa por 8 dias de atraso'),
(5, 15, 15.00, '2025-09-20', 'paga', 'Multa por 6 dias de atraso');

-- Atualizar datas de pagamento para multas pagas
UPDATE multas 
SET data_pagamento = data_multa + INTERVAL '3 days'
WHERE status = 'paga' AND data_multa >= '2025-10-01';

UPDATE multas 
SET data_pagamento = data_multa + INTERVAL '5 days'
WHERE status = 'paga' AND data_multa < '2025-10-01';

-- ====================================================================
-- 7. QUERIES ÚTEIS PARA CONSULTA DE MULTAS
-- ====================================================================

-- ============================================================
-- 7.1. LISTAR TODAS AS MULTAS COM INFORMAÇÕES DO CLIENTE
-- ============================================================

CREATE OR REPLACE VIEW view_multas_completas AS
SELECT 
    m.id,
    m.cliente_id,
    c.nome || ' ' || c.sobrenome AS nome_cliente,
    c.cpf,
    m.reserva_id,
    r.livro_id,
    l.titulo AS nome_livro,
    m.valor,
    m.data_multa,
    m.data_pagamento,
    m.status,
    m.observacoes,
    CASE 
        WHEN m.status = 'pendente' THEN CURRENT_DATE - m.data_multa
        ELSE 0
    END AS dias_pendente,
    m.criado_em,
    m.atualizado_em
FROM multas m
INNER JOIN cliente c ON m.cliente_id = c.id
INNER JOIN reservas r ON m.reserva_id = r.id
INNER JOIN livro l ON r.livro_id = l.id
ORDER BY m.data_multa DESC;

-- ============================================================
-- 7.2. BUSCAR MULTAS POR CLIENTE
-- ============================================================

-- Query para buscar multas de um cliente específico
-- Substitua {cliente_id} pelo ID do cliente
/*
SELECT 
    id,
    reserva_id,
    valor,
    data_multa,
    data_pagamento,
    status,
    observacoes
FROM multas
WHERE cliente_id = {cliente_id}
ORDER BY data_multa DESC;
*/

-- ============================================================
-- 7.3. LISTAR MULTAS PENDENTES
-- ============================================================

-- Todas as multas pendentes do sistema
CREATE OR REPLACE VIEW view_multas_pendentes AS
SELECT 
    m.id,
    m.cliente_id,
    c.nome || ' ' || c.sobrenome AS nome_cliente,
    c.cpf,
    c.email,
    c.telefone,
    m.reserva_id,
    m.valor,
    m.data_multa,
    CURRENT_DATE - m.data_multa AS dias_pendente,
    m.observacoes
FROM multas m
INNER JOIN cliente c ON m.cliente_id = c.id
WHERE m.status = 'pendente'
ORDER BY m.data_multa ASC;

-- ============================================================
-- 7.4. ESTATÍSTICAS DE MULTAS POR CLIENTE
-- ============================================================

CREATE OR REPLACE VIEW view_estatisticas_multas_cliente AS
SELECT 
    c.id AS cliente_id,
    c.nome || ' ' || c.sobrenome AS nome_cliente,
    c.cpf,
    COUNT(*) AS total_multas,
    COUNT(CASE WHEN m.status = 'pendente' THEN 1 END) AS multas_pendentes,
    COUNT(CASE WHEN m.status = 'paga' THEN 1 END) AS multas_pagas,
    SUM(m.valor) AS valor_total,
    SUM(CASE WHEN m.status = 'pendente' THEN m.valor ELSE 0 END) AS valor_pendente,
    SUM(CASE WHEN m.status = 'paga' THEN m.valor ELSE 0 END) AS valor_pago,
    MAX(m.data_multa) AS ultima_multa
FROM cliente c
LEFT JOIN multas m ON c.id = m.cliente_id
GROUP BY c.id, c.nome, c.sobrenome, c.cpf
HAVING COUNT(*) > 0
ORDER BY valor_pendente DESC;

-- ============================================================
-- 7.5. MULTAS ATRASADAS (PENDENTES HÁ MAIS DE 30 DIAS)
-- ============================================================

CREATE OR REPLACE VIEW view_multas_atrasadas AS
SELECT 
    m.id,
    m.cliente_id,
    c.nome || ' ' || c.sobrenome AS nome_cliente,
    c.cpf,
    c.email,
    c.telefone,
    m.valor,
    m.data_multa,
    CURRENT_DATE - m.data_multa AS dias_pendente,
    m.observacoes
FROM multas m
INNER JOIN cliente c ON m.cliente_id = c.id
WHERE m.status = 'pendente'
    AND CURRENT_DATE - m.data_multa > 30
ORDER BY dias_pendente DESC;

-- ============================================================
-- 7.6. HISTÓRICO DE PAGAMENTOS (MULTAS PAGAS)
-- ============================================================

CREATE OR REPLACE VIEW view_historico_pagamentos AS
SELECT 
    m.id,
    m.cliente_id,
    c.nome || ' ' || c.sobrenome AS nome_cliente,
    m.reserva_id,
    m.valor,
    m.data_multa,
    m.data_pagamento,
    m.data_pagamento - m.data_multa AS dias_para_pagar,
    m.observacoes
FROM multas m
INNER JOIN cliente c ON m.cliente_id = c.id
WHERE m.status = 'paga'
ORDER BY m.data_pagamento DESC;

-- ============================================================
-- 7.7. TOTAL DE MULTAS POR PERÍODO
-- ============================================================

CREATE OR REPLACE VIEW view_multas_por_mes AS
SELECT 
    TO_CHAR(data_multa, 'YYYY-MM') AS mes,
    COUNT(*) AS total_multas,
    COUNT(CASE WHEN status = 'pendente' THEN 1 END) AS pendentes,
    COUNT(CASE WHEN status = 'paga' THEN 1 END) AS pagas,
    SUM(valor) AS valor_total,
    SUM(CASE WHEN status = 'paga' THEN valor ELSE 0 END) AS valor_pago,
    SUM(CASE WHEN status = 'pendente' THEN valor ELSE 0 END) AS valor_pendente
FROM multas
GROUP BY TO_CHAR(data_multa, 'YYYY-MM')
ORDER BY mes DESC;

-- ============================================================
-- 7.8. CLIENTES COM MAIS MULTAS
-- ============================================================

CREATE OR REPLACE VIEW view_clientes_mais_multas AS
SELECT 
    c.id,
    c.nome || ' ' || c.sobrenome AS nome_cliente,
    c.cpf,
    c.email,
    COUNT(*) AS total_multas,
    SUM(CASE WHEN m.status = 'pendente' THEN 1 ELSE 0 END) AS multas_pendentes,
    SUM(m.valor) AS valor_total,
    SUM(CASE WHEN m.status = 'pendente' THEN m.valor ELSE 0 END) AS valor_pendente
FROM cliente c
INNER JOIN multas m ON c.id = m.cliente_id
GROUP BY c.id, c.nome, c.sobrenome, c.cpf, c.email
ORDER BY total_multas DESC
LIMIT 20;

-- ====================================================================
-- 8. QUERIES PARA API (ENDPOINTS)
-- ====================================================================

-- ============================================================
-- 8.1. GET /multas/:clienteId - Buscar multas por cliente
-- ============================================================
/*
SELECT 
    id,
    cliente_id,
    reserva_id,
    valor,
    TO_CHAR(data_multa, 'YYYY-MM-DD') AS data_multa,
    TO_CHAR(data_pagamento, 'YYYY-MM-DD') AS data_pagamento,
    status,
    observacoes
FROM multas
WHERE cliente_id = $1
ORDER BY data_multa DESC;
*/

-- ============================================================
-- 8.2. GET /multas?status=pendente - Listar multas por status
-- ============================================================
/*
SELECT 
    m.id,
    m.cliente_id,
    m.reserva_id,
    m.valor,
    TO_CHAR(m.data_multa, 'YYYY-MM-DD') AS data_multa,
    TO_CHAR(m.data_pagamento, 'YYYY-MM-DD') AS data_pagamento,
    m.status,
    m.observacoes,
    c.nome || ' ' || c.sobrenome AS nome_cliente
FROM multas m
INNER JOIN cliente c ON m.cliente_id = c.id
WHERE m.status = $1
ORDER BY m.data_multa DESC;
*/

-- ============================================================
-- 8.3. POST /multas - Criar nova multa
-- ============================================================
/*
INSERT INTO multas (cliente_id, reserva_id, valor, data_multa, observacoes)
VALUES ($1, $2, $3, $4, $5)
RETURNING 
    id,
    cliente_id,
    reserva_id,
    valor,
    TO_CHAR(data_multa, 'YYYY-MM-DD') AS data_multa,
    status;
*/

-- ============================================================
-- 8.4. PATCH /multas/:id/pagar - Registrar pagamento
-- ============================================================
/*
UPDATE multas
SET 
    status = 'paga',
    data_pagamento = $1,
    atualizado_em = CURRENT_TIMESTAMP
WHERE id = $2
    AND status = 'pendente'
RETURNING 
    id,
    cliente_id,
    reserva_id,
    valor,
    TO_CHAR(data_multa, 'YYYY-MM-DD') AS data_multa,
    TO_CHAR(data_pagamento, 'YYYY-MM-DD') AS data_pagamento,
    status;
*/

-- ============================================================
-- 8.5. GET /multas/:id - Buscar multa específica
-- ============================================================
/*
SELECT 
    m.id,
    m.cliente_id,
    c.nome || ' ' || c.sobrenome AS nome_cliente,
    c.cpf,
    m.reserva_id,
    r.livro_id,
    l.titulo AS nome_livro,
    m.valor,
    TO_CHAR(m.data_multa, 'YYYY-MM-DD') AS data_multa,
    TO_CHAR(m.data_pagamento, 'YYYY-MM-DD') AS data_pagamento,
    m.status,
    m.observacoes
FROM multas m
INNER JOIN cliente c ON m.cliente_id = c.id
INNER JOIN reservas r ON m.reserva_id = r.id
INNER JOIN livro l ON r.livro_id = l.id
WHERE m.id = $1;
*/

-- ====================================================================
-- 9. COMENTÁRIOS NA TABELA
-- ====================================================================

COMMENT ON TABLE multas IS 'Tabela de multas por atraso na devolução de livros';
COMMENT ON COLUMN multas.id IS 'Identificador único da multa';
COMMENT ON COLUMN multas.cliente_id IS 'ID do cliente que recebeu a multa';
COMMENT ON COLUMN multas.reserva_id IS 'ID da reserva relacionada à multa';
COMMENT ON COLUMN multas.valor IS 'Valor da multa em reais';
COMMENT ON COLUMN multas.data_multa IS 'Data de emissão da multa';
COMMENT ON COLUMN multas.data_pagamento IS 'Data do pagamento da multa';
COMMENT ON COLUMN multas.status IS 'Status da multa: pendente, paga ou cancelada';
COMMENT ON COLUMN multas.observacoes IS 'Observações adicionais sobre a multa';

-- ====================================================================
-- 10. GRANT DE PERMISSÕES (SE NECESSÁRIO)
-- ====================================================================

-- Conceder permissões ao usuário da aplicação
-- GRANT SELECT, INSERT, UPDATE ON multas TO app_user;
-- GRANT USAGE, SELECT ON SEQUENCE multas_id_seq TO app_user;

-- ====================================================================
-- FIM DO SCRIPT
-- ====================================================================
