"""
Telas de consulta melhoradas com interface moderna.
"""

import customtkinter as ctk
from src.views.componentes import (
    TabelaResultados,
    criar_frame_entrada,
    mostrar_mensagem_padrao,
)


def tela_consulta_por_nome(janela: ctk.CTkFrame, api_client, callback_voltar):
    """Tela de consulta de cliente por nome."""
    
    # Limpar frame
    for widget in janela.winfo_children():
        widget.destroy()
    
    janela.configure(fg_color="#0a0e27")
    
    # Header
    header = ctk.CTkFrame(janela, fg_color="#131829", height=100)
    header.pack(fill="x")
    header.pack_propagate(False)
    
    titulo = ctk.CTkLabel(
        header,
        text="👤 Consultar Cliente por Nome",
        font=("Arial Black", 22, "bold"),
        text_color="#6366f1"
    )
    titulo.pack(pady=20)
    
    # Container principal
    container = ctk.CTkFrame(janela, fg_color="#0a0e27")
    container.pack(fill="both", expand=True, padx=30, pady=30)
    
    # Entry para nome
    entry_nome = criar_frame_entrada(
        container,
        "Nome do Cliente:",
        "Digite o nome (ex: Gabriel)"
    )
    
    # Função de busca
    def buscar():
        nome = entry_nome.get().strip()
        if not nome:
            mostrar_mensagem_padrao("Atenção", "Digite um nome válido", "aviso")
            return
        
        sucesso, dados, erro = api_client.buscar_cliente_por_nome(nome)
        
        if sucesso:
            if not dados:
                mostrar_mensagem_padrao("Sem Resultados", "Nenhum cliente encontrado com este nome", "info")
                return
            
            TabelaResultados(
                dados,
                ["ClienteID", "Nome", "Sobrenome", "CPF", "DataNascimento", "DataAfiliacao", "QuantidadeLivrosReservados", "QuantidadePendencias", "Cidade", "Estado"],
                f"Clientes - {nome}"
            )
        else:
            mostrar_mensagem_padrao("Erro", erro or "Nenhum cliente encontrado", "erro")
    
    # Botões
    frame_botoes = ctk.CTkFrame(container, fg_color="transparent")
    frame_botoes.pack(fill="x", pady=30)
    
    btn_buscar = ctk.CTkButton(
        frame_botoes,
        text="🔍 Buscar",
        command=buscar,
        fg_color="#6366f1",
        hover_color="#818cf8",
        font=("Arial", 14, "bold"),
        height=45,
        corner_radius=8
    )
    btn_buscar.pack(fill="x", pady=10)
    
    btn_voltar = ctk.CTkButton(
        frame_botoes,
        text="⬅️ Voltar",
        command=callback_voltar,
        fg_color="#ef4444",
        hover_color="#f87171",
        font=("Arial", 14, "bold"),
        height=45,
        corner_radius=8
    )
    btn_voltar.pack(fill="x", pady=10)


def tela_consulta_por_estado(janela: ctk.CTkFrame, api_client, callback_voltar):
    """Tela de consulta de cliente por estado.

    Mantém compatibilidade com imports antigos: esta função delega para a
    implementação "melhorada".
    """

    return tela_consulta_por_estado_melhorada(janela, api_client, callback_voltar)


