"""Verificar tokens carregados pelo cliente da API (debug).

Este script é uma ferramenta rápida para inspecionar os tokens atuais
mantidos pelo `APIClient` da aplicação Python.

Uso:
	python verificar_token.py
"""

import sys
sys.path.append('Biblioteca/Python')
from src.models.api_client import APIClient

client = APIClient()
print('Access token:', client._access_token)
print('Refresh token:', client._refresh_token)
print('Auth header:', client.session.headers.get('Authorization'))
