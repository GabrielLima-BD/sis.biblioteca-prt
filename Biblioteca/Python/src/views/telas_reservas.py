"""Telas de reservas (criar, listar, consultar, editar e finalizar).

Este módulo implementa as telas da GUI relacionadas ao ciclo de vida da reserva,
consumindo a API via `APIClient`.
"""

import customtkinter as ctk
from datetime import datetime, timedelta
from src.utils.formatters import (
    formatar_data_para_exibicao,
    normalizar_data_para_api,
    interpretar_data,
)
from src.utils.validators import validar_data
from src.views.componentes import (
    criar_frame_entrada,
    criar_combobox,
    criar_seletor_data,
    mostrar_mensagem_padrao,
    TabelaResultados,
    criar_header_padrao,
    criar_container_scroll,
    criar_container_simples,
    criar_busca_entidade,
    criar_botoes_acao,
    limpar_frame,
    criar_frame_info,
    solicitar_senha_operador,
)


def tela_nova_reserva(janela: ctk.CTkFrame, api_client, callback_voltar):
    """Tela para criar nova reserva."""
    limpar_frame(janela)
    
    # Header padronizado
    criar_header_padrao(janela, "Nova Reserva", "📅", callback_voltar)
    
    # Container com scroll
    container = criar_container_scroll(janela)
    
    # CPF do Cliente
    entry_cpf = criar_frame_entrada(container, "CPF do Cliente *", "000.000.000-00")
    
    # Buscar cliente com componente reutilizável
    label_cliente, atualizar_cliente, frame_buscar = criar_busca_entidade(
        container,
        "Cliente: Não encontrado"
    )
    
    cliente_encontrado = {}
    
    def buscar_cliente():
        cpf = entry_cpf.get().strip().replace(".", "").replace("-", "").replace(" ", "")
        if not cpf:
            mostrar_mensagem_padrao("Atenção", "Digite o CPF do cliente", "aviso")
            return
        
        sucesso, dados, erro = api_client.buscar_cliente_por_cpf(cpf)
        
        if sucesso and dados:
            cliente_encontrado.clear()
            cliente_encontrado.update(dados)
            atualizar_cliente(
                f"Cliente: {dados.get('Nome', '')} {dados.get('Sobrenome', '')}",
                "encontrado"
            )
            mostrar_mensagem_padrao("Sucesso", "Cliente encontrado!", "sucesso")
        else:
            atualizar_cliente("Cliente: Não encontrado", "erro")
            mostrar_mensagem_padrao("Erro", erro or "Cliente não encontrado", "erro")
    
    # Auto-busca ao digitar 11 dígitos
    def verificar_cpf_completo(event):
        cpf_limpo = entry_cpf.get().strip().replace(".", "").replace("-", "").replace(" ", "")
        if len(cpf_limpo) == 11 and cpf_limpo.isdigit():
            buscar_cliente()
    
    entry_cpf.bind("<KeyRelease>", verificar_cpf_completo)
    
    btn_buscar_cliente = ctk.CTkButton(
        frame_buscar,
        text="🔍 Buscar",
        command=buscar_cliente,
        font=("Segoe UI", 11, "bold"),
        fg_color="#4f46e5",
        hover_color="#818cf8",
        width=120,
        height=38
    )
    btn_buscar_cliente.pack(side="right", padx=10)
    
    # Nome do Livro
    entry_nome_livro = criar_frame_entrada(container, "Nome do Livro *", "Digite o nome")
    
    # Buscar livro com componente reutilizável
    label_livro, atualizar_livro, frame_buscar_livro = criar_busca_entidade(
        container,
        "Livro: Não selecionado"
    )
    
    livro_encontrado = {}
    
    def buscar_livro():
        nome_livro = entry_nome_livro.get().strip()
        if not nome_livro:
            mostrar_mensagem_padrao("Atenção", "Digite o nome do livro", "aviso")
            return
        
        sucesso, lista_livros, erro = api_client.buscar_livro_por_nome(nome_livro)
        
        if sucesso and lista_livros:
            # Criar janela de seleção
            janela_selecao = ctk.CTkToplevel()
            janela_selecao.title("📚 Selecionar Livro")
            janela_selecao.geometry("900x600")
            janela_selecao.configure(fg_color="#0a0e27")
            janela_selecao.attributes('-topmost', True)
            janela_selecao.after(100, lambda: janela_selecao.attributes('-topmost', False))
            
            # Header
            header = ctk.CTkFrame(janela_selecao, fg_color="#0f1937")
            header.pack(fill="x", pady=(0, 20))
            ctk.CTkLabel(
                header,
                text=f"📚 {len(lista_livros)} livro(s) encontrado(s)",
                font=("Segoe UI", 20, "bold"),
                text_color="#818cf8"
            ).pack(pady=15)

            # Lista com scroll (evita Canvas manual e bugs de frame não definido)
            lista_scroll = ctk.CTkScrollableFrame(
                janela_selecao,
                fg_color="#0a0e27",
                scrollbar_button_color="#4f46e5",
                scrollbar_button_hover_color="#818cf8",
            )
            lista_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

            # Criar linhas de livros
            for idx, livro in enumerate(lista_livros):
                frame_livro = ctk.CTkFrame(
                    lista_scroll,
                    fg_color="#131829" if idx % 2 == 0 else "#0f1937",
                    corner_radius=10
                )
                frame_livro.pack(fill="x", pady=5, padx=10)
                
                # Info do livro
                info_frame = ctk.CTkFrame(frame_livro, fg_color="transparent")
                info_frame.pack(side="left", fill="both", expand=True, padx=15, pady=12)
                
                ctk.CTkLabel(
                    info_frame,
                    text=livro.get('NomeLivro', 'N/A'),
                    font=("Segoe UI", 14, "bold"),
                    text_color="#e0e7ff",
                    anchor="w"
                ).pack(anchor="w")
                
                ctk.CTkLabel(
                    info_frame,
                    text=f"Autor: {livro.get('Autor', 'N/A')} | Gênero: {livro.get('NomeGenero', 'N/A')} | Qtd: {livro.get('QuantidadeDisponivel', 0)}",
                    font=("Segoe UI", 11),
                    text_color="#a5b4fc",
                    anchor="w"
                ).pack(anchor="w", pady=(5, 0))
                
                # Botão selecionar
                def criar_callback(l):
                    def selecionar():
                        livro_encontrado.clear()
                        livro_encontrado.update(l)
                        atualizar_livro(
                            f"Livro: {l.get('NomeLivro', '')} - {l.get('Autor', '')}",
                            "encontrado"
                        )
                        janela_selecao.destroy()
                        mostrar_mensagem_padrao("Sucesso", "Livro selecionado!", "sucesso")
                    return selecionar
                
                btn_selecionar = ctk.CTkButton(
                    frame_livro,
                    text="✓ Selecionar",
                    command=criar_callback(livro),
                    font=("Segoe UI", 12, "bold"),
                    fg_color="#10b981",
                    hover_color="#34d399",
                    width=120,
                    height=40
                )
                btn_selecionar.pack(side="right", padx=15)
        else:
            atualizar_livro("Livro: Nenhum encontrado", "erro")
            mostrar_mensagem_padrao("Erro", erro or "Nenhum livro encontrado", "erro")
    
    btn_buscar_livro = ctk.CTkButton(
        frame_buscar_livro,
        text="🔍 Buscar",
        command=buscar_livro,
        font=("Segoe UI", 11, "bold"),
        fg_color="#4f46e5",
        hover_color="#818cf8",
        width=120,
        height=38
    )
    btn_buscar_livro.pack(side="right", padx=10)
    
    # Datas
    entry_data_retirada = criar_seletor_data(container, "Data de Retirada *")
    entry_data_retirada.insert(0, datetime.now().strftime("%d/%m/%Y"))
    
    entry_data_devolucao = criar_seletor_data(container, "Data de Devolução Prevista *")
    data_devolucao = datetime.now() + timedelta(days=14)
    entry_data_devolucao.insert(0, data_devolucao.strftime("%d/%m/%Y"))

    # Forma de Retirada
    combo_forma = criar_combobox(
        container,
        "Forma de Retirada",
        ["Retirada", "Entrega"]
    )
    combo_forma.set("Retirada")

    # Quantidade Reservada
    entry_quantidade = criar_frame_entrada(container, "Quantidade Reservada", "1")
    entry_quantidade.insert(0, "1")

    # Observação (opcional)
    entry_observacao = criar_frame_entrada(container, "Observação (opcional)", "")
    
    # Função de salvar
    def salvar_reserva():
        if not cliente_encontrado:
            mostrar_mensagem_padrao("Erro", "Busque um cliente válido primeiro", "erro")
            return
        
        if not livro_encontrado:
            mostrar_mensagem_padrao("Erro", "Busque um livro válido primeiro", "erro")
            return
        
        data_retirada = entry_data_retirada.get().strip()
        data_devolucao = entry_data_devolucao.get().strip()
        
        if not data_retirada or not data_devolucao:
            mostrar_mensagem_padrao("Erro", "Preencha todas as datas", "erro")
            return
        
        # Pegar CPF limpo
        cpf_limpo = entry_cpf.get().strip().replace(".", "").replace("-", "").replace(" ", "")
        
        if not cpf_limpo:
            mostrar_mensagem_padrao("Erro", "CPF não pode estar vazio", "erro")
            return
        
        # Resolve IDs com fallback para diferentes chaves
        livro_id = (
            livro_encontrado.get("LivroID")
            or livro_encontrado.get("id")
            or livro_encontrado.get("livro_id")
        )
        
        nome_livro = (
            livro_encontrado.get("NomeLivro")
            or livro_encontrado.get("nome_livro")
            or livro_encontrado.get("nome")
        )

        # Campos adicionais
        forma_retirada = combo_forma.get().strip() or "Retirada"
        try:
            quantidade_reservada = int(entry_quantidade.get().strip() or "1")
        except ValueError:
            quantidade_reservada = 1
        observacao = entry_observacao.get().strip() or ""
        
        # Converter datas: GUI recebe YYYY-MM-DD, envia DD/MM/YYYY, API converte para YYYY-MM-DD
        data_ret_obj = interpretar_data(data_retirada)
        data_dev_obj = interpretar_data(data_devolucao)

        if not data_ret_obj or not data_dev_obj:
            mostrar_mensagem_padrao("Erro", "Formato de data inválido", "erro")
            return

        data_ret_formatada = data_ret_obj.strftime("%d/%m/%Y")
        data_dev_formatada = data_dev_obj.strftime("%d/%m/%Y")

        dados_reserva = {
            "CPFReserva": cpf_limpo,
            "NomeLivro": nome_livro,
            "LivroID": livro_id,
            "DataRetirada": data_ret_formatada,  # Envia DD/MM/YYYY, API converte para YYYY-MM-DD
            "DataVolta": data_dev_formatada,      # Envia DD/MM/YYYY, API converte para YYYY-MM-DD
            "Entrega": forma_retirada,
            "QntdLivro": quantidade_reservada,
            "Observacao": observacao
        }
        
        sucesso, mensagem = api_client.cadastrar_reserva(dados_reserva)
        
        if sucesso:
            mostrar_mensagem_padrao("Sucesso", "Reserva criada com sucesso!", "sucesso")
            callback_voltar()
        else:
            mostrar_mensagem_padrao("Erro", mensagem, "erro")
    
    # Botões de ação padronizados
    criar_botoes_acao(
        container,
        "Criar Reserva",
        salvar_reserva,
        callback_voltar
    )