def tela_consulta_por_estado_melhorada(janela: ctk.CTkFrame, api_client, callback_voltar):
    """Tela de consulta por estado (versão melhorada)."""
    
    for widget in janela.winfo_children():
        widget.destroy()
    
    janela.configure(fg_color="#0a0e27")
    
    # Header
    header = ctk.CTkFrame(janela, fg_color="#131829", height=100)
    header.pack(fill="x")
    header.pack_propagate(False)
    
    titulo = ctk.CTkLabel(
        header,
        text="🗺️ Consultar Clientes por Estado",
        font=("Arial Black", 22, "bold"),
        text_color="#6366f1"
    )
    titulo.pack(pady=20)
    
    # Container principal
    container = ctk.CTkFrame(janela, fg_color="#0a0e27")
    container.pack(fill="both", expand=True, padx=30, pady=30)
    
    # Entry para estado
    entry_estado = criar_frame_entrada(
        container,
        "Estado (Sigla ou Nome):",
        "Ex: RS, RJ, São Paulo"
    )
    
    # Função de busca
    def buscar():
        estado = entry_estado.get().strip()
        if not estado:
            mostrar_mensagem_padrao("Atenção", "Digite um estado válido", "aviso")
            return
        
        sucesso, dados, erro = api_client.buscar_clientes_por_estado(estado)
        
        if sucesso:
            if not dados:
                mostrar_mensagem_padrao("Sem Resultados", f"Nenhum cliente encontrado no estado {estado.upper()}", "info")
                return
            
            TabelaResultados(
                dados,
                ["ClienteID", "Nome", "Sobrenome", "CPF", "DataNascimento", "DataAfiliacao", "QuantidadeLivrosReservados", "QuantidadePendencias", "Cidade", "Estado"],
                f"Clientes - {estado.upper()}"
            )
        else:
            mostrar_mensagem_padrao("Erro", erro or "Nenhum cliente encontrado", "erro")
    
    # Botões
    frame_botoes = ctk.CTkFrame(container, fg_color="transparent")
    frame_botoes.pack(fill="x", pady=30)
    
    btn_buscar = ctk.CTkButton(
        frame_botoes,
        text="🔍 Buscar",
        command=buscar,
        fg_color="#6366f1",
        hover_color="#818cf8",
        font=("Arial", 14, "bold"),
        height=45,
        corner_radius=8
    )
    btn_buscar.pack(fill="x", pady=10)
    
    btn_voltar = ctk.CTkButton(
        frame_botoes,
        text="⬅️ Voltar",
        command=callback_voltar,
        fg_color="#ef4444",
        hover_color="#f87171",
        font=("Arial", 14, "bold"),
        height=45,
        corner_radius=8
    )
    btn_voltar.pack(fill="x", pady=10)


def tela_consulta_livro(janela: ctk.CTkFrame, api_client, callback_voltar, tipo: str):
    """Tela de consulta de livro.

    Mantém compatibilidade com imports antigos: esta função delega para a
    implementação "melhorada".
    """

    return tela_consulta_livro_melhorada(janela, api_client, callback_voltar, tipo)


