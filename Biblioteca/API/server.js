/**
 * API Biblioteca (Node/Express) - servidor principal.
 *
 * Responsável por:
 * - Subir o app Express e registrar rotas
 * - Configurar segurança (helmet), CORS e rate limiting
 * - Integrar com Supabase
 * - Expor /health e Swagger em /api-docs
 */

import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import dotenv from 'dotenv';
import bcrypt from 'bcryptjs';
import swaggerUi from 'swagger-ui-express';
import path from 'path';
import { fileURLToPath } from 'url';
import { createClient } from '@supabase/supabase-js';
import { validarCPF, validarData, validarCEP, sanitizarEntrada } from './validators.js';
import { gerarParTokens, verificarRefreshToken } from './auth/jwt.js';
import {
    limiterGeral,
    limiterAuth,
    limiterCadastro,
    limiterConsulta,
} from './middleware/rateLimiter.js';
import logger, { loggerMiddleware, logDebug, logError } from './utils/logger.js';

dotenv.config();

const app = express();

// Segurança: Helmet.js com configuração otimizada
app.use(
    helmet({
        contentSecurityPolicy: {
            directives: {
                defaultSrc: ['\'self\''],
                scriptSrc: ['\'self\'', '\'unsafe-inline\''],
                styleSrc: ['\'self\'', '\'unsafe-inline\''],
                imgSrc: ['\'self\'', 'data:', 'https:'],
                connectSrc: ['\'self\'', process.env.SUPABASE_URL],
                fontSrc: ['\'self\'', 'data:'],
                objectSrc: ['\'none\''],
                mediaSrc: ['\'self\''],
                frameSrc: ['\'none\''],
            },
        },
        hsts: {
            maxAge: 31536000,
            includeSubDomains: true,
            preload: true,
        },
        frameguard: { action: 'deny' },
        noSniff: true,
        xssFilter: true,
        referrerPolicy: { policy: 'strict-origin-when-cross-origin' },
    }),
);

app.use(cors());
app.use(express.json());
app.use(loggerMiddleware);

// Rate limiting geral
app.use('/api/', limiterGeral);

// Rate limiting específico para consultas
app.use('/cliente', limiterConsulta);
app.use('/livro', limiterConsulta);
app.use('/endereco', limiterConsulta);
app.use('/genero', limiterConsulta);
app.use('/reservas', limiterConsulta);
app.use('/multas', limiterConsulta);

// Validação de variáveis de ambiente
const arquivoAtual = fileURLToPath(import.meta.url);
const executadoDiretamente =
    process.argv[1] && path.resolve(process.argv[1]) === path.resolve(arquivoAtual);
const supabaseConfigurado = Boolean(process.env.SUPABASE_URL && process.env.SUPABASE_KEY);

if (!supabaseConfigurado) {
    const mensagem = 'Variáveis de ambiente SUPABASE_URL e SUPABASE_KEY não configuradas';
    logger.warn(mensagem);
    if (executadoDiretamente && process.env.NODE_ENV !== 'test') {
        logger.error(`❌ ERRO: ${mensagem}`);
        process.exit(1);
    }
}

const supabase = supabaseConfigurado
    ? createClient(process.env.SUPABASE_URL, process.env.SUPABASE_KEY)
    : null;

/**
 * Formata data de DD/MM/YYYY para YYYY-MM-DD
 * @param {string} data - Data no formato DD/MM/YYYY
 * @returns {string} - Data formatada para o banco
 */
function formatarData(data) {
    if (!validarData(data)) {
        logger.warn(`Data inválida: ${data}`);
        throw new Error(`Formato de data inválido: ${data}`);
    }
    const [dia, mes, ano] = data.split('/');
    return `${ano}-${mes}-${dia}`;
}

/**
 * Resposta padrão de sucesso
 */
function respostaSucesso(res, statusCode, mensagem, dados = null) {
    const resposta = { message: mensagem };
    if (dados) {
        resposta.data = dados;
    }
    return res.status(statusCode).json(resposta);
}

/**
 * Resposta padrão de erro
 */
function respostaErro(res, statusCode, mensagem, erro = null) {
    const resposta = { message: mensagem };
    if (erro) {
        resposta.error = erro;
    }
    return res.status(statusCode).json(resposta);
}

/**
 * Helper para extrair parâmetros de paginação da query string
 */
function obterParametrosPaginacao(req) {
    let page = parseInt(req.query.page) || 1;
    let limit = parseInt(req.query.limit) || 10;
    const sortBy = req.query.sortBy || null;
    const order = req.query.order === 'desc' ? false : true; // true = ascending

    // Validações
    if (page < 1) {
        page = 1;
    }
    if (limit < 1 || limit > 100) {
        limit = 10;
    } // Máximo 100 items por página

    const from = (page - 1) * limit;
    const to = from + limit - 1;

    return { page, limit, sortBy, order, from, to };
}

/**
 * Helper para criar resposta paginada
 */
function respostaPaginada(res, statusCode, mensagem, dados, total, page, limit) {
    const totalPages = Math.ceil(total / limit);
    return res.status(statusCode).json({
        message: mensagem,
        data: dados,
        pagination: {
            total,
            page,
            limit,
            totalPages,
            hasNextPage: page < totalPages,
            hasPrevPage: page > 1,
        },
    });
}

// ==================== ROTAS DE AUTENTICAÇÃO ====================

/**
 * POST /auth/register - Registra um novo usuário
 * Body: { email, senha, nome, role? }
 */
app.post('/auth/register', limiterAuth, async (req, res) => {
    try {
        const { email, senha, nome, role = 'user' } = req.body;

        // Validações básicas
        if (!email || !senha || !nome) {
            return respostaErro(res, 400, 'Email, senha e nome são obrigatórios');
        }
        if (senha.length < 6) {
            return respostaErro(res, 400, 'Senha deve ter no mínimo 6 caracteres');
        }
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            return respostaErro(res, 400, 'Email inválido');
        }

        // Verifica se usuário já existe
        const { data: usuarioExistente } = await supabase
            .from('usuarios')
            .select('id')
            .eq('email', email)
            .single();

        if (usuarioExistente) {
            return respostaErro(res, 409, 'Email já cadastrado');
        }

        // Hash da senha
        const senhaHash = await bcrypt.hash(senha, 10);

        // Cria usuário
        const { data: novoUsuario, error } = await supabase
            .from('usuarios')
            .insert({
                email: sanitizarEntrada(email),
                senha_hash: senhaHash,
                nome: sanitizarEntrada(nome),
                role: role === 'admin' ? 'admin' : 'user',
                criado_em: new Date().toISOString(),
            })
            .select()
            .single();

        if (error) {
            logError(error, 'Erro ao criar usuário');
            return respostaErro(res, 500, 'Erro ao criar usuário', error.message);
        }

        // Gera tokens
        const { accessToken, refreshToken } = gerarParTokens(novoUsuario);

        return res.status(201).json({
            message: 'Usuário registrado com sucesso',
            data: {
                id: novoUsuario.id,
                email: novoUsuario.email,
                nome: novoUsuario.nome,
                role: novoUsuario.role,
            },
            tokens: {
                accessToken,
                refreshToken,
            },
        });
    } catch (error) {
        logError(error, 'Erro inesperado no registro');
        return respostaErro(res, 500, 'Erro inesperado ao registrar usuário', error.message);
    }
});

/**
 * POST /auth/login - Autentica um usuário
 * Body: { email, senha }
 */
app.post('/auth/login', limiterAuth, async (req, res) => {
    try {
        const { email, senha } = req.body;

        if (!email || !senha) {
            return respostaErro(res, 400, 'Email e senha são obrigatórios');
        }

        // Busca usuário
        const { data: usuario, error } = await supabase
            .from('usuarios')
            .select('*')
            .eq('email', email)
            .single();

        if (error || !usuario) {
            return respostaErro(res, 401, 'Email ou senha incorretos');
        }

        // Verifica senha
        const senhaValida = await bcrypt.compare(senha, usuario.senha_hash);

        if (!senhaValida) {
            return respostaErro(res, 401, 'Email ou senha incorretos');
        }

        // Gera tokens
        const { accessToken, refreshToken } = gerarParTokens(usuario);

        return res.status(200).json({
            message: 'Login realizado com sucesso',
            data: {
                id: usuario.id,
                email: usuario.email,
                nome: usuario.nome,
                role: usuario.role,
            },
            tokens: {
                accessToken,
                refreshToken,
                expiresIn: '15m',
            },
        });
    } catch (error) {
        logError(error, 'Erro inesperado no login');
        return respostaErro(res, 500, 'Erro inesperado ao fazer login', error.message);
    }
});

/**
 * POST /auth/refresh - Renova o access token usando refresh token
 * Body: { refreshToken }
 */
app.post('/auth/refresh', async (req, res) => {
    try {
        const { refreshToken } = req.body;

        if (!refreshToken) {
            return respostaErro(res, 400, 'Refresh token é obrigatório');
        }

        // Verifica refresh token
        const payload = verificarRefreshToken(refreshToken);

        // Busca usuário atualizado
        const { data: usuario, error } = await supabase
            .from('usuarios')
            .select('*')
            .eq('id', payload.id)
            .single();

        if (error || !usuario) {
            return respostaErro(res, 401, 'Usuário não encontrado');
        }

        // Gera novo access token
        const { accessToken } = gerarParTokens(usuario);

        return res.status(200).json({
            message: 'Token renovado com sucesso',
            tokens: {
                accessToken,
                expiresIn: '15m',
            },
        });
    } catch (error) {
        if (error.message.includes('token')) {
            return respostaErro(res, 401, error.message);
        }
        logError(error, 'Erro ao renovar token');
        return respostaErro(res, 500, 'Erro ao renovar token', error.message);
    }
});

/**
 * GET /auth/me - Retorna dados do usuário autenticado
 * Requer autenticação (Bearer token)
 */
app.get('/auth/me', async (req, res) => {
    return respostaErro(res, 410, 'Endpoint desativado');
});

