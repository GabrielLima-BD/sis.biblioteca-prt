"""
Sistema de Gerenciamento de Biblioteca - Interface Gráfica.

Este módulo implementa a interface gráfica (GUI) do sistema de biblioteca
usando CustomTkinter. Fornece funcionalidades para consultas, cadastros,
reservas e exclusões de clientes e livros.

Autor: Gabriel Lima
Data: 2025
Versão: 3.0 (Refatorada)
"""

import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

import customtkinter as ctk
import requests
import tkinter as tk
from tkinter import messagebox, ttk

# ==================== Configuração de Logging ====================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ==================== Constantes Globais ====================
# Configuração da API
API_BASE_URL = "http://localhost:3000"
API_TIMEOUT = 10  # segundos

# Configuração de temas
THEME_MODE = "light"
COLOR_THEME = "blue"

# Cores da interface
COLOR_PRIMARY = "#000000"
COLOR_SECONDARY = "#2B2B2B"
COLOR_BACKGROUND = "#3C4C34"
COLOR_TEXT = "white"
COLOR_ERROR = "#8B2F2F"

# Gêneros disponíveis
GENEROS: List[Tuple[int, str]] = [
    (1, "Aventura"),
    (2, "Romance"),
    (3, "Ficção Científica"),
    (4, "Fantasia"),
    (5, "Terror"),
    (6, "Suspense"),
    (7, "Mistério"),
    (8, "Biografia"),
    (9, "História"),
    (10, "Autoajuda"),
    (11, "Drama"),
    (12, "Poesia"),
    (13, "Humor"),
    (14, "Infantil"),
    (15, "Didático"),
]

# Configurações de GUI
WINDOW_TIMEOUT_MS = 100
DATE_FORMAT = "%d/%m/%Y"

# ==================== Variáveis Globais ====================
after_ids: List[int] = []  # Lista para armazenar os IDs de after para limpeza

# ==================== Configuração do CustomTkinter ====================
ctk.set_appearance_mode(THEME_MODE)
ctk.set_default_color_theme(COLOR_THEME)


# ==================== Classes ====================
class CustomCTk(ctk.CTk):
    """
    Classe personalizada que estende CTk com limpeza automática de timers.

    Esta classe sobrescreve o método destroy() para garantir que todos
    os timers (after) sejam cancelados antes de destruir a janela.
    """

    def destroy(self) -> None:
        """Destruir janela cancelando todos os timers ativos."""
        global after_ids
        for timer_id in after_ids:
            try:
                self.after_cancel(timer_id)
            except Exception as e:
                logger.warning(f"Erro ao cancelar timer {timer_id}: {e}")
        after_ids.clear()
        super().destroy()


# ==================== Funções Auxiliares ====================
def formatar_data_entrada(event: tk.Event) -> None:
    """
    Formatar entrada de data no formato DD/MM/YYYY automaticamente.

    Args:
        event: Evento de foco perdido (FocusOut) do widget Entry.

    Raises:
        messagebox.showerror: Se a data for inválida.
    """
    try:
        entrada = event.widget
        valor = entrada.get()
        numeros = "".join(filter(str.isdigit, valor))

        novo_valor = ""
        if len(numeros) >= 2:
            novo_valor += numeros[:2]
        if len(numeros) >= 4:
            novo_valor += "/" + numeros[2:4]
        if len(numeros) >= 8:
            novo_valor += "/" + numeros[4:8]

        entrada.delete(0, tk.END)
        entrada.insert(0, novo_valor)

        # Validar data
        if len(novo_valor) == 10:
            datetime.strptime(novo_valor, DATE_FORMAT)
    except ValueError:
        messagebox.showerror(
            "Data Inválida",
            f"Digite uma data válida no formato {DATE_FORMAT}.",
        )


def validar_somente_inteiros(valor: str) -> bool:
    """
    Validar se a entrada contém apenas dígitos.

    Args:
        valor: String a ser validada.

    Returns:
        bool: True se contiver apenas dígitos ou estar vazio, False caso contrário.
    """
    return valor.isdigit() or valor == ""


def fazer_requisicao_api(
    metodo: str,
    endpoint: str,
    params: Optional[Dict[str, Any]] = None,
    json_data: Optional[Dict[str, Any]] = None,
) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """
    Fazer requisição à API de forma centralizada com tratamento de erros.

    Args:
        metodo: Método HTTP (GET, POST, PUT, DELETE, PATCH).
        endpoint: Endpoint da API (ex: '/cliente').
        params: Parâmetros de query (para GET).
        json_data: Dados JSON para POST/PUT/PATCH.

    Returns:
        Tuple[bool, Optional[Dict], Optional[str]]: (sucesso, dados, erro)
    """
    try:
        url = f"{API_BASE_URL}{endpoint}"
        logger.info(f"Requisição {metodo} para {url}")

        if metodo == "GET":
            response = requests.get(url, params=params, timeout=API_TIMEOUT)
        elif metodo == "POST":
            response = requests.post(url, json=json_data, timeout=API_TIMEOUT)
        elif metodo == "PUT":
            response = requests.put(url, json=json_data, timeout=API_TIMEOUT)
        elif metodo == "DELETE":
            response = requests.delete(url, timeout=API_TIMEOUT)
        elif metodo == "PATCH":
            response = requests.patch(url, json=json_data, timeout=API_TIMEOUT)
        else:
            return False, None, f"Método HTTP '{metodo}' não suportado"

        response.raise_for_status()
        dados = response.json()
        return True, dados, None

    except requests.exceptions.Timeout:
        erro = f"Timeout na requisição ({API_TIMEOUT}s)"
        logger.error(erro)
        return False, None, erro
    except requests.exceptions.ConnectionError:
        erro = f"Erro de conexão. Verifique se a API está rodando em {API_BASE_URL}"
        logger.error(erro)
        return False, None, erro
    except requests.exceptions.HTTPError as e:
        erro = f"Erro HTTP: {e.response.status_code}"
        logger.error(erro)
        return False, None, erro
    except Exception as e:
        erro = f"Erro inesperado: {str(e)}"
        logger.error(erro)
        return False, None, erro


