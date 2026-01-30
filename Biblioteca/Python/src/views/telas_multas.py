"""Telas de gerenciamento de multas com layout padronizado."""

from __future__ import annotations

import customtkinter as ctk
from typing import Any, Dict

from src.controllers.multas_controller import MultasController
from src.utils.validators import validar_cpf
from src.views.componentes import (
    TabelaResultados,
    criar_botoes_acao,
    criar_container_scroll,
    criar_container_simples,
    criar_frame_entrada,
    criar_frame_info,
    criar_header_padrao,
    criar_seletor_data,
    limpar_frame,
    mostrar_mensagem_padrao,
    solicitar_senha_operador,
)


def tela_menu_multas(janela: ctk.CTkFrame, api_client, callback_voltar) -> None:
    """Exibe menu principal do módulo de multas."""
    limpar_frame(janela)

    criar_header_padrao(janela, "Central de Multas", "💰", callback_voltar)
    container = criar_container_simples(janela)

    opcoes = [
        ("🔎 Consultar multas por CPF", lambda: tela_consultar_multas_por_cpf(janela, api_client, callback_voltar)),
        ("⏳ Multas pendentes", lambda: tela_listar_multas_pendentes(janela, api_client, callback_voltar)),
        ("➕ Registrar nova multa", lambda: tela_registrar_multa(janela, api_client, callback_voltar)),
        ("💸 Registrar pagamento", lambda: tela_registrar_pagamento(janela, api_client, callback_voltar)),
        ("⬅️ Voltar", callback_voltar),
    ]

    for texto, comando in opcoes:
        is_voltar = texto.startswith("⬅️")
        btn = ctk.CTkButton(
            container,
            text=texto,
            command=comando,
            font=("Segoe UI", 16, "bold"),
            height=55,
            corner_radius=10,
            fg_color="#4f46e5" if not is_voltar else "#ef4444",
            hover_color="#6366f1" if not is_voltar else "#f87171",
        )
        btn.pack(fill="x", pady=12)