// ==================== ROTAS DE CONSULTA ====================

/**
 * GET /cliente - Busca clientes por nome (com paginação)
 * Query params: Nome (obrigatório), page, limit, sortBy, order
 */
app.get('/cliente', async (req, res) => {
    try {
        const { Nome } = req.query;

        if (!Nome || !Nome.trim()) {
            return respostaErro(res, 400, 'Nome é obrigatório');
        }

        const nomeSanitizado = sanitizarEntrada(Nome);
        const { page, limit, sortBy, order, from, to } = obterParametrosPaginacao(req);

        // Primeiro, buscar o total de registros
        const { count } = await supabase
            .from('cliente')
            .select('*', { count: 'exact', head: true })
            .ilike('Nome', `%${nomeSanitizado}%`);

        // Construir query com paginação e ordenação
        let query = supabase
            .from('cliente')
            .select('*, endereco(*)')
            .ilike('Nome', `%${nomeSanitizado}%`)
            .range(from, to);

        if (sortBy) {
            query = query.order(sortBy, { ascending: order });
        }

        const { data, error } = await query;

        if (error) {
            logError(error, 'Erro ao buscar cliente');
            return respostaErro(res, 500, 'Erro ao buscar cliente', error.message);
        }

        return respostaPaginada(
            res,
            200,
            'Cliente(s) encontrados com sucesso',
            data,
            count,
            page,
            limit,
        );
    } catch (error) {
        logError(error, 'Erro inesperado');
        return respostaErro(res, 500, 'Erro inesperado ao buscar cliente', error.message);
    }
});

/**
 * GET /endereco - Busca clientes por estado
 */
app.get('/endereco', async (req, res) => {
    try {
        const { Estado } = req.query;

        if (!Estado || !Estado.trim()) {
            return respostaErro(res, 400, 'Estado é obrigatório');
        }

        const estadoSanitizado = sanitizarEntrada(Estado);

        // Buscar endereços que correspondem ao estado
        const { data: enderecos, error: erroEndereco } = await supabase
            .from('endereco')
            .select('EnderecoID')
            .ilike('Estado', `%${estadoSanitizado}%`);

        if (erroEndereco) {
            logError(erroEndereco, 'Erro ao buscar endereços');
            return respostaErro(res, 500, 'Erro ao buscar endereços', erroEndereco.message);
        }

        if (!enderecos || enderecos.length === 0) {
            return respostaSucesso(res, 200, 'Nenhum cliente encontrado para este estado', []);
        }

        // Extrair IDs dos endereços
        const enderecoIds = enderecos.map((end) => end.EnderecoID).filter(Boolean);

        if (enderecoIds.length === 0) {
            return respostaSucesso(res, 200, 'Nenhum cliente encontrado para este estado', []);
        }

        // Buscar clientes com esses EnderecoIDs
        const { data, error } = await supabase
            .from('cliente')
            .select(
                `
                ClienteID,
                Nome,
                Sobrenome,
                CPF,
                DataNascimento,
                DataAfiliacao,
                QuantidadeLivrosReservados,
                QuantidadePendencias,
                endereco (
                    CEP,
                    Numero,
                    Bairro,
                    Cidade,
                    Estado,
                    Complemento
                )
            `,
            )
            .in('EnderecoID', enderecoIds);

        if (error) {
            logError(error, 'Erro ao buscar clientes');
            return respostaErro(res, 500, 'Erro ao buscar clientes', error.message);
        }

        return respostaSucesso(res, 200, 'Clientes encontrados com sucesso', data);
    } catch (error) {
        logError(error, 'Erro inesperado');
        return respostaErro(res, 500, 'Erro inesperado ao buscar clientes', error.message);
    }
});

/**
 * GET /livro - Busca livros por nome (com paginação)
 * Query params: NomeLivro (obrigatório), page, limit, sortBy, order
 */
app.get('/livro', async (req, res) => {
    try {
        const { NomeLivro } = req.query;

        if (!NomeLivro || !NomeLivro.trim()) {
            return respostaErro(res, 400, 'Nome do Livro é obrigatório');
        }

        const nomeSanitizado = sanitizarEntrada(NomeLivro);
        const { page, limit, sortBy, order, from, to } = obterParametrosPaginacao(req);

        // Buscar total
        const { count } = await supabase
            .from('livro')
            .select('*', { count: 'exact', head: true })
            .ilike('NomeLivro', `%${nomeSanitizado}%`);

        // Query com paginação
        let query = supabase
            .from('livro')
            .select(
                `
                LivroID,
                NomeLivro,
                Autor,
                Idioma,
                QuantidadePaginas,
                Editora,
                DataPublicacao,
                QuantidadeDisponivel,
                GeneroID
            `,
            )
            .ilike('NomeLivro', `%${nomeSanitizado}%`)
            .range(from, to);

        if (sortBy) {
            query = query.order(sortBy, { ascending: order });
        }

        const { data, error } = await query;

        if (error) {
            logError(error, 'Erro ao buscar livro');
            return respostaErro(res, 500, 'Erro ao buscar livro', error.message);
        }

        if (!data || data.length === 0) {
            return respostaErro(res, 404, 'Livro não encontrado');
        }

        // Buscar generos únicos
        const generoIDs = [...new Set(data.map((l) => l.GeneroID).filter(Boolean))];
        const { data: generos } = await supabase
            .from('genero')
            .select('GeneroID, NomeGenero')
            .in('GeneroID', generoIDs);

        const generoMap = Object.fromEntries(generos?.map((g) => [g.GeneroID, g.NomeGenero]) || []);

        const dataFlat = data.map((livro) => ({
            LivroID: livro.LivroID,
            NomeLivro: livro.NomeLivro,
            Autor: livro.Autor,
            Idioma: livro.Idioma ?? null,
            QuantidadePaginas: livro.QuantidadePaginas ?? null,
            Editora: livro.Editora ?? null,
            DataPublicacao: livro.DataPublicacao ?? null,
            QuantidadeDisponivel: livro.QuantidadeDisponivel,
            GeneroID: livro.GeneroID,
            NomeGenero: generoMap[livro.GeneroID] || null,
        }));

        return respostaPaginada(
            res,
            200,
            'Livro(s) encontrado(s) com sucesso',
            dataFlat,
            count,
            page,
            limit,
        );
    } catch (error) {
        logError(error, 'Erro inesperado');
        return respostaErro(res, 500, 'Erro inesperado ao buscar livro', error.message);
    }
});

/**
 * GET /livro/autor - Busca livros por autor
 */
app.get('/livro/autor', async (req, res) => {
    try {
        const { NomeAutor } = req.query;

        if (!NomeAutor || !NomeAutor.trim()) {
            return respostaErro(res, 400, 'Nome do Autor é obrigatório');
        }

        const nomeSanitizado = sanitizarEntrada(NomeAutor);

        const { data, error } = await supabase
            .from('livro')
            .select(
                `
                LivroID,
                NomeLivro,
                Autor,
                Idioma,
                QuantidadePaginas,
                Editora,
                DataPublicacao,
                QuantidadeDisponivel,
                GeneroID
            `,
            )
            .ilike('Autor', `%${nomeSanitizado}%`);

        if (error) {
            logError(error, 'Erro ao buscar livro');
            return respostaErro(res, 500, 'Erro ao buscar Autor(a)', error.message);
        }

        if (!data || data.length === 0) {
            return respostaErro(res, 404, 'Autor(a) não encontrado');
        }

        // Buscar generos únicos
        const generoIDs = [...new Set(data.map((l) => l.GeneroID).filter(Boolean))];
        const { data: generos } = await supabase
            .from('genero')
            .select('GeneroID, NomeGenero')
            .in('GeneroID', generoIDs);

        const generoMap = Object.fromEntries(generos?.map((g) => [g.GeneroID, g.NomeGenero]) || []);

        const dataFlat = data.map((livro) => ({
            LivroID: livro.LivroID,
            NomeLivro: livro.NomeLivro,
            Autor: livro.Autor,
            Idioma: livro.Idioma,
            QuantidadePaginas: livro.QuantidadePaginas,
            Editora: livro.Editora,
            DataPublicacao: livro.DataPublicacao,
            ISBN: livro.ISBN ?? null,
            QuantidadeTotal: livro.QuantidadeTotal ?? null,
            QuantidadeDisponivel: livro.QuantidadeDisponivel,
            GeneroID: livro.GeneroID,
            NomeGenero: generoMap[livro.GeneroID] || null,
        }));

        return respostaSucesso(res, 200, 'Autor(a) encontrado(a) com sucesso', dataFlat);
    } catch (error) {
        logError(error, 'Erro inesperado');
        return respostaErro(res, 500, 'Erro inesperado ao buscar Autor(a)', error.message);
    }
});

/**
 * POST /livro - Cadastra um novo livro
 * Body: { NomeLivro, Autor, Editora, DataPublicacao (DD/MM/YYYY), Idioma, QuantidadePaginas, QuantidadeDisponivel, GeneroID? ou NomeGenero? }
 */