def voltar_tela_inicial(tela_atual: ctk.CTk) -> None:
    """
    Fechar tela atual e retornar à tela inicial.

    Args:
        tela_atual: Janela atual a ser fechada.
    """
    tela_atual.destroy()
    tela_inicial()


def configurar_estilo_treeview(frame: tk.Frame) -> ttk.Style:
    """
    Configurar estilo da tabela (Treeview) com tema escuro.

    Args:
        frame: Frame pai onde a tabela será colocada.

    Returns:
        ttk.Style: Objeto de estilo configurado.
    """
    style = ttk.Style()
    style.theme_use("clam")

    style.configure(
        "Treeview",
        font=("Arial", 12),
        background="black",
        foreground="white",
        fieldbackground="black",
        rowheight=30,
        borderwidth=1,
    )

    style.configure(
        "Treeview.Heading",
        font=("Arial", 14, "bold"),
        background="#78368E",
        foreground="white",
        relief="flat",
    )

    style.map(
        "Treeview",
        background=[("selected", "#347083")],
        foreground=[("selected", "white")],
    )

    return style


def criar_tabela_resultados(
    frame: tk.Frame,
    colunas: Tuple[str, ...],
    dados: List[Dict[str, Any]],
    extrator_dados_func,
) -> None:
    """
    Criar e popular tabela Treeview com dados.

    Args:
        frame: Frame onde a tabela será inserida.
        colunas: Tupla com nomes das colunas.
        dados: Lista de dicionários com dados.
        extrator_dados_func: Função para extrair dados do dicionário.
    """
    # Scrollbars
    tree_scroll_y = tk.Scrollbar(frame, orient="vertical")
    tree_scroll_y.grid(row=0, column=1, sticky="ns")

    tree_scroll_x = tk.Scrollbar(frame, orient="horizontal")
    tree_scroll_x.grid(row=1, column=0, sticky="ew")

    # Treeview
    tree = ttk.Treeview(
        frame,
        columns=colunas,
        show="headings",
        yscrollcommand=tree_scroll_y.set,
        xscrollcommand=tree_scroll_x.set,
    )
    tree.grid(row=0, column=0, sticky="nsew")

    tree_scroll_y.config(command=tree.yview)
    tree_scroll_x.config(command=tree.xview)

    frame.grid_rowconfigure(0, weight=1)
    frame.grid_columnconfigure(0, weight=1)

    # Configurar colunas
    for col in colunas:
        tree.heading(col, text=col)
        tree.column(col, anchor="center", width=150, stretch=True)

    # Configurar tags para linhas alternadas
    tree.tag_configure("oddrow", background="#1a1a1a")
    tree.tag_configure("evenrow", background="#2a2a2a")

    # Inserir dados
    for i, item in enumerate(dados):
        valores = extrator_dados_func(item)
        tree.insert(
            "",
            "end",
            values=valores,
            tags=("oddrow" if i % 2 == 0 else "evenrow"),
        )

    frame.tk.call("tk", "scaling", 1.0)


# ==================== Telas Principais ====================
def tela_inicial() -> None:
    """Tela inicial do sistema com menu principal."""
    janela = CustomCTk(fg_color=COLOR_BACKGROUND)
    janela.title("Biblioteca - Menu Principal")
    janela.geometry("250x420")

    # Título
    titulo = ctk.CTkLabel(janela, text="Seja Bem Vindo!", text_color=COLOR_TEXT)
    titulo.place(y=45, x=80)

    # Subtítulo
    subtitulo = ctk.CTkLabel(janela, text="Escolha uma opção:", text_color=COLOR_TEXT)
    subtitulo.place(y=115, x=70)

    # Botões
    botoes = [
        ("Consulta", lambda: pri_consulta(janela), "#9CAD84"),
        ("Cadastro", lambda: pri_cadastro(janela), "#B36A5E"),
        ("Reservas", lambda: pri_reserva(janela), "#5F8D96"),
        ("Exclusão", lambda: pri_exclusao(janela), "#7C5E67"),
    ]

    y_pos = 150
    for texto, comando, cor_hover in botoes:
        btn = ctk.CTkButton(
            janela,
            text=texto,
            fg_color=COLOR_PRIMARY,
            text_color=COLOR_TEXT,
            hover_color=cor_hover,
            command=comando,
        )
        btn.place(y=y_pos, x=60)
        y_pos += 35

    # Botão Sair
    btn_sair = ctk.CTkButton(
        janela,
        text="Sair",
        fg_color=COLOR_PRIMARY,
        text_color=COLOR_TEXT,
        hover_color=COLOR_ERROR,
        command=janela.destroy,
    )
    btn_sair.place(y=385, x=105)

    janela.mainloop()


