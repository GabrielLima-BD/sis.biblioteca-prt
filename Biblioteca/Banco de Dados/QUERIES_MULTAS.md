# 📊 QUERIES DE CONSULTA DE MULTAS - EXEMPLOS PRÁTICOS

## 🔍 QUERIES BÁSICAS

### 1. Buscar todas as multas de um cliente específico

```sql
-- Buscar multas do cliente com ID 1
SELECT 
    id,
    reserva_id,
    valor,
    TO_CHAR(data_multa, 'DD/MM/YYYY') AS data_multa,
    TO_CHAR(data_pagamento, 'DD/MM/YYYY') AS data_pagamento,
    status,
    observacoes
FROM multas
WHERE cliente_id = 1
ORDER BY data_multa DESC;
```

### 2. Listar apenas multas pendentes

```sql
SELECT 
    m.id,
    m.cliente_id,
    c.nome || ' ' || c.sobrenome AS cliente,
    m.valor,
    TO_CHAR(m.data_multa, 'DD/MM/YYYY') AS data_multa,
    CURRENT_DATE - m.data_multa AS dias_pendente
FROM multas m
INNER JOIN cliente c ON m.cliente_id = c.id
WHERE m.status = 'pendente'
ORDER BY m.data_multa ASC;
```

### 3. Buscar multa por ID

```sql
SELECT 
    m.id,
    m.cliente_id,
    c.nome || ' ' || c.sobrenome AS cliente,
    c.cpf,
    c.email,
    m.reserva_id,
    l.titulo AS livro,
    m.valor,
    TO_CHAR(m.data_multa, 'DD/MM/YYYY') AS data_multa,
    TO_CHAR(m.data_pagamento, 'DD/MM/YYYY') AS data_pagamento,
    m.status,
    m.observacoes
FROM multas m
INNER JOIN cliente c ON m.cliente_id = c.id
INNER JOIN reservas r ON m.reserva_id = r.id
INNER JOIN livro l ON r.livro_id = l.id
WHERE m.id = 1;
```

---

## 💰 QUERIES DE VALOR E ESTATÍSTICAS

### 4. Total de multas pendentes por cliente

```sql
SELECT 
    c.id,
    c.nome || ' ' || c.sobrenome AS cliente,
    c.cpf,
    COUNT(*) AS total_multas,
    SUM(m.valor) AS total_devido
FROM cliente c
INNER JOIN multas m ON c.id = m.cliente_id
WHERE m.status = 'pendente'
GROUP BY c.id, c.nome, c.sobrenome, c.cpf
ORDER BY total_devido DESC;
```

### 5. Valor total de multas no sistema

```sql
SELECT 
    COUNT(*) AS total_multas,
    COUNT(CASE WHEN status = 'pendente' THEN 1 END) AS pendentes,
    COUNT(CASE WHEN status = 'paga' THEN 1 END) AS pagas,
    SUM(valor) AS valor_total,
    SUM(CASE WHEN status = 'pendente' THEN valor ELSE 0 END) AS valor_pendente,
    SUM(CASE WHEN status = 'paga' THEN valor ELSE 0 END) AS valor_recebido
FROM multas;
```

### 6. Multas por mês (últimos 6 meses)

```sql
SELECT 
    TO_CHAR(data_multa, 'MM/YYYY') AS mes,
    COUNT(*) AS quantidade,
    SUM(valor) AS valor_total,
    COUNT(CASE WHEN status = 'paga' THEN 1 END) AS pagas,
    COUNT(CASE WHEN status = 'pendente' THEN 1 END) AS pendentes
FROM multas
WHERE data_multa >= CURRENT_DATE - INTERVAL '6 months'
GROUP BY TO_CHAR(data_multa, 'MM/YYYY'), TO_CHAR(data_multa, 'YYYY-MM')
ORDER BY TO_CHAR(data_multa, 'YYYY-MM') DESC;
```

---

## ⏰ QUERIES DE ANÁLISE TEMPORAL

### 7. Multas atrasadas (pendentes há mais de 30 dias)

```sql
SELECT 
    m.id,
    c.nome || ' ' || c.sobrenome AS cliente,
    c.telefone,
    c.email,
    m.valor,
    TO_CHAR(m.data_multa, 'DD/MM/YYYY') AS data_multa,
    CURRENT_DATE - m.data_multa AS dias_pendente,
    m.observacoes
FROM multas m
INNER JOIN cliente c ON m.cliente_id = c.id
WHERE m.status = 'pendente'
    AND CURRENT_DATE - m.data_multa > 30
ORDER BY dias_pendente DESC;
```