def tela_listar_reservas(janela: ctk.CTkFrame, api_client, callback_voltar):
    """Tela para listar reservas ativas."""
    limpar_frame(janela)
    
    # Header padronizado
    criar_header_padrao(janela, "Reservas Ativas", "📋", callback_voltar)
    
    # Container simples (sem scroll)
    container = criar_container_simples(janela)
    
    # Filtros
    frame_filtro = ctk.CTkFrame(container, fg_color="#0f1937")
    frame_filtro.pack(fill="x", pady=(0, 20), padx=10)
    
    combo_status = criar_combobox(
        frame_filtro,
        "Filtrar por Status",
        ["Todas", "Ativas", "Atrasadas", "Devolvidas"]
    )
    combo_status.set("Ativas")
    
    def buscar_reservas():
        status_filtro = combo_status.get()
        params = {}
        
        if status_filtro != "Todas":
            if status_filtro == "Ativas":
                params["status"] = "ativa"
            elif status_filtro == "Atrasadas":
                params["atrasada"] = "true"
            elif status_filtro == "Devolvidas":
                params["status"] = "devolvida"
        
        sucesso, dados, erro = api_client.get("/reservas", params=params)
        
        if sucesso and dados.get("dados"):
            reservas = dados["dados"]
            
            # Calcular atrasos
            hoje = datetime.now().date()
            for reserva in reservas:
                if reserva.get("data_devolucao_prevista"):
                    data_prevista = interpretar_data(reserva.get("data_devolucao_prevista"))
                    if data_prevista:
                        data_prevista = data_prevista.date()
                        if reserva.get("status") == "ativa" and hoje > data_prevista:
                            dias_atraso = (hoje - data_prevista).days
                            reserva["dias_atraso"] = dias_atraso
                            reserva["multa_calculada"] = dias_atraso * 2.5  # R$ 2,50 por dia
                        else:
                            reserva["dias_atraso"] = 0
                            reserva["multa_calculada"] = 0.0
                    else:
                        reserva["dias_atraso"] = 0
                        reserva["multa_calculada"] = 0.0
            
            colunas = [
                "id", "cliente_id", "livro_id", "data_retirada",
                "data_devolucao_prevista", "status", "dias_atraso", "multa_calculada"
            ]
            
            TabelaResultados(reservas, colunas, f"Reservas ({len(reservas)})")
        else:
            mostrar_mensagem_padrao("Aviso", erro or "Nenhuma reserva encontrada", "aviso")
    
    btn_buscar = ctk.CTkButton(
        container,
        text="🔍 Buscar Reservas",
        command=buscar_reservas,
        font=("Segoe UI", 13, "bold"),
        fg_color="#4f46e5",
        hover_color="#818cf8",
        height=45
    )
    btn_buscar.pack(pady=20)