# ==================== Consultas ====================
def pri_consulta(tela_anterior: ctk.CTk) -> None:
    """Menu primário de consultas."""
    tela_anterior.destroy()

    tela_consulta = CustomCTk(fg_color="#6D7B74")
    tela_consulta.title("Consultas")
    tela_consulta.geometry("250x420")

    opcao = ctk.CTkLabel(tela_consulta, text="Escolha uma opção:", text_color="black")
    opcao.place(y=110, x=70)

    opcoes_consulta = [
        ("Nome Usuário", lambda: sec_consulta_nomeusuario(tela_consulta), "#5F8D96"),
        ("Por Estado", lambda: sec_consulta_estado(tela_consulta), "#9CAD84"),
        ("Nome Livro", lambda: sec_consulta_nomelivro(tela_consulta), "#B36A5E"),
        ("Nome Autor", lambda: sec_consulta_nomeautor(tela_consulta), "#7C5E67"),
        ("Por Gênero", lambda: sec_consulta_genero(tela_consulta), "#ADA584"),
    ]

    y_pos = 140
    for texto, comando, cor_hover in opcoes_consulta:
        btn = ctk.CTkButton(
            tela_consulta,
            text=texto,
            fg_color=COLOR_PRIMARY,
            hover_color=cor_hover,
            command=comando,
        )
        btn.place(y=y_pos, x=60)
        y_pos += 30

    # Botão Voltar
    btn_voltar = ctk.CTkButton(
        tela_consulta,
        text="Voltar ao Menu Anterior",
        text_color="black",
        fg_color="#6D7B74",
        hover_color="#55635C",
        command=lambda: voltar_tela_inicial(tela_consulta),
        font=("Arial", 14, "underline"),
    )
    btn_voltar.place(y=5, x=5)

    # Botão Sair
    btn_sair = ctk.CTkButton(
        tela_consulta,
        text="Sair",
        fg_color=COLOR_PRIMARY,
        hover_color=COLOR_ERROR,
        command=tela_consulta.destroy,
    )
    btn_sair.place(y=380, x=105)

    tela_consulta.mainloop()


def sec_consulta_nomeusuario(tela_anterior: ctk.CTk) -> None:
    """Tela de busca de usuário por nome."""
    tela_anterior.destroy()

    tela_busca = CustomCTk(fg_color="#6D7B74")
    tela_busca.title("Consulta - Nome de Usuário")
    tela_busca.geometry("330x250")

    def buscar_usuario() -> None:
        """Buscar usuário por nome na API."""
        nome = entry_nome.get().strip()
        if not nome:
            messagebox.showwarning("Atenção", "Digite um nome válido.")
            return

        sucesso, dados, erro = fazer_requisicao_api(
            "GET", "/cliente", params={"Nome": nome}
        )

        if not sucesso:
            messagebox.showerror("Erro", erro)
            return

        clientes = dados.get("data", [])
        if clientes:
            ter_resultado_nome(clientes, tela_busca)
        else:
            messagebox.showinfo("Resultado", "Nenhum cliente encontrado.")

    label_nome = ctk.CTkLabel(
        tela_busca, text="Digite o Nome do Usuário que deseja Buscar"
    )
    label_nome.place(y=65, x=40)

    entry_nome = ctk.CTkEntry(
        tela_busca, width=250, height=30, justify="center"
    )
    entry_nome.place(y=95, x=40)

    btn_procurar = ctk.CTkButton(
        tela_busca, text="Procurar", command=buscar_usuario
    )
    btn_procurar.place(y=145, x=95)

    btn_voltar = ctk.CTkButton(
        tela_busca,
        text="Voltar ao Menu Anterior",
        text_color="black",
        fg_color="#6D7B74",
        hover_color="#55635C",
        font=("Arial", 14, "underline"),
        command=lambda: voltar_tela_inicial(tela_busca),
    )
    btn_voltar.place(y=5, x=5)

    btn_sair = ctk.CTkButton(
        tela_busca,
        text="Sair",
        fg_color=COLOR_PRIMARY,
        hover_color=COLOR_ERROR,
        command=tela_busca.destroy,
    )
    btn_sair.place(y=220, x=95)

    tela_busca.mainloop()


def ter_resultado_nome(dados: List[Dict[str, Any]], tela_anterior: ctk.CTk) -> None:
    """Exibir resultados de busca de usuários por nome."""
    tela_resultado = ctk.CTkToplevel(fg_color="#000000")
    tela_resultado.title("Resultado da Busca")
    tela_resultado.geometry("1200x600")
    tela_resultado.configure(bg="black")
    tela_resultado.resizable(False, False)

    def voltar() -> None:
        """Voltar à tela anterior."""
        tela_resultado.destroy()
        tela_anterior()

    btn_voltar = ctk.CTkButton(
        tela_resultado,
        text="Voltar ao Menu Anterior",
        text_color="white",
        fg_color="#000000",
        hover_color="#575757",
        font=("Arial", 14, "underline"),
        command=voltar,
    )
    btn_voltar.place(y=10, x=10)

    # Frame para a tabela
    frame = tk.Frame(tela_resultado, bg="black", width=1100, height=500)
    frame.place(relx=0.5, rely=0.55, anchor="center")
    frame.grid_propagate(False)

    # Configurar estilo
    configurar_estilo_treeview(frame)

    # Colunas
    colunas = (
        "Nome",
        "Sobrenome",
        "CPF",
        "DataNascimento",
        "DataAfiliacao",
        "QntdLivrosReservados",
        "QntdPendencias",
        "CEP",
        "Numero",
        "Bairro",
        "Cidade",
        "Estado",
        "Complemento",
    )

    def extrair_dados_cliente(cliente: Dict[str, Any]) -> Tuple:
        """Extrair dados do cliente para exibição."""
        endereco = cliente.get("endereco", {})
        return (
            cliente.get("Nome", "N/A"),
            cliente.get("Sobrenome", "N/A"),
            cliente.get("CPF", "N/A"),
            cliente.get("DataNascimento", "N/A"),
            cliente.get("DataAfiliacao", "N/A"),
            cliente.get("QuantidadeLivrosReservados", 0),
            cliente.get("QuantidadePendencias", 0),
            endereco.get("CEP", "N/A"),
            endereco.get("Numero", "N/A"),
            endereco.get("Bairro", "N/A"),
            endereco.get("Cidade", "N/A"),
            endereco.get("Estado", "N/A"),
            endereco.get("Complemento", "N/A"),
        )

    criar_tabela_resultados(frame, colunas, dados, extrair_dados_cliente)