def tela_consultar_multas_por_cpf(janela: ctk.CTkFrame, api_client, callback_voltar) -> None:
    """Tela para consulta detalhada de multas de um cliente."""
    limpar_frame(janela)

    controller = MultasController(api_client)

    criar_header_padrao(janela, "Consultar Multas", "🔎", lambda: tela_menu_multas(janela, api_client, callback_voltar))
    container = criar_container_scroll(janela)

    entry_cpf = criar_frame_entrada(container, "CPF do Cliente", "000.000.000-00")

    frame_status = ctk.CTkFrame(container, fg_color="transparent")
    frame_status.pack(fill="x", pady=(0, 20))

    label_status = ctk.CTkLabel(
        frame_status,
        text="Informe o CPF e clique em buscar.",
        font=("Segoe UI", 11),
        text_color="#a5b4fc",
        anchor="w",
    )
    label_status.pack(anchor="w", padx=14)

    frame_resultados = ctk.CTkFrame(container, fg_color="transparent")
    frame_resultados.pack(fill="both", expand=True)

    def renderizar_resultados(payload: Dict[str, Any]) -> None:
        limpar_frame(frame_resultados)

        cliente = payload.get("cliente", {})
        resumo = payload.get("resumo", {})
        multas = payload.get("multas", [])

        nome_cliente = f"{cliente.get('Nome', '')} {cliente.get('Sobrenome', '')}".strip() or "Cliente"

        frame_info_cliente = criar_frame_info(
            frame_resultados,
            f"Cliente: {nome_cliente} | CPF: {cliente.get('CPF', 'N/D')} | Multas registradas: {len(multas)}",
            icone="👤",
        )
        frame_info_cliente.configure(fg_color="#131829")

        frame_resumo = ctk.CTkFrame(frame_resultados, fg_color="#0f1937", corner_radius=12)
        frame_resumo.pack(fill="x", padx=10, pady=10)

        def criar_card(parent: ctk.CTkFrame, titulo: str, valor: str) -> None:
            card = ctk.CTkFrame(parent, fg_color="#131829", corner_radius=12)
            card.pack(side="left", expand=True, fill="x", padx=10, pady=10)

            ctk.CTkLabel(
                card,
                text=titulo,
                font=("Segoe UI", 12, "bold"),
                text_color="#a5b4fc",
            ).pack(anchor="w", padx=14, pady=(14, 6))

            ctk.CTkLabel(
                card,
                text=valor,
                font=("Segoe UI", 18, "bold"),
                text_color="#e0e7ff",
            ).pack(anchor="w", padx=14, pady=(0, 14))

        criar_card(frame_resumo, "Total em multas", resumo.get("total_formatado", "R$ 0,00"))
        criar_card(frame_resumo, "Total pendente", resumo.get("total_pendente_formatado", "R$ 0,00"))
        criar_card(frame_resumo, "Total pago", resumo.get("total_pago_formatado", "R$ 0,00"))
        criar_card(frame_resumo, "Multas vencidas", str(resumo.get("quantidade_vencidas", 0)))

        frame_lista = ctk.CTkFrame(frame_resultados, fg_color="transparent")
        frame_lista.pack(fill="both", expand=True, padx=10, pady=10)

        if not multas:
            ctk.CTkLabel(
                frame_lista,
                text="Nenhuma multa encontrada para os filtros informados.",
                font=("Segoe UI", 12),
                text_color="#a5b4fc",
            ).pack(pady=20)
        else:
            for multa in multas:
                card = ctk.CTkFrame(frame_lista, fg_color="#131829", corner_radius=12)
                card.pack(fill="x", padx=6, pady=6)

                header = ctk.CTkFrame(card, fg_color="transparent")
                header.pack(fill="x", padx=14, pady=(12, 6))

                ctk.CTkLabel(
                    header,
                    text=f"Multa #{multa.get('MultaID', multa.get('multa_id', ''))}",
                    font=("Segoe UI", 14, "bold"),
                    text_color="#e0e7ff",
                ).pack(side="left")

                ctk.CTkLabel(
                    header,
                    text=f"Status: {multa.get('Status', 'Desconhecido')}",
                    font=("Segoe UI", 12, "bold"),
                    text_color="#818cf8" if not multa.get('EmAtraso') else "#f97316",
                ).pack(side="right")

                corpo = ctk.CTkFrame(card, fg_color="transparent")
                corpo.pack(fill="x", padx=14, pady=(0, 12))

                linhas = [
                    f"Reserva: {multa.get('ReservaID', multa.get('reserva_id', 'N/D'))} | Livro: {multa.get('LivroNome', 'N/D')}",
                    f"Valor: {multa.get('ValorFormatado', 'R$ 0,00')} | Vencimento: {multa.get('DataVencimentoFormatada', 'N/D')}",
                    f"Pagamento: {multa.get('DataPagamentoFormatada', 'N/D')} | Dias em atraso: {multa.get('DiasEmAtraso', 0)}",
                ]

                for linha in linhas:
                    ctk.CTkLabel(
                        corpo,
                        text=linha,
                        font=("Segoe UI", 12),
                        text_color="#cbd5f5",
                        anchor="w",
                    ).pack(fill="x", pady=2)

            def abrir_tabela() -> None:
                colunas = [
                    {"key": "MultaID", "label": "ID"},
                    {"key": "ClienteNome", "label": "Cliente"},
                    {"key": "LivroNome", "label": "Livro"},
                    {"key": "ValorFormatado", "label": "Valor"},
                    {"key": "Status", "label": "Status"},
                    {"key": "DataVencimentoFormatada", "label": "Vencimento"},
                    {"key": "DataPagamentoFormatada", "label": "Pagamento"},
                    {"key": "DiasEmAtraso", "label": "Dias atraso"},
                ]
                TabelaResultados(multas, colunas, f"Multas de {nome_cliente}")

            ctk.CTkButton(
                frame_lista,
                text="📊 Ver em tabela",
                command=abrir_tabela,
                font=("Segoe UI", 13, "bold"),
                fg_color="#4f46e5",
                hover_color="#6366f1",
                height=42,
            ).pack(fill="x", padx=6, pady=(12, 6))

    def buscar_multas() -> None:
        cpf = entry_cpf.get().strip()
        if not cpf:
            mostrar_mensagem_padrao("Atenção", "Informe o CPF do cliente.", "aviso")
            return

        if not validar_cpf(cpf):
            mostrar_mensagem_padrao("Erro", "CPF inválido.", "erro")
            return

        label_status.configure(text="Buscando multas do cliente...", text_color="#a5b4fc")
        janela.update_idletasks()

        sucesso, payload, erro = controller.listar_multas_por_cpf(cpf)
        if sucesso:
            label_status.configure(
                text=f"Consulta realizada com sucesso. {len(payload.get('multas', []))} multas encontradas.",
                text_color="#10b981",
            )
            renderizar_resultados(payload)
        else:
            label_status.configure(text=erro or "Não foi possível concluir a consulta.", text_color="#f87171")
            limpar_frame(frame_resultados)

    btn_buscar = ctk.CTkButton(
        container,
        text="🔍 Buscar Multas",
        command=buscar_multas,
        font=("Segoe UI", 14, "bold"),
        fg_color="#4f46e5",
        hover_color="#6366f1",
        height=48,
    )
    btn_buscar.pack(fill="x", padx=10, pady=(0, 10))