### 8. Histórico de pagamentos (últimos 30 dias)

```sql
SELECT 
    m.id,
    c.nome || ' ' || c.sobrenome AS cliente,
    m.valor,
    TO_CHAR(m.data_multa, 'DD/MM/YYYY') AS data_multa,
    TO_CHAR(m.data_pagamento, 'DD/MM/YYYY') AS data_pagamento,
    m.data_pagamento - m.data_multa AS dias_para_pagar
FROM multas m
INNER JOIN cliente c ON m.cliente_id = c.id
WHERE m.status = 'paga'
    AND m.data_pagamento >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY m.data_pagamento DESC;
```

### 9. Tempo médio de pagamento

```sql
SELECT 
    AVG(data_pagamento - data_multa) AS media_dias_pagamento,
    MIN(data_pagamento - data_multa) AS menor_tempo,
    MAX(data_pagamento - data_multa) AS maior_tempo,
    COUNT(*) AS total_pagas
FROM multas
WHERE status = 'paga'
    AND data_pagamento IS NOT NULL;
```

---

## 👥 QUERIES DE CLIENTES

### 10. Top 10 clientes com mais multas

```sql
SELECT 
    c.id,
    c.nome || ' ' || c.sobrenome AS cliente,
    c.cpf,
    COUNT(*) AS total_multas,
    SUM(m.valor) AS valor_total,
    SUM(CASE WHEN m.status = 'pendente' THEN m.valor ELSE 0 END) AS valor_pendente
FROM cliente c
INNER JOIN multas m ON c.id = m.cliente_id
GROUP BY c.id, c.nome, c.sobrenome, c.cpf
ORDER BY total_multas DESC
LIMIT 10;
```

### 11. Clientes sem multas pendentes

```sql
SELECT 
    c.id,
    c.nome || ' ' || c.sobrenome AS cliente,
    c.cpf,
    COUNT(m.id) AS total_multas_historico,
    SUM(CASE WHEN m.status = 'paga' THEN m.valor ELSE 0 END) AS total_pago
FROM cliente c
LEFT JOIN multas m ON c.id = m.cliente_id
GROUP BY c.id, c.nome, c.sobrenome, c.cpf
HAVING COUNT(CASE WHEN m.status = 'pendente' THEN 1 END) = 0
ORDER BY total_pago DESC;
```

### 12. Clientes inadimplentes (com multas pendentes)

```sql
SELECT 
    c.id,
    c.nome || ' ' || c.sobrenome AS cliente,
    c.cpf,
    c.telefone,
    c.email,
    COUNT(*) AS multas_pendentes,
    SUM(m.valor) AS total_devido,
    MIN(m.data_multa) AS multa_mais_antiga,
    MAX(CURRENT_DATE - m.data_multa) AS dias_mais_antigo
FROM cliente c
INNER JOIN multas m ON c.id = m.cliente_id
WHERE m.status = 'pendente'
GROUP BY c.id, c.nome, c.sobrenome, c.cpf, c.telefone, c.email
ORDER BY total_devido DESC;
```

---

## 📚 QUERIES COM INFORMAÇÕES DE LIVROS

### 13. Multas por livro (quais livros geram mais multas)

```sql
SELECT 
    l.id,
    l.titulo,
    l.autor,
    COUNT(*) AS total_multas,
    SUM(m.valor) AS valor_total_multas,
    AVG(m.valor) AS media_multa
FROM livro l
INNER JOIN reservas r ON l.id = r.livro_id
INNER JOIN multas m ON r.id = m.reserva_id
GROUP BY l.id, l.titulo, l.autor
ORDER BY total_multas DESC
LIMIT 20;
```

### 14. Multas com detalhes completos (cliente, livro, reserva)

```sql
SELECT 
    m.id AS multa_id,
    c.nome || ' ' || c.sobrenome AS cliente,
    c.cpf,
    l.titulo AS livro,
    l.autor,
    r.data_retirada,
    r.data_devolucao_prevista,
    r.data_devolucao_real,
    r.data_devolucao_real - r.data_devolucao_prevista AS dias_atraso,
    m.valor,
    TO_CHAR(m.data_multa, 'DD/MM/YYYY') AS data_multa,
    m.status,
    m.observacoes
FROM multas m
INNER JOIN cliente c ON m.cliente_id = c.id
INNER JOIN reservas r ON m.reserva_id = r.id
INNER JOIN livro l ON r.livro_id = l.id
ORDER BY m.data_multa DESC;
```

---

## 🔧 QUERIES DE ADMINISTRAÇÃO

### 15. Atualizar multa para paga