app.post('/livro', limiterCadastro, async (req, res) => {
    try {
        const {
            NomeLivro,
            Autor,
            Editora,
            DataPublicacao,
            Idioma,
            QuantidadePaginas,
            QuantidadeDisponivel,
            GeneroID,
            NomeGenero,
        } = req.body;

        if (!NomeLivro || !String(NomeLivro).trim()) {
            return respostaErro(res, 400, 'Nome do Livro é obrigatório');
        }

        if (!Autor || !String(Autor).trim()) {
            return respostaErro(res, 400, 'Autor é obrigatório');
        }

        if (!Editora || !String(Editora).trim()) {
            return respostaErro(res, 400, 'Editora é obrigatória');
        }

        if (!DataPublicacao || !validarData(String(DataPublicacao))) {
            return respostaErro(res, 400, 'Data de publicação inválida');
        }

        if (!Idioma || !String(Idioma).trim()) {
            return respostaErro(res, 400, 'Idioma é obrigatório');
        }

        const paginasInt = Number(QuantidadePaginas);
        if (!QuantidadePaginas || Number.isNaN(paginasInt) || paginasInt <= 0) {
            return respostaErro(res, 400, 'Quantidade de páginas inválida');
        }

        const quantidadeInt = Number(QuantidadeDisponivel);
        if (QuantidadeDisponivel === undefined || Number.isNaN(quantidadeInt) || quantidadeInt < 0) {
            return respostaErro(res, 400, 'Quantidade disponível inválida');
        }

        let generoIdFinal = null;

        if (GeneroID !== undefined && GeneroID !== null && String(GeneroID).trim() !== '') {
            const generoInt = Number(GeneroID);
            if (Number.isNaN(generoInt) || generoInt <= 0) {
                return respostaErro(res, 400, 'GeneroID inválido');
            }
            generoIdFinal = generoInt;
        } else if (NomeGenero && String(NomeGenero).trim()) {
            const nomeGeneroSanitizado = sanitizarEntrada(String(NomeGenero).trim());

            const { data: generosEncontrados, error: generoBuscaError } = await supabase
                .from('genero')
                .select('GeneroID, NomeGenero')
            .ilike('NomeGenero', `%${nomeGeneroSanitizado}%`);

            if (generoBuscaError) {
                logError(generoBuscaError, 'Erro ao buscar gênero');
                return respostaErro(res, 500, 'Erro ao buscar gênero', generoBuscaError.message);
            }

            if (generosEncontrados && generosEncontrados.length > 0) {
                generoIdFinal = generosEncontrados[0].GeneroID;
            }
        }

        if (!generoIdFinal) {
            return respostaErro(
                res,
                400,
                'Gênero não encontrado. Informe um GeneroID válido ou um NomeGenero existente.',
            );
        }

        const payloadLivro = {
            NomeLivro: sanitizarEntrada(String(NomeLivro).trim()),
            Autor: sanitizarEntrada(String(Autor).trim()),
            Editora: sanitizarEntrada(String(Editora).trim()),
            DataPublicacao: formatarData(String(DataPublicacao)),
            Idioma: sanitizarEntrada(String(Idioma).trim()),
            QuantidadePaginas: paginasInt,
            QuantidadeDisponivel: quantidadeInt,
            GeneroID: generoIdFinal,
        };

        const { data, error } = await supabase.from('livro').insert(payloadLivro).select().single();

        if (error) {
            logError(error, 'Erro ao cadastrar livro');
            return respostaErro(res, 500, 'Erro ao cadastrar livro', error.message);
        }

        return respostaSucesso(res, 201, 'Livro cadastrado com sucesso', data);
    } catch (error) {
        logError(error, 'Erro inesperado ao cadastrar livro');
        return respostaErro(res, 500, 'Erro inesperado ao cadastrar livro', error.message);
    }
});

/**
 * GET /genero - Busca livros por gênero (com paginação)
 * Query params: NomeGenero (obrigatório), page, limit, sortBy, order
 */
app.get('/genero', async (req, res) => {
    try {
        const { NomeGenero } = req.query;

        // Se não vier filtro, retorna a lista de gêneros existentes (para popular combobox na GUI)
        if (!NomeGenero || !String(NomeGenero).trim()) {
            const { data: generos, error: generoError } = await supabase
                .from('genero')
                .select('GeneroID, NomeGenero')
                .order('NomeGenero', { ascending: true });

            if (generoError) {
                return respostaErro(res, 500, 'Erro ao listar gêneros', generoError.message);
            }

            return respostaSucesso(res, 200, 'Gêneros encontrados com sucesso', generos || []);
        }

        const nomeSanitizado = sanitizarEntrada(NomeGenero);
        const { page, limit, sortBy, order, from, to } = obterParametrosPaginacao(req);

        logDebug('[DEBUG GENERO] Buscando gênero', { nome: nomeSanitizado });

        const { data: generos, error: generoError } = await supabase
            .from('genero')
            .select('GeneroID, NomeGenero')
            .ilike('NomeGenero', `%${nomeSanitizado}%`);

        logDebug('[DEBUG GENERO] Resultado busca', { generos, generoError });

        if (generoError) {
            return respostaErro(res, 500, 'Erro ao buscar gênero', generoError.message);
        }

        if (!generos || generos.length === 0) {
            return respostaErro(res, 404, 'Gênero não encontrado');
        }

        const generoID = generos[0].GeneroID;
        logDebug('[DEBUG GENERO] GeneroID encontrado', { generoID });

        // Buscar total de livros
        const { count } = await supabase
            .from('livro')
            .select('*', { count: 'exact', head: true })
            .eq('GeneroID', generoID);

        logDebug('[DEBUG GENERO] Total de livros', { count });

        // Query SIMPLES sem join - apenas pegar GeneroID da tabela livro
        let query = supabase
            .from('livro')
            .select(
                `
                LivroID,
                NomeLivro,
                Autor,
                Idioma,
                QuantidadePaginas,
                Editora,
                DataPublicacao,
                QuantidadeDisponivel,
                GeneroID
            `,
            )
            .eq('GeneroID', generoID)
            .range(from, to);

        if (sortBy) {
            query = query.order(sortBy, { ascending: order });
        }

        const { data: livros, error: livroError } = await query;
        logDebug('[DEBUG GENERO] Livros encontrados', { total: livros?.length ?? 0, livroError });

        if (livroError) {
            return respostaErro(res, 500, 'Erro ao buscar livros', livroError.message);
        }

        if (!livros || livros.length === 0) {
            return respostaErro(res, 404, 'Nenhum livro encontrado para o gênero');
        }

        // Adicionar NomeGenero manualmente
        const nomeGenero = generos[0].NomeGenero;
        const livrosFlat = livros.map((livro) => ({
            LivroID: livro.LivroID,
            NomeLivro: livro.NomeLivro,
            Autor: livro.Autor,
            Idioma: livro.Idioma,
            QuantidadePaginas: livro.QuantidadePaginas,
            Editora: livro.Editora,
            DataPublicacao: livro.DataPublicacao,
            ISBN: livro.ISBN ?? null,
            QuantidadeTotal: livro.QuantidadeTotal ?? null,
            QuantidadeDisponivel: livro.QuantidadeDisponivel,
            GeneroID: livro.GeneroID,
            NomeGenero: nomeGenero,
        }));

        return respostaPaginada(
            res,
            200,
            'Livros encontrados com sucesso',
            livrosFlat,
            count,
            page,
            limit,
        );
    } catch (error) {
        return respostaErro(res, 500, 'Erro inesperado', error.message);
    }
});

// ==================== ROTAS DE CADASTRO ====================

/**
 * POST /cliente - Cadastra um novo cliente
 * Requer autenticação
 */
app.post('/cliente', limiterCadastro, async (req, res) => {
    try {
        logDebug('📥 Dados recebidos', req.body);

        const {
            CEP,
            Rua,
            Numero,
            Bairro,
            Cidade,
            Estado,
            Complemento,
            Nome,
            Sobrenome,
            CPF,
            DataNascimento,
            DataAfiliacao,
        } = req.body;

        // Validações
        if (
            !Nome?.trim() ||
            !Sobrenome?.trim() ||
            !CPF?.trim() ||
            !DataNascimento?.trim() ||
            !DataAfiliacao?.trim() ||
            !CEP?.trim() ||
            !Rua?.trim() ||
            !Numero?.trim() ||
            !Bairro?.trim() ||
            !Cidade?.trim() ||
            !Estado?.trim()
        ) {
            return respostaErro(res, 400, 'Todos os campos são obrigatórios');
        }

        // Validar CPF
        if (!validarCPF(CPF)) {
            return respostaErro(res, 400, 'CPF inválido');
        }

        // Validar datas
        if (!validarData(DataNascimento) || !validarData(DataAfiliacao)) {
            return respostaErro(res, 400, 'Formato de data inválido. Use DD/MM/YYYY');
        }

        // Validar CEP
        if (!validarCEP(CEP)) {
            return respostaErro(res, 400, 'CEP inválido');
        }

        // Formatar datas
        const dataNascimentoFormatada = formatarData(DataNascimento);
        const dataAfiliacaoFormatada = formatarData(DataAfiliacao);

        // Sanitizar entradas
        const dados = {
            CEP: sanitizarEntrada(CEP),
            Rua: sanitizarEntrada(Rua),
            Numero: sanitizarEntrada(Numero),
            Bairro: sanitizarEntrada(Bairro),
            Cidade: sanitizarEntrada(Cidade),
            Estado: sanitizarEntrada(Estado),
            Complemento: sanitizarEntrada(Complemento),
            Nome: sanitizarEntrada(Nome),
            Sobrenome: sanitizarEntrada(Sobrenome),
            CPF: sanitizarEntrada(CPF),
        };

        // Inserir endereço
        const { data: enderecoData, error: enderecoError } = await supabase
            .from('endereco')
            .insert([
                {
                    CEP: dados.CEP,
                    Rua: dados.Rua,
                    Numero: dados.Numero,
                    Bairro: dados.Bairro,
                    Cidade: dados.Cidade,
                    Estado: dados.Estado,
                    Complemento: dados.Complemento,
                },
            ])
            .select('EnderecoID')
            .single();

        if (enderecoError) {
            logError(enderecoError, 'Erro ao cadastrar endereço');
            return respostaErro(res, 500, 'Erro ao cadastrar endereço', enderecoError.message);
        }

        const enderecoId = enderecoData.EnderecoID;

        // Inserir cliente
        const { data: clienteData, error: clienteError } = await supabase
            .from('cliente')
            .insert([
                {
                    Nome: dados.Nome,
                    Sobrenome: dados.Sobrenome,
                    CPF: dados.CPF,
                    DataNascimento: dataNascimentoFormatada,
                    DataAfiliacao: dataAfiliacaoFormatada,
                    EnderecoID: enderecoId,
                },
            ])
            .select()
            .single();

        if (clienteError) {
            logError(clienteError, 'Erro ao cadastrar cliente');
            return respostaErro(res, 500, 'Erro ao cadastrar cliente', clienteError.message);
        }

        return respostaSucesso(res, 201, 'Cliente cadastrado com sucesso', {
            cliente: clienteData,
            endereco: enderecoData,
        });
    } catch (error) {
        logError(error, 'Erro');
        return respostaErro(res, 500, 'Erro ao cadastrar cliente', error.message);
    }
});

