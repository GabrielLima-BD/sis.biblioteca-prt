"""Verificar variáveis de ambiente da aplicação Python (debug).

Imprime credenciais/configs lidas de `Biblioteca/Python/src/config/settings.py`.

Uso:
	python verificar_ambiente.py
"""

import sys
sys.path.append('Biblioteca/Python')
from src.config.settings import API_AUTH_EMAIL, API_AUTH_PASSWORD
print(API_AUTH_EMAIL)
print(API_AUTH_PASSWORD)
