"""Módulo de controllers - lógica de negócio."""

from .consulta_controller import ConsultaController
from .cadastro_controller import CadastroController
from .multas_controller import MultasController

__all__ = [
    "ConsultaController",
    "CadastroController",
    "MultasController",
]
