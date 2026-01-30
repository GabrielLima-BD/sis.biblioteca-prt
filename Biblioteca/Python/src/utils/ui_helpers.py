"""
Helpers para construção de interfaces gráficas
"""
import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
from typing import List, Dict, Any, Callable


def criar_treeview_customizado(parent: tk.Widget, colunas: List[str], 
                               dados: List[Dict[str, Any]]) -> ttk.Treeview:
    """
    Cria uma Treeview customizada com estilos
    
    Args:
        parent: Widget pai
        colunas: Lista de nomes das colunas
        dados: Lista de dicionários com os dados
    
    Returns:
        ttk.Treeview: Widget Treeview customizado
    """
    frame = tk.Frame(parent, bg='black', width=1100, height=500)
    frame.place(relx=0.5, rely=0.55, anchor='center')
    frame.grid_propagate(False)
    
    # Configurar estilo
    style = ttk.Style()
    style.theme_use('clam')
    
    style.configure('Treeview',
                    font=('Arial', 12),
                    background='black',
                    foreground='white',
                    fieldbackground='black',
                    rowheight=30,
                    borderwidth=1)
    
    style.configure('Treeview.Heading',
                    font=('Arial', 14, 'bold'),
                    background='#78368E',
                    foreground='white',
                    relief='flat')
    
    style.map('Treeview',
              background=[('selected', '#347083')],
              foreground=[('selected', 'white')])
    
    # Scrollbars
    tree_scroll_y = tk.Scrollbar(frame, orient='vertical')
    tree_scroll_y.grid(row=0, column=1, sticky='ns')
    
    tree_scroll_x = tk.Scrollbar(frame, orient='horizontal')
    tree_scroll_x.grid(row=1, column=0, sticky='ew')
    
    # Treeview
    tree = ttk.Treeview(
        frame,
        columns=colunas,
        show='headings',
        yscrollcommand=tree_scroll_y.set,
        xscrollcommand=tree_scroll_x.set
    )
    tree.grid(row=0, column=0, sticky='nsew')
    
    tree_scroll_y.config(command=tree.yview)
    tree_scroll_x.config(command=tree.xview)
    
    frame.grid_rowconfigure(0, weight=1)
    frame.grid_columnconfigure(0, weight=1)
    
    # Configurar colunas
    for col in colunas:
        tree.heading(col, text=col)
        tree.column(col, anchor='center', width=150, stretch=True)
    
    tree.tag_configure('oddrow', background='#1a1a1a')
    tree.tag_configure('evenrow', background='#2a2a2a')
    
    # Inserir dados
    for i, linha in enumerate(dados):
        valores = tuple(linha.get(col, 'N/A') for col in colunas)
        tree.insert('', 'end', values=valores, 
                   tags=('oddrow' if i % 2 == 0 else 'evenrow'))
    
    return tree


def criar_botao_voltar(parent: ctk.CTk, comando: Callable) -> ctk.CTkButton:
    """
    Cria um botão padrão para voltar ao menu anterior
    
    Args:
        parent: Widget pai
        comando: Função a executar ao clicar
    
    Returns:
        ctk.CTkButton: Botão configurado
    """
    return ctk.CTkButton(
        parent,
        text='Voltar ao Menu Anterior',
        text_color='black',
        fg_color='#6D7B74',
        hover_color='#55635C',
        font=('Arial', 14, 'underline'),
        command=comando
    )


def criar_botao_sair(parent: ctk.CTk) -> ctk.CTkButton:
    """
    Cria um botão padrão para sair
    
    Args:
        parent: Widget pai
    
    Returns:
        ctk.CTkButton: Botão configurado
    """
    return ctk.CTkButton(
        parent,
        text='Sair',
        fg_color='black',
        text_color='white',
        hover_color='#8B2F2F',
        command=parent.destroy
    )
