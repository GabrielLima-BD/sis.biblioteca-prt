"""Views (camada de apresentação).

Este pacote exporta apenas a interface "melhorada" (GUI atual).
"""

from .componentes import TabelaResultados, criar_frame_entrada, mostrar_mensagem_padrao

from .telas_consultas import (
    tela_consulta_por_nome,
    tela_consulta_por_estado,
    tela_consulta_livro,
)

from .telas_cadastro import tela_cadastro_cliente
from .telas_reservas import tela_nova_reserva
from .telas_multas import (
    tela_menu_multas,
    tela_consultar_multas_por_cpf,
    tela_listar_multas_pendentes,
    tela_registrar_multa,
    tela_registrar_pagamento,
)

__all__ = [
    # Componentes Melhorados
    "TabelaResultados",
    "criar_frame_entrada",
    "mostrar_mensagem_padrao",
    # Telas (Consultas)
    "tela_consulta_por_nome",
    "tela_consulta_por_estado",
    "tela_consulta_livro",
    # Cadastro e Reserva
    "tela_cadastro_cliente",
    "tela_nova_reserva",
    # Multas
    "tela_menu_multas",
    "tela_consultar_multas_por_cpf",
    "tela_listar_multas_pendentes",
    "tela_registrar_multa",
    "tela_registrar_pagamento",
    
]