def tela_devolucao_reserva(janela: ctk.CTkFrame, api_client, callback_voltar):
    """Tela para registrar devolução de livro."""
    limpar_frame(janela)
    
    # Header padronizado
    criar_header_padrao(janela, "Registrar Devolução", "📦", callback_voltar)
    
    # Container simples
    container = criar_container_simples(janela)
    
    # ID da Reserva
    entry_reserva_id = criar_frame_entrada(container, "ID da Reserva *", "Digite o ID")
    
    # Info da reserva - usando componente reutilizável
    frame_info, label_info = criar_frame_info(
        container,
        "Busque uma reserva para ver detalhes"
    )
    
    reserva_encontrada = {}
    
    def buscar_reserva():
        reserva_id = entry_reserva_id.get().strip()
        if not reserva_id:
            mostrar_mensagem_padrao("Atenção", "Digite o ID da reserva", "aviso")
            return
        
        sucesso, dados, erro = api_client.get("/reservas", params={"id": reserva_id})
        
        if sucesso and dados.get("dados"):
            reserva = dados["dados"][0]
            reserva_encontrada.clear()
            reserva_encontrada.update(reserva)
            
            # Calcular atraso de forma segura
            try:
                hoje = datetime.now().date()
                data_prevista = datetime.strptime(
                    reserva["data_devolucao_prevista"], 
                    "%Y-%m-%d"
                ).date()
                
                dias_atraso = max(0, (hoje - data_prevista).days)
                multa = dias_atraso * 2.5
            except (ValueError, KeyError):
                dias_atraso = 0
                multa = 0.0
            
            data_retirada_txt = formatar_data_para_exibicao(reserva.get('data_retirada')) or 'N/A'
            data_prevista_txt = formatar_data_para_exibicao(reserva.get('data_devolucao_prevista')) or 'N/A'

            info_texto = f"""✅ Reserva #{reserva['id']} encontrada!

Cliente: {reserva.get('cliente_id', 'N/A')}
Livro: {reserva.get('livro_id', 'N/A')}
Data Retirada: {data_retirada_txt}
Data Prevista: {data_prevista_txt}
Status: {reserva.get('status', 'N/A')}

Dias de Atraso: {dias_atraso}
Multa a Pagar: R$ {multa:.2f}"""
            
            label_info.configure(
                text=info_texto,
                text_color="#10b981" if dias_atraso == 0 else "#ef4444"
            )
        else:
            label_info.configure(
                text="❌ Reserva não encontrada",
                text_color="#ef4444"
            )
            mostrar_mensagem_padrao("Erro", erro or "Reserva não encontrada", "erro")
    
    btn_buscar = ctk.CTkButton(
        container,
        text="🔍 Buscar Reserva",
        command=buscar_reserva,
        font=("Segoe UI", 12, "bold"),
        fg_color="#4f46e5",
        hover_color="#818cf8",
        height=42
    )
    btn_buscar.pack(pady=10)
    
    # Data de devolução real
    entry_data_devolucao = criar_seletor_data(container, "Data de Devolução Real *")
    entry_data_devolucao.insert(0, datetime.now().strftime("%d/%m/%y"))
    
    # Função de registrar
    def registrar_devolucao():
        if not reserva_encontrada:
            mostrar_mensagem_padrao("Erro", "Busque uma reserva válida primeiro", "erro")
            return
        
        data_devolucao = entry_data_devolucao.get().strip()
        
        if not data_devolucao:
            mostrar_mensagem_padrao("Erro", "Preencha a data de devolução", "erro")
            return
        if not interpretar_data(data_devolucao):
            mostrar_mensagem_padrao("Erro", "Data de devolução inválida", "erro")
            return
        
        dados_devolucao = {
            "reserva_id": reserva_encontrada["id"],
            "data_devolucao_real": normalizar_data_para_api(data_devolucao)
        }
        
        sucesso, dados, erro = api_client.post("/devolucoes", json=dados_devolucao)
        
        if sucesso:
            mostrar_mensagem_padrao("Sucesso", "Devolução registrada com sucesso!", "sucesso")
            callback_voltar()
        else:
            mostrar_mensagem_padrao("Erro", erro or "Erro ao registrar devolução", "erro")
    
    # Botões de ação padronizados
    criar_botoes_acao(
        container,
        "Confirmar Devolução",
        registrar_devolucao,
        callback_voltar
    )