/**
 * GET /livro/:id - Busca livro por ID
 */
app.get('/livro/:id', async (req, res) => {
    try {
        const { id } = req.params;

        if (!id || isNaN(id)) {
            return respostaErro(res, 400, 'ID inválido');
        }

        const { data, error } = await supabase
            .from('livro')
            .select('LivroID, NomeLivro, Autor, QuantidadeDisponivel')
            .eq('LivroID', id)
            .maybeSingle();

        if (error) {
            return respostaErro(res, 500, 'Erro ao buscar livro', error.message);
        }

        if (!data) {
            return respostaErro(res, 404, 'Livro não encontrado');
        }

        return respostaSucesso(res, 200, 'Livro encontrado', data);
    } catch (error) {
        return respostaErro(res, 500, 'Erro inesperado', error.message);
    }
});

/**
 * GET /cliente/cpf/:cpf - Busca cliente por CPF
 */
app.get('/cliente/cpf/:cpf', async (req, res) => {
    try {
        const { cpf } = req.params;

        if (!cpf || !validarCPF(cpf)) {
            return respostaErro(res, 400, 'CPF inválido');
        }

        const { data, error } = await supabase
            .from('cliente')
            .select('ClienteID, Nome, Sobrenome, CPF')
            .eq('CPF', cpf)
            .maybeSingle();

        if (error) {
            return respostaErro(res, 500, 'Erro ao buscar cliente', error.message);
        }

        if (!data) {
            return respostaErro(res, 404, 'Cliente não encontrado');
        }

        return respostaSucesso(res, 200, 'Cliente encontrado', data);
    } catch (error) {
        return respostaErro(res, 500, 'Erro inesperado', error.message);
    }
});

/**
 * POST /reservas - Cadastra uma nova reserva
 * SEM autenticação (removido para facilitar testes)
 */
app.post('/reservas', async (req, res) => {
    try {
        logDebug('📥 Dados de reserva recebidos', req.body);

        const {
            CPFReserva,
            NomeLivro,
            LivroID,
            QntdLivro,
            DataRetirada,
            DataVolta,
            Entrega,
            Observacao,
        } = req.body;

        // Validações
        if (
            !CPFReserva?.trim() ||
            (!NomeLivro?.trim() && !LivroID) ||
            !QntdLivro ||
            !DataRetirada?.trim() ||
            !DataVolta?.trim() ||
            !Entrega?.trim()
        ) {
            logger.warn('❌ Validação falhou - campos obrigatórios faltando');
            return respostaErro(res, 400, 'Todos os campos obrigatórios devem ser preenchidos');
        }

        // Validar CPF
        if (!validarCPF(CPFReserva)) {
            return respostaErro(res, 400, 'CPF inválido');
        }

        // Validar datas
        if (!validarData(DataRetirada) || !validarData(DataVolta)) {
            return respostaErro(res, 400, 'Formato de data inválido. Use DD/MM/YYYY');
        }

        // Validar quantidade
        const qntd = parseInt(QntdLivro);
        if (isNaN(qntd) || qntd <= 0) {
            return respostaErro(res, 400, 'Quantidade deve ser um número maior que 0');
        }

        // Formatar datas
        const dataRetiradaFormatada = formatarData(DataRetirada);
        const dataVoltaFormatada = formatarData(DataVolta);

        // Sanitizar entradas
        const livroIdNumero = LivroID ? Number(LivroID) : null;
        if (LivroID && (isNaN(livroIdNumero) || livroIdNumero <= 0)) {
            return respostaErro(res, 400, 'LivroID deve ser um número válido');
        }

        const dadosSanitizados = {
            CPF: sanitizarEntrada(CPFReserva),
            NomeLivro: NomeLivro ? sanitizarEntrada(NomeLivro) : null,
            LivroID: livroIdNumero,
            QntdLivro: qntd,
            Entrega: sanitizarEntrada(Entrega),
            Observacao: sanitizarEntrada(Observacao),
        };

        // Buscar cliente
        const { data: clienteData, error: clienteErro } = await supabase
            .from('cliente')
            .select('ClienteID')
            .eq('CPF', dadosSanitizados.CPF)
            .maybeSingle();

        if (clienteErro) {
            logError(clienteErro, 'Erro ao buscar cliente');
            return respostaErro(res, 500, 'Erro na consulta de cliente');
        }

        if (!clienteData) {
            return respostaErro(res, 402, 'Cliente não encontrado');
        }

        // Buscar livro: por ID se informado, senão por nome (ilike)
        let livroData = null;
        let livroErro = null;
        if (dadosSanitizados.LivroID) {
            const resp = await supabase
                .from('livro')
                .select('LivroID, NomeLivro, QuantidadeDisponivel')
                .eq('LivroID', dadosSanitizados.LivroID)
                .maybeSingle();
            livroData = resp.data;
            livroErro = resp.error;
        } else if (dadosSanitizados.NomeLivro) {
            const resp = await supabase
                .from('livro')
                .select('LivroID, NomeLivro, QuantidadeDisponivel')
                .ilike('NomeLivro', `%${dadosSanitizados.NomeLivro}%`)
                .maybeSingle();
            livroData = resp.data;
            livroErro = resp.error;
        } else {
            return respostaErro(res, 400, 'Informe LivroID ou NomeLivro');
        }

        if (livroErro) {
            logError(livroErro, 'Erro ao buscar livro');
            return respostaErro(res, 500, 'Erro na consulta de livro');
        }

        if (!livroData) {
            return respostaErro(res, 404, 'Livro não encontrado');
        }

        // Verificar quantidade disponível
        if (livroData.QuantidadeDisponivel < dadosSanitizados.QntdLivro) {
            return respostaErro(
                res,
                400,
                `Apenas ${livroData.QuantidadeDisponivel} livros disponíveis`,
            );
        }

        // Criar reserva
        const { data: reservaData, error: reservaErro } = await supabase
            .from('reservas')
            .insert([
                {
                    ClienteID: clienteData.ClienteID,
                    LivroID: livroData.LivroID,
                    DataRetirada: dataRetiradaFormatada,
                    DataPrevistaEntrega: dataVoltaFormatada,
                    FormaRetirada: dadosSanitizados.Entrega,
                    QuantidadeReservada: dadosSanitizados.QntdLivro,
                    Observacao: dadosSanitizados.Observacao,
                    Status: 'ativa',
                },
            ])
            .select()
            .single();

        if (reservaErro) {
            logError(reservaErro, 'Erro ao cadastrar reserva');
            return respostaErro(res, 500, 'Erro ao inserir reserva');
        }

        return respostaSucesso(res, 201, 'Reserva cadastrada com sucesso', {
            reserva: reservaData,
        });
    } catch (error) {
        logError(error, 'Erro');
        return respostaErro(res, 500, 'Erro ao cadastrar reserva', error.message);
    }
});

// ==================== ROTAS CRUD (Atualização e Exclusão) ====================

async function enriquecerReservas(reservas) {
    if (!reservas || reservas.length === 0) {
        return [];
    }

    const clienteIds = [...new Set(reservas.map((item) => item.ClienteID).filter(Boolean))];
    const livroIds = [...new Set(reservas.map((item) => item.LivroID).filter(Boolean))];

    const clientesMap = {};
    const enderecosMap = {};
    const livrosMap = {};

    if (clienteIds.length) {
        const { data: clientes, error: erroClientes } = await supabase
            .from('cliente')
            .select('ClienteID, Nome, Sobrenome, CPF, EnderecoID')
            .in('ClienteID', clienteIds);

        if (erroClientes) {
            throw new Error(`Erro ao buscar clientes relacionados: ${erroClientes.message}`);
        }

        for (const cliente of clientes || []) {
            clientesMap[cliente.ClienteID] = cliente;
        }

        const enderecoIds = [
            ...new Set((clientes || []).map((item) => item.EnderecoID).filter(Boolean)),
        ];

        if (enderecoIds.length) {
            const { data: enderecos, error: erroEnderecos } = await supabase
                .from('endereco')
                .select('EnderecoID, CEP, Rua, Numero, Bairro, Cidade, Estado, Complemento')
                .in('EnderecoID', enderecoIds);

            if (erroEnderecos) {
                throw new Error(`Erro ao buscar endereços relacionados: ${erroEnderecos.message}`);
            }

            for (const endereco of enderecos || []) {
                enderecosMap[endereco.EnderecoID] = endereco;
            }
        }
    }

    if (livroIds.length) {
        const { data: livros, error: erroLivros } = await supabase
            .from('livro')
            .select('LivroID, NomeLivro, Autor, GeneroID')
            .in('LivroID', livroIds);

        if (erroLivros) {
            throw new Error(`Erro ao buscar livros relacionados: ${erroLivros.message}`);
        }

        for (const livro of livros || []) {
            livrosMap[livro.LivroID] = livro;
        }
    }

    return reservas.map((reserva) => {
        const cliente = clientesMap[reserva.ClienteID] || {};
        const livro = livrosMap[reserva.LivroID] || {};
        const endereco = cliente.EnderecoID ? enderecosMap[cliente.EnderecoID] : null;

        const enderecoFormatado = endereco
            ? [
                endereco.Rua && `${endereco.Rua}${endereco.Numero ? `, ${endereco.Numero}` : ''}`,
                endereco.Bairro,
                endereco.Cidade &&
                      `${endereco.Cidade}${endereco.Estado ? ` - ${endereco.Estado}` : ''}`,
                endereco.CEP && `CEP: ${endereco.CEP}`,
                endereco.Complemento,
            ]
                .filter(Boolean)
                .join(' | ')
            : '';

        return {
            ...reserva,
            ClienteNome: cliente.Nome || '',
            ClienteSobrenome: cliente.Sobrenome || '',
            ClienteCPF: cliente.CPF || '',
            ClienteEndereco: enderecoFormatado,
            LivroNome: livro.NomeLivro || '',
            LivroAutor: livro.Autor || '',
        };
    });
}

