"""
Configurações globais da aplicação
"""
import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:3000')
API_TIMEOUT = int(os.getenv('API_TIMEOUT', '10'))
API_AUTH_EMAIL = os.getenv('API_AUTH_EMAIL', '').strip()
API_AUTH_PASSWORD = os.getenv('API_AUTH_PASSWORD', '').strip()
OPERATOR_PASSWORD = os.getenv('OPERATOR_PASSWORD', '4321').strip()

# UI Configuration
THEME_MODE = os.getenv('THEME_MODE', 'light')
THEME_COLOR = os.getenv('THEME_COLOR', 'blue')

# Gêneros disponíveis
GENEROS = [
    (1, 'Aventura'),
    (2, 'Romance'),
    (3, 'Ficção Científica'),
    (4, 'Fantasia'),
    (5, 'Terror'),
    (6, 'Suspense'),
    (7, 'Mistério'),
    (8, 'Biografia'),
    (9, 'História'),
    (10, 'Autoajuda'),
    (11, 'Drama'),
    (12, 'Poesia'),
    (13, 'Humor'),
    (14, 'Infantil'),
    (15, 'Didático')
]

# Colors Theme
COLORS = {
    'primary': '#3C4C34',
    'secondary': '#6D7B74',
    'success': '#1E5128',
    'warning': '#B36A5E',
    'danger': '#8B2F2F',
    'info': '#5F8D96',
    'dark': '#000000',
    'light': '#FFFFFF'
}
