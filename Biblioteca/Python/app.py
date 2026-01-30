"""Sistema de Gerenciamento de Biblioteca - Aplicação Principal.

Interface moderna e responsiva com tema dark profissional.
"""

import logging
import customtkinter as ctk
from tkinter import ttk, messagebox

from src.config.settings import API_BASE_URL, THEME_MODE, THEME_COLOR
from src.models.api_client import APIClient
from src.views.telas_consultas import (
    tela_consulta_por_nome,
    tela_consulta_por_estado,
    tela_consulta_livro,
)
from src.views.telas_cadastro import (
    tela_cadastro_cliente,
    tela_cadastro_livro,
)
from src.views.telas_reservas import (
    tela_nova_reserva,
    tela_listar_reservas,
    tela_devolucao_reserva,
    tela_consultar_reservas,
    tela_editar_reserva,
    tela_cancelar_reserva,
    tela_finalizar_reserva,
    tela_editar_cliente_da_reserva,
    tela_editar_livro_da_reserva
)
from src.views.telas_multas import tela_menu_multas

# ==================== Configuração ====================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class BibliotecaApp:
    """Aplicação principal com interface moderna."""

    def __init__(self):
        """Inicializar aplicação."""
        self.janela = ctk.CTk()
        self.janela.title("📚 Sistema de Biblioteca")
        self.janela.geometry("1000x700")
        self.janela.minsize(800, 600)
        
        self.api_client = APIClient(base_url=API_BASE_URL)
        
        # Configurar tema cores
        self.cores = {
            'bg_principal': '#0a0e27',
            'bg_secundario': '#131829',
            'accent': '#6366f1',
            'accent_hover': '#818cf8',
            'text': '#e0e7ff',
            'text_secundario': '#a5b4fc',
            'verde': '#10b981',
            'verde_hover': '#34d399',
            'vermelho': '#ef4444',
            'vermelho_hover': '#f87171',
        }
        
        self.janela.configure(fg_color=self.cores['bg_principal'])
        
        logger.info("✅ Aplicação inicializada")
        self.tela_inicial()

    def limpar_janela(self):
        """Limpar todos os widgets da janela."""
        for widget in self.janela.winfo_children():
            widget.destroy()

    def tela_inicial(self):
        """Tela inicial com menu principal."""
        self.limpar_janela()
        
        # Header
        header = ctk.CTkFrame(self.janela, fg_color=self.cores['bg_secundario'], height=120)
        header.pack(fill="x", padx=0, pady=0)
        header.pack_propagate(False)
        
        titulo = ctk.CTkLabel(
            header,
            text="📚 Sistema de Biblioteca",
            font=("Arial Black", 40, "bold"),
            text_color=self.cores['accent']
        )
        titulo.pack(pady=20)
        
        subtitulo = ctk.CTkLabel(
            header,
            text="Gerenciamento Moderno e Eficiente",
            font=("Arial", 14),
            text_color=self.cores['text_secundario']
        )
        subtitulo.pack()
        
        # Container de botões
        container = ctk.CTkFrame(self.janela, fg_color=self.cores['bg_principal'])
        container.pack(fill="both", expand=True, padx=40, pady=40)
        
        # Grid de botões (3x2)
        botoes = [
            ("🔍 CONSULTAS", self.menu_consultas, self.cores['accent'], self.cores['accent_hover']),
            ("➕ CADASTROS", self.menu_cadastros, self.cores['verde'], self.cores['verde_hover']),
            ("📚 RESERVAS", self.menu_reservas, self.cores['accent'], self.cores['accent_hover']),
            ("💰 MULTAS", self.menu_multas, "#f59e0b", "#fbbf24"),
            ("❌ SAIR", self.janela.destroy, self.cores['vermelho'], self.cores['vermelho_hover']),
        ]
        
        for idx, (texto, cmd, cor, cor_hover) in enumerate(botoes):
            linha = idx // 2
            coluna = idx % 2
            
            btn = ctk.CTkButton(
                container,
                text=texto,
                command=cmd,
                font=("Arial", 18, "bold"),
                fg_color=cor,
                hover_color=cor_hover,
                height=120,
                corner_radius=15,
                text_color="white"
            )
            btn.grid(row=linha, column=coluna, padx=20, pady=20, sticky="nsew")
        
        # Configurar grid para 3 linhas
        container.grid_rowconfigure(0, weight=1)
        container.grid_rowconfigure(1, weight=1)
        container.grid_rowconfigure(2, weight=1)
        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=1)

    def menu_consultas(self):
        """Menu de consultas."""
        self.limpar_janela()
        self._criar_menu_padrao(
            "🔍 CONSULTAS",
            [
                ("👤 Cliente por Nome", lambda: tela_consulta_por_nome(self.janela, self.api_client, self.menu_consultas)),
                ("🗺️ Clientes por Estado", lambda: tela_consulta_por_estado(self.janela, self.api_client, self.menu_consultas)),
                ("📖 Livro por Nome", lambda: tela_consulta_livro(self.janela, self.api_client, self.menu_consultas, tipo="nome")),
                ("✍️ Livros por Autor", lambda: tela_consulta_livro(self.janela, self.api_client, self.menu_consultas, tipo="autor")),
                ("🎭 Livros por Gênero", lambda: tela_consulta_livro(self.janela, self.api_client, self.menu_consultas, tipo="genero")),
            ]
        )

    def menu_cadastros(self):
        """Menu de cadastros."""
        self.limpar_janela()
        self._criar_menu_padrao(
            "➕ CADASTROS",
            [
                ("👤 Novo Cliente", lambda: tela_cadastro_cliente(self.janela, self.api_client, self.menu_cadastros)),
                ("📚 Novo Livro", lambda: tela_cadastro_livro(self.janela, self.api_client, self.menu_cadastros)),
                ("✏️ Atualizar Cliente (via Reserva)", lambda: tela_editar_cliente_da_reserva(self.janela, self.api_client, self.menu_cadastros)),
                ("✏️ Atualizar Livro (via Reserva)", lambda: tela_editar_livro_da_reserva(self.janela, self.api_client, self.menu_cadastros)),
            ]
        )

    def menu_reservas(self):
        """Menu de reservas."""
        self.limpar_janela()
        self._criar_menu_padrao(
            "📚 RESERVAS",
            [
                ("📅 Nova Reserva", lambda: tela_nova_reserva(self.janela, self.api_client, self.menu_reservas)),
                ("📋 Consultar Reservas", lambda: tela_consultar_reservas(self.janela, self.api_client, self.menu_reservas)),
                ("⚙️ Ajustar Reserva", lambda: tela_editar_reserva(self.janela, self.api_client, self.menu_reservas)),
                ("✅ Finalizar Reserva", lambda: tela_finalizar_reserva(self.janela, self.api_client, self.menu_reservas)),
                ("❌ Cancelar Reserva", lambda: tela_cancelar_reserva(self.janela, self.api_client, self.menu_reservas)),
                ("📦 Registrar Devolução", lambda: tela_devolucao_reserva(self.janela, self.api_client, self.menu_reservas)),
            ]
        )
    def menu_multas(self):
        """Menu de multas."""
        # Redireciona para o módulo de multas (já implementado)
        tela_menu_multas(self.janela, self.api_client, self.tela_inicial)

    def _criar_menu_padrao(self, titulo: str, opcoes: list):
        """Criar menu padrão com opções."""
        # Header com botão voltar
        header = ctk.CTkFrame(self.janela, fg_color=self.cores['bg_secundario'], height=100)
        header.pack(fill="x", padx=0, pady=0)
        header.pack_propagate(False)
        
        top_frame = ctk.CTkFrame(header, fg_color=self.cores['bg_secundario'])
        top_frame.pack(fill="x", padx=20, pady=10)
        
        btn_voltar = ctk.CTkButton(
            top_frame,
            text="⬅️ Voltar",
            command=self.tela_inicial,
            font=("Arial", 12),
            fg_color="transparent",
            hover_color=self.cores['accent_hover'],
            text_color=self.cores['accent'],
            width=100,
            height=35,
            corner_radius=8
        )
        btn_voltar.pack(side="left")
        
        titulo_label = ctk.CTkLabel(
            header,
            text=titulo,
            font=("Arial Black", 28, "bold"),
            text_color=self.cores['accent']
        )
        titulo_label.pack(fill="x", padx=20, pady=10)
        
        # Container de opções
        container = ctk.CTkFrame(self.janela, fg_color=self.cores['bg_principal'])
        container.pack(fill="both", expand=True, padx=40, pady=40)
        
        for idx, (texto, cmd) in enumerate(opcoes):
            btn = ctk.CTkButton(
                container,
                text=texto,
                command=cmd,
                font=("Arial", 16, "bold"),
                fg_color=self.cores['accent'],
                hover_color=self.cores['accent_hover'],
                height=60,
                corner_radius=10,
                text_color="white"
            )
            btn.pack(fill="x", pady=12)

    def mostrar_mensagem(self, titulo: str, mensagem: str, tipo: str = "info"):
        """Exibir mensagem simples via messagebox."""
        if tipo == "erro":
            messagebox.showerror(titulo, mensagem)
        elif tipo == "aviso":
            messagebox.showwarning(titulo, mensagem)
        else:
            messagebox.showinfo(titulo, mensagem)

    def executar(self):
        """Executar aplicação (loop principal)."""
        logger.info("🚀 Iniciando loop principal")
        self.janela.mainloop()


def main():
    """Função principal."""
    try:
        app = BibliotecaApp()
        app.executar()
    except KeyboardInterrupt:
        logger.info("⚠️ Aplicação interrompida pelo usuário")
    except Exception as e:
        logger.error(f"❌ Erro fatal: {e}")
        raise


if __name__ == "__main__":
    main()
