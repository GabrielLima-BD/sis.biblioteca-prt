/**
 * auth/middleware.js
 * Middleware de autenticação JWT para proteger rotas
 */

import { verificarAccessToken, extrairTokenDoHeader } from './jwt.js';

/**
 * Middleware para autenticar requisições com JWT
 * Verifica o token no header Authorization e adiciona o usuário à requisição
 */
export function autenticarToken(req, res, next) {
    try {
        const authHeader = req.headers['authorization'];
        const token = extrairTokenDoHeader(authHeader);

        if (!token) {
            return res.status(401).json({
                message: 'Acesso negado. Token não fornecido.',
                error: 'NO_TOKEN',
            });
        }

        // Verifica e decodifica o token
        const payload = verificarAccessToken(token);

        // Adiciona os dados do usuário à requisição
        req.usuario = {
            id: payload.id,
            email: payload.email,
            role: payload.role,
        };

        next();
    } catch (error) {
        if (error.message === 'Token expirado') {
            return res.status(401).json({
                message: 'Token expirado. Faça login novamente.',
                error: 'TOKEN_EXPIRED',
            });
        }

        if (error.message === 'Token inválido') {
            return res.status(403).json({
                message: 'Token inválido.',
                error: 'INVALID_TOKEN',
            });
        }

        return res.status(500).json({
            message: 'Erro ao verificar token.',
            error: error.message,
        });
    }
}

/**
 * Middleware para verificar role/permissão do usuário
 * @param {String[]} rolesPermitidas - Array de roles permitidas (ex: ['admin', 'moderator'])
 */
export function verificarRole(...rolesPermitidas) {
    return (req, res, next) => {
        if (!req.usuario) {
            return res.status(401).json({
                message: 'Usuário não autenticado.',
                error: 'NOT_AUTHENTICATED',
            });
        }

        if (!rolesPermitidas.includes(req.usuario.role)) {
            return res.status(403).json({
                message: 'Permissão negada. Você não tem autorização para acessar este recurso.',
                error: 'INSUFFICIENT_PERMISSIONS',
                required: rolesPermitidas,
                current: req.usuario.role,
            });
        }

        next();
    };
}

/**
 * Middleware opcional de autenticação
 * Se o token for fornecido, valida e adiciona o usuário à requisição
 * Se não for fornecido, continua sem adicionar o usuário
 */
export function autenticacaoOpcional(req, res, next) {
    try {
        const authHeader = req.headers['authorization'];
        const token = extrairTokenDoHeader(authHeader);

        if (token) {
            const payload = verificarAccessToken(token);
            req.usuario = {
                id: payload.id,
                email: payload.email,
                role: payload.role,
            };
        }

        next();
    } catch (error) {
        // Ignora erros de token em autenticação opcional
        next();
    }
}
