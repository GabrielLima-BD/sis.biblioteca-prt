/**
 * utils/logger.js
 * Sistema de logging com Winston para gerenciar logs da API
 */

import winston from 'winston';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Configuração de níveis de log
const levels = {
    error: 0,
    warn: 1,
    info: 2,
    http: 3,
    debug: 4,
};

// Cores para exibição no console
const colors = {
    error: 'red',
    warn: 'yellow',
    info: 'green',
    http: 'magenta',
    debug: 'white',
};

winston.addColors(colors);

// Formato padrão
const format = winston.format.combine(
    winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss:ms' }),
    winston.format.colorize({ all: true }),
    winston.format.printf((info) => `${info.timestamp} ${info.level}: ${info.message}`),
);

// Transports - define onde e como os logs serão armazenados
const transports = [
    // Console - exibe logs coloridos no terminal
    new winston.transports.Console(),

    // Arquivo geral - todos os logs
    new winston.transports.File({
        filename: path.join(__dirname, '../../logs/all.log'),
        format: winston.format.combine(
            winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss:ms' }),
            winston.format.printf((info) => `${info.timestamp} ${info.level}: ${info.message}`),
        ),
    }),

    // Arquivo de erros - apenas logs de erro
    new winston.transports.File({
        filename: path.join(__dirname, '../../logs/errors.log'),
        level: 'error',
        format: winston.format.combine(
            winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss:ms' }),
            winston.format.printf((info) => `${info.timestamp} ${info.level}: ${info.message}`),
        ),
    }),

    // Arquivo de requisições HTTP
    new winston.transports.File({
        filename: path.join(__dirname, '../../logs/http.log'),
        level: 'http',
        format: winston.format.combine(
            winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss:ms' }),
            winston.format.printf((info) => `${info.timestamp} ${info.level}: ${info.message}`),
        ),
    }),
];

// Criar instância do logger
const logger = winston.createLogger({
    level: process.env.LOG_LEVEL || 'debug',
    levels,
    format,
    transports,
});

// Exportar logger
export default logger;

/**
 * Middleware para logging de requisições HTTP
 */
export function loggerMiddleware(req, res, next) {
    const start = Date.now();

    // Log da requisição
    logger.http(`${req.method} ${req.path}`);

    // Interceptar a resposta
    const originalSend = res.send;

    res.send = function (data) {
        const duration = Date.now() - start;
        logger.http(`${req.method} ${req.path} - Status: ${res.statusCode} - ${duration}ms`);

        // Log de erro se status >= 400
        if (res.statusCode >= 400) {
            logger.warn(`Erro na requisição: ${req.method} ${req.path} - ${res.statusCode}`);
        }

        originalSend.call(this, data);
    };

    next();
}

/**
 * Helper para logs de erro com detalhes
 */
export function logError(error, context = '') {
    const errorMessage = `${context ? `[${context}] ` : ''}${error.message || error}`;
    logger.error(errorMessage);

    if (process.env.NODE_ENV === 'development' && error.stack) {
        logger.debug(error.stack);
    }
}

/**
 * Helper para logs de sucesso
 */
export function logSuccess(message, data = null) {
    logger.info(message);
    if (data && process.env.NODE_ENV === 'development') {
        logger.debug(JSON.stringify(data));
    }
}

/**
 * Helper para logs de debug
 */
export function logDebug(message, data = null) {
    logger.debug(message);
    if (data) {
        logger.debug(JSON.stringify(data, null, 2));
    }
}