```sql
UPDATE multas
SET 
    status = 'paga',
    data_pagamento = CURRENT_DATE,
    atualizado_em = CURRENT_TIMESTAMP
WHERE id = 1
    AND status = 'pendente'
RETURNING *;
```

### 16. Cancelar multa

```sql
UPDATE multas
SET 
    status = 'cancelada',
    observacoes = observacoes || ' - CANCELADA EM ' || TO_CHAR(CURRENT_DATE, 'DD/MM/YYYY'),
    atualizado_em = CURRENT_TIMESTAMP
WHERE id = 1
RETURNING *;
```

### 17. Inserir nova multa manualmente

```sql
INSERT INTO multas (cliente_id, reserva_id, valor, data_multa, observacoes)
VALUES (1, 1, 25.00, CURRENT_DATE, 'Multa por 10 dias de atraso')
RETURNING *;
```

---

## 📊 QUERIES DE RELATÓRIOS

### 18. Relatório mensal de multas

```sql
SELECT 
    TO_CHAR(data_multa, 'Month YYYY') AS periodo,
    COUNT(*) AS quantidade_multas,
    SUM(valor) AS valor_total,
    COUNT(CASE WHEN status = 'paga' THEN 1 END) AS pagas,
    COUNT(CASE WHEN status = 'pendente' THEN 1 END) AS pendentes,
    ROUND(
        COUNT(CASE WHEN status = 'paga' THEN 1 END)::NUMERIC / 
        COUNT(*)::NUMERIC * 100, 
        2
    ) AS percentual_pago
FROM multas
WHERE data_multa >= CURRENT_DATE - INTERVAL '1 year'
GROUP BY TO_CHAR(data_multa, 'Month YYYY'), TO_CHAR(data_multa, 'YYYY-MM')
ORDER BY TO_CHAR(data_multa, 'YYYY-MM') DESC;
```

### 19. Taxa de recuperação de multas

```sql
SELECT 
    COUNT(*) AS total_multas,
    COUNT(CASE WHEN status = 'paga' THEN 1 END) AS multas_pagas,
    ROUND(
        COUNT(CASE WHEN status = 'paga' THEN 1 END)::NUMERIC / 
        COUNT(*)::NUMERIC * 100, 
        2
    ) AS taxa_recuperacao,
    SUM(valor) AS valor_total,
    SUM(CASE WHEN status = 'paga' THEN valor ELSE 0 END) AS valor_recuperado,
    ROUND(
        SUM(CASE WHEN status = 'paga' THEN valor ELSE 0 END) / 
        SUM(valor) * 100, 
        2
    ) AS percentual_valor_recuperado
FROM multas;
```

### 20. Multas por faixa de valor

```sql
SELECT 
    CASE 
        WHEN valor < 10 THEN '< R$ 10,00'
        WHEN valor >= 10 AND valor < 25 THEN 'R$ 10,00 - R$ 24,99'
        WHEN valor >= 25 AND valor < 50 THEN 'R$ 25,00 - R$ 49,99'
        WHEN valor >= 50 AND valor < 100 THEN 'R$ 50,00 - R$ 99,99'
        ELSE '>= R$ 100,00'
    END AS faixa_valor,
    COUNT(*) AS quantidade,
    SUM(valor) AS valor_total,
    ROUND(AVG(valor), 2) AS media
FROM multas
GROUP BY 
    CASE 
        WHEN valor < 10 THEN '< R$ 10,00'
        WHEN valor >= 10 AND valor < 25 THEN 'R$ 10,00 - R$ 24,99'
        WHEN valor >= 25 AND valor < 50 THEN 'R$ 25,00 - R$ 49,99'
        WHEN valor >= 50 AND valor < 100 THEN 'R$ 50,00 - R$ 99,99'
        ELSE '>= R$ 100,00'
    END
ORDER BY MIN(valor);
```

---

## 🎯 QUERIES AVANÇADAS

### 21. Prever multas baseado em reservas atrasadas

```sql
SELECT 
    r.id AS reserva_id,
    c.nome || ' ' || c.sobrenome AS cliente,
    l.titulo AS livro,
    r.data_devolucao_prevista,
    CURRENT_DATE - r.data_devolucao_prevista AS dias_atraso,
    (CURRENT_DATE - r.data_devolucao_prevista) * 2.50 AS multa_prevista
FROM reservas r
INNER JOIN cliente c ON r.cliente_id = c.id
INNER JOIN livro l ON r.livro_id = l.id
WHERE r.status = 'ativa'
    AND r.data_devolucao_real IS NULL
    AND r.data_devolucao_prevista < CURRENT_DATE
    AND NOT EXISTS (
        SELECT 1 FROM multas m 
        WHERE m.reserva_id = r.id
    )
ORDER BY dias_atraso DESC;
```

