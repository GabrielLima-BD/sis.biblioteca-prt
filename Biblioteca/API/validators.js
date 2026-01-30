/**
 * Validadores e sanitizadores (reutilizáveis) da API.
 *
 * Centraliza regras como:
 * - validação de CPF/CEP/data
 * - sanitização básica de entradas (evitar SQL injection em strings)
 */

/**
 * Validar CPF (formato: 000.000.000-00 ou 11 dígitos)
 * @param {string} cpf - CPF a validar
 * @returns {boolean} - True se válido
 */
export function validarCPF(cpf) {
    if (!cpf || typeof cpf !== 'string') {
        return false;
    }

    const cpfLimpo = cpf.replace(/\D/g, '');
    if (cpfLimpo.length !== 11) {
        return false;
    }
    if (/^(\d)\1{10}$/.test(cpfLimpo)) {
        return false;
    }

    const numeros = cpfLimpo.split('').map((n) => Number(n));

    // Primeiro dígito verificador
    let soma = 0;
    for (let i = 0; i < 9; i += 1) {
        soma += numeros[i] * (10 - i);
    }
    let resto = soma % 11;
    const dv1 = resto < 2 ? 0 : 11 - resto;
    if (numeros[9] !== dv1) {
        return false;
    }

    // Segundo dígito verificador
    soma = 0;
    for (let i = 0; i < 10; i += 1) {
        soma += numeros[i] * (11 - i);
    }
    resto = soma % 11;
    const dv2 = resto < 2 ? 0 : 11 - resto;
    return numeros[10] === dv2;
}

/**
 * Validar data no formato DD/MM/YYYY
 * @param {string} data - Data a validar
 * @returns {boolean} - True se válida
 */
export function validarData(data) {
    if (!data || typeof data !== 'string') {
        return false;
    }

    const regex = /^(0[1-9]|[12][0-9]|3[01])\/(0[1-9]|1[0-2])\/(\d{4})$/;
    if (!regex.test(data)) {
        return false;
    }

    const [dia, mes, ano] = data.split('/').map(Number);
    const date = new Date(ano, mes - 1, dia);

    return date.getFullYear() === ano && date.getMonth() === mes - 1 && date.getDate() === dia;
}

/**
 * Validar CEP no formato 00000-000
 * @param {string} cep - CEP a validar
 * @returns {boolean} - True se válido
 */
export function validarCEP(cep) {
    if (!cep || typeof cep !== 'string') {
        return false;
    }
    const regex = /^\d{5}-?\d{3}$/;
    return regex.test(cep);
}

/**
 * Formatar data de DD/MM/YYYY para YYYY-MM-DD
 * @param {string} data - Data em formato DD/MM/YYYY
 * @returns {string} - Data em formato YYYY-MM-DD
 */
export function formatarData(data) {
    if (!data) {
        return null;
    }
    const [dia, mes, ano] = data.split('/');
    return `${ano}-${mes}-${dia}`;
}

/**
 * Sanitizar entrada para evitar injeção SQL e XSS
 * @param {string} entrada - Texto a sanitizar
 * @returns {string} - Texto sanitizado
 */
export function sanitizarEntrada(entrada) {
    if (typeof entrada !== 'string') {
        return entrada;
    }

    return entrada
        .replace(/[<>]/g, '') // Remove < e >
        .replace(/["']/g, '') // Remove aspas
        .trim(); // Remove espaços em branco
}

/**
 * Sanitizar entrada com foco em SQL Injection.
 * Mantido por compatibilidade com a suíte de testes.
 * @param {string} entrada - Texto a sanitizar
 * @returns {string} - Texto sanitizado
 */
export function sanitizarSQLInjection(entrada) {
    if (entrada === null || entrada === undefined) {
        return '';
    }

    const base = typeof entrada === 'string' ? entrada : String(entrada);
    const semAspasEHtml = sanitizarEntrada(base);
    const texto = typeof semAspasEHtml === 'string' ? semAspasEHtml : base;

    return (
        texto
            // Remove delimitadores/tokens comuns
            .replace(/--/g, '')
            .replace(/\/\*/g, '')
            .replace(/\*\//g, '')
            .replace(/;/g, '')
            // Remove keywords perigosas como palavras inteiras
            .replace(/\b(drop|union|select|insert|delete|update|alter|create|truncate)\b/gi, '')
            .trim()
    );
}

/**
 * Validar email
 * @param {string} email - Email a validar
 * @returns {boolean} - True se válido
 */
export function validarEmail(email) {
    if (!email || typeof email !== 'string') {
        return false;
    }
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(email);
}

/**
 * Validar comprimento de string
 * @param {string} str - String a validar
 * @param {number} min - Comprimento mínimo
 * @param {number} max - Comprimento máximo
 * @returns {boolean} - True se válido
 */
export function validarComprimento(str, min = 0, max = Infinity) {
    if (typeof str !== 'string') {
        return false;
    }
    return str.length >= min && str.length <= max;
}
