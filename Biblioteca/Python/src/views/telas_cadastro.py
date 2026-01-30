"""Telas de cadastro (Clientes e Livros).

Contém as telas da GUI responsáveis por criar registros na API:
- Cadastro de cliente
- Cadastro de livro
"""

import customtkinter as ctk

from src.utils.formatters import interpretar_data, normalizar_data_para_api
from src.views.componentes import (
    criar_frame_entrada,
    criar_combobox,
    criar_seletor_data,
    mostrar_mensagem_padrao
)


def tela_cadastro_cliente(janela: ctk.CTkFrame, api_client, callback_voltar):
    """Tela de cadastro de cliente."""
    
    for widget in janela.winfo_children():
        widget.destroy()
    
    janela.configure(fg_color="#0a0e27")
    
    # Header
    header = ctk.CTkFrame(janela, fg_color="#131829", height=100)
    header.pack(fill="x")
    header.pack_propagate(False)
    
    titulo = ctk.CTkLabel(
        header,
        text="➕ Cadastrar Novo Cliente",
        font=("Arial Black", 22, "bold"),
        text_color="#6366f1"
    )
    titulo.pack(pady=20)
    
    # Container com scroll
    container_scroll = ctk.CTkScrollableFrame(
        janela, 
        fg_color="#0a0e27",
        scrollbar_button_color="#6366f1",
        scrollbar_button_hover_color="#818cf8"
    )
    container_scroll.pack(fill="both", expand=True, padx=20, pady=20)
    
    # Seção: Dados Pessoais
    label_secao = ctk.CTkLabel(
        container_scroll,
        text="👤 Dados Pessoais",
        font=("Arial Black", 14, "bold"),
        text_color="#6366f1"
    )
    label_secao.pack(anchor="w", pady=(20, 15))
    
    entry_nome = criar_frame_entrada(container_scroll, "Nome*:", "Digite o nome completo")
    entry_sobrenome = criar_frame_entrada(container_scroll, "Sobrenome*:", "Digite o sobrenome")
    entry_cpf = criar_frame_entrada(container_scroll, "CPF*:", "000.000.000-00")
    entry_data_nasc = criar_seletor_data(container_scroll, "Data de Nascimento*:")
    entry_data_afil = criar_seletor_data(container_scroll, "Data de Afiliação*:")
    
    # Seção: Endereço
    label_secao = ctk.CTkLabel(
        container_scroll,
        text="📍 Endereço",
        font=("Arial Black", 14, "bold"),
        text_color="#6366f1"
    )
    label_secao.pack(anchor="w", pady=(30, 15))
    
    entry_cep = criar_frame_entrada(container_scroll, "CEP*:", "00000-000")
    entry_rua = criar_frame_entrada(container_scroll, "Rua*:", "Digite o nome da rua")
    entry_numero = criar_frame_entrada(container_scroll, "Número*:", "Digite o número")
    entry_bairro = criar_frame_entrada(container_scroll, "Bairro*:", "Digite o bairro")
    entry_cidade = criar_frame_entrada(container_scroll, "Cidade*:", "Digite a cidade")
    
    # Combobox para estado
    estados = ["AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", 
               "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", 
               "RS", "RO", "RR", "SC", "SP", "SE", "TO"]
    entry_estado = criar_combobox(container_scroll, "Estado*:", estados)
    
    entry_complemento = criar_frame_entrada(container_scroll, "Complemento:", "Apto, Bloco, etc")
    
    def cadastrar():
        """Validar e cadastrar novo cliente."""
        # Validar campos obrigatórios
        nome = entry_nome.get().strip()
        sobrenome = entry_sobrenome.get().strip()
        cpf = entry_cpf.get().strip()
        data_nasc = entry_data_nasc.get().strip()
        data_afil = entry_data_afil.get().strip()
        cep = entry_cep.get().strip()
        rua = entry_rua.get().strip()
        numero = entry_numero.get().strip()
        bairro = entry_bairro.get().strip()
        cidade = entry_cidade.get().strip()
        estado = entry_estado.get().strip()
        
        if not all([nome, sobrenome, cpf, data_nasc, data_afil, cep, rua, numero, bairro, cidade, estado]):
            mostrar_mensagem_padrao("Erro", "Preencha todos os campos obrigatórios (*)", "erro")
            return
        
        # Validar CPF (formato básico)
        cpf_limpo = cpf.replace(".", "").replace("-", "")
        if len(cpf_limpo) != 11 or not cpf_limpo.isdigit():
            mostrar_mensagem_padrao("Erro", "CPF deve conter 11 dígitos", "erro")
            return
        
        # Validar/normalizar datas para o padrão da API (DD/MM/AAAA)
        if not interpretar_data(data_nasc):
            mostrar_mensagem_padrao("Erro", "Data de nascimento inválida. Use DD/MM/AAAA.", "erro")
            return

        if not interpretar_data(data_afil):
            mostrar_mensagem_padrao("Erro", "Data de afiliação inválida. Use DD/MM/AAAA.", "erro")
            return

        data_nasc_api = normalizar_data_para_api(data_nasc)
        data_afil_api = normalizar_data_para_api(data_afil)
        
        # Preparar dados para envio
        dados_cliente = {
            "Nome": nome,
            "Sobrenome": sobrenome,
            "CPF": cpf_limpo,
            "DataNascimento": data_nasc_api,
            "DataAfiliacao": data_afil_api,
            "endereco": {
                "CEP": cep,
                "Rua": rua,
                "Numero": numero,
                "Bairro": bairro,
                "Cidade": cidade,
                "Estado": estado,
                "Complemento": entry_complemento.get().strip() or None
            }
        }
        
        sucesso, mensagem = api_client.cadastrar_cliente(dados_cliente)
        
        if sucesso:
            mostrar_mensagem_padrao("✅ Sucesso", "Cliente cadastrado com sucesso!", "sucesso")
            # Limpar formulário
            for entry in [entry_nome, entry_sobrenome, entry_cpf, entry_data_nasc, entry_data_afil,
                         entry_cep, entry_rua, entry_numero, entry_bairro, entry_cidade, 
                         entry_estado, entry_complemento]:
                entry.delete(0, "end")
        else:
            mostrar_mensagem_padrao("Erro", mensagem, "erro")
    
    # Botões
    frame_botoes = ctk.CTkFrame(container_scroll, fg_color="transparent")
    frame_botoes.pack(fill="x", pady=30)
    
    btn_cadastrar = ctk.CTkButton(
        frame_botoes,
        text="✅ Cadastrar",
        command=cadastrar,
        fg_color="#10b981",
        hover_color="#059669",
        font=("Arial", 14, "bold"),
        height=45,
        corner_radius=8
    )
    btn_cadastrar.pack(fill="x", pady=10)
    
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


