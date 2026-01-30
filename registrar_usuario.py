"""Registrar usuário na API (utilitário).

Dispara um POST em `http://localhost:3000/auth/register`.

Pré-requisito:
- API rodando (node Biblioteca/API/server.js)

Uso:
    python registrar_usuario.py
"""

import requests

payload = {
    "email": "gerenciabiblioteca@hotmail.com",
    "senha": "gerenciabiblioteca",
    "nome": "Gerente Biblioteca"
}

resp = requests.post("http://localhost:3000/auth/register", json=payload, timeout=10)
print(resp.status_code)
print(resp.text)
