/**
 * middleware/rateLimiter.js
 * Configurações de rate limiting para proteger a API
 */

import rateLimit from 'express-rate-limit';

/**
 * Rate limiter geral para todas as rotas
 * Limite: 100 requisições por hora por IP
 */
export const limiterGeral = rateLimit({
    windowMs: 60 * 60 * 1000, // 1 hora
    max: 100, // 100 requisições
    message: {
        message: 'Muitas requisições deste IP. Tente novamente em uma hora.',
        error: 'RATE_LIMIT_EXCEEDED',
    },
    standardHeaders: true, // Retorna info no `RateLimit-*` headers
    legacyHeaders: false, // Desabilita `X-RateLimit-*` headers
    // Store em memória (para produção, usar Redis)
    handler: (req, res) => {
        res.status(429).json({
            message: 'Muitas requisições. Tente novamente mais tarde.',
            error: 'RATE_LIMIT_EXCEEDED',
            retryAfter: res.getHeader('RateLimit-Reset'),
        });
    },
});

/**
 * Rate limiter para rotas de autenticação (login/register)
 * Limite: 5 requisições por 15 minutos por IP
 * Previne ataques de força bruta
 */
export const limiterAuth = rateLimit({
    windowMs: 15 * 60 * 1000, // 15 minutos
    max: 5, // 5 tentativas
    message: {
        message: 'Muitas tentativas de login. Tente novamente em 15 minutos.',
        error: 'AUTH_RATE_LIMIT_EXCEEDED',
    },
    skipSuccessfulRequests: true, // Não conta requisições bem-sucedidas
    handler: (req, res) => {
        res.status(429).json({
            message: 'Muitas tentativas de autenticação. Tente novamente em 15 minutos.',
            error: 'AUTH_RATE_LIMIT_EXCEEDED',
            retryAfter: Math.ceil((req.rateLimit.resetTime - Date.now()) / 1000),
        });
    },
});

/**
 * Rate limiter para rotas de cadastro (POST)
 * Limite: 10 cadastros por hora por IP
 */
export const limiterCadastro = rateLimit({
    windowMs: 60 * 60 * 1000, // 1 hora
    max: 10, // 10 cadastros
    message: {
        message: 'Muitos cadastros realizados. Tente novamente em uma hora.',
        error: 'CADASTRO_RATE_LIMIT_EXCEEDED',
    },
    handler: (req, res) => {
        res.status(429).json({
            message: 'Limite de cadastros atingido. Tente novamente mais tarde.',
            error: 'CADASTRO_RATE_LIMIT_EXCEEDED',
            retryAfter: res.getHeader('RateLimit-Reset'),
        });
    },
});

/**
 * Rate limiter estrito para operações sensíveis
 * Limite: 20 requisições por 15 minutos
 */
export const limiterSensivel = rateLimit({
    windowMs: 15 * 60 * 1000, // 15 minutos
    max: 20, // 20 requisições
    message: {
        message: 'Muitas operações sensíveis. Aguarde 15 minutos.',
        error: 'SENSITIVE_RATE_LIMIT_EXCEEDED',
    },
    handler: (req, res) => {
        res.status(429).json({
            message: 'Limite de operações sensíveis atingido.',
            error: 'SENSITIVE_RATE_LIMIT_EXCEEDED',
            retryAfter: Math.ceil((req.rateLimit.resetTime - Date.now()) / 1000),
        });
    },
});

/**
 * Rate limiter para consultas (GET)
 * Limite: 200 consultas por hora
 */
export const limiterConsulta = rateLimit({
    windowMs: 60 * 60 * 1000, // 1 hora
    max: 200, // 200 consultas
    message: {
        message: 'Muitas consultas realizadas. Aguarde um pouco.',
        error: 'CONSULTA_RATE_LIMIT_EXCEEDED',
    },
    standardHeaders: true,
    legacyHeaders: false,
});

/**
 * Configuração para uso com Redis (produção)
 * Descomente e configure para usar Redis como store
 */
/*
import RedisStore from 'rate-limit-redis';
import Redis from 'ioredis';

const redisClient = new Redis({
    host: process.env.REDIS_HOST || 'localhost',
    port: process.env.REDIS_PORT || 6379,
    password: process.env.REDIS_PASSWORD
});

export const limiterGeralRedis = rateLimit({
    windowMs: 60 * 60 * 1000,
    max: 100,
    store: new RedisStore({
        client: redisClient,
        prefix: 'rl:general:'
    })
});
*/
