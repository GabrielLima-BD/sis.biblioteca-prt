/**
 * auth/jwt.js
 * Gerenciamento de JSON Web Tokens para autenticação
 */

import jwt from 'jsonwebtoken';

// Chaves secretas (devem estar no .env em produção)
const JWT_SECRET = process.env.JWT_SECRET || 'sua_chave_secreta_super_segura_aqui';
const JWT_REFRESH_SECRET = process.env.JWT_REFRESH_SECRET || 'sua_chave_refresh_super_segura_aqui';

// Configurações de expiração
const ACCESS_TOKEN_EXPIRY = '15m'; // Token de acesso expira em 15 minutos
const REFRESH_TOKEN_EXPIRY = '7d'; // Token de refresh expira em 7 dias

/**
 * Gera um token de acesso JWT
 * @param {Object} payload - Dados do usuário (id, email, role)
 * @returns {String} Token JWT assinado
 */
export function gerarAccessToken(payload) {
    return jwt.sign(payload, JWT_SECRET, {
        expiresIn: ACCESS_TOKEN_EXPIRY,
        issuer: 'biblioteca-api',
        audience: 'biblioteca-frontend',
    });
}

/**
 * Gera um token de refresh JWT
 * @param {Object} payload - Dados do usuário (id, email)
 * @returns {String} Refresh token JWT assinado
 */
export function gerarRefreshToken(payload) {
    return jwt.sign(payload, JWT_REFRESH_SECRET, {
        expiresIn: REFRESH_TOKEN_EXPIRY,
        issuer: 'biblioteca-api',
        audience: 'biblioteca-frontend',
    });
}

/**
 * Verifica e decodifica um token de acesso
 * @param {String} token - Token JWT a ser verificado
 * @returns {Object} Payload decodificado ou null se inválido
 */
export function verificarAccessToken(token) {
    try {
        return jwt.verify(token, JWT_SECRET, {
            issuer: 'biblioteca-api',
            audience: 'biblioteca-frontend',
        });
    } catch (error) {
        if (error.name === 'TokenExpiredError') {
            throw new Error('Token expirado');
        }
        if (error.name === 'JsonWebTokenError') {
            throw new Error('Token inválido');
        }
        throw error;
    }
}

/**
 * Verifica e decodifica um refresh token
 * @param {String} token - Refresh token JWT a ser verificado
 * @returns {Object} Payload decodificado ou null se inválido
 */
export function verificarRefreshToken(token) {
    try {
        return jwt.verify(token, JWT_REFRESH_SECRET, {
            issuer: 'biblioteca-api',
            audience: 'biblioteca-frontend',
        });
    } catch (error) {
        if (error.name === 'TokenExpiredError') {
            throw new Error('Refresh token expirado');
        }
        if (error.name === 'JsonWebTokenError') {
            throw new Error('Refresh token inválido');
        }
        throw error;
    }
}

/**
 * Extrai o token do header Authorization
 * @param {String} authHeader - Header Authorization (Bearer token)
 * @returns {String|null} Token extraído ou null
 */
export function extrairTokenDoHeader(authHeader) {
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
        return null;
    }
    return authHeader.substring(7); // Remove "Bearer "
}

/**
 * Gera par de tokens (access + refresh)
 * @param {Object} usuario - Dados do usuário
 * @returns {Object} { accessToken, refreshToken }
 */
export function gerarParTokens(usuario) {
    const payload = {
        id: usuario.id,
        email: usuario.email,
        role: usuario.role || 'user',
    };

    const accessToken = gerarAccessToken(payload);
    const refreshToken = gerarRefreshToken({
        id: usuario.id,
        email: usuario.email,
    });

    return { accessToken, refreshToken };
}