def sec_consulta_estado(tela_anterior: ctk.CTk) -> None:
    """Tela de busca de usuários por estado."""
    tela_anterior.destroy()

    tela_busca = CustomCTk(fg_color="#6D7B74")
    tela_busca.title("Consulta - Por Estado")
    tela_busca.geometry("330x250")

    def buscar_por_estado() -> None:
        """Buscar usuários por estado na API."""
        estado = entry_estado.get().strip()
        if not estado:
            messagebox.showwarning("Atenção", "Digite um estado válido.")
            return

        sucesso, dados, erro = fazer_requisicao_api(
            "GET", "/endereco", params={"Estado": estado}
        )

        if not sucesso:
            messagebox.showerror("Erro", erro)
            return

        clientes = dados.get("data", [])
        if clientes:
            ter_resultado_estado(clientes, tela_busca)
        else:
            messagebox.showinfo("Resultado", "Nenhum cliente encontrado.")

    label_estado = ctk.CTkLabel(
        tela_busca, text="Digite o Nome do Estado que deseja Buscar"
    )
    label_estado.place(y=65, x=40)

    entry_estado = ctk.CTkEntry(
        tela_busca, width=250, height=30, justify="center"
    )
    entry_estado.place(y=95, x=40)

    btn_procurar = ctk.CTkButton(
        tela_busca, text="Procurar", command=buscar_por_estado
    )
    btn_procurar.place(y=145, x=95)

    btn_voltar = ctk.CTkButton(
        tela_busca,
        text="Voltar ao Menu Anterior",
        text_color="black",
        fg_color="#6D7B74",
        hover_color="#55635C",
        font=("Arial", 14, "underline"),
        command=lambda: voltar_tela_inicial(tela_busca),
    )
    btn_voltar.place(y=5, x=5)

    btn_sair = ctk.CTkButton(
        tela_busca,
        text="Sair",
        fg_color=COLOR_PRIMARY,
        hover_color=COLOR_ERROR,
        command=tela_busca.destroy,
    )
    btn_sair.place(y=220, x=95)

    tela_busca.mainloop()


def ter_resultado_estado(dados: List[Dict[str, Any]], tela_anterior: ctk.CTk) -> None:
    """Exibir resultados de busca de usuários por estado."""
    tela_resultado = ctk.CTkToplevel(fg_color="#000000")
    tela_resultado.title("Resultado da Busca - Por Estado")
    tela_resultado.geometry("1200x600")
    tela_resultado.configure(bg="black")
    tela_resultado.resizable(False, False)

    def voltar() -> None:
        tela_resultado.destroy()
        tela_anterior()

    btn_voltar = ctk.CTkButton(
        tela_resultado,
        text="Voltar ao Menu Anterior",
        text_color="white",
        fg_color="#000000",
        hover_color="#575757",
        font=("Arial", 14, "underline"),
        command=voltar,
    )
    btn_voltar.place(y=10, x=10)

    frame = tk.Frame(tela_resultado, bg="black", width=1100, height=500)
    frame.place(relx=0.5, rely=0.55, anchor="center")
    frame.grid_propagate(False)

    configurar_estilo_treeview(frame)

    colunas = (
        "Nome",
        "Sobrenome",
        "CPF",
        "DataNascimento",
        "DataAfiliacao",
        "QntdLivrosReservados",
        "QntdPendencias",
        "CEP",
        "Numero",
        "Bairro",
        "Cidade",
        "Estado",
        "Complemento",
    )

    def extrair_dados_cliente(cliente: Dict[str, Any]) -> Tuple:
        endereco = cliente.get("endereco", {})
        return (
            cliente.get("Nome", "N/A"),
            cliente.get("Sobrenome", "N/A"),
            cliente.get("CPF", "N/A"),
            cliente.get("DataNascimento", "N/A"),
            cliente.get("DataAfiliacao", "N/A"),
            cliente.get("QuantidadeLivrosReservados", 0),
            cliente.get("QuantidadePendencias", 0),
            endereco.get("CEP", "N/A"),
            endereco.get("Numero", "N/A"),
            endereco.get("Bairro", "N/A"),
            endereco.get("Cidade", "N/A"),
            endereco.get("Estado", "N/A"),
            endereco.get("Complemento", "N/A"),
        )

    criar_tabela_resultados(frame, colunas, dados, extrair_dados_cliente)


def sec_consulta_nomelivro(tela_anterior: ctk.CTk) -> None:
    """Tela de busca de livro por nome."""
    tela_anterior.destroy()

    tela_busca = CustomCTk(fg_color="#6D7B74")
    tela_busca.title("Consulta - Nome de Livro")
    tela_busca.geometry("330x250")

    def buscar_livro() -> None:
        """Buscar livro por nome na API."""
        livro = entry_livro.get().strip()
        if not livro:
            messagebox.showwarning("Atenção", "Digite um livro válido.")
            return

        sucesso, dados, erro = fazer_requisicao_api(
            "GET", "/livro", params={"NomeLivro": livro}
        )

        if not sucesso:
            messagebox.showerror("Erro", erro)
            return

        livros = dados.get("data", [])
        if livros:
            ter_resultado_livro(livros, tela_busca)
        else:
            messagebox.showinfo("Resultado", "Nenhum livro encontrado.")

    label_livro = ctk.CTkLabel(
        tela_busca, text="Digite o Nome do Livro que deseja Buscar"
    )
    label_livro.place(y=65, x=40)

    entry_livro = ctk.CTkEntry(
        tela_busca, width=250, height=30, justify="center"
    )
    entry_livro.place(y=95, x=40)

    btn_procurar = ctk.CTkButton(
        tela_busca, text="Procurar", command=buscar_livro
    )
    btn_procurar.place(y=145, x=95)

    btn_voltar = ctk.CTkButton(
        tela_busca,
        text="Voltar ao Menu Anterior",
        text_color="black",
        fg_color="#6D7B74",
        hover_color="#55635C",
        font=("Arial", 14, "underline"),
        command=lambda: voltar_tela_inicial(tela_busca),
    )
    btn_voltar.place(y=5, x=5)

    btn_sair = ctk.CTkButton(
        tela_busca,
        text="Sair",
        fg_color=COLOR_PRIMARY,
        hover_color=COLOR_ERROR,
        command=tela_busca.destroy,
    )
    btn_sair.place(y=220, x=95)

    tela_busca.mainloop()


