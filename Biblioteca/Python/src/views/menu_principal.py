"""
Menu Principal da Aplicação - Interface de navegação
"""

import customtkinter as ctk
from src.models.api_client import APIClient
from src.views.telas_melhoradas import (
    tela_consulta_por_nome_melhorada,
    tela_consulta_por_estado_melhorada,
    tela_consulta_livro_melhorada
)
from src.views.telas_cadastro_melhoradas import tela_cadastro_cliente_melhorada
from src.views.telas_reservas import tela_nova_reserva
from src.views.telas_multas import tela_menu_multas
from src.views.gui_components import limpar_frame


class MenuPrincipal(ctk.CTk):
    """Janela principal do sistema de biblioteca"""
    
    def __init__(self):
        super().__init__()
        
        # Configuração da janela
        self.title("📚 Sistema de Biblioteca")
        self.geometry("800x600")
        self.resizable(True, True)
        self.configure(fg_color="#0a0e27")
        
        # Client API
        self.api_client = APIClient()
        
        # Frame principal
        self.main_frame = ctk.CTkFrame(self, fg_color="#0a0e27")
        self.main_frame.pack(fill="both", expand=True)
        
        # Mostrar menu inicial
        self.mostrar_menu()
    
    def mostrar_menu(self):
        """Exibe o menu principal"""
        limpar_frame(self.main_frame)
        
        # Header
        header = ctk.CTkFrame(self.main_frame, fg_color="#131829", height=150)
        header.pack(fill="x", padx=0, pady=0)
        header.pack_propagate(False)
        
        titulo = ctk.CTkLabel(
            header,
            text="📚 SISTEMA DE BIBLIOTECA",
            font=("Arial Black", 32, "bold"),
            text_color="#6366f1"
        )
        titulo.pack(pady=30)
        
        subtitulo = ctk.CTkLabel(
            header,
            text="Gerenciamento de Livros e Clientes",
            font=("Arial", 14),
            text_color="#a5b4fc"
        )
        subtitulo.pack()
        
        # Container com botões
        container = ctk.CTkFrame(self.main_frame, fg_color="#0a0e27")
        container.pack(fill="both", expand=True, padx=30, pady=40)
        
        # Botões principais
        botoes = [
            ("👤 Consultar Cliente", self.submenu_clientes),
            ("📖 Consultar Livro", self.submenu_livros),
            ("📝 Cadastrar Cliente", lambda: tela_cadastro_cliente_melhorada(self.main_frame, self.api_client, self.mostrar_menu)),
            ("📚 Reservar Livro", lambda: tela_nova_reserva(self.main_frame, self.api_client, self.mostrar_menu)),
            ("💰 Gerenciar Multas", lambda: tela_menu_multas(self.main_frame, self.api_client, self.mostrar_menu)),
            ("❌ Sair", self.quit)
        ]
        
        for texto, comando in botoes:
            btn = ctk.CTkButton(
                container,
                text=texto,
                command=comando,
                font=("Arial", 16, "bold"),
                height=60,
                corner_radius=10,
                fg_color="#6366f1",
                hover_color="#818cf8"
            )
            btn.pack(fill="x", pady=12)
    
    def submenu_clientes(self):
        """Submenu para consultas de clientes"""
        limpar_frame(self.main_frame)
        
        # Header
        header = ctk.CTkFrame(self.main_frame, fg_color="#131829", height=100)
        header.pack(fill="x", padx=0, pady=0)
        header.pack_propagate(False)
        
        titulo = ctk.CTkLabel(
            header,
            text="👤 CONSULTAR CLIENTE",
            font=("Arial Black", 26, "bold"),
            text_color="#6366f1"
        )
        titulo.pack(pady=25)
        
        # Container
        container = ctk.CTkFrame(self.main_frame, fg_color="#0a0e27")
        container.pack(fill="both", expand=True, padx=30, pady=30)
        
        opcoes = [
            ("🔍 Por Nome", lambda: tela_consulta_por_nome_melhorada(self.main_frame, self.api_client, self.mostrar_menu)),
            ("🗺️ Por Estado", lambda: tela_consulta_por_estado_melhorada(self.main_frame, self.api_client, self.mostrar_menu)),
            ("⬅️ Voltar", self.mostrar_menu)
        ]
        
        for texto, comando in opcoes:
            btn = ctk.CTkButton(
                container,
                text=texto,
                command=comando,
                font=("Arial", 16, "bold"),
                height=50,
                corner_radius=8,
                fg_color="#6366f1" if "Voltar" not in texto else "#ef4444",
                hover_color="#818cf8" if "Voltar" not in texto else "#f87171"
            )
            btn.pack(fill="x", pady=10)
    
    def submenu_livros(self):
        """Submenu para consultas de livros"""
        limpar_frame(self.main_frame)
        
        # Header
        header = ctk.CTkFrame(self.main_frame, fg_color="#131829", height=100)
        header.pack(fill="x", padx=0, pady=0)
        header.pack_propagate(False)
        
        titulo = ctk.CTkLabel(
            header,
            text="📖 CONSULTAR LIVRO",
            font=("Arial Black", 26, "bold"),
            text_color="#6366f1"
        )
        titulo.pack(pady=25)
        
        # Container
        container = ctk.CTkFrame(self.main_frame, fg_color="#0a0e27")
        container.pack(fill="both", expand=True, padx=30, pady=30)
        
        opcoes = [
            ("🔍 Por Nome", lambda: tela_consulta_livro_melhorada(self.main_frame, self.api_client, self.mostrar_menu, "nome")),
            ("✍️ Por Autor", lambda: tela_consulta_livro_melhorada(self.main_frame, self.api_client, self.mostrar_menu, "autor")),
            ("🏷️ Por Gênero", lambda: tela_consulta_livro_melhorada(self.main_frame, self.api_client, self.mostrar_menu, "genero")),
            ("⬅️ Voltar", self.mostrar_menu)
        ]
        
        for texto, comando in opcoes:
            btn = ctk.CTkButton(
                container,
                text=texto,
                command=comando,
                font=("Arial", 16, "bold"),
                height=50,
                corner_radius=8,
                fg_color="#6366f1" if "Voltar" not in texto else "#ef4444",
                hover_color="#818cf8" if "Voltar" not in texto else "#f87171"
            )
            btn.pack(fill="x", pady=10)
