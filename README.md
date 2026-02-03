# sis.biblioteca-prt

Sistema de Biblioteca com **API REST (Node.js/Express)** + **aplicativo desktop (Python/CustomTkinter)** integrado ao **Supabase (Postgres)**.

A ideia do projeto é centralizar as regras/validações na API e consumir isso pela interface gráfica, mantendo o uso do banco de dados no Supabase.

---

## O que tem neste projeto

- **API (Node.js + Express)** em `Biblioteca/API`
  - Integração com Supabase
  - Endpoints para clientes, livros, endereços, gêneros, reservas e multas
  - Segurança básica (Helmet), CORS e rate limiting
  - Swagger em `/api-docs`
  - Health-check em `/health`

- **App Desktop (Python + CustomTkinter)** em `Biblioteca/Python`
  - Telas de cadastro/consulta/reservas/multas
  - Comunicação com a API via HTTP (`requests`)
  - Carrega dados como **gêneros direto do banco** via API (evita gêneros “inventados”)

- **Scripts auxiliares** na raiz
  - `executar_tudo.py` / `executar_tudo.bat`: sobem API + App juntos (modo local)
  - `verificar_ambiente.py`: checagens rápidas de ambiente
  - `verificar_token.py` / `registrar_usuario.py`: utilitários (se aplicável ao seu cenário)

---

## Estrutura de pastas (resumo)

- `Biblioteca/API/`
  - `server.js` (servidor Express)
  - `auth/`, `middleware/`, `utils/`
  - `.env.example` (modelo de variáveis)

- `Biblioteca/Python/`
  - `app.py` (GUI)
  - `main.py` (entrypoint alternativo)
  - `src/` (código modularizado: controllers/models/views/utils)
  - `.env.example` (modelo de variáveis)

---

## Requisitos

### Para rodar localmente (recomendado)
- **Node.js 18+** e **npm 9+**
- **Python 3.11+**

### Banco de dados
- Um projeto no **Supabase** com as tabelas esperadas (clientes, livros, gênero, reservas, multa, etc.).

---

## Configuração de ambiente

### 1) API (Node)

Arquivo: `Biblioteca/API/.env` (crie a partir do `.env.example`)

Exemplo (modelo):

- `SUPABASE_URL=...`
- `SUPABASE_KEY=...`
- `PORT=3000`

> Importante: **não suba seu `.env` com chave real para o GitHub**. O repositório já ignora `.env`.

### 2) App Python

Arquivo: `Biblioteca/Python/.env` (crie a partir do `.env.example`)

Campos principais:
- `API_BASE_URL=http://localhost:3000`
- `API_TIMEOUT=10`
- `OPERATOR_PASSWORD=4321` (senha solicitada em ações sensíveis no app)

---

## Como rodar (modo local)

### Opção A (mais simples): iniciar tudo pelo script

Na raiz do projeto:

- Windows (Python):
  - `python executar_tudo.py`

Ou (Windows bat):
- `executar_tudo.bat`

Esse fluxo:
1. Sobe a API (`node server.js` em `Biblioteca/API`)
2. Aguarda `/health` responder
3. Abre o App Python (`Biblioteca/Python/app.py`)

### Opção B: rodar API e App separadamente

#### 1) Subir a API

Em `Biblioteca/API`:

1. `npm install`
2. `npm run dev` (ou `npm start`)

A API fica em:
- `http://localhost:3000`

Endpoints úteis:
- `GET /health`
- `GET /api-docs`

#### 2) Rodar o App Python

Em `Biblioteca/Python`:

1. (Opcional mas recomendado) criar venv:
   - `python -m venv .venv`
   - `./.venv/Scripts/activate`
2. Instalar dependências:
   - `pip install -r requirements.txt`
3. Rodar:
   - `python main.py`
   - ou `python run.py`
   - ou `python app.py`

---

## Docker (API)

O `docker-compose.yml` deste repositório foi simplificado para subir **somente a API**.

Pré-requisito: ter `SUPABASE_URL` e `SUPABASE_KEY` definidos no seu ambiente (ou em um arquivo `.env` local que você exporte).

Na raiz:
- `docker compose up --build`

A API sobe em `http://localhost:3000`.

> Observação: o app Python é uma GUI desktop; rodar GUI dentro de container normalmente exige configuração de display (não recomendado como padrão).

---

## Notas importantes

- Este repositório **não versiona** arquivos sensíveis (`.env`) nem artefatos gerados (logs/coverage/cache).
- Se algo “sumir” do GitHub (ex.: logs/resultados), é esperado: esses arquivos são gerados em runtime e não fazem parte do código-fonte.

---

## Troubleshooting rápido

- API não sobe e sai na hora:
  - verifique se `SUPABASE_URL` e `SUPABASE_KEY` estão configurados no `Biblioteca/API/.env`.

- App abre, mas não carrega dados:
  - confirme se a API está rodando em `API_BASE_URL` (por padrão `http://localhost:3000`).

- Porta 3000 em uso:
  - altere `PORT` no `.env` da API e ajuste `API_BASE_URL` no `.env` do Python.