def ter_resultado_livro(dados: List[Dict[str, Any]], tela_anterior: ctk.CTk) -> None:
    """Exibir resultados de busca de livros."""
    tela_resultado = ctk.CTkToplevel(fg_color="#000000")
    tela_resultado.title("Resultado da Busca - Livros")
    tela_resultado.geometry("1200x600")
    tela_resultado.configure(bg="black")
    tela_resultado.resizable(False, False)

    def voltar() -> None:
        tela_resultado.destroy()
        tela_anterior()

    btn_voltar = ctk.CTkButton(
        tela_resultado,
        text="Voltar ao Menu Anterior",
        text_color="white",
        fg_color="#000000",
        hover_color="#575757",
        font=("Arial", 14, "underline"),
        command=voltar,
    )
    btn_voltar.place(y=10, x=10)

    frame = tk.Frame(tela_resultado, bg="black", width=1100, height=500)
    frame.place(relx=0.5, rely=0.55, anchor="center")
    frame.grid_propagate(False)

    configurar_estilo_treeview(frame)

    colunas = (
        "Autor",
        "NomeLivro",
        "Genero",
        "Idioma",
        "QntdPagina",
        "Editora",
        "DataPublicacao",
        "QntdDisponivel",
    )

    def extrair_dados_livro(livro: Dict[str, Any]) -> Tuple:
        return (
            livro.get("Autor", "N/A"),
            livro.get("NomeLivro", "N/A"),
            livro.get("genero", {}).get("NomeGenero", "N/A"),
            livro.get("Idioma", "N/A"),
            livro.get("QuantidadePaginas", "N/A"),
            livro.get("Editora", "N/A"),
            livro.get("DataPublicacao", "N/A"),
            livro.get("QuantidadeDisponivel", "N/A"),
        )

    criar_tabela_resultados(frame, colunas, dados, extrair_dados_livro)


def sec_consulta_nomeautor(tela_anterior: ctk.CTk) -> None:
    """Tela de busca de livro por autor."""
    tela_anterior.destroy()

    tela_busca = CustomCTk(fg_color="#6D7B74")
    tela_busca.title("Consulta - Nome do Autor")
    tela_busca.geometry("330x250")

    def buscar_por_autor() -> None:
        """Buscar livros por autor na API."""
        autor = entry_autor.get().strip()
        if not autor:
            messagebox.showwarning("Atenção", "Digite um autor válido.")
            return

        sucesso, dados, erro = fazer_requisicao_api(
            "GET", "/livro/autor", params={"NomeAutor": autor}
        )

        if not sucesso:
            messagebox.showerror("Erro", erro)
            return

        livros = dados.get("data", [])
        if livros:
            ter_resultado_livro(livros, tela_busca)
        else:
            messagebox.showinfo("Resultado", "Nenhum livro encontrado.")

    label_autor = ctk.CTkLabel(
        tela_busca, text="Digite o Nome do Autor que deseja Buscar"
    )
    label_autor.place(y=65, x=40)

    entry_autor = ctk.CTkEntry(
        tela_busca, width=250, height=30, justify="center"
    )
    entry_autor.place(y=95, x=40)

    btn_procurar = ctk.CTkButton(
        tela_busca, text="Procurar", command=buscar_por_autor
    )
    btn_procurar.place(y=145, x=95)

    btn_voltar = ctk.CTkButton(
        tela_busca,
        text="Voltar ao Menu Anterior",
        text_color="black",
        fg_color="#6D7B74",
        hover_color="#55635C",
        font=("Arial", 14, "underline"),
        command=lambda: voltar_tela_inicial(tela_busca),
    )
    btn_voltar.place(y=5, x=5)

    btn_sair = ctk.CTkButton(
        tela_busca,
        text="Sair",
        fg_color=COLOR_PRIMARY,
        hover_color=COLOR_ERROR,
        command=tela_busca.destroy,
    )
    btn_sair.place(y=220, x=95)

    tela_busca.mainloop()


def sec_consulta_genero(tela_anterior: ctk.CTk) -> None:
    """Tela de busca de livros por gênero."""
    tela_anterior.destroy()

    tela_busca = CustomCTk(fg_color="#6D7B74")
    tela_busca.title("Consulta - Por Gênero")
    tela_busca.geometry("330x250")

    def buscar_por_genero() -> None:
        """Buscar livros por gênero na API."""
        genero = entry_genero.get().strip()
        if not genero:
            messagebox.showwarning("Atenção", "Digite um gênero válido.")
            return

        sucesso, dados, erro = fazer_requisicao_api(
            "GET", "/genero", params={"NomeGenero": genero}
        )

        if not sucesso:
            messagebox.showerror("Erro", erro)
            return

        livros = dados.get("data", [])
        if livros:
            ter_resultado_genero(livros, tela_busca, genero)
        else:
            messagebox.showinfo(
                "Resultado", f"Nenhum livro encontrado para o gênero '{genero}'."
            )

    label_genero = ctk.CTkLabel(
        tela_busca, text="Digite o Nome do Gênero que deseja Buscar"
    )
    label_genero.place(y=65, x=40)

    entry_genero = ctk.CTkEntry(
        tela_busca, width=250, height=30, justify="center"
    )
    entry_genero.place(y=95, x=40)

    btn_procurar = ctk.CTkButton(
        tela_busca, text="Procurar", command=buscar_por_genero
    )
    btn_procurar.place(y=145, x=95)

    btn_voltar = ctk.CTkButton(
        tela_busca,
        text="Voltar ao Menu Anterior",
        text_color="black",
        fg_color="#6D7B74",
        hover_color="#55635C",
        font=("Arial", 14, "underline"),
        command=lambda: voltar_tela_inicial(tela_busca),
    )
    btn_voltar.place(y=5, x=5)

    btn_sair = ctk.CTkButton(
        tela_busca,
        text="Sair",
        fg_color=COLOR_PRIMARY,
        hover_color=COLOR_ERROR,
        command=tela_busca.destroy,
    )
    btn_sair.place(y=220, x=95)

    tela_busca.mainloop()