def tela_consultar_reservas(janela: ctk.CTkFrame, api_client, callback_voltar):
    """Tela para consultar todas as reservas com filtros."""
    limpar_frame(janela)
    
    # Header padronizado
    criar_header_padrao(janela, "Consultar Reservas", "📋", callback_voltar)
    
    # Container com scroll
    container = criar_container_scroll(janela)
    
    # Filtros
    frame_filtro = ctk.CTkFrame(container, fg_color="#0f1937", corner_radius=10)
    frame_filtro.pack(fill="x", pady=10, padx=10)
    
    ctk.CTkLabel(
        frame_filtro,
        text="🔍 Filtros",
        font=("Segoe UI", 13, "bold"),
        text_color="#818cf8"
    ).pack(anchor="w", padx=15, pady=(15, 5))
    
    combo_status = criar_combobox(
        frame_filtro,
        "Status da Reserva",
        ["Todas", "Ativas", "Finalizadas", "Canceladas"]
    )
    combo_status.set("Ativas")
    
    # Tabela de resultados
    frame_tabela = ctk.CTkFrame(container, fg_color="transparent")
    frame_tabela.pack(fill="both", expand=True, padx=10, pady=10)
    
    tabela_janela = None
    
    def buscar_reservas():
        nonlocal tabela_janela
        
        status_filtro = combo_status.get()
        mapa_status = {
            "Ativas": "ativa",
            "Finalizadas": "finalizada",
            "Canceladas": "cancelada"
        }
        filtro = mapa_status.get(status_filtro, "todas")
        
        sucesso, reservas, erro = api_client.listar_reservas(filtro)
        
        if sucesso and reservas:
            for reserva in reservas:
                if not isinstance(reserva, dict):
                    continue

                # Converter datas para exibição amigável
                for campo_data in ['DataRetirada', 'DataPrevistaEntrega', 'DataEntrega']:
                    if reserva.get(campo_data):
                        reserva[campo_data] = formatar_data_para_exibicao(reserva[campo_data])

                nome_cliente = f"{reserva.get('ClienteNome', '')} {reserva.get('ClienteSobrenome', '')}".strip()
                reserva['ClienteNomeCompleto'] = nome_cliente or 'N/A'
                reserva['ClienteEnderecoFormatado'] = reserva.get('ClienteEndereco') or 'N/A'
                reserva['LivroNomeFormatado'] = reserva.get('LivroNome') or 'N/A'
                reserva['LivroAutorNome'] = reserva.get('LivroAutor') or 'N/A'
                status = reserva.get('Status')
                reserva['Status'] = status.capitalize() if isinstance(status, str) and status else 'N/A'

            if tabela_janela and tabela_janela.winfo_exists():
                tabela_janela.destroy()

            colunas = [
                ('ReservaID', 'Reserva #', 110),
                ('ClienteNomeCompleto', 'Cliente', 220),
                ('ClienteEnderecoFormatado', 'Endereço', 260),
                ('LivroNomeFormatado', 'Livro', 220),
                ('LivroAutorNome', 'Autor', 180),
                ('DataRetirada', 'Retirada', 130),
                ('DataPrevistaEntrega', 'Prevista', 130),
                ('DataEntrega', 'Entrega', 130),
                ('Status', 'Status', 130),
                ('QuantidadeReservada', 'Quantidade', 120)
            ]

            tabela_janela = TabelaResultados(
                reservas,
                colunas,
                f"Reservas ({len(reservas)})"
            )
        else:
            mostrar_mensagem_padrao("Aviso", erro or "Nenhuma reserva encontrada", "aviso")
    
    # Botão buscar
    btn_buscar = ctk.CTkButton(
        container,
        text="🔍 Buscar Reservas",
        command=buscar_reservas,
        font=("Segoe UI", 13, "bold"),
        fg_color="#4f46e5",
        hover_color="#818cf8",
        height=45
    )
    btn_buscar.pack(pady=10)


