/**
 * Testes para validadores - Cobertura expandida
 */
import { validarCPF, validarData, validarCEP, sanitizarSQLInjection } from '../validators.js';

describe('Validadores - CPF', () => {
    test('deve validar CPF correto formatado', () => {
        expect(validarCPF('123.456.789-09')).toBe(true);
    });

    test('deve validar CPF correto sem formatação', () => {
        expect(validarCPF('12345678909')).toBe(true);
    });

    test('deve rejeitar CPF com todos zeros', () => {
        expect(validarCPF('000.000.000-00')).toBe(false);
    });

    test('deve rejeitar CPF com todos noves', () => {
        expect(validarCPF('999.999.999-99')).toBe(false);
    });

    test('deve rejeitar CPF com tamanho incorreto', () => {
        expect(validarCPF('123.456.789')).toBe(false);
    });

    test('deve rejeitar CPF com letras', () => {
        expect(validarCPF('12A.456.789-09')).toBe(false);
    });

    test('deve rejeitar CPF vazio', () => {
        expect(validarCPF('')).toBe(false);
    });

    test('deve rejeitar CPF com dígitos verificadores inválidos', () => {
        expect(validarCPF('123.456.789-00')).toBe(false);
    });

    test('deve rejeitar null', () => {
        expect(validarCPF(null)).toBe(false);
    });

    test('deve rejeitar undefined', () => {
        expect(validarCPF(undefined)).toBe(false);
    });
});

describe('Validadores - Data', () => {
    test('deve validar data válida simples', () => {
        expect(validarData('01/01/2024')).toBe(true);
    });

    test('deve validar último dia do mês', () => {
        expect(validarData('31/01/2024')).toBe(true);
    });

    test('deve validar Fevereiro 28 em ano não bissexto', () => {
        expect(validarData('28/02/2023')).toBe(true);
    });

    test('deve validar Fevereiro 29 em ano bissexto', () => {
        expect(validarData('29/02/2024')).toBe(true);
    });

    test('deve rejeitar Fevereiro 29 em ano não bissexto', () => {
        expect(validarData('29/02/2023')).toBe(false);
    });

    test('deve rejeitar mês inválido', () => {
        expect(validarData('01/13/2024')).toBe(false);
    });

    test('deve rejeitar dia inválido', () => {
        expect(validarData('32/01/2024')).toBe(false);
    });

    test('deve rejeitar dia zero', () => {
        expect(validarData('00/01/2024')).toBe(false);
    });

    test('deve rejeitar mês zero', () => {
        expect(validarData('01/00/2024')).toBe(false);
    });

    test('deve rejeitar formato inválido', () => {
        expect(validarData('01-01-2024')).toBe(false);
    });

    test('deve rejeitar data vazia', () => {
        expect(validarData('')).toBe(false);
    });

    test('deve validar anos bissextos múltiplos de 400', () => {
        expect(validarData('29/02/2000')).toBe(true);
    });

    test('deve rejeitar anos não bissextos múltiplos de 100', () => {
        expect(validarData('29/02/1900')).toBe(false);
    });

    test('deve rejeitar null', () => {
        expect(validarData(null)).toBe(false);
    });

    test('deve rejeitar undefined', () => {
        expect(validarData(undefined)).toBe(false);
    });
});

describe('Validadores - CEP', () => {
    test('deve validar CEP correto formatado', () => {
        expect(validarCEP('12345-678')).toBe(true);
    });

    test('deve validar CEP correto sem formatação', () => {
        expect(validarCEP('12345678')).toBe(true);
    });

    test('deve rejeitar CEP com tamanho incorreto', () => {
        expect(validarCEP('1234-567')).toBe(false);
    });

    test('deve rejeitar CEP com letras', () => {
        expect(validarCEP('1234A-678')).toBe(false);
    });

    test('deve rejeitar CEP vazio', () => {
        expect(validarCEP('')).toBe(false);
    });

    test('deve validar CEP com todos zeros (formato válido)', () => {
        expect(validarCEP('00000-000')).toBe(true);
    });

    test('deve rejeitar CEP com formatação incorreta', () => {
        expect(validarCEP('123456-78')).toBe(false);
    });

    test('deve rejeitar null', () => {
        expect(validarCEP(null)).toBe(false);
    });

    test('deve rejeitar undefined', () => {
        expect(validarCEP(undefined)).toBe(false);
    });
});

describe('Sanitizadores - SQL Injection', () => {
    test('deve escapar aspas simples', () => {
        const resultado = sanitizarSQLInjection('João\'s');
        expect(resultado).not.toBe('João\'s');
    });

    test('deve escapar aspas duplas', () => {
        const resultado = sanitizarSQLInjection('João"s');
        expect(resultado).not.toBe('João"s');
    });

    test('deve remover SQL DROP', () => {
        const entrada = 'João\'; DROP TABLE clientes; --';
        const resultado = sanitizarSQLInjection(entrada);
        expect(resultado.toLowerCase()).not.toContain('drop');
    });

    test('deve remover UNION', () => {
        const entrada = '\' UNION SELECT * FROM --';
        const resultado = sanitizarSQLInjection(entrada);
        expect(resultado.toLowerCase()).not.toContain('union');
    });

    test('deve manter texto limpo', () => {
        const entrada = 'João Silva';
        const resultado = sanitizarSQLInjection(entrada);
        expect(resultado).toContain('Silva');
    });

    test('deve sanitizar valor vazio', () => {
        expect(sanitizarSQLInjection('')).toBe('');
    });

    test('deve sanitizar null', () => {
        expect(sanitizarSQLInjection(null)).toBe('');
    });

    test('deve remover semicolons', () => {
        const entrada = 'valor;DROP TABLE';
        const resultado = sanitizarSQLInjection(entrada);
        expect(resultado).not.toContain(';');
    });

    test('deve remover comentários SQL (--)', () => {
        const entrada = 'valor -- comentário';
        const resultado = sanitizarSQLInjection(entrada);
        expect(resultado).not.toContain('--');
    });

    test('deve remover comentários SQL (/* */)', () => {
        const entrada = 'valor /* comentário */';
        const resultado = sanitizarSQLInjection(entrada);
        expect(resultado).not.toContain('/*');
        expect(resultado).not.toContain('*/');
    });
});