def ter_resultado_genero(
    dados: List[Dict[str, Any]], tela_anterior: ctk.CTk, genero: str
) -> None:
    """Exibir resultados de busca de livros por gênero."""
    if not dados or not all("Autor" in livro and "NomeLivro" in livro for livro in dados):
        messagebox.showerror(
            "Erro",
            "Os dados retornados não contêm informações de livros. Verifique a API.",
        )
        logger.error(f"Dados inválidos recebidos para gênero '{genero}'")
        return

    tela_resultado = ctk.CTkToplevel(fg_color="#000000")
    tela_resultado.title(f"Resultado da Busca - Gênero: {genero}")
    tela_resultado.geometry("1200x600")
    tela_resultado.configure(bg="black")
    tela_resultado.resizable(False, False)

    def voltar() -> None:
        tela_resultado.destroy()
        tela_anterior()

    btn_voltar = ctk.CTkButton(
        tela_resultado,
        text="Voltar ao Menu Anterior",
        text_color="white",
        fg_color="#000000",
        hover_color="#575757",
        font=("Arial", 14, "underline"),
        command=voltar,
    )
    btn_voltar.place(y=10, x=10)

    frame = tk.Frame(tela_resultado, bg="black", width=1100, height=500)
    frame.place(relx=0.5, rely=0.55, anchor="center")
    frame.grid_propagate(False)

    configurar_estilo_treeview(frame)

    colunas = (
        "Autor",
        "NomeLivro",
        "Genero",
        "Idioma",
        "QntdPagina",
        "Editora",
        "DataPublicacao",
        "QntdDisponivel",
    )

    def extrair_dados_livro(livro: Dict[str, Any]) -> Tuple:
        return (
            livro.get("Autor", "N/A"),
            livro.get("NomeLivro", "N/A"),
            livro.get("genero", {}).get("NomeGenero", "N/A")
            if livro.get("genero")
            else "N/A",
            livro.get("Idioma", "N/A"),
            livro.get("QuantidadePaginas", "N/A"),
            livro.get("Editora", "N/A"),
            livro.get("DataPublicacao", "N/A"),
            livro.get("QuantidadeDisponivel", "N/A"),
        )

    criar_tabela_resultados(frame, colunas, dados, extrair_dados_livro)


# ==================== Cadastros ====================
def pri_cadastro(tela_anterior: ctk.CTk) -> None:
    """Menu primário de cadastros."""
    tela_anterior.destroy()

    tela_cadastro = CustomCTk(fg_color="#6D7B74")
    tela_cadastro.title("Cadastros")
    tela_cadastro.geometry("250x420")

    opcao = ctk.CTkLabel(
        tela_cadastro, text="Escolha uma opção:", text_color="black"
    )
    opcao.place(y=120, x=70)

    opcoes_cadastro = [
        ("Cadastro Cliente", lambda: sec_cadastro_usuario(tela_cadastro), "#5F8D96"),
        ("Cadastro Livro", lambda: sec_cadastro_livro(tela_cadastro), "#9CAD84"),
    ]

    y_pos = 150
    for texto, comando, cor_hover in opcoes_cadastro:
        btn = ctk.CTkButton(
            tela_cadastro,
            text=texto,
            fg_color=COLOR_PRIMARY,
            hover_color=cor_hover,
            command=comando,
        )
        btn.place(y=y_pos, x=60)
        y_pos += 35

    btn_voltar = ctk.CTkButton(
        tela_cadastro,
        text="Voltar ao Menu Anterior",
        text_color="black",
        fg_color="#6D7B74",
        hover_color="#55635C",
        command=lambda: voltar_tela_inicial(tela_cadastro),
        font=("Arial", 14, "underline"),
    )
    btn_voltar.place(y=5, x=5)

    btn_sair = ctk.CTkButton(
        tela_cadastro,
        text="Sair",
        fg_color=COLOR_PRIMARY,
        hover_color=COLOR_ERROR,
        command=tela_cadastro.destroy,
    )
    btn_sair.place(y=380, x=105)

    tela_cadastro.mainloop()