def tela_cadastro_livro(janela: ctk.CTkFrame, api_client, callback_voltar):
    """Tela de cadastro de livro."""
    
    for widget in janela.winfo_children():
        widget.destroy()
    
    janela.configure(fg_color="#0a0e27")
    
    # Header
    header = ctk.CTkFrame(janela, fg_color="#131829", height=100)
    header.pack(fill="x")
    header.pack_propagate(False)
    
    titulo = ctk.CTkLabel(
        header,
        text="📚 Cadastrar Novo Livro",
        font=("Arial Black", 22, "bold"),
        text_color="#6366f1"
    )
    titulo.pack(pady=20)
    
    # Container com scroll
    container_scroll = ctk.CTkScrollableFrame(
        janela,
        fg_color="#0a0e27",
        scrollbar_button_color="#6366f1",
        scrollbar_button_hover_color="#818cf8"
    )
    container_scroll.pack(fill="both", expand=True, padx=20, pady=20)
    
    # Seção: Informações Básicas
    label_secao = ctk.CTkLabel(
        container_scroll,
        text="📖 Informações Básicas",
        font=("Arial Black", 14, "bold"),
        text_color="#6366f1"
    )
    label_secao.pack(anchor="w", pady=(20, 15))
    
    entry_nome = criar_frame_entrada(container_scroll, "Nome do Livro*:", "Digite o título")
    entry_autor = criar_frame_entrada(container_scroll, "Autor*:", "Digite o nome do autor")
    entry_editora = criar_frame_entrada(container_scroll, "Editora*:", "Digite a editora")
    
    # Seção: Informações de Publicação
    label_secao = ctk.CTkLabel(
        container_scroll,
        text="📅 Publicação",
        font=("Arial Black", 14, "bold"),
        text_color="#6366f1"
    )
    label_secao.pack(anchor="w", pady=(30, 15))
    
    entry_data_pub = criar_seletor_data(container_scroll, "Data de Publicação*:")
    entry_idioma = criar_frame_entrada(container_scroll, "Idioma*:", "Ex: Português, Inglês")
    entry_paginas = criar_frame_entrada(container_scroll, "Número de Páginas*:", "Ex: 300")
    
    # Seção: Gênero e Quantidade
    label_secao = ctk.CTkLabel(
        container_scroll,
        text="🎭 Categoria e Quantidade",
        font=("Arial Black", 14, "bold"),
        text_color="#6366f1"
    )
    label_secao.pack(anchor="w", pady=(30, 15))
    
    # Combobox para gênero
    generos_validos = []
    generos_validos_set = set()

    entry_genero = criar_combobox(container_scroll, "Gênero*:", ["(carregando...)"])
    try:
        entry_genero.configure(values=["(carregando...)"], state="disabled")
    except Exception:
        # Alguns wrappers de combobox não expõem state; seguimos sem travar.
        pass

    frame_atualizar_generos = ctk.CTkFrame(container_scroll, fg_color="transparent")
    frame_atualizar_generos.pack(fill="x", pady=(8, 0))

    status_generos = ctk.CTkLabel(
        frame_atualizar_generos,
        text="Carregando gêneros do banco...",
        font=("Arial", 11),
        text_color="#a5b4fc",
        anchor="w"
    )
    status_generos.pack(side="left", fill="x", expand=True)

    def carregar_generos():
        nonlocal generos_validos, generos_validos_set
        sucesso, lista, erro = api_client.listar_generos()
        if not sucesso:
            status_generos.configure(text=f"Falha ao carregar gêneros: {erro}", text_color="#ef4444")
            try:
                entry_genero.configure(values=["(erro ao carregar)"])
            except Exception:
                pass
            return

        nomes = []
        for item in lista or []:
            nome = item.get('NomeGenero') if isinstance(item, dict) else None
            if nome:
                nomes.append(str(nome))

        nomes = sorted(set(nomes), key=lambda s: s.lower())
        generos_validos = nomes
        generos_validos_set = set(nomes)

        if not nomes:
            status_generos.configure(text="Nenhum gênero encontrado no banco.", text_color="#ef4444")
            try:
                entry_genero.configure(values=["(nenhum gênero)"])
            except Exception:
                pass
            return

        status_generos.configure(text=f"{len(nomes)} gênero(s) carregado(s) do banco.", text_color="#10b981")
        try:
            entry_genero.configure(values=nomes, state="normal")
            # Seleciona o primeiro como default
            entry_genero.set(nomes[0])
        except Exception:
            # Se não houver set/configure, ao menos não quebra a tela.
            pass

    btn_atualizar_generos = ctk.CTkButton(
        frame_atualizar_generos,
        text="🔄 Atualizar",
        command=carregar_generos,
        fg_color="#6366f1",
        hover_color="#818cf8",
        font=("Arial", 12, "bold"),
        height=34,
        corner_radius=8,
        width=120
    )
    btn_atualizar_generos.pack(side="right", padx=(10, 0))

    # Carrega uma vez ao abrir a tela
    carregar_generos()
    
    entry_quantidade = criar_frame_entrada(container_scroll, "Quantidade Disponível*:", "Digite a quantidade")
    
    def cadastrar():
        """Validar e cadastrar novo livro."""
        nome = entry_nome.get().strip()
        autor = entry_autor.get().strip()
        editora = entry_editora.get().strip()
        data_pub = entry_data_pub.get().strip()
        idioma = entry_idioma.get().strip()
        paginas = entry_paginas.get().strip()
        genero = entry_genero.get().strip()
        quantidade = entry_quantidade.get().strip()
        
        if not all([nome, autor, editora, data_pub, idioma, paginas, genero, quantidade]):
            mostrar_mensagem_padrao("Erro", "Preencha todos os campos obrigatórios (*)", "erro")
            return

        # Gênero deve ser um dos existentes no banco
        if generos_validos_set and genero not in generos_validos_set:
            mostrar_mensagem_padrao("Erro", "Selecione um gênero válido (apenas os do banco)", "erro")
            return
        
        # Validar número de páginas
        try:
            paginas_int = int(paginas)
            if paginas_int <= 0:
                raise ValueError
        except ValueError:
            mostrar_mensagem_padrao("Erro", "Número de páginas deve ser um número positivo", "erro")
            return
        
        # Validar quantidade
        try:
            quantidade_int = int(quantidade)
            if quantidade_int < 0:
                raise ValueError
        except ValueError:
            mostrar_mensagem_padrao("Erro", "Quantidade deve ser um número não-negativo", "erro")
            return
        
        # Validar/normalizar data para o padrão da API (DD/MM/AAAA)
        if not interpretar_data(data_pub):
            mostrar_mensagem_padrao("Erro", "Data de publicação inválida. Use DD/MM/AAAA.", "erro")
            return

        data_pub_api = normalizar_data_para_api(data_pub)
        
        # Preparar dados para envio
        dados_livro = {
            "NomeLivro": nome,
            "Autor": autor,
            "Editora": editora,
            "DataPublicacao": data_pub_api,
            "Idioma": idioma,
            "QuantidadePaginas": paginas_int,
            "NomeGenero": genero,
            "QuantidadeDisponivel": quantidade_int
        }
        
        sucesso, mensagem = api_client.cadastrar_livro(dados_livro)
        
        if sucesso:
            mostrar_mensagem_padrao("✅ Sucesso", "Livro cadastrado com sucesso!", "sucesso")
            # Limpar formulário
            for entry in [entry_nome, entry_autor, entry_editora, entry_data_pub, entry_idioma,
                         entry_paginas, entry_genero, entry_quantidade]:
                entry.delete(0, "end")
        else:
            mostrar_mensagem_padrao("Erro", mensagem, "erro")
    
    # Botões
    frame_botoes = ctk.CTkFrame(container_scroll, fg_color="transparent")
    frame_botoes.pack(fill="x", pady=30)
    
    btn_cadastrar = ctk.CTkButton(
        frame_botoes,
        text="✅ Cadastrar",
        command=cadastrar,
        fg_color="#10b981",
        hover_color="#059669",
        font=("Arial", 14, "bold"),
        height=45,
        corner_radius=8
    )
    btn_cadastrar.pack(fill="x", pady=10)
    
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