def tela_editar_reserva(janela: ctk.CTkFrame, api_client, callback_voltar):
    """Tela para editar dados de uma reserva existente."""
    limpar_frame(janela)
    
    # Header padronizado
    criar_header_padrao(janela, "Editar Reserva", "✏️", callback_voltar)
    
    # Container com scroll
    container = criar_container_scroll(janela)
    
    # ID da reserva
    entry_reserva_id = criar_frame_entrada(container, "ID da Reserva *", "Digite o ID")
    
    # Info da reserva
    frame_info, label_info = criar_frame_info(container, "Busque uma reserva para editar")
    
    reserva_encontrada = {}
    
    def buscar_reserva():
        reserva_id = entry_reserva_id.get().strip()
        if not reserva_id or not reserva_id.isdigit():
            mostrar_mensagem_padrao("Erro", "Digite um ID válido", "erro")
            return
        
        sucesso, dados, erro = api_client.obter_reserva_por_id(int(reserva_id))
        
        if sucesso and dados:
            reserva_encontrada.clear()
            reserva_encontrada.update(dados)
            
            info_texto = f"""✅ Reserva #{dados.get('ReservaID', 'N/A')} encontrada!

Cliente ID: {dados.get('ClienteID', 'N/A')}
Livro ID: {dados.get('LivroID', 'N/A')}
Quantidade: {dados.get('QuantidadeReservada', 'N/A')}
Status: {dados.get('Status', 'N/A')}"""
            
            label_info.configure(text=info_texto, text_color="#10b981")
            
            # Preencher campos
            data_ret = formatar_data_para_exibicao(dados.get('DataRetirada'))
            if data_ret:
                entry_data_retirada.delete(0, "end")
                entry_data_retirada.insert(0, data_ret)

            data_prev = formatar_data_para_exibicao(dados.get('DataPrevistaEntrega'))
            if data_prev:
                entry_data_prevista.delete(0, "end")
                entry_data_prevista.insert(0, data_prev)
            
            if dados.get('FormaRetirada'):
                combo_forma.set(dados['FormaRetirada'])
            
            if dados.get('QuantidadeReservada'):
                entry_quantidade.delete(0, "end")
                entry_quantidade.insert(0, str(dados['QuantidadeReservada']))
            
            if dados.get('Observacao'):
                entry_observacao.delete(0, "end")
                entry_observacao.insert(0, dados['Observacao'])
        else:
            label_info.configure(text="❌ Reserva não encontrada", text_color="#ef4444")
            mostrar_mensagem_padrao("Erro", erro or "Reserva não encontrada", "erro")
    
    btn_buscar = ctk.CTkButton(
        container,
        text="🔍 Buscar",
        command=buscar_reserva,
        font=("Segoe UI", 11, "bold"),
        fg_color="#4f46e5",
        hover_color="#818cf8",
        width=120,
        height=38
    )
    btn_buscar.pack(pady=10)
    
    # Campos editáveis
    entry_data_retirada = criar_seletor_data(container, "Data de Retirada")
    entry_data_prevista = criar_seletor_data(container, "Data de Devolução Prevista")
    
    combo_forma = criar_combobox(
        container,
        "Forma de Retirada",
        ["Retirada", "Entrega"]
    )
    
    entry_quantidade = criar_frame_entrada(container, "Quantidade", "")
    entry_observacao = criar_frame_entrada(container, "Observação", "")
    
    def salvar_edicao():
        if not reserva_encontrada:
            mostrar_mensagem_padrao("Erro", "Busque uma reserva primeiro", "erro")
            return
        
        dados_atualizacao = {}
        
        data_retirada = entry_data_retirada.get().strip()
        if data_retirada:
            if not interpretar_data(data_retirada):
                mostrar_mensagem_padrao("Erro", "Data de retirada inválida", "erro")
                return
            dados_atualizacao['DataRetirada'] = normalizar_data_para_api(data_retirada)
        
        data_prevista = entry_data_prevista.get().strip()
        if data_prevista:
            if not interpretar_data(data_prevista):
                mostrar_mensagem_padrao("Erro", "Data prevista inválida", "erro")
                return
            dados_atualizacao['DataPrevistaEntrega'] = normalizar_data_para_api(data_prevista)
        
        forma = combo_forma.get().strip()
        if forma:
            dados_atualizacao['FormaRetirada'] = forma
        
        quantidade = entry_quantidade.get().strip()
        if quantidade:
            try:
                dados_atualizacao['QuantidadeReservada'] = int(quantidade)
            except ValueError:
                mostrar_mensagem_padrao("Erro", "Quantidade deve ser um número", "erro")
                return
        
        observacao = entry_observacao.get().strip()
        if observacao:
            dados_atualizacao['Observacao'] = observacao
        
        if not dados_atualizacao:
            mostrar_mensagem_padrao("Aviso", "Nenhum campo para atualizar", "aviso")
            return
        
        sucesso, mensagem = api_client.atualizar_reserva(reserva_encontrada['ReservaID'], dados_atualizacao)
        
        if sucesso:
            mostrar_mensagem_padrao("Sucesso", "Reserva atualizada com sucesso!", "sucesso")
            callback_voltar()
        else:
            mostrar_mensagem_padrao("Erro", mensagem, "erro")
    
    criar_botoes_acao(
        container,
        "Salvar Alterações",
        salvar_edicao,
        callback_voltar
    )