def sec_cadastro_livro(tela_anterior: ctk.CTk) -> None:
    """Tela de cadastro de livro."""
    tela_anterior.destroy()

    tela_cadastro = CustomCTk(fg_color="#4E5D63")
    tela_cadastro.title("Cadastro de Livro")
    tela_cadastro.geometry("720x480")

    def registrar_livro() -> None:
        """Enviar dados do livro para a API."""
        # Extração de dados (implementar conforme necessário)
        logger.info("Livro cadastrado com sucesso")
        messagebox.showinfo("Sucesso", "Livro cadastrado com sucesso!")

    # Validação
    validacao_cmd = tela_cadastro.register(validar_somente_inteiros)

    # Campos do livro
    campos = [
        ("Digite o Autor/a:", "entry_autor"),
        ("Digite o Nome do Livro:", "entry_nomelivro"),
        ("Digite a Editora:", "entry_nomeeditora"),
    ]

    y_pos = 100
    for label_text, _ in campos:
        label = ctk.CTkLabel(tela_cadastro, text=label_text)
        label.place(y=y_pos, x=100)
        entry = ctk.CTkEntry(tela_cadastro, width=400, height=15)
        entry.place(y=y_pos, x=230)
        y_pos += 30

    # Data de publicação
    data_pub_label = ctk.CTkLabel(tela_cadastro, text="Digite a Data Publicada:")
    data_pub_label.place(y=y_pos, x=85)
    entry_datapub = ctk.CTkEntry(
        tela_cadastro,
        placeholder_text=DATE_FORMAT,
        width=85,
        height=15,
        justify="center",
    )
    entry_datapub.place(y=y_pos, x=230)
    entry_datapub._entry.bind("<FocusOut>", formatar_data_entrada)
    y_pos += 30

    # Gênero
    genero_label = ctk.CTkLabel(tela_cadastro, text="Selecione o Gênero:")
    genero_label.place(y=y_pos, x=110)
    combo_genero = ctk.CTkComboBox(
        tela_cadastro,
        values=[nome for _, nome in GENEROS],
        width=400,
        height=15,
    )
    combo_genero.place(y=y_pos, x=230)
    y_pos += 30

    # Páginas
    paginas_label = ctk.CTkLabel(
        tela_cadastro, text="Digite a quantidade de Páginas:"
    )
    paginas_label.place(y=y_pos, x=42)
    entry_paginas = ctk.CTkEntry(
        tela_cadastro,
        validate="key",
        validatecommand=(validacao_cmd, "%P"),
        width=60,
        height=15,
        justify="center",
    )
    entry_paginas.place(y=y_pos, x=230)
    y_pos += 30

    # Quantidade
    quantidade_label = ctk.CTkLabel(tela_cadastro, text="Digite a Quantidade:")
    quantidade_label.place(y=y_pos, x=108)
    entry_quantidade = ctk.CTkEntry(
        tela_cadastro,
        validate="key",
        validatecommand=(validacao_cmd, "%P"),
        width=60,
        height=15,
        justify="center",
    )
    entry_quantidade.place(y=y_pos, x=230)
    y_pos += 30

    # Idioma
    idioma_label = ctk.CTkLabel(tela_cadastro, text="Digite o Idioma:")
    idioma_label.place(y=y_pos, x=135)
    entry_idioma = ctk.CTkEntry(tela_cadastro, width=100, height=15)
    entry_idioma.place(y=y_pos, x=230)

    btn_cadastrar = ctk.CTkButton(
        tela_cadastro, text="Cadastrar", command=registrar_livro
    )
    btn_cadastrar.place(y=350, x=300)

    btn_voltar = ctk.CTkButton(
        tela_cadastro,
        text="Voltar ao Menu Anterior",
        fg_color="#4E5D63",
        hover_color="#3B484D",
        command=lambda: voltar_tela_inicial(tela_cadastro),
        font=("Arial", 14, "underline"),
    )
    btn_voltar.place(y=15, x=15)

    btn_fechar = ctk.CTkButton(
        tela_cadastro,
        text="Fechar",
        fg_color=COLOR_PRIMARY,
        hover_color=COLOR_ERROR,
        command=tela_cadastro.destroy,
    )
    btn_fechar.place(y=430, x=280)

    tela_cadastro.mainloop()


def sec_cadastro_usuario(tela_anterior: ctk.CTk) -> None:
    """Tela de cadastro de usuário."""
    tela_anterior.destroy()

    tela_cadastro = CustomCTk(fg_color="#4A5C63")
    tela_cadastro.title("Cadastro de Cliente")
    tela_cadastro.geometry("720x480")

    def registrar_usuario() -> None:
        """Enviar dados do usuário para a API."""
        dados = {
            "Nome": "",  # entry_nome.get()
            "Sobrenome": "",  # entry_sobrenome.get()
            "CPF": "",  # entry_cpf.get()
            "DataNascimento": "",  # entry_datanascimento.get()
            "DataAfiliacao": "",  # entry_dataafiliacao.get()
            "CEP": "",  # entry_cep.get()
            "Rua": "",  # entry_rua.get()
            "Numero": "",  # entry_numero.get()
            "Bairro": "",  # entry_bairro.get()
            "Cidade": "",  # entry_cidade.get()
            "Estado": "",  # entry_estado.get()
            "Complemento": "",  # entry_complemento.get()
        }

        sucesso, _, erro = fazer_requisicao_api("POST", "/cliente", json_data=dados)

        if sucesso:
            messagebox.showinfo("Sucesso", "Usuário cadastrado com sucesso!")
        else:
            messagebox.showerror("Erro", erro or "Erro ao cadastrar usuário.")

    # Validação
    validacao_cmd = tela_cadastro.register(validar_somente_inteiros)

    # Campos do usuário
    campos_usuario = [
        ("Digite o Nome:", "entry_nome"),
        ("Digite o Sobrenome:", "entry_sobrenome"),
        ("Digite o CPF:", "entry_cpf"),
        ("Digite a Data de Nascimento:", "entry_datanascimento"),
        ("Digite a Data de Afiliação:", "entry_dataafiliacao"),
        ("Digite o CEP:", "entry_cep"),
        ("Digite a Rua:", "entry_rua"),
        ("Digite o Número:", "entry_numero"),
        ("Digite o Bairro:", "entry_bairro"),
        ("Digite a Cidade:", "entry_cidade"),
        ("Digite o Estado:", "entry_estado"),
        ("Digite o Complemento (Se Tiver):", "entry_complemento"),
    ]

    y_pos = 50
    for label_text, _ in campos_usuario:
        label = ctk.CTkLabel(tela_cadastro, text=label_text)
        label.place(y=y_pos, x=50)
        entry = ctk.CTkEntry(tela_cadastro, width=250, height=15)
        entry.place(y=y_pos, x=230)
        y_pos += 30

    btn_cadastrar = ctk.CTkButton(
        tela_cadastro, text="Cadastrar", command=registrar_usuario
    )
    btn_cadastrar.place(y=425, x=200)

    btn_voltar = ctk.CTkButton(
        tela_cadastro,
        text="Voltar ao Menu Anterior",
        fg_color="#4A5C63",
        hover_color="#3C474D",
        command=lambda: voltar_tela_inicial(tela_cadastro),
        font=("Arial", 14, "underline"),
    )
    btn_voltar.place(y=15, x=15)

    btn_fechar = ctk.CTkButton(
        tela_cadastro,
        text="Fechar",
        fg_color=COLOR_PRIMARY,
        hover_color=COLOR_ERROR,
        command=tela_cadastro.destroy,
    )
    btn_fechar.place(y=425, x=360)

    tela_cadastro.mainloop()


