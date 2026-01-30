"""
Componentes e helpers para construção da interface gráfica.

Este módulo fornece funções reutilizáveis para criar e estilizar
componentes da GUI.
"""

import logging
from typing import List, Dict, Any, Callable, Optional
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk

logger = logging.getLogger(__name__)


def criar_frame_container(
    parent: ctk.CTk,
    fg_color: str = "#3C4C34"
) -> ctk.CTkFrame:
    """
    Criar frame container principal.

    Args:
        parent: Widget pai
        fg_color: Cor de fundo

    Returns:
        Frame configurado
    """
    frame = ctk.CTkFrame(master=parent, fg_color=fg_color)
    frame.pack(fill="both", expand=True)
    return frame


def criar_label_titulo(
    parent: ctk.CTkFrame,
    texto: str,
    font_size: int = 50
) -> ctk.CTkLabel:
    """
    Criar label de título.

    Args:
        parent: Frame pai
        texto: Texto do título
        font_size: Tamanho da fonte

    Returns:
        Label configurado
    """
    label = ctk.CTkLabel(
        master=parent,
        text=texto,
        font=("Arial Black", font_size),
        text_color="white"
    )
    label.pack(padx=30, pady=30)
    return label


def criar_botao_padrao(
    parent: ctk.CTkFrame,
    texto: str,
    comando: Callable,
    width: int = 200,
    height: int = 60,
    font_size: int = 20,
    fg_color: str = "#000000",
    hover_color: str = "#2B2B2B"
) -> ctk.CTkButton:
    """
    Criar botão padrão da interface.

    Args:
        parent: Frame pai
        texto: Texto do botão
        comando: Função a executar no clique
        width: Largura do botão
        height: Altura do botão
        font_size: Tamanho da fonte
        fg_color: Cor de fundo
        hover_color: Cor ao passar o mouse

    Returns:
        Botão configurado
    """
    botao = ctk.CTkButton(
        master=parent,
        text=texto,
        command=comando,
        width=width,
        height=height,
        font=("Arial", font_size),
        fg_color=fg_color,
        hover_color=hover_color,
        text_color="white",
        corner_radius=10
    )
    botao.pack(padx=10, pady=10)
    return botao


def criar_entry_com_label(
    parent: ctk.CTkFrame,
    texto_label: str,
    placeholder: str = "",
    width: int = 300
) -> tuple[ctk.CTkLabel, ctk.CTkEntry]:
    """
    Criar campo de entrada com label.

    Args:
        parent: Frame pai
        texto_label: Texto do label
        placeholder: Texto placeholder do entry
        width: Largura do entry

    Returns:
        Tupla (label, entry)
    """
    label = ctk.CTkLabel(
        master=parent,
        text=texto_label,
        font=("Arial", 16),
        text_color="white"
    )
    label.pack(padx=10, pady=(10, 5))

    entry = ctk.CTkEntry(
        master=parent,
        placeholder_text=placeholder,
        width=width,
        font=("Arial", 14)
    )
    entry.pack(padx=10, pady=(0, 10))

    return label, entry


def criar_tabela_resultados(
    parent: tk.Frame,
    colunas: List[str],
    dados: List[Dict[str, Any]]
) -> ttk.Treeview:
    """
    Criar tabela (Treeview) com resultados.

    Args:
        parent: Frame pai
        colunas: Lista de nomes das colunas
        dados: Lista de dicionários com dados

    Returns:
        Treeview configurado com dados
    """
    # Criar Treeview
    tree = ttk.Treeview(parent, columns=colunas, show="headings", height=15)

    # Configurar cabeçalhos
    for coluna in colunas:
        tree.heading(coluna, text=coluna)
        tree.column(coluna, width=150, anchor="center")

    # Configurar estilo
    configurar_estilo_treeview()

    # Inserir dados
    for item in dados:
        valores = [item.get(col, "") for col in colunas]
        tree.insert("", "end", values=valores)

    # Scrollbar
    scrollbar = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)

    tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    logger.info(f"Tabela criada com {len(dados)} registros")
    return tree


def configurar_estilo_treeview() -> None:
    """Configurar estilo global do Treeview."""
    style = ttk.Style()
    style.theme_use("clam")

    style.configure(
        "Treeview",
        background="#2B2B2B",
        foreground="white",
        rowheight=25,
        fieldbackground="#2B2B2B",
        bordercolor="#3C4C34",
        borderwidth=2
    )

    style.configure(
        "Treeview.Heading",
        background="#000000",
        foreground="white",
        relief="flat",
        font=("Arial", 12, "bold")
    )

    style.map(
        "Treeview",
        background=[("selected", "#3C4C34")],
        foreground=[("selected", "white")]
    )


def criar_combobox(
    parent: ctk.CTkFrame,
    texto_label: str,
    valores: List[str],
    width: int = 300
) -> tuple[ctk.CTkLabel, ctk.CTkComboBox]:
    """
    Criar combobox com label.

    Args:
        parent: Frame pai
        texto_label: Texto do label
        valores: Lista de valores para o combobox
        width: Largura do combobox

    Returns:
        Tupla (label, combobox)
    """
    label = ctk.CTkLabel(
        master=parent,
        text=texto_label,
        font=("Arial", 16),
        text_color="white"
    )
    label.pack(padx=10, pady=(10, 5))

    combobox = ctk.CTkComboBox(
        master=parent,
        values=valores,
        width=width,
        font=("Arial", 14)
    )
    combobox.pack(padx=10, pady=(0, 10))

    return label, combobox


def limpar_frame(frame: ctk.CTkFrame) -> None:
    """
    Limpar todos os widgets de um frame.

    Args:
        frame: Frame a ser limpo
    """
    for widget in frame.winfo_children():
        widget.destroy()
    logger.debug("Frame limpo")


def mostrar_mensagem_erro(titulo: str, mensagem: str) -> None:
    """
    Mostrar mensagem de erro.

    Args:
        titulo: Título da janela de erro
        mensagem: Mensagem de erro
    """
    from tkinter import messagebox
    messagebox.showerror(titulo, mensagem)
    logger.error(f"{titulo}: {mensagem}")


def mostrar_mensagem_sucesso(titulo: str, mensagem: str) -> None:
    """
    Mostrar mensagem de sucesso.

    Args:
        titulo: Título da janela
        mensagem: Mensagem de sucesso
    """
    from tkinter import messagebox
    messagebox.showinfo(titulo, mensagem)
    logger.info(f"{titulo}: {mensagem}")


def mostrar_mensagem_aviso(titulo: str, mensagem: str) -> None:
    """
    Mostrar mensagem de aviso.

    Args:
        titulo: Título da janela
        mensagem: Mensagem de aviso
    """
    from tkinter import messagebox
    messagebox.showwarning(titulo, mensagem)
    logger.warning(f"{titulo}: {mensagem}")