def tela_cancelar_reserva(janela: ctk.CTkFrame, api_client, callback_voltar):
    """Tela para cancelar uma reserva."""
    limpar_frame(janela)
    
    # Header padronizado
    criar_header_padrao(janela, "Cancelar Reserva", "❌", callback_voltar)
    
    # Container simples
    container = criar_container_simples(janela)

    entry_reserva_id = criar_frame_entrada(container, "ID da Reserva", "Digite o ID para buscar direto")
    entry_nome_cliente = criar_frame_entrada(container, "Nome do Cliente", "Digite para filtrar reservas")

    frame_info, label_info = criar_frame_info(container, "Busque uma reserva para cancelar")

    reserva_encontrada = {}

    def formatar_data_resumo(data_original: str) -> str:
        if not data_original:
            return 'N/A'
        valor = formatar_data_para_exibicao(data_original)
        return valor or 'N/A'

    def atualizar_info_reserva(dados):
        if not dados:
            label_info.configure(text="❌ Reserva não encontrada", text_color="#ef4444")
            return

        nome_cliente = f"{dados.get('ClienteNome', '')} {dados.get('ClienteSobrenome', '')}".strip() or 'N/A'
        livro_nome = dados.get('LivroNome') or 'N/A'
        endereco = dados.get('ClienteEndereco') or 'N/A'
        status = (dados.get('Status') or 'N/A')

        info_texto = (
            f"⚠️ Reserva #{dados.get('ReservaID', 'N/A')} será cancelada!\n\n"
            f"Cliente: {nome_cliente}\n"
            f"Livro: {livro_nome}\n"
            f"Endereço: {endereco}\n"
            f"Status: {status}\n"
            f"Data Retirada: {formatar_data_resumo(dados.get('DataRetirada'))}\n"
            f"Data Prevista: {formatar_data_resumo(dados.get('DataPrevistaEntrega'))}"
        )

        label_info.configure(text=info_texto, text_color="#ef4444")

    def buscar_por_id():
        reserva_id = entry_reserva_id.get().strip()
        if not reserva_id or not reserva_id.isdigit():
            mostrar_mensagem_padrao("Erro", "Digite um ID válido", "erro")
            return

        sucesso, dados, erro = api_client.obter_reserva_por_id(int(reserva_id))

        if sucesso and dados:
            reserva_encontrada.clear()
            reserva_encontrada.update(dados)
            atualizar_info_reserva(dados)
        else:
            atualizar_info_reserva(None)
            mostrar_mensagem_padrao("Erro", erro or "Reserva não encontrada", "erro")

    def abrir_modal_reservas():
        sucesso, reservas, erro = api_client.listar_reservas('todas')

        if not sucesso:
            mostrar_mensagem_padrao("Erro", erro or "Não foi possível listar reservas", "erro")
            return

        nome_busca = entry_nome_cliente.get().strip().lower()
        if nome_busca:
            reservas = [
                r for r in reservas
                if isinstance(r, dict) and nome_busca in f"{r.get('ClienteNome', '')} {r.get('ClienteSobrenome', '')}".lower()
            ]

        if not reservas:
            mostrar_mensagem_padrao("Aviso", "Nenhuma reserva encontrada para os filtros informados", "aviso")
            return

        janela_lista = ctk.CTkToplevel()
        janela_lista.title("Selecionar Reserva")
        janela_lista.geometry("900x600")
        janela_lista.configure(fg_color="#0a0e27")
        janela_lista.grab_set()

        header = ctk.CTkFrame(janela_lista, fg_color="#0f1937")
        header.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(
            header,
            text=f"Reservas encontradas: {len(reservas)}",
            font=("Segoe UI", 18, "bold"),
            text_color="#6366f1"
        ).pack(pady=12)

        frame_tabela = ctk.CTkFrame(janela_lista, fg_color="transparent")
        frame_tabela.pack(fill="both", expand=True, padx=15, pady=10)

        canvas = ctk.CTkCanvas(frame_tabela, bg="#0a0e27", highlightthickness=0)
        scrollbar = ctk.CTkScrollbar(frame_tabela, command=canvas.yview)
        frame_interno = ctk.CTkFrame(canvas, fg_color="transparent")

        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        canvas_window = canvas.create_window((0, 0), window=frame_interno, anchor="nw")

        def configurar_scroll(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(canvas_window, width=event.width)

        frame_interno.bind("<Configure>", configurar_scroll)
        canvas.bind("<Configure>", configurar_scroll)

        def selecionar_reserva(dados):
            reserva_encontrada.clear()
            reserva_encontrada.update(dados)
            entry_reserva_id.delete(0, "end")
            entry_reserva_id.insert(0, str(dados.get('ReservaID', '')))
            atualizar_info_reserva(dados)
            janela_lista.destroy()

        for idx, reserva in enumerate(reservas):
            frame_item = ctk.CTkFrame(
                frame_interno,
                fg_color="#131829" if idx % 2 == 0 else "#0f1937",
                corner_radius=10
            )
            frame_item.pack(fill="x", pady=6, padx=8)

            cliente_nome = f"{reserva.get('ClienteNome', '')} {reserva.get('ClienteSobrenome', '')}".strip() or 'N/A'
            livro_nome = reserva.get('LivroNome') or 'N/A'
            status = (reserva.get('Status') or '').capitalize() or 'N/A'

            ctk.CTkLabel(
                frame_item,
                text=f"#{reserva.get('ReservaID', 'N/A')} - {cliente_nome}",
                font=("Segoe UI", 14, "bold"),
                text_color="#e0e7ff"
            ).pack(anchor="w", padx=15, pady=(10, 0))

            ctk.CTkLabel(
                frame_item,
                text=f"Livro: {livro_nome} | Status: {status}",
                font=("Segoe UI", 12),
                text_color="#a5b4fc"
            ).pack(anchor="w", padx=15, pady=(2, 10))

            ctk.CTkButton(
                frame_item,
                text="Selecionar",
                command=lambda r=reserva: selecionar_reserva(r),
                width=140,
                fg_color="#10b981",
                hover_color="#34d399"
            ).pack(anchor="e", padx=15, pady=(0, 12))

    botoes_frame = ctk.CTkFrame(container, fg_color="transparent")
    botoes_frame.pack(fill="x", pady=10)

    ctk.CTkButton(
        botoes_frame,
        text="🔍 Buscar por ID",
        command=buscar_por_id,
        font=("Segoe UI", 12, "bold"),
        fg_color="#4f46e5",
        hover_color="#818cf8",
        height=42
    ).pack(side="left", padx=5)

    ctk.CTkButton(
        botoes_frame,
        text="📄 Listar Reservas",
        command=abrir_modal_reservas,
        font=("Segoe UI", 12, "bold"),
        fg_color="#6366f1",
        hover_color="#818cf8",
        height=42
    ).pack(side="left", padx=5)

    def confirmar_cancelamento():
        if not reserva_encontrada:
            mostrar_mensagem_padrao("Erro", "Selecione ou busque uma reserva primeiro", "erro")
            return

        if not solicitar_senha_operador("Confirmar cancelamento"):
            return

        sucesso, mensagem = api_client.cancelar_reserva(reserva_encontrada['ReservaID'])

        if sucesso:
            mostrar_mensagem_padrao("Sucesso", "Reserva cancelada com sucesso!", "sucesso")
            callback_voltar()
        else:
            mostrar_mensagem_padrao("Erro", mensagem, "erro")
    
    criar_botoes_acao(
        container,
        "Confirmar Cancelamento",
        confirmar_cancelamento,
        callback_voltar
    )


def tela_finalizar_reserva(janela: ctk.CTkFrame, api_client, callback_voltar):
    """Tela para finalizar uma reserva (marcar como devolvida)."""
    limpar_frame(janela)
    
    # Header padronizado
    criar_header_padrao(janela, "Finalizar Reserva", "✅", callback_voltar)
    
    # Container com scroll
    container = criar_container_scroll(janela)
    
    # Info da reserva
    frame_info, label_info = criar_frame_info(container, "Selecione uma reserva ativa para finalizar")
    
    reserva_encontrada = {}
    
    def abrir_seletor_reservas():
        sucesso, reservas, erro = api_client.listar_reservas('ativa')
        if not sucesso or not reservas:
            mostrar_mensagem_padrao("Aviso", erro or "Nenhuma reserva ativa encontrada", "aviso")
            return
        
        janela_selecao = ctk.CTkToplevel()
        janela_selecao.title("📋 Reservas Ativas")
        janela_selecao.geometry("960x640")
        janela_selecao.configure(fg_color="#0a0e27")
        janela_selecao.attributes('-topmost', True)
        janela_selecao.after(100, lambda: janela_selecao.attributes('-topmost', False))
        
        header = ctk.CTkFrame(janela_selecao, fg_color="#0f1937")
        header.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(
            header,
            text=f"📋 {len(reservas)} reserva(s) ativa(s) encontrada(s)",
            font=("Segoe UI", 20, "bold"),
            text_color="#818cf8"
        ).pack(pady=15)
        
        frame_tabela = ctk.CTkFrame(janela_selecao, fg_color="#0a0e27")
        frame_tabela.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        canvas = ctk.CTkCanvas(frame_tabela, bg="#0a0e27", highlightthickness=0)
        scrollbar = ctk.CTkScrollbar(frame_tabela, command=canvas.yview)
        frame_interno = ctk.CTkFrame(canvas, fg_color="transparent")
        
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        canvas_window = canvas.create_window((0, 0), window=frame_interno, anchor="nw")
        
        def configurar_scroll(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(canvas_window, width=event.width)
        
        frame_interno.bind("<Configure>", configurar_scroll)
        canvas.bind("<Configure>", configurar_scroll)
        
        for idx, reserva in enumerate(reservas):
            frame_reserva = ctk.CTkFrame(
                frame_interno,
                fg_color="#131829" if idx % 2 == 0 else "#0f1937",
                corner_radius=10
            )
            frame_reserva.pack(fill="x", pady=5, padx=10)
            
            info_frame = ctk.CTkFrame(frame_reserva, fg_color="transparent")
            info_frame.pack(side="left", fill="both", expand=True, padx=15, pady=12)
            
            reserva_id = reserva.get('ReservaID') or reserva.get('id') or reserva.get('reserva_id')
            cliente_nome = f"{reserva.get('ClienteNome', '')} {reserva.get('ClienteSobrenome', '')}".strip()
            livro_nome = reserva.get('LivroNome') or reserva.get('livro_nome') or 'Livro não informado'
            data_prevista = formatar_data_para_exibicao(reserva.get('DataPrevistaEntrega'))
            data_retirada = formatar_data_para_exibicao(reserva.get('DataRetirada'))
            
            ctk.CTkLabel(
                info_frame,
                text=f"Reserva #{reserva_id} - {livro_nome}",
                font=("Segoe UI", 14, "bold"),
                text_color="#e0e7ff",
                anchor="w"
            ).pack(anchor="w")
            
            ctk.CTkLabel(
                info_frame,
                text=f"Cliente: {cliente_nome or 'N/A'} | Retirada: {data_retirada or 'N/A'} | Prevista: {data_prevista or 'N/A'}",
                font=("Segoe UI", 11),
                text_color="#a5b4fc",
                anchor="w"
            ).pack(anchor="w", pady=(6, 0))
            
            def criar_callback(info_reserva):
                def selecionar():
                    reserva_encontrada.clear()
                    reserva_encontrada.update(info_reserva)
                    reserva_id_sel = (
                        info_reserva.get('ReservaID')
                        or info_reserva.get('id')
                        or info_reserva.get('reserva_id')
                    )
                    cliente_sel = f"{info_reserva.get('ClienteNome', '')} {info_reserva.get('ClienteSobrenome', '')}".strip()
                    livro_sel = info_reserva.get('LivroNome') or info_reserva.get('livro_nome') or 'Livro não informado'
                    retirada_sel = formatar_data_para_exibicao(info_reserva.get('DataRetirada')) or 'N/A'
                    prevista_sel = formatar_data_para_exibicao(info_reserva.get('DataPrevistaEntrega')) or 'N/A'
                    status_sel = info_reserva.get('Status', 'N/A')
                    texto = (
                        f"✅ Reserva #{reserva_id_sel} selecionada!\n\n"
                        f"Cliente: {cliente_sel or 'N/A'}\n"
                        f"Livro: {livro_sel}\n"
                        f"Retirada: {retirada_sel}\n"
                        f"Prevista: {prevista_sel}\n"
                        f"Status: {status_sel}"
                    )
                    label_info.configure(text=texto, text_color="#10b981")
                    entry_data_entrega.delete(0, "end")
                    entry_data_entrega.insert(0, datetime.now().strftime("%d/%m/%y"))
                    janela_selecao.destroy()
                return selecionar
            
            btn_selecionar = ctk.CTkButton(
                frame_reserva,
                text="✓ Selecionar",
                command=criar_callback(reserva),
                font=("Segoe UI", 12, "bold"),
                fg_color="#10b981",
                hover_color="#34d399",
                width=140,
                height=42
            )
            btn_selecionar.pack(side="right", padx=15)
    
    btn_selecionar_reserva = ctk.CTkButton(
        container,
        text="📋 Selecionar Reserva Ativa",
        command=abrir_seletor_reservas,
        font=("Segoe UI", 13, "bold"),
        fg_color="#4f46e5",
        hover_color="#818cf8",
        height=45
    )
    btn_selecionar_reserva.pack(pady=10)
    
    # Data de entrega real
    entry_data_entrega = criar_seletor_data(container, "Data de Entrega Real *")
    entry_data_entrega.insert(0, datetime.now().strftime("%d/%m/%y"))
    
    def confirmar_finalizacao():
        if not reserva_encontrada:
            mostrar_mensagem_padrao("Erro", "Selecione uma reserva ativa", "erro")
            return
        
        data_entrega = entry_data_entrega.get().strip()
        if not data_entrega:
            mostrar_mensagem_padrao("Erro", "Preencha a data de entrega", "erro")
            return
        
        if not interpretar_data(data_entrega):
            mostrar_mensagem_padrao("Erro", "Data de entrega inválida", "erro")
            return
        
        if not solicitar_senha_operador("Confirmar finalização"):
            return

        data_para_api = normalizar_data_para_api(data_entrega)
        sucesso, mensagem = api_client.finalizar_reserva(reserva_encontrada['ReservaID'], data_para_api)
        
        if sucesso:
            mostrar_mensagem_padrao("Sucesso", "Reserva finalizada com sucesso!", "sucesso")
            callback_voltar()
        else:
            mostrar_mensagem_padrao("Erro", mensagem, "erro")
    
    criar_botoes_acao(
        container,
        "Confirmar Finalização",
        confirmar_finalizacao,
        callback_voltar
    )


def tela_editar_cliente_da_reserva(janela: ctk.CTkFrame, api_client, callback_voltar):
    """Tela para editar dados do cliente associado a uma reserva."""
    limpar_frame(janela)
    
    # Header padronizado
    criar_header_padrao(janela, "Editar Cliente (via Reserva)", "👤", callback_voltar)
    
    # Container com scroll
    container = criar_container_scroll(janela)
    
    # ID da reserva
    entry_reserva_id = criar_frame_entrada(container, "ID da Reserva *", "Digite o ID")
    
    # Info da reserva e cliente
    frame_info, label_info = criar_frame_info(container, "Busque uma reserva para editar o cliente")
    
    reserva_encontrada = {}
    cliente_id = None
    
    def buscar_reserva():
        nonlocal cliente_id
        
        reserva_id = entry_reserva_id.get().strip()
        if not reserva_id or not reserva_id.isdigit():
            mostrar_mensagem_padrao("Erro", "Digite um ID válido", "erro")
            return
        
        sucesso, dados, erro = api_client.obter_reserva_por_id(int(reserva_id))
        
        if sucesso and dados:
            reserva_encontrada.clear()
            reserva_encontrada.update(dados)
            cliente_id = dados.get('ClienteID')
            
            info_texto = f"""✅ Reserva #{dados.get('ReservaID', 'N/A')} encontrada!

Cliente ID: {cliente_id}
Livro ID: {dados.get('LivroID', 'N/A')}

Preencha os dados do cliente para editar:"""
            
            label_info.configure(text=info_texto, text_color="#10b981")
        else:
            label_info.configure(text="❌ Reserva não encontrada", text_color="#ef4444")
            mostrar_mensagem_padrao("Erro", erro or "Reserva não encontrada", "erro")
    
    btn_buscar = ctk.CTkButton(
        container,
        text="🔍 Buscar Reserva",
        command=buscar_reserva,
        font=("Segoe UI", 12, "bold"),
        fg_color="#4f46e5",
        hover_color="#818cf8",
        height=42
    )
    btn_buscar.pack(pady=10)
    
    # Campos de cliente
    entry_nome = criar_frame_entrada(container, "Nome (deixe em branco para não alterar)", "")
    entry_sobrenome = criar_frame_entrada(container, "Sobrenome (deixe em branco para não alterar)", "")
    
    def salvar_edicao_cliente():
        if not reserva_encontrada or not cliente_id:
            mostrar_mensagem_padrao("Erro", "Busque uma reserva primeiro", "erro")
            return
        
        dados_atualizacao = {}
        
        nome = entry_nome.get().strip()
        if nome:
            dados_atualizacao['Nome'] = nome
        
        sobrenome = entry_sobrenome.get().strip()
        if sobrenome:
            dados_atualizacao['Sobrenome'] = sobrenome
        
        if not dados_atualizacao:
            mostrar_mensagem_padrao("Aviso", "Nenhum campo para atualizar", "aviso")
            return
        
        # Usar endpoint de atualização de cliente
        sucesso, resposta, erro = api_client.put(f'/cliente/{cliente_id}', json=dados_atualizacao)
        
        if sucesso:
            mostrar_mensagem_padrao("Sucesso", "Dados do cliente atualizados com sucesso!", "sucesso")
            callback_voltar()
        else:
            mostrar_mensagem_padrao("Erro", erro or "Erro ao atualizar cliente", "erro")
    
    criar_botoes_acao(
        container,
        "Salvar Alterações",
        salvar_edicao_cliente,
        callback_voltar
    )


def tela_editar_livro_da_reserva(janela: ctk.CTkFrame, api_client, callback_voltar):
    """Tela para editar dados do livro associado a uma reserva."""
    limpar_frame(janela)
    
    # Header padronizado
    criar_header_padrao(janela, "Editar Livro (via Reserva)", "📖", callback_voltar)
    
    # Container com scroll
    container = criar_container_scroll(janela)
    
    # ID da reserva
    entry_reserva_id = criar_frame_entrada(container, "ID da Reserva *", "Digite o ID")
    
    # Info da reserva e livro
    frame_info, label_info = criar_frame_info(container, "Busque uma reserva para editar o livro")
    
    reserva_encontrada = {}
    livro_id = None
    
    def buscar_reserva():
        nonlocal livro_id
        
        reserva_id = entry_reserva_id.get().strip()
        if not reserva_id or not reserva_id.isdigit():
            mostrar_mensagem_padrao("Erro", "Digite um ID válido", "erro")
            return
        
        sucesso, dados, erro = api_client.obter_reserva_por_id(int(reserva_id))
        
        if sucesso and dados:
            reserva_encontrada.clear()
            reserva_encontrada.update(dados)
            livro_id = dados.get('LivroID')
            
            info_texto = f"""✅ Reserva #{dados.get('ReservaID', 'N/A')} encontrada!

Cliente ID: {dados.get('ClienteID')}
Livro ID: {livro_id}

Preencha os dados do livro para editar:"""
            
            label_info.configure(text=info_texto, text_color="#10b981")
        else:
            label_info.configure(text="❌ Reserva não encontrada", text_color="#ef4444")
            mostrar_mensagem_padrao("Erro", erro or "Reserva não encontrada", "erro")
    
    btn_buscar = ctk.CTkButton(
        container,
        text="🔍 Buscar Reserva",
        command=buscar_reserva,
        font=("Segoe UI", 12, "bold"),
        fg_color="#4f46e5",
        hover_color="#818cf8",
        height=42
    )
    btn_buscar.pack(pady=10)
    
    # Campos de livro
    entry_nome_livro = criar_frame_entrada(container, "Nome do Livro (deixe em branco para não alterar)", "")
    entry_autor = criar_frame_entrada(container, "Autor (deixe em branco para não alterar)", "")
    
    def salvar_edicao_livro():
        if not reserva_encontrada or not livro_id:
            mostrar_mensagem_padrao("Erro", "Busque uma reserva primeiro", "erro")
            return
        
        dados_atualizacao = {}
        
        nome_livro = entry_nome_livro.get().strip()
        if nome_livro:
            dados_atualizacao['NomeLivro'] = nome_livro
        
        autor = entry_autor.get().strip()
        if autor:
            dados_atualizacao['Autor'] = autor
        
        if not dados_atualizacao:
            mostrar_mensagem_padrao("Aviso", "Nenhum campo para atualizar", "aviso")
            return
        
        # Usar endpoint de atualização de livro
        sucesso, resposta, erro = api_client.put(f'/livro/{livro_id}', json=dados_atualizacao)
        
        if sucesso:
            mostrar_mensagem_padrao("Sucesso", "Dados do livro atualizados com sucesso!", "sucesso")
            callback_voltar()
        else:
            mostrar_mensagem_padrao("Erro", erro or "Erro ao atualizar livro", "erro")
    
    criar_botoes_acao(
        container,
        "Salvar Alterações",
        salvar_edicao_livro,
        callback_voltar
    )