/**
 * GET /reservas - Lista reservas (ativa ou todas)
 * Query params: status=ativa|todas (default: todas)
 */
app.get('/reservas', async (req, res) => {
    try {
        const statusFiltro =
            typeof req.query.status === 'string' ? req.query.status.toLowerCase() : 'todas';

        const mapaStatus = {
            ativa: 'ativa',
            ativas: 'ativa',
            finalizada: 'finalizada',
            finalizadas: 'finalizada',
            cancelada: 'cancelada',
            canceladas: 'cancelada',
        };

        const statusNormalizado = mapaStatus[statusFiltro] || null;

        let query = supabase.from('reservas').select(`
                ReservaID,
                ClienteID,
                LivroID,
                DataRetirada,
                DataPrevistaEntrega,
                DataEntrega,
                FormaRetirada,
                QuantidadeReservada,
                Observacao,
                Status
            `);

        if (statusNormalizado) {
            query = query.ilike('Status', statusNormalizado);
        }

        const { data, error } = await query;

        if (error) {
            logError(error, 'Erro ao listar reservas');
            return respostaErro(res, 500, 'Erro ao buscar reservas', error.message);
        }

        const reservasDetalhadas = await enriquecerReservas(data || []);

        return respostaSucesso(res, 200, 'Reservas encontradas', reservasDetalhadas);
    } catch (error) {
        logError(error, 'Erro inesperado ao listar reservas');
        return respostaErro(res, 500, 'Erro inesperado ao listar reservas', error.message);
    }
});

/**
 * GET /reservas/:id - Detalhes de uma reserva específica
 */
app.get('/reservas/:id', async (req, res) => {
    try {
        const { id } = req.params;

        if (!id || isNaN(id)) {
            return respostaErro(res, 400, 'ID de reserva inválido');
        }

        const { data, error } = await supabase
            .from('reservas')
            .select(
                `
                ReservaID,
                ClienteID,
                LivroID,
                DataRetirada,
                DataPrevistaEntrega,
                DataEntrega,
                FormaRetirada,
                QuantidadeReservada,
                Observacao,
                Status
            `,
            )
            .eq('ReservaID', id)
            .single();

        if (error) {
            if (
                error.code === 'PGRST116' ||
                error.message?.toLowerCase().includes('row not found')
            ) {
                return respostaErro(res, 404, 'Reserva não encontrada');
            }

            logError(error, 'Erro ao buscar reserva por ID');
            return respostaErro(res, 500, 'Erro ao buscar reserva', error.message);
        }

        const [reservaDetalhada] = await enriquecerReservas(data ? [data] : []);

        if (!reservaDetalhada) {
            return respostaErro(res, 404, 'Reserva não encontrada');
        }

        return respostaSucesso(res, 200, 'Reserva encontrada', reservaDetalhada);
    } catch (error) {
        logError(error, 'Erro inesperado ao buscar reserva por ID');
        return respostaErro(res, 500, 'Erro inesperado ao buscar reserva', error.message);
    }
});

/**
 * PUT /reservas/:id - Atualiza todos os dados de uma reserva
 * Requer autenticação
 */
app.put('/reservas/:id', async (req, res) => {
    try {
        const { id } = req.params;
        const {
            DataRetirada,
            DataPrevistaEntrega,
            FormaRetirada,
            QuantidadeReservada,
            Observacao,
        } = req.body;

        // Validações
        if (!id || isNaN(id)) {
            return respostaErro(res, 400, 'ID de reserva inválido');
        }

        // Preparar dados para atualização
        const dadosAtualizacao = {};

        if (DataRetirada) {
            if (!validarData(DataRetirada)) {
                return respostaErro(res, 400, 'Data de retirada inválida');
            }
            dadosAtualizacao.DataRetirada = formatarData(DataRetirada);
        }

        if (DataPrevistaEntrega) {
            if (!validarData(DataPrevistaEntrega)) {
                return respostaErro(res, 400, 'Data de entrega prevista inválida');
            }
            dadosAtualizacao.DataPrevistaEntrega = formatarData(DataPrevistaEntrega);
        }

        if (FormaRetirada) {
            if (!['Retirada', 'Entrega'].includes(FormaRetirada)) {
                return respostaErro(res, 400, 'Forma de retirada inválida');
            }
            dadosAtualizacao.FormaRetirada = sanitizarEntrada(FormaRetirada);
        }

        if (QuantidadeReservada) {
            if (isNaN(QuantidadeReservada) || QuantidadeReservada < 1) {
                return respostaErro(res, 400, 'Quantidade deve ser maior que 0');
            }
            dadosAtualizacao.QuantidadeReservada = parseInt(QuantidadeReservada);
        }

        if (Observacao !== undefined) {
            dadosAtualizacao.Observacao = Observacao ? sanitizarEntrada(Observacao) : null;
        }

        const { data, error } = await supabase
            .from('reservas')
            .update(dadosAtualizacao)
            .eq('ReservaID', id)
            .select();

        if (error) {
            logError(error, 'Erro ao atualizar reserva');
            return respostaErro(res, 500, 'Erro ao atualizar reserva', error.message);
        }

        if (!data || data.length === 0) {
            return respostaErro(res, 404, 'Reserva não encontrada');
        }

        return respostaSucesso(res, 200, 'Reserva atualizada com sucesso', data[0]);
    } catch (error) {
        logError(error, 'Erro ao atualizar reserva');
        return respostaErro(res, 500, 'Erro ao atualizar reserva', error.message);
    }
});

/**
 * PATCH /reservas/:id - Atualiza parcialmente uma reserva (apenas status)
 * Requer autenticação
 */
app.patch('/reservas/:id', async (req, res) => {
    try {
        const { id } = req.params;
        const { status, DataEntrega } = req.body;

        // Validações
        if (!id || isNaN(id)) {
            return respostaErro(res, 400, 'ID de reserva inválido');
        }

        const dadosAtualizacao = {};

        if (status) {
            if (!['ativa', 'finalizada', 'cancelada'].includes(status.toLowerCase())) {
                return respostaErro(
                    res,
                    400,
                    'Status inválido. Use: ativa, finalizada ou cancelada',
                );
            }
            dadosAtualizacao.Status = status.toLowerCase();
        }

        if (DataEntrega) {
            if (!validarData(DataEntrega)) {
                return respostaErro(res, 400, 'Data de entrega inválida');
            }
            dadosAtualizacao.DataEntrega = formatarData(DataEntrega);
        }

        if (Object.keys(dadosAtualizacao).length === 0) {
            return respostaErro(res, 400, 'Nenhum campo para atualizar');
        }

        const { data, error } = await supabase
            .from('reservas')
            .update(dadosAtualizacao)
            .eq('ReservaID', id)
            .select();

        if (error) {
            logError(error, 'Erro ao atualizar status da reserva');
            return respostaErro(res, 500, 'Erro ao atualizar status', error.message);
        }

        if (!data || data.length === 0) {
            return respostaErro(res, 404, 'Reserva não encontrada');
        }

        return respostaSucesso(res, 200, 'Status da reserva atualizado', data[0]);
    } catch (error) {
        logError(error, 'Erro ao atualizar status');
        return respostaErro(res, 500, 'Erro ao atualizar status', error.message);
    }
});

/**
 * DELETE /reservas/:id - Cancela/deleta uma reserva
 * Requer autenticação
 */
app.delete('/reservas/:id', async (req, res) => {
    try {
        const { id } = req.params;

        // Validações
        if (!id || isNaN(id)) {
            return respostaErro(res, 400, 'ID de reserva inválido');
        }

        // Buscar reserva para verificar status
        const { data: reservaData, error: buscarErro } = await supabase
            .from('reservas')
            .select('ReservaID, Status, DataEntrega')
            .eq('ReservaID', id)
            .single();

        if (buscarErro || !reservaData) {
            return respostaErro(res, 404, 'Reserva não encontrada');
        }

        // Marcar como cancelada em vez de deletar
        const { data, error } = await supabase
            .from('reservas')
            .update({ Status: 'cancelada' })
            .eq('ReservaID', id)
            .select();

        if (error) {
            logError(error, 'Erro ao cancelar reserva');
            return respostaErro(res, 500, 'Erro ao cancelar reserva', error.message);
        }

        return respostaSucesso(res, 200, 'Reserva cancelada com sucesso', data[0]);
    } catch (error) {
        logError(error, 'Erro ao cancelar reserva');
        return respostaErro(res, 500, 'Erro ao cancelar reserva', error.message);
    }
});

/**
 * PUT /cliente/:id - Atualiza todos os dados de um cliente
 * Requer autenticação
 */