def tela_consulta_livro_melhorada(janela: ctk.CTkFrame, api_client, callback_voltar, tipo: str):
    """Tela genérica de consulta de livro."""
    
    for widget in janela.winfo_children():
        widget.destroy()
    
    janela.configure(fg_color="#0a0e27")
    
    # Configurar por tipo
    config = {
        "nome": {
            "titulo": "📖 Consultar Livro por Nome",
            "label": "Nome do Livro:",
            "placeholder": "Digite o nome",
            "funcao": api_client.buscar_livro_por_nome,
            "colunas": ["LivroID", "NomeLivro", "Autor", "Editora", "DataPublicacao", "ISBN", "QuantidadeTotal", "QuantidadeDisponivel", "NomeGenero"],
        },
        "autor": {
            "titulo": "✍️ Consultar Livros por Autor",
            "label": "Nome do Autor:",
            "placeholder": "Digite o autor",
            "funcao": api_client.buscar_livros_por_autor,
            "colunas": ["LivroID", "NomeLivro", "Autor", "Editora", "DataPublicacao", "ISBN", "QuantidadeTotal", "QuantidadeDisponivel", "NomeGenero"],
        },
        "genero": {
            "titulo": "🎭 Consultar Livros por Gênero",
            "label": "Gênero:",
            "placeholder": "Selecione o gênero",
            "funcao": api_client.buscar_livros_por_genero,
            "colunas": ["LivroID", "NomeLivro", "Autor", "Editora", "DataPublicacao", "ISBN", "QuantidadeTotal", "QuantidadeDisponivel", "NomeGenero"],
            "é_combo": True,
        },
    }
    
    conf = config.get(tipo, config["nome"])
    
    # Header
    header = ctk.CTkFrame(janela, fg_color="#131829", height=100)
    header.pack(fill="x")
    header.pack_propagate(False)
    
    titulo = ctk.CTkLabel(
        header,
        text=conf["titulo"],
        font=("Arial Black", 22, "bold"),
        text_color="#6366f1"
    )
    titulo.pack(pady=20)
    
    # Container principal
    container = ctk.CTkFrame(janela, fg_color="#0a0e27")
    container.pack(fill="both", expand=True, padx=30, pady=30)
    
    # Entry ou ComboBox conforme tipo
    generos_disponiveis: set[str] | None = None
    if conf.get("é_combo"):
        # ComboBox para Gênero
        frame_genero = ctk.CTkFrame(container, fg_color="transparent")
        frame_genero.pack(fill="x", pady=12)
        
        label_genero = ctk.CTkLabel(
            frame_genero,
            text=conf["label"],
            font=("Segoe UI", 12, "bold"),
            text_color="#e0e7ff"
        )
        label_genero.pack(anchor="w", padx=10, pady=(0, 6))

        # Barra de status + atualizar
        frame_tools = ctk.CTkFrame(frame_genero, fg_color="transparent")
        frame_tools.pack(fill="x", padx=10, pady=(0, 8))

        status_genero = ctk.CTkLabel(
            frame_tools,
            text="Carregando gêneros do banco...",
            font=("Segoe UI", 11),
            text_color="#a5b4fc",
        )
        status_genero.pack(side="left")

        entry = ctk.CTkComboBox(
            frame_genero,
            values=["(carregando...)"],
            font=("Segoe UI", 11),
            fg_color="#1e293b",
            border_color="#4f46e5",
            border_width=2,
            height=42,
            corner_radius=10,
            text_color="#e0e7ff",
            button_color="#6366f1",
            button_hover_color="#818cf8",
        )
        entry.pack(fill="x", padx=10, pady=5)

        generos_disponiveis = set()

        def carregar_generos() -> None:
            nonlocal generos_disponiveis

            status_genero.configure(text="Carregando gêneros do banco...", text_color="#a5b4fc")

            sucesso, generos, erro = api_client.listar_generos()
            if not sucesso:
                generos_disponiveis = set()
                entry.configure(values=["(falha ao carregar)"])
                entry.set("")
                status_genero.configure(
                    text=f"Falha ao carregar gêneros: {erro or 'erro desconhecido'}",
                    text_color="#fca5a5",
                )
                return

            nomes: list[str] = []
            for genero in generos:
                if isinstance(genero, dict):
                    nome = (
                        genero.get("NomeGenero")
                        or genero.get("nome")
                        or genero.get("nome_genero")
                    )
                else:
                    nome = str(genero)

                if nome and str(nome).strip():
                    nomes.append(str(nome).strip())

            nomes = sorted(set(nomes), key=str.casefold)
            generos_disponiveis = set(nomes)

            if not nomes:
                entry.configure(values=["(nenhum gênero cadastrado)"])
                entry.set("")
                status_genero.configure(text="Nenhum gênero cadastrado no banco.", text_color="#fbbf24")
                return

            entry.configure(values=nomes)
            entry.set(nomes[0])
            status_genero.configure(text=f"{len(nomes)} gêneros carregados.", text_color="#86efac")

        btn_atualizar = ctk.CTkButton(
            frame_tools,
            text="🔄 Atualizar",
            command=carregar_generos,
            fg_color="#334155",
            hover_color="#475569",
            font=("Segoe UI", 11, "bold"),
            height=32,
            corner_radius=8,
        )
        btn_atualizar.pack(side="right")

        carregar_generos()
    else:
        # Entry normal
        entry = criar_frame_entrada(container, conf["label"], conf["placeholder"])
    
    # Função de busca
    def buscar():
        valor = entry.get().strip()
        if not valor:
            mostrar_mensagem_padrao("Atenção", f"Digite um {conf['label'].lower()}", "aviso")
            return

        if conf.get("é_combo") and isinstance(generos_disponiveis, set):
            if valor not in generos_disponiveis:
                mostrar_mensagem_padrao(
                    "Atenção",
                    "Selecione um gênero válido (somente os do banco).",
                    "aviso",
                )
                return
        
        sucesso, dados, erro = conf["funcao"](valor)
        
        if sucesso:
            if not dados:
                mostrar_mensagem_padrao("Sem Resultados", f"Nenhum livro encontrado", "info")
                return
            
            TabelaResultados(dados, conf["colunas"], conf["titulo"])
        else:
            mostrar_mensagem_padrao("Erro", erro or "Nenhum livro encontrado", "erro")
    
    # Botões
    frame_botoes = ctk.CTkFrame(container, fg_color="transparent")
    frame_botoes.pack(fill="x", pady=30)
    
    btn_buscar = ctk.CTkButton(
        frame_botoes,
        text="🔍 Buscar",
        command=buscar,
        fg_color="#6366f1",
        hover_color="#818cf8",
        font=("Arial", 14, "bold"),
        height=45,
        corner_radius=8
    )
    btn_buscar.pack(fill="x", pady=10)
    
    btn_voltar = ctk.CTkButton(
        frame_botoes,
        text="⬅️ Voltar",
        command=callback_voltar,
        fg_color="#ef4444",
        hover_color="#f87171",
        font=("Arial", 14, "bold"),
        height=45,
        corner_radius=8
    )
    btn_voltar.pack(fill="x", pady=10)