### 22. Análise de reincidência (clientes com múltiplas multas)

```sql
SELECT 
    c.id,
    c.nome || ' ' || c.sobrenome AS cliente,
    COUNT(*) AS total_multas,
    COUNT(DISTINCT DATE_TRUNC('month', m.data_multa)) AS meses_com_multa,
    SUM(m.valor) AS valor_total,
    MIN(m.data_multa) AS primeira_multa,
    MAX(m.data_multa) AS ultima_multa,
    CASE 
        WHEN COUNT(*) >= 5 THEN 'Alto Risco'
        WHEN COUNT(*) >= 3 THEN 'Médio Risco'
        ELSE 'Baixo Risco'
    END AS nivel_risco
FROM cliente c
INNER JOIN multas m ON c.id = m.cliente_id
GROUP BY c.id, c.nome, c.sobrenome
HAVING COUNT(*) > 1
ORDER BY total_multas DESC;
```

### 23. Comparação de períodos

```sql
-- Comparar multas deste mês com o mês anterior
WITH mes_atual AS (
    SELECT 
        COUNT(*) AS quantidade,
        SUM(valor) AS valor_total
    FROM multas
    WHERE DATE_TRUNC('month', data_multa) = DATE_TRUNC('month', CURRENT_DATE)
),
mes_anterior AS (
    SELECT 
        COUNT(*) AS quantidade,
        SUM(valor) AS valor_total
    FROM multas
    WHERE DATE_TRUNC('month', data_multa) = DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month')
)
SELECT 
    'Mês Atual' AS periodo,
    ma.quantidade,
    ma.valor_total,
    ROUND((ma.quantidade - mat.quantidade)::NUMERIC / NULLIF(mat.quantidade, 0) * 100, 2) AS variacao_quantidade,
    ROUND((ma.valor_total - mat.valor_total) / NULLIF(mat.valor_total, 0) * 100, 2) AS variacao_valor
FROM mes_atual ma, mes_anterior mat
UNION ALL
SELECT 
    'Mês Anterior',
    quantidade,
    valor_total,
    NULL,
    NULL
FROM mes_anterior;
```

---

## 📧 QUERIES PARA NOTIFICAÇÕES

### 24. Clientes para lembrete de pagamento (multas pendentes há 7 dias)

```sql
SELECT 
    c.id,
    c.nome || ' ' || c.sobrenome AS cliente,
    c.email,
    c.telefone,
    COUNT(*) AS multas_pendentes,
    SUM(m.valor) AS valor_total,
    STRING_AGG(
        'Multa #' || m.id || ' - R$ ' || m.valor::TEXT, 
        ', ' 
        ORDER BY m.data_multa
    ) AS detalhes_multas
FROM cliente c
INNER JOIN multas m ON c.id = m.cliente_id
WHERE m.status = 'pendente'
    AND m.data_multa <= CURRENT_DATE - INTERVAL '7 days'
GROUP BY c.id, c.nome, c.sobrenome, c.email, c.telefone;
```

### 25. Dashboard - Resumo executivo

```sql
SELECT 
    (SELECT COUNT(*) FROM multas) AS total_multas,
    (SELECT COUNT(*) FROM multas WHERE status = 'pendente') AS pendentes,
    (SELECT SUM(valor) FROM multas WHERE status = 'pendente') AS valor_pendente,
    (SELECT COUNT(*) FROM multas WHERE status = 'paga') AS pagas,
    (SELECT SUM(valor) FROM multas WHERE status = 'paga') AS valor_recebido,
    (SELECT COUNT(DISTINCT cliente_id) FROM multas WHERE status = 'pendente') AS clientes_inadimplentes,
    (SELECT COUNT(*) FROM multas WHERE status = 'pendente' AND CURRENT_DATE - data_multa > 30) AS multas_atrasadas,
    (SELECT SUM(valor) FROM multas WHERE data_multa >= CURRENT_DATE - INTERVAL '30 days') AS valor_ultimo_mes;
```

---

## 💡 DICAS DE USO

1. **Para API**: Use as queries das seções 1-3 e 15-17
2. **Para relatórios**: Use as queries das seções 18-20
3. **Para análise**: Use as queries das seções 21-23
4. **Para notificações**: Use as queries da seção 24
5. **Para dashboard**: Use a query 25

**Lembre-se de substituir:**
- `$1`, `$2`, etc. pelos valores reais quando usar em código
- IDs de exemplo (1, 2, etc.) pelos IDs reais do seu banco