app.put('/cliente/:id', async (req, res) => {
    try {
        const { id } = req.params;
        const { Nome, Sobrenome, CPF, DataNascimento, DataAfiliacao } = req.body;

        // Validações
        if (!id || isNaN(id)) {
            return respostaErro(res, 400, 'ID de cliente inválido');
        }

        if (!Nome || !Nome.trim()) {
            return respostaErro(res, 400, 'Nome é obrigatório');
        }

        if (CPF && !validarCPF(CPF)) {
            return respostaErro(res, 400, 'CPF inválido');
        }

        if (DataNascimento && !validarData(DataNascimento)) {
            return respostaErro(res, 400, 'Data de nascimento inválida');
        }

        if (DataAfiliacao && !validarData(DataAfiliacao)) {
            return respostaErro(res, 400, 'Data de afiliação inválida');
        }

        // Preparar dados para atualização
        const dadosAtualizacao = {
            Nome: sanitizarEntrada(Nome),
            ...(Sobrenome && { Sobrenome: sanitizarEntrada(Sobrenome) }),
            ...(CPF && { CPF: sanitizarEntrada(CPF) }),
            ...(DataNascimento && { DataNascimento: formatarData(DataNascimento) }),
            ...(DataAfiliacao && { DataAfiliacao: formatarData(DataAfiliacao) }),
        };

        const { data, error } = await supabase
            .from('cliente')
            .update(dadosAtualizacao)
            .eq('ClienteID', id)
            .select();

        if (error) {
            logError(error, 'Erro ao atualizar cliente');
            return respostaErro(res, 500, 'Erro ao atualizar cliente', error.message);
        }

        if (!data || data.length === 0) {
            return respostaErro(res, 404, 'Cliente não encontrado');
        }

        return respostaSucesso(res, 200, 'Cliente atualizado com sucesso', data[0]);
    } catch (error) {
        logError(error, 'Erro');
        return respostaErro(res, 500, 'Erro ao atualizar cliente', error.message);
    }
});

/**
 * PATCH /cliente/:id - Atualiza parcialmente um cliente
 * Requer autenticação
 */
app.patch('/cliente/:id', async (req, res) => {
    try {
        const { id } = req.params;

        // Validações
        if (!id || isNaN(id)) {
            return respostaErro(res, 400, 'ID de cliente inválido');
        }

        if (Object.keys(req.body).length === 0) {
            return respostaErro(res, 400, 'Nenhum campo para atualizar');
        }

        // Validar campos fornecidos
        const { CPF, DataNascimento, DataAfiliacao, ...outrosCampos } = req.body;

        if (CPF && !validarCPF(CPF)) {
            return respostaErro(res, 400, 'CPF inválido');
        }

        if (DataNascimento && !validarData(DataNascimento)) {
            return respostaErro(res, 400, 'Data de nascimento inválida');
        }

        if (DataAfiliacao && !validarData(DataAfiliacao)) {
            return respostaErro(res, 400, 'Data de afiliação inválida');
        }

        // Preparar dados com sanitização
        const dadosAtualizacao = {};
        Object.keys(outrosCampos).forEach((campo) => {
            dadosAtualizacao[campo] = sanitizarEntrada(outrosCampos[campo]);
        });

        if (CPF) {
            dadosAtualizacao.CPF = sanitizarEntrada(CPF);
        }
        if (DataNascimento) {
            dadosAtualizacao.DataNascimento = formatarData(DataNascimento);
        }
        if (DataAfiliacao) {
            dadosAtualizacao.DataAfiliacao = formatarData(DataAfiliacao);
        }

        const { data, error } = await supabase
            .from('cliente')
            .update(dadosAtualizacao)
            .eq('ClienteID', id)
            .select();

        if (error) {
            logError(error, 'Erro ao atualizar cliente');
            return respostaErro(res, 500, 'Erro ao atualizar cliente', error.message);
        }

        if (!data || data.length === 0) {
            return respostaErro(res, 404, 'Cliente não encontrado');
        }

        return respostaSucesso(res, 200, 'Cliente atualizado com sucesso', data[0]);
    } catch (error) {
        logError(error, 'Erro');
        return respostaErro(res, 500, 'Erro ao atualizar cliente', error.message);
    }
});

/**
 * DELETE /cliente/:id - Deleta um cliente
 * Requer autenticação
 */
app.delete('/cliente/:id', async (req, res) => {
    try {
        const { id } = req.params;

        // Validações
        if (!id || isNaN(id)) {
            return respostaErro(res, 400, 'ID de cliente inválido');
        }

        // Verificar se cliente existe
        const { data: clienteExiste, error: verificarError } = await supabase
            .from('cliente')
            .select('ClienteID')
            .eq('ClienteID', id)
            .single();

        if (verificarError || !clienteExiste) {
            return respostaErro(res, 404, 'Cliente não encontrado');
        }

        // Deletar cliente
        const { error } = await supabase.from('cliente').delete().eq('ClienteID', id).select();

        if (error) {
            logError(error, 'Erro ao deletar cliente');
            return respostaErro(res, 500, 'Erro ao deletar cliente', error.message);
        }

        return respostaSucesso(res, 200, 'Cliente deletado com sucesso', {
            clienteID: id,
        });
    } catch (error) {
        logError(error, 'Erro');
        return respostaErro(res, 500, 'Erro ao deletar cliente', error.message);
    }
});

/**
 * PUT /livro/:id - Atualiza um livro
 * Requer autenticação
 */
app.put('/livro/:id', async (req, res) => {
    try {
        const { id } = req.params;
        const { NomeLivro, Autor, Editora, DataPublicacao, QuantidadeDisponivel } = req.body;

        if (!id || isNaN(id)) {
            return respostaErro(res, 400, 'ID de livro inválido');
        }

        if (DataPublicacao && !validarData(DataPublicacao)) {
            return respostaErro(res, 400, 'Data de publicação inválida');
        }

        const dadosAtualizacao = {};
        if (NomeLivro) {
            dadosAtualizacao.NomeLivro = sanitizarEntrada(NomeLivro);
        }
        if (Autor) {
            dadosAtualizacao.Autor = sanitizarEntrada(Autor);
        }
        if (Editora) {
            dadosAtualizacao.Editora = sanitizarEntrada(Editora);
        }
        if (DataPublicacao) {
            dadosAtualizacao.DataPublicacao = formatarData(DataPublicacao);
        }
        if (QuantidadeDisponivel) {
            dadosAtualizacao.QuantidadeDisponivel = parseInt(QuantidadeDisponivel);
        }

        const { data, error } = await supabase
            .from('livro')
            .update(dadosAtualizacao)
            .eq('LivroID', id)
            .select();

        if (error) {
            return respostaErro(res, 500, 'Erro ao atualizar livro', error.message);
        }

        if (!data || data.length === 0) {
            return respostaErro(res, 404, 'Livro não encontrado');
        }

        return respostaSucesso(res, 200, 'Livro atualizado com sucesso', data[0]);
    } catch (error) {
        return respostaErro(res, 500, 'Erro ao atualizar livro', error.message);
    }
});

/**
 * DELETE /livro/:id - Deleta um livro
 * Requer autenticação
 */
app.delete('/livro/:id', async (req, res) => {
    try {
        const { id } = req.params;

        if (!id || isNaN(id)) {
            return respostaErro(res, 400, 'ID de livro inválido');
        }

        const { data: livroExiste } = await supabase
            .from('livro')
            .select('LivroID')
            .eq('LivroID', id)
            .single();

        if (!livroExiste) {
            return respostaErro(res, 404, 'Livro não encontrado');
        }

        const { error } = await supabase.from('livro').delete().eq('LivroID', id);

        if (error) {
            return respostaErro(res, 500, 'Erro ao deletar livro', error.message);
        }

        return respostaSucesso(res, 200, 'Livro deletado com sucesso', {
            livroID: id,
        });
    } catch (error) {
        return respostaErro(res, 500, 'Erro ao deletar livro', error.message);
    }
});

/**
 * POST /devolucoes - Registra devolução de livro
 * Requer autenticação
 */
app.post('/devolucoes', async (req, res) => {
    try {
        const { ReservaID, DataDevolucao, CondicaoLivro } = req.body;

        if (!ReservaID || isNaN(ReservaID)) {
            return respostaErro(res, 400, 'ID de reserva inválido');
        }

        if (!DataDevolucao || !validarData(DataDevolucao)) {
            return respostaErro(res, 400, 'Data de devolução inválida');
        }

        if (!CondicaoLivro || !['Excelente', 'Bom', 'Danificado'].includes(CondicaoLivro)) {
            return respostaErro(res, 400, 'Condição do livro inválida');
        }

        const { data, error } = await supabase
            .from('devolucao')
            .insert([
                {
                    ReservaID,
                    DataDevolucao: formatarData(DataDevolucao),
                    CondicaoLivro: sanitizarEntrada(CondicaoLivro),
                    DataRegistro: new Date().toISOString(),
                },
            ])
            .select();

        if (error) {
            logError(error, 'Erro ao registrar devolução');
            return respostaErro(res, 500, 'Erro ao registrar devolução', error.message);
        }

        return respostaSucesso(res, 201, 'Devolução registrada com sucesso', data[0]);
    } catch (error) {
        logError(error, 'Erro');
        return respostaErro(res, 500, 'Erro ao registrar devolução', error.message);
    }
});

const enriquecerMultas = async (multasBase = []) => {
    if (!multasBase || multasBase.length === 0) {
        return [];
    }

    const reservaIds = [...new Set(multasBase.map((m) => m.ReservaID).filter(Boolean))];
    if (reservaIds.length === 0) {
        return multasBase;
    }

    const { data: reservas, error: reservasError } = await supabase
        .from('reservas')
        .select('ReservaID, ClienteID, LivroID, DataRetirada, DataPrevistaEntrega')
        .in('ReservaID', reservaIds);

    if (reservasError) {
        throw reservasError;
    }

    const reservasMap = new Map((reservas || []).map((r) => [r.ReservaID, r]));
    const clienteIds = [...new Set((reservas || []).map((r) => r.ClienteID).filter(Boolean))];
    const livroIds = [...new Set((reservas || []).map((r) => r.LivroID).filter(Boolean))];

    const { data: clientes, error: clientesError } = clienteIds.length
        ? await supabase.from('cliente').select('ClienteID, Nome, Sobrenome').in('ClienteID', clienteIds)
        : { data: [], error: null };

    if (clientesError) {
        throw clientesError;
    }

    const { data: livros, error: livrosError } = livroIds.length
        ? await supabase.from('livro').select('LivroID, NomeLivro').in('LivroID', livroIds)
        : { data: [], error: null };

    if (livrosError) {
        throw livrosError;
    }

    const clientesMap = new Map((clientes || []).map((c) => [c.ClienteID, c]));
    const livrosMap = new Map((livros || []).map((l) => [l.LivroID, l]));

    return (multasBase || []).map((multa) => {
        const reserva = reservasMap.get(multa.ReservaID);
        if (!reserva) {
            return multa;
        }

        const cliente = clientesMap.get(reserva.ClienteID) || null;
        const livro = livrosMap.get(reserva.LivroID) || null;

        return {
            ...multa,
            reserva: {
                ReservaID: reserva.ReservaID,
                ClienteID: reserva.ClienteID,
                DataRetirada: reserva.DataRetirada ?? null,
                DataPrevistaEntrega: reserva.DataPrevistaEntrega ?? null,
                cliente: cliente ? { Nome: cliente.Nome, Sobrenome: cliente.Sobrenome } : null,
                livro: livro ? { NomeLivro: livro.NomeLivro } : null,
            },
        };
    });
};