def tela_listar_multas_pendentes(janela: ctk.CTkFrame, api_client, callback_voltar) -> None:
    """Lista multas pendentes com opção de destacar vencidas."""
    limpar_frame(janela)

    controller = MultasController(api_client)

    criar_header_padrao(janela, "Multas Pendentes", "⏳", lambda: tela_menu_multas(janela, api_client, callback_voltar))
    container = criar_container_simples(janela)

    switch_vencidas = ctk.CTkSwitch(
        container,
        text="Mostrar apenas multas vencidas",
        font=("Segoe UI", 12, "bold"),
        fg_color="#4f46e5",
        progress_color="#10b981",
    )
    switch_vencidas.pack(pady=(0, 14))

    frame_resumo = ctk.CTkFrame(container, fg_color="#131829", corner_radius=12)
    frame_resumo.pack(fill="x", padx=10, pady=10)

    label_resumo = ctk.CTkLabel(
        frame_resumo,
        text="Nenhuma consulta realizada.",
        font=("Segoe UI", 12),
        text_color="#a5b4fc",
        anchor="w",
    )
    label_resumo.pack(fill="x", padx=16, pady=12)

    def buscar_pendentes() -> None:
        apenas_vencidas = bool(switch_vencidas.get())
        sucesso, multas, erro = controller.listar_multas_pendentes(apenas_vencidas=apenas_vencidas)
        if not sucesso:
            mostrar_mensagem_padrao("Erro", erro or "Não foi possível carregar as multas.", "erro")
            label_resumo.configure(text="Erro ao carregar dados.", text_color="#f87171")
            return

        resumo = controller.calcular_resumo(multas)
        label_resumo.configure(
            text=(
                "Total: {total} | Pendentes: {pendentes} | Vencidas: {vencidas} | Pagas: {pagas}".format(
                    total=resumo.get("total_formatado", "R$ 0,00"),
                    pendentes=resumo.get("quantidade_pendentes", 0),
                    vencidas=resumo.get("quantidade_vencidas", 0),
                    pagas=resumo.get("quantidade_pagas", 0),
                )
            ),
            text_color="#a5b4fc",
        )

        if not multas:
            mostrar_mensagem_padrao("Aviso", "Nenhuma multa encontrada para os filtros.", "aviso")
            return

        colunas = [
            {"key": "MultaID", "label": "ID"},
            {"key": "ClienteNome", "label": "Cliente"},
            {"key": "LivroNome", "label": "Livro"},
            {"key": "ValorFormatado", "label": "Valor"},
            {"key": "Status", "label": "Status"},
            {"key": "DataVencimentoFormatada", "label": "Vencimento"},
            {"key": "DiasEmAtraso", "label": "Dias atraso"},
        ]
        titulo = "Multas vencidas" if apenas_vencidas else "Multas pendentes"
        TabelaResultados(multas, colunas, titulo)

    btn_buscar = ctk.CTkButton(
        container,
        text="🔍 Buscar Multas",
        command=buscar_pendentes,
        font=("Segoe UI", 14, "bold"),
        fg_color="#4f46e5",
        hover_color="#6366f1",
        height=48,
    )
    btn_buscar.pack(fill="x", pady=(10, 0))


def tela_registrar_multa(janela: ctk.CTkFrame, api_client, callback_voltar) -> None:
    """Tela para criação manual de multas."""
    limpar_frame(janela)

    controller = MultasController(api_client)

    criar_header_padrao(janela, "Registrar Multa", "➕", lambda: tela_menu_multas(janela, api_client, callback_voltar))
    container = criar_container_scroll(janela)

    entry_reserva_id = criar_frame_entrada(container, "ID da Reserva", "Ex.: 123")
    entry_valor = criar_frame_entrada(container, "Valor da Multa", "Ex.: 45,90")
    entry_vencimento = criar_seletor_data(container, "Data de Vencimento")

    instrucoes = criar_frame_info(
        container,
        "Informe os dados da multa. Será solicitada a senha do operador antes da confirmação.",
        icone="ℹ️",
    )
    instrucoes.configure(fg_color="#131829")

    def salvar_multa() -> None:
        if not solicitar_senha_operador():
            return

        try:
            reserva_id = int(entry_reserva_id.get().strip())
        except ValueError:
            mostrar_mensagem_padrao("Erro", "ID da reserva inválido.", "erro")
            return

        valor = entry_valor.get().strip()
        data_vencimento = entry_vencimento.get().strip()

        sucesso, mensagem = controller.registrar_multa(reserva_id, valor, data_vencimento)
        if sucesso:
            mostrar_mensagem_padrao("Sucesso", mensagem or "Multa registrada com sucesso.", "sucesso")
            tela_menu_multas(janela, api_client, callback_voltar)
        else:
            mostrar_mensagem_padrao("Erro", mensagem or "Não foi possível registrar a multa.", "erro")

    criar_botoes_acao(container, "Registrar Multa", salvar_multa, lambda: tela_menu_multas(janela, api_client, callback_voltar))