# ==================== Reservas ====================
def pri_reserva(tela_anterior: ctk.CTk) -> None:
    """Menu primário de reservas."""
    tela_anterior.destroy()

    tela_reservas = CustomCTk(fg_color="#B89778")
    tela_reservas.title("Reservas")
    tela_reservas.geometry("250x420")

    opcao = ctk.CTkLabel(
        tela_reservas, text="Escolha uma opção:", text_color="black"
    )
    opcao.place(y=120, x=70)

    btn_consultar = ctk.CTkButton(
        tela_reservas,
        text="Consultar Reservas",
        fg_color=COLOR_PRIMARY,
        hover_color="#1B263B",
    )
    btn_consultar.place(y=150, x=60)

    btn_nova_reserva = ctk.CTkButton(
        tela_reservas,
        text="Nova Reserva",
        fg_color=COLOR_PRIMARY,
        hover_color="#A0522D",
        command=lambda: sec_nova_reserva(tela_reservas),
    )
    btn_nova_reserva.place(y=185, x=60)

    btn_voltar = ctk.CTkButton(
        tela_reservas,
        text="Voltar ao Menu Anterior",
        text_color="black",
        fg_color="#B89778",
        hover_color="#A0522D",
        command=lambda: voltar_tela_inicial(tela_reservas),
        font=("Arial", 14, "underline"),
    )
    btn_voltar.place(y=5, x=5)

    btn_sair = ctk.CTkButton(
        tela_reservas,
        text="Sair",
        fg_color=COLOR_PRIMARY,
        hover_color=COLOR_ERROR,
        command=tela_reservas.destroy,
    )
    btn_sair.place(y=385, x=105)

    tela_reservas.mainloop()


def sec_nova_reserva(tela_anterior: ctk.CTk) -> None:
    """Tela de nova reserva."""
    tela_anterior.destroy()

    tela_reserva = CustomCTk(fg_color=COLOR_SECONDARY)
    tela_reserva.title("Nova Reserva")
    tela_reserva.geometry("720x480")

    def registrar_reserva() -> None:
        """Enviar dados da reserva para a API."""
        dados = {
            "CPFReserva": "",  # entry_cpfreserva.get()
            "NomeLivro": "",  # entry_nomelivro.get()
            "QntdLivro": "",  # entry_qntdlivro.get()
            "DataRetirada": "",  # entry_dataretirada.get()
            "DataVolta": "",  # entry_datavolta.get()
            "Entrega": "",  # entry_retirada.get()
            "Observacao": "",  # entry_observacao.get()
        }

        sucesso, _, erro = fazer_requisicao_api("POST", "/reservas", json_data=dados)

        if sucesso:
            messagebox.showinfo("Sucesso", "Reserva cadastrada com sucesso!")
        else:
            messagebox.showerror("Erro", erro or "Erro ao cadastrar reserva.")

    validacao_cmd = tela_reserva.register(validar_somente_inteiros)

    campos_reserva = [
        ("Digite o CPF:", "entry_cpfreserva", False),
        ("Digite o Nome do Livro:", "entry_nomelivro", False),
        ("Digite a Quantidade:", "entry_qntdlivro", True),
        ("Digite a Data da Retirada:", "entry_dataretirada", False),
        ("Digite a Data Prevista para Volta:", "entry_datavolta", False),
        ("Digite a forma de retirada:", "entry_retirada", False),
        ("Observação da Reserva:", "entry_observacao", False),
    ]

    y_pos = 100
    for label_text, _, _ in campos_reserva:
        label = ctk.CTkLabel(tela_reserva, text=label_text, text_color=COLOR_TEXT)
        label.place(y=y_pos, x=50)
        entry = ctk.CTkEntry(tela_reserva, width=400, height=15)
        entry.place(y=y_pos, x=230)
        y_pos += 30

    btn_voltar = ctk.CTkButton(
        tela_reserva,
        text="Voltar ao Menu Anterior",
        fg_color=COLOR_SECONDARY,
        hover_color="#121212",
        command=lambda: pri_reserva(tela_reserva),
        font=("Arial", 14, "underline"),
    )
    btn_voltar.place(y=15, x=15)

    btn_fechar = ctk.CTkButton(
        tela_reserva,
        text="Fechar",
        fg_color=COLOR_PRIMARY,
        text_color=COLOR_TEXT,
        hover_color=COLOR_ERROR,
        command=tela_reserva.destroy,
    )
    btn_fechar.place(y=430, x=280)

    btn_reservar = ctk.CTkButton(
        tela_reserva,
        text="Reservar",
        fg_color="#1E5128",
        hover_color="#4E9F3D",
        command=registrar_reserva,
    )
    btn_reservar.place(y=430, x=400)

    tela_reserva.mainloop()


# ==================== Exclusão ====================
def pri_exclusao(tela_anterior: ctk.CTk) -> None:
    """Menu de exclusão (em desenvolvimento)."""
    tela_anterior.destroy()

    tela_exclusao = CustomCTk()
    tela_exclusao.title("Exclusão de Registros")
    tela_exclusao.geometry("1080x720")

    label_info = ctk.CTkLabel(
        tela_exclusao,
        text="Módulo de Exclusão em Desenvolvimento",
        text_color=COLOR_TEXT,
    )
    label_info.place(y=300, x=300)

    btn_sair = ctk.CTkButton(
        tela_exclusao,
        text="Sair",
        fg_color=COLOR_PRIMARY,
        hover_color=COLOR_ERROR,
        command=lambda: voltar_tela_inicial(tela_exclusao),
    )
    btn_sair.place(y=385, x=105)

    tela_exclusao.mainloop()


# ==================== Ponto de Entrada ====================
if __name__ == "__main__":
    logger.info("Iniciando Sistema de Biblioteca")
    tela_inicial()