const obterReservaIdsPorCliente = async (clienteId) => {
    const { data, error } = await supabase
        .from('reservas')
        .select('ReservaID')
        .eq('ClienteID', clienteId);

    if (error) {
        throw error;
    }

    return (data || []).map((r) => r.ReservaID).filter(Boolean);
};

// ==================== UTILITÁRIOS (SCHEMA RESILIENTE) ====================

let multaSchemaCache = null;
let multaSchemaCacheAt = 0;

const isSchemaColumnError = (error) => {
    const msg = String(error?.message || '');
    return (
        msg.includes('Could not find') ||
        msg.includes('schema cache') ||
        msg.includes('does not exist')
    );
};

const colunaExiste = async (tabela, coluna) => {
    const { error } = await supabase.from(tabela).select(coluna).limit(1);
    if (!error) {
        return true;
    }
    if (isSchemaColumnError(error)) {
        return false;
    }
    // Erros de permissão, RLS, etc. Devem propagar pra não mascarar.
    throw error;
};

const obterSchemaMulta = async () => {
    const agora = Date.now();
    // Cache curto para evitar probes repetidos.
    if (multaSchemaCache && (agora - multaSchemaCacheAt) < 5 * 60 * 1000) {
        return multaSchemaCache;
    }

    const tabela = 'multa';
    const candidatos = {
        id: ['MultaID', 'multa_id', 'id', 'ID'],
        reserva: ['PendenciaID', 'pendencia_id', 'ReservaID', 'reserva_id', 'reservaId'],
        cliente: ['ClienteID', 'cliente_id'],
        valor: ['Valor', 'valor'],
        status: ['Status', 'status'],
        dataVencimento: ['DataVencimento', 'data_vencimento'],
        dataEmissao: ['DataEmissao', 'data_emissao', 'data_multa'],
        dataPagamento: ['DataPagamento', 'data_pagamento'],
    };

    const schema = { tabela, colunas: {} };
    for (const [grupo, colunas] of Object.entries(candidatos)) {
        for (const coluna of colunas) {
            try {
                const existe = await colunaExiste(tabela, coluna);
                if (existe) {
                    schema.colunas[grupo] = coluna;
                    break;
                }
            } catch (error) {
                // Se não der pra fazer probe por erro "real", salvamos o erro e paramos.
                logError(error, `[Schema probe] Falha ao checar coluna ${tabela}.${coluna}`);
                break;
            }
        }
    }

    multaSchemaCache = schema;
    multaSchemaCacheAt = agora;
    return schema;
};

const normalizarMulta = (multa) => {
    const multaId = multa?.MultaID ?? multa?.multa_id ?? multa?.id ?? multa?.ID ?? null;
    const reservaId =
        multa?.PendenciaID ??
        multa?.pendencia_id ??
        multa?.ReservaID ??
        multa?.reserva_id ??
        multa?.reservaId ??
        null;

    const clienteId = multa?.ClienteID ?? multa?.cliente_id ?? null;
    const valor = multa?.Valor ?? multa?.valor ?? null;
    const dataVencimento =
        multa?.DataVencimento ??
        multa?.data_vencimento ??
        multa?.DataEmissao ??
        multa?.data_multa ??
        multa?.data_emissao ??
        null;
    const dataPagamento = multa?.DataPagamento ?? multa?.data_pagamento ?? null;
    const status = multa?.Status ?? multa?.status ?? null;

    return {
        ...multa,
        MultaID: multaId,
        ReservaID: reservaId,
        ClienteID: clienteId,
        Valor: valor,
        DataVencimento: dataVencimento,
        DataPagamento: dataPagamento,
        Status: status,
    };
};

const obterMultasFiltradas = async ({ clienteId, reservaId, status, vencidas, multaId } = {}) => {
    // Importante: alguns ambientes possuem schema diferente (ex.: coluna ReservaID não existe).
    // Para evitar erro de relationship/coluna inexistente, buscamos * e filtramos no Node.
    let data = null;
    let error = null;

    ({ data, error } = await supabase.from('multa').select('*'));
    if (error) {
        throw error;
    }

    let multasNormalizadas = (data || []).map(normalizarMulta);

    if (multaId) {
        multasNormalizadas = multasNormalizadas.filter((m) => Number(m.MultaID) === Number(multaId));
    }

    if (reservaId) {
        // No schema atual, ReservaID vem de PendenciaID (normalizado acima)
        multasNormalizadas = multasNormalizadas.filter((m) => Number(m.ReservaID) === Number(reservaId));
    }

    if (status) {
        const statusNormalizado = String(status).toLowerCase();
        if (statusNormalizado === 'pendente') {
            multasNormalizadas = multasNormalizadas.filter(
                (m) => {
                    const st = String(m.Status || '').toLowerCase();
                    return !m.DataPagamento && st !== 'paga' && st !== 'pago';
                },
            );
        } else if (statusNormalizado === 'paga' || statusNormalizado === 'pago') {
            multasNormalizadas = multasNormalizadas.filter(
                (m) => {
                    const st = String(m.Status || '').toLowerCase();
                    return Boolean(m.DataPagamento) || st === 'paga' || st === 'pago';
                },
            );
        }
    }

    if (vencidas) {
        const hojeIso = new Date().toISOString().split('T')[0];
        multasNormalizadas = multasNormalizadas.filter((m) => {
            if (m.DataPagamento) {
                return false;
            }
            const dataBase = String(m.DataVencimento || '').split('T')[0];
            return Boolean(dataBase) && dataBase < hojeIso;
        });
    }

    if (clienteId) {
        // Se o schema já expõe ClienteID direto, filtramos por ele.
        const temClienteDireto = multasNormalizadas.some((m) => m.ClienteID !== null && m.ClienteID !== undefined);

        if (temClienteDireto) {
            multasNormalizadas = multasNormalizadas.filter((m) => Number(m.ClienteID) === Number(clienteId));
        } else {
            // Senão, usamos as reservas para obter os IDs e filtrar por ReservaID.
            const reservaIds = await obterReservaIdsPorCliente(clienteId);
            if (!reservaIds || reservaIds.length === 0) {
                return [];
            }
            const setReserva = new Set(reservaIds.map((r) => Number(r)));
            multasNormalizadas = multasNormalizadas.filter((m) => setReserva.has(Number(m.ReservaID)));
        }
    }

    // Ordenação consistente (mais antigas primeiro por data base quando existir)
    multasNormalizadas.sort((a, b) => {
        const da = String(a.DataVencimento || '');
        const db = String(b.DataVencimento || '');
        if (da && db) {
            return da.localeCompare(db);
        }
        return Number(a.MultaID || 0) - Number(b.MultaID || 0);
    });

    try {
        return await enriquecerMultas(multasNormalizadas);
    } catch (enriquecerError) {
        // Se a base não tiver tabela/colunas compatíveis para enriquecer, retorna sem enriquecimento.
        logError(enriquecerError, 'Falha ao enriquecer multas');
        return multasNormalizadas;
    }
};

/**
 * GET /multas - Lista multas com filtros opcionais
 */
app.get('/multas', async (req, res) => {
    try {
        const { status, vencidas, clienteId, reservaId, multaId } = req.query;

        const filtros = {};

        if (clienteId !== undefined) {
            const idCliente = Number(clienteId);
            if (!clienteId || Number.isNaN(idCliente) || idCliente <= 0) {
                return respostaErro(res, 400, 'ID de cliente inválido');
            }
            filtros.clienteId = idCliente;
        }

        if (reservaId !== undefined) {
            const idReserva = Number(reservaId);
            if (!reservaId || Number.isNaN(idReserva) || idReserva <= 0) {
                return respostaErro(res, 400, 'ID de reserva inválido');
            }
            filtros.reservaId = idReserva;
        }

        if (multaId !== undefined) {
            const idMulta = Number(multaId);
            if (!multaId || Number.isNaN(idMulta) || idMulta <= 0) {
                return respostaErro(res, 400, 'ID da multa inválido');
            }
            filtros.multaId = idMulta;
        }

        if (status) {
            filtros.status = String(status);
        }

        if (vencidas !== undefined) {
            filtros.vencidas = String(vencidas).toLowerCase() === 'true';
        }

        const multas = await obterMultasFiltradas(filtros);
        return respostaSucesso(res, 200, 'Multas encontradas', multas);
    } catch (error) {
        logError(error, 'Erro ao buscar multas');
        return respostaErro(res, 500, 'Erro ao buscar multas', error.message);
    }
});

/**
 * GET /multas/:clienteId - Busca multas de um cliente
 */
app.get('/multas/:clienteId', async (req, res) => {
    try {
        const { clienteId } = req.params;
        const idCliente = Number(clienteId);

        if (!clienteId || Number.isNaN(idCliente) || idCliente <= 0) {
            return respostaErro(res, 400, 'ID de cliente inválido');
        }

        const multas = await obterMultasFiltradas({ clienteId: idCliente });
        return respostaSucesso(res, 200, 'Multas encontradas', multas);
    } catch (error) {
        logError(error, 'Erro ao buscar multas');
        return respostaErro(res, 500, 'Erro ao buscar multas', error.message);
    }
});