def tela_registrar_pagamento(janela: ctk.CTkFrame, api_client, callback_voltar) -> None:
    """Tela para quitação de multas."""
    limpar_frame(janela)

    controller = MultasController(api_client)

    criar_header_padrao(janela, "Registrar Pagamento", "💸", lambda: tela_menu_multas(janela, api_client, callback_voltar))
    container = criar_container_scroll(janela)

    entry_multa_id = criar_frame_entrada(container, "ID da Multa", "Ex.: 321")
    entry_data_pagamento = criar_seletor_data(container, "Data do Pagamento (opcional)")

    info_multa = criar_frame_info(
        container,
        "Busque a multa pelo ID para visualizar os detalhes antes de registrá-la como paga.",
        icone="ℹ️",
    )
    info_multa.configure(fg_color="#131829")

    frame_detalhes = ctk.CTkFrame(container, fg_color="transparent")
    frame_detalhes.pack(fill="x", padx=10, pady=10)

    def atualizar_detalhes(texto: str, cor: str = "#a5b4fc") -> None:
        limpar_frame(frame_detalhes)
        ctk.CTkLabel(
            frame_detalhes,
            text=texto,
            font=("Segoe UI", 12),
            text_color=cor,
            anchor="w",
        ).pack(fill="x", padx=6, pady=3)

    def buscar_multa() -> None:
        try:
            multa_id = int(entry_multa_id.get().strip())
        except ValueError:
            mostrar_mensagem_padrao("Erro", "Informe um ID de multa válido.", "erro")
            return

        sucesso, multa, erro = controller.obter_multa_por_id(multa_id)
        if not sucesso:
            mostrar_mensagem_padrao("Erro", erro or "Multa não encontrada.", "erro")
            atualizar_detalhes("Nenhuma multa carregada.", cor="#f87171")
            return

        detalhes = [
            f"Multa #{multa.get('MultaID', multa.get('multa_id'))}",
            f"Cliente: {multa.get('ClienteNome', 'N/D')}",
            f"Livro: {multa.get('LivroNome', 'N/D')}",
            f"Valor: {multa.get('ValorFormatado', 'R$ 0,00')}",
            f"Vencimento: {multa.get('DataVencimentoFormatada', 'N/D')}",
            f"Status atual: {multa.get('Status', 'Desconhecido')}",
        ]
        atualizar_detalhes("\n".join(detalhes), cor="#e0e7ff")

    def confirmar_pagamento() -> None:
        try:
            multa_id = int(entry_multa_id.get().strip())
        except ValueError:
            mostrar_mensagem_padrao("Erro", "Informe um ID de multa válido.", "erro")
            return

        if not solicitar_senha_operador():
            return

        data_pagamento = entry_data_pagamento.get().strip() or None
        sucesso, mensagem = controller.registrar_pagamento(multa_id, data_pagamento)
        if sucesso:
            mostrar_mensagem_padrao("Sucesso", mensagem or "Pagamento registrado com sucesso.", "sucesso")
            tela_menu_multas(janela, api_client, callback_voltar)
        else:
            mostrar_mensagem_padrao("Erro", mensagem or "Não foi possível registrar o pagamento.", "erro")

    botoes_extras = ctk.CTkFrame(container, fg_color="transparent")
    botoes_extras.pack(fill="x", padx=10, pady=10)

    ctk.CTkButton(
        botoes_extras,
        text="🔎 Buscar Multa",
        command=buscar_multa,
        font=("Segoe UI", 13, "bold"),
        fg_color="#4f46e5",
        hover_color="#6366f1",
        height=44,
    ).pack(side="left", expand=True, fill="x", padx=(0, 6))

    ctk.CTkButton(
        botoes_extras,
        text="💾 Registrar Pagamento",
        command=confirmar_pagamento,
        font=("Segoe UI", 13, "bold"),
        fg_color="#10b981",
        hover_color="#34d399",
        height=44,
    ).pack(side="right", expand=True, fill="x", padx=(6, 0))


__all__ = [
    "tela_menu_multas",
    "tela_consultar_multas_por_cpf",
    "tela_listar_multas_pendentes",
    "tela_registrar_multa",
    "tela_registrar_pagamento",
]