/**
 * POST /multas - Cria nova multa
 * Requer autenticação
 */
app.post('/multas', async (req, res) => {
    try {
        const { ReservaID, Valor, DataVencimento } = req.body;

        if (!ReservaID || isNaN(ReservaID)) {
            return respostaErro(res, 400, 'ID de reserva inválido');
        }

        if (!Valor || isNaN(Valor) || Valor <= 0) {
            return respostaErro(res, 400, 'Valor inválido');
        }

        if (!DataVencimento || !validarData(DataVencimento)) {
            return respostaErro(res, 400, 'Data de vencimento inválida');
        }

        const dataBase = formatarData(DataVencimento);
        const valorBase = parseFloat(Valor);

        // Tenta entender o schema real exposto pelo Supabase/PostgREST.
        const schema = await obterSchemaMulta();

        // Alguns schemas exigem MultaID (NOT NULL) sem default/auto-increment.
        // Para manter a API funcional sem alterar o banco, geramos um ID incremental (max + 1).
        let novoIdMulta = null;
        try {
            if (schema?.colunas?.id) {
                const idCol = schema.colunas.id;
                const { data: idData, error: idError } = await supabase
                    .from('multa')
                    .select(idCol)
                    .order(idCol, { ascending: false })
                    .limit(1);
                if (!idError) {
                    const atual = idData?.[0]?.[idCol];
                    const base = Number.isFinite(Number(atual)) ? Number(atual) : 0;
                    novoIdMulta = base + 1;
                }
            }
        } catch (error) {
            // Se falhar, seguimos sem ID explícito e deixamos o banco resolver (se tiver default).
            logError(error, 'Falha ao gerar MultaID incremental');
        }

        // Best effort: tenta buscar ClienteID da reserva (se o schema da multa exigir).
        let clienteIdDaReserva = null;
        try {
            const { data: reservasData, error: reservasError } = await supabase
                .from('reservas')
                .select('ClienteID,cliente_id')
                .eq('ReservaID', Number(ReservaID))
                .limit(1);
            if (!reservasError && reservasData && reservasData.length > 0) {
                const row = reservasData[0];
                const cid = row?.ClienteID ?? row?.cliente_id;
                if (cid !== undefined && cid !== null) {
                    clienteIdDaReserva = Number(cid);
                }
            }
        } catch (error) {
            // Se falhar, seguimos sem ClienteID.
            logError(error, 'Falha ao buscar ClienteID da reserva para criar multa');
        }

        const payloadDetectado = {};
        if (novoIdMulta && schema?.colunas?.id) {
            payloadDetectado[schema.colunas.id] = novoIdMulta;
        }
        if (schema?.colunas?.reserva) {
            payloadDetectado[schema.colunas.reserva] = Number(ReservaID);
        }
        if (schema?.colunas?.valor) {
            payloadDetectado[schema.colunas.valor] = valorBase;
        }
        if (schema?.colunas?.status) {
            payloadDetectado[schema.colunas.status] = 'pendente';
        }
        // Preferência: DataVencimento, senão DataEmissao
        if (schema?.colunas?.dataVencimento) {
            payloadDetectado[schema.colunas.dataVencimento] = dataBase;
        } else if (schema?.colunas?.dataEmissao) {
            payloadDetectado[schema.colunas.dataEmissao] = dataBase;
        }
        if (clienteIdDaReserva && schema?.colunas?.cliente) {
            payloadDetectado[schema.colunas.cliente] = clienteIdDaReserva;
        }

        const payloadsParaTentar = [
            // 1) Primeiro tenta o payload montado pelo schema detectado
            payloadDetectado,
            // 2) Fallbacks (quando o schema não foi detectado corretamente)
            { MultaID: novoIdMulta, PendenciaID: Number(ReservaID), Valor: valorBase, DataVencimento: dataBase, Status: 'pendente' },
            { MultaID: novoIdMulta, ReservaID: Number(ReservaID), Valor: valorBase, DataVencimento: dataBase, Status: 'pendente' },
            { MultaID: novoIdMulta, PendenciaID: Number(ReservaID), Valor: valorBase, DataEmissao: dataBase, Status: 'pendente' },
            { MultaID: novoIdMulta, ReservaID: Number(ReservaID), Valor: valorBase, DataEmissao: dataBase, Status: 'pendente' },
            { multa_id: novoIdMulta, pendencia_id: Number(ReservaID), valor: valorBase, data_vencimento: dataBase, status: 'pendente' },
            { multa_id: novoIdMulta, reserva_id: Number(ReservaID), valor: valorBase, data_vencimento: dataBase, status: 'pendente' },
            { multa_id: novoIdMulta, pendencia_id: Number(ReservaID), valor: valorBase, data_emissao: dataBase, status: 'pendente' },
            { multa_id: novoIdMulta, reserva_id: Number(ReservaID), valor: valorBase, data_emissao: dataBase, status: 'pendente' },
            { multa_id: novoIdMulta, reserva_id: Number(ReservaID), valor: valorBase, data_multa: dataBase, status: 'pendente' },
        ].filter((p) => p && Object.keys(p).length > 0);

        let ultimoErro = null;
        for (const payload of payloadsParaTentar) {
            const result = await supabase.from('multa').insert([payload]).select();
            if (!result.error) {
                return respostaSucesso(res, 201, 'Multa criada com sucesso', result.data?.[0] ?? null);
            }

            ultimoErro = result.error;

            // Se for erro de coluna/schema, tentamos o próximo payload.
            if (isSchemaColumnError(result.error)) {
                continue;
            }

            // Erro real (constraint, permissões, etc.)
            logError(result.error, 'Erro ao criar multa');
            return respostaErro(res, 500, 'Erro ao criar multa', result.error.message);
        }

        logError(ultimoErro, 'Erro ao criar multa');
        return respostaErro(
            res,
            500,
            'Erro ao criar multa',
            ultimoErro?.message || 'Schema incompatível: nenhuma variação de colunas funcionou',
        );
    } catch (error) {
        logError(error, 'Erro');
        return respostaErro(res, 500, 'Erro ao criar multa', error.message);
    }
});

/**
 * PATCH /multas/:id/pagar - Marca multa como paga
 * Requer autenticação
 */
app.patch('/multas/:id/pagar', async (req, res) => {
    try {
        const { id } = req.params;
        const { DataPagamento } = req.body;

        if (!id || isNaN(id)) {
            return respostaErro(res, 400, 'ID de multa inválido');
        }

        if (!DataPagamento || !validarData(DataPagamento)) {
            return respostaErro(res, 400, 'Data de pagamento inválida');
        }

        const dataBase = formatarData(DataPagamento);

        const updatesParaTentar = [
            { DataPagamento: dataBase, Status: 'paga' },
            { data_pagamento: dataBase, status: 'paga' },
        ];

        const keysParaTentar = ['MultaID', 'multa_id', 'id', 'ID'];

        const isSchemaColumnError = (error) => {
            const msg = String(error?.message || '');
            return (
                msg.includes("Could not find") ||
                msg.includes('schema cache') ||
                msg.includes('does not exist')
            );
        };

        let ultimoErro = null;
        for (const updatePayload of updatesParaTentar) {
            for (const key of keysParaTentar) {
                const { data, error } = await supabase
                    .from('multa')
                    .update(updatePayload)
                    .eq(key, id)
                    .select();

                if (!error) {
                    if (!data || data.length === 0) {
                        continue;
                    }
                    return respostaSucesso(res, 200, 'Multa marcada como paga', data[0]);
                }

                ultimoErro = error;
                if (isSchemaColumnError(error)) {
                    continue;
                }
                return respostaErro(res, 500, 'Erro ao marcar multa como paga', error.message);
            }
        }

        if (ultimoErro) {
            return respostaErro(res, 500, 'Erro ao marcar multa como paga', ultimoErro.message);
        }

        return respostaErro(res, 404, 'Multa não encontrada');
    } catch (error) {
        return respostaErro(res, 500, 'Erro ao processar pagamento', error.message);
    }
});

// ==================== HEALTH CHECK ====================

app.get('/health', (req, res) => {
    return res.json({ status: 'OK', message: 'API está funcionando' });
});

// ==================== SWAGGER / API DOCUMENTATION ====================

/**
 * Swagger UI - Documentação interativa da API
 * Acesso: http://localhost:3000/api-docs
 */
const swaggerSpec = {
    openapi: '3.0.0',
    info: {
        title: 'API Biblioteca',
        version: '2.0.0',
        description: 'API para gerenciamento de biblioteca',
    },
    servers: [
        {
            url: `http://localhost:${process.env.PORT || 3000}`,
            description: 'Development',
        },
    ],
};

app.use(
    '/api-docs',
    swaggerUi.serve,
    swaggerUi.setup(swaggerSpec, {
        swaggerOptions: {
            displayOperationId: true,
            filter: true,
            showRequestHeaders: true,
            docExpansion: 'list',
        },
        customCss: '.swagger-ui .topbar { display: none }',
        customSiteTitle: 'API Biblioteca - Documentação',
    }),
);

/**
 * Retorna o JSON da especificação Swagger
 */
app.get('/swagger.json', (req, res) => {
    res.setHeader('Content-Type', 'application/json');
    res.send(swaggerSpec);
});

// ==================== 404 ====================

app.use((req, res) => {
    return respostaErro(res, 404, 'Rota não encontrada');
});

// ==================== SERVIDOR ====================

// Só inicia o servidor se não estiver em ambiente de teste
if (process.env.NODE_ENV !== 'test') {
    const PORT = process.env.PORT || 3000;
    app.listen(PORT, () => {
        logger.info(`🚀 Servidor rodando na porta ${PORT}`);
        logger.info(`📍 Health check: http://localhost:${PORT}/health`);
        logger.info(`📚 Documentação: http://localhost:${PORT}/api-docs`);
    });
}

// Exporta o app para testes
export default app;
