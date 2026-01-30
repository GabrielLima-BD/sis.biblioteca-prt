"""
Cliente HTTP para comunicação com a API
"""
import logging
from datetime import datetime
import requests
from typing import Dict, Any, Optional
from requests.exceptions import (
    RequestException,
    Timeout,
    ConnectionError,
    HTTPError,
)
from src.config.settings import (
    API_BASE_URL,
    API_TIMEOUT,
    API_AUTH_EMAIL,
    API_AUTH_PASSWORD,
)
from src.utils.formatters import normalizar_data_para_api


logger = logging.getLogger(__name__)


class APIClient:
    """Cliente para fazer requisições HTTP para a API"""
    
    def __init__(
        self,
        base_url: str = API_BASE_URL,
        timeout: int = API_TIMEOUT,
        email: str = API_AUTH_EMAIL,
        senha: str = API_AUTH_PASSWORD,
    ):
        """
        Inicializa o cliente da API
        
        Args:
            base_url: URL base da API
            timeout: Tempo máximo de espera em segundos
        """
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session()
        self._access_token: Optional[str] = None
        self._refresh_token: Optional[str] = None
        self._email = email
        self._senha = senha

        if self._email and self._senha:
            logger.info('Autenticação desativada: a API agora opera sem tokens.')
        self.session.headers.update({'Content-Type': 'application/json'})

    def _definir_token(self, token: Optional[str]) -> None:
        """Atualiza o header Authorization conforme o token atual."""
        if token:
            self.session.headers.update({'Authorization': f'Bearer {token}'})
        else:
            self.session.headers.pop('Authorization', None)

    def _autenticar_inicial(self) -> None:
        """Executa login inicial usando as credenciais configuradas."""
        if not self._executar_login():
            logger.error('Falha ao autenticar na inicialização da API; endpoints protegidos indisponíveis.')

    def _executar_login(self) -> bool:
        """Realiza login e armazena tokens quando possível."""
        if not self._email or not self._senha:
            return False

        payload = {
            'email': self._email,
            'senha': self._senha,
        }

        url = f"{self.base_url}/auth/login"
        auth_backup = self.session.headers.get('Authorization')
        if auth_backup:
            self.session.headers.pop('Authorization', None)

        try:
            response = self.session.post(url, json=payload, timeout=self.timeout)
        except (Timeout, ConnectionError, RequestException) as exc:
            logger.error('Erro ao autenticar na API: %s', exc)
            if auth_backup:
                self.session.headers['Authorization'] = auth_backup
            return False

        if response.status_code != 200:
            mensagem = self._extrair_mensagem_erro(response)
            if response.status_code == 401 and self._tentar_registro_automatico():
                return self._executar_login()
            logger.error('Falha no login (%s): %s', response.status_code, mensagem)
            if auth_backup:
                self.session.headers['Authorization'] = auth_backup
            return False

        try:
            dados = response.json()
        except ValueError:
            logger.error('Resposta inválida ao autenticar: JSON ausente.')
            if auth_backup:
                self.session.headers['Authorization'] = auth_backup
            return False

        tokens = dados.get('tokens', {})
        access_token = tokens.get('accessToken')
        refresh_token = tokens.get('refreshToken')

        if not access_token:
            logger.error('Resposta de login sem accessToken.')
            if auth_backup:
                self.session.headers['Authorization'] = auth_backup
            return False

        self._atualizar_tokens(access_token, refresh_token)
        return True

    def _atualizar_tokens(self, access_token: Optional[str], refresh_token: Optional[str] = None) -> None:
        """Persistir tokens atuais e atualizar cabeçalho Authorization."""
        self._access_token = access_token
        if refresh_token:
            self._refresh_token = refresh_token
        self._definir_token(access_token)

    def _renovar_token(self) -> bool:
        """Tenta renovar o access token usando o refresh token armazenado."""
        if not self._refresh_token:
            return False

        url = f"{self.base_url}/auth/refresh"
        payload = {'refreshToken': self._refresh_token}

        try:
            response = self.session.post(url, json=payload, timeout=self.timeout)
        except (Timeout, ConnectionError, RequestException) as exc:
            logger.error('Erro ao renovar token: %s', exc)
            return False

        if response.status_code != 200:
            mensagem = self._extrair_mensagem_erro(response)
            logger.warning('Falha ao renovar token (%s): %s', response.status_code, mensagem)
            return False

        try:
            dados = response.json()
        except ValueError:
            logger.error('Resposta inválida ao renovar token: JSON ausente.')
            return False

        tokens = dados.get('tokens', {})
        access_token = tokens.get('accessToken')
        refresh_token = tokens.get('refreshToken', self._refresh_token)

        if not access_token:
            logger.error('Resposta de renovação sem accessToken.')
            return False

        self._atualizar_tokens(access_token, refresh_token)
        return True

    def _tentar_registro_automatico(self) -> bool:
        """Tenta registrar o usuário padrão quando login falhar por credenciais inexistentes."""
        if not self._email or not self._senha:
            return False

        url = f"{self.base_url}/auth/register"
        nome_base = self._email.split('@')[0] if '@' in self._email else 'Biblioteca'
        payload = {
            'email': self._email,
            'senha': self._senha,
            'nome': nome_base.replace('.', ' ').title()
        }

        try:
            response = self.session.post(url, json=payload, timeout=self.timeout)
        except (Timeout, ConnectionError, RequestException) as exc:
            logger.error('Erro ao tentar registro automático: %s', exc)
            return False

        if response.status_code == 201:
            logger.info('Registro automático criado para %s', self._email)
            return True

        if response.status_code == 409:
            logger.info('Usuário %s já existe; prosseguindo com login.', self._email)
            return True

        mensagem = self._extrair_mensagem_erro(response)
        logger.error('Registro automático falhou (%s): %s', response.status_code, mensagem)
        return False

    def _tentar_reautenticacao(self) -> bool:
        """Tenta renovar o token ou efetuar novo login."""
        if self._renovar_token():
            return True
        return self._executar_login()

    def autenticar(self, email: str, senha: str) -> bool:
        """Permite definir credenciais em tempo de execução e autenticar."""
        self._email = email
        self._senha = senha
        return self._executar_login()

    @staticmethod
    def _extrair_mensagem_erro(response: requests.Response) -> str:
        """Extrai mensagem amigável de um response HTTP."""
        try:
            payload = response.json()
        except ValueError:
            texto = response.text.strip()
            return texto or f'HTTP {response.status_code}'

        for chave in ('message', 'mensagem', 'error', 'detail', 'errors'):
            valor = payload.get(chave)
            if isinstance(valor, str) and valor.strip():
                return valor.strip()
            if isinstance(valor, dict):
                return next((str(v) for v in valor.values() if v), f'HTTP {response.status_code}')
            if isinstance(valor, list):
                for item in valor:
                    if isinstance(item, str) and item.strip():
                        return item.strip()
                    if isinstance(item, dict):
                        mensagem = next((str(v) for v in item.values() if v), None)
                        if mensagem:
                            return mensagem
        return f'HTTP {response.status_code}'
    
    def _fazer_requisicao(self, metodo: str, endpoint: str, 
                         **kwargs) -> tuple[bool, Dict[str, Any], str]:
        """
        Faz uma requisição HTTP genérica
        
        Args:
            metodo: Método HTTP (GET, POST, PUT, DELETE, PATCH)
            endpoint: Endpoint da API
            **kwargs: Argumentos adicionais para requests
        
        Returns:
            tuple: (sucesso, dados, mensagem_erro)
        """
        url = f"{self.base_url}{endpoint}"
        kwargs['timeout'] = self.timeout
        tentativas = 0

        while tentativas < 2:
            tentativas += 1

            try:
                response = self.session.request(metodo, url, **kwargs)
            except Timeout:
                return False, {}, 'Timeout: A API levou muito tempo para responder'
            except ConnectionError:
                return False, {}, 'Erro de conexão: Não foi possível conectar à API'
            except RequestException as exc:
                return False, {}, f'Erro na requisição: {str(exc)}'

            if response.status_code == 401:
                mensagem = self._extrair_mensagem_erro(response)
                return False, {}, f'Não autorizado: {mensagem}'

            try:
                response.raise_for_status()
            except HTTPError as exc:
                mensagem = self._extrair_mensagem_erro(response)
                logger.warning('Falha na requisição %s %s: %s', metodo.upper(), endpoint, mensagem)
                return False, {}, mensagem or str(exc)

            try:
                return True, response.json(), ''
            except ValueError:
                return True, {}, ''

        return False, {}, 'Não foi possível completar a requisição após reautenticar'
    
    def get(self, endpoint: str, params: Optional[Dict] = None) -> tuple[bool, Dict, str]:
        """Faz uma requisição GET"""
        return self._fazer_requisicao('GET', endpoint, params=params)
    
    def post(self, endpoint: str, json: Optional[Dict] = None) -> tuple[bool, Dict, str]:
        """Faz uma requisição POST"""
        return self._fazer_requisicao('POST', endpoint, json=json)
    
    def put(self, endpoint: str, json: Optional[Dict] = None) -> tuple[bool, Dict, str]:
        """Faz uma requisição PUT"""
        return self._fazer_requisicao('PUT', endpoint, json=json)
    
    def patch(self, endpoint: str, json: Optional[Dict] = None) -> tuple[bool, Dict, str]:
        """Faz uma requisição PATCH"""
        return self._fazer_requisicao('PATCH', endpoint, json=json)
    
    def delete(self, endpoint: str) -> tuple[bool, Dict, str]:
        """Faz uma requisição DELETE"""
        return self._fazer_requisicao('DELETE', endpoint)
    
    def fechar(self):
        """Fecha a sessão HTTP"""
        self.session.close()
    
    def _processar_resposta_lista(self, sucesso: bool, dados: Dict, erro: str, chave_dados: str = 'data') -> tuple[bool, list, str]:
        """
        Helper para processar respostas que retornam listas.
        
        Args:
            sucesso: Se a requisição foi bem-sucedida
            dados: Dados retornados
            erro: Mensagem de erro
            chave_dados: Chave onde estão os dados (default: 'data')
            
        Returns:
            tuple: (sucesso, lista_dados, mensagem_erro)
        """
        if sucesso:
            resultado = dados.get(chave_dados, [])
            lista = resultado if isinstance(resultado, list) else [resultado] if resultado else []
            return True, lista, ''
        return False, [], erro
    
    def _processar_resposta_objeto(self, sucesso: bool, dados: Dict, erro: str, chave_dados: str = 'data') -> tuple[bool, Dict, str]:
        """
        Helper para processar respostas que retornam objetos.
        
        Args:
            sucesso: Se a requisição foi bem-sucedida
            dados: Dados retornados
            erro: Mensagem de erro
            chave_dados: Chave onde estão os dados (default: 'data')
            
        Returns:
            tuple: (sucesso, dados_objeto, mensagem_erro)
        """
        if sucesso:
            return True, dados.get(chave_dados, {}), ''
        return False, {}, erro
    
    # ==================== Métodos de Consulta de Clientes ====================
    
    def buscar_cliente_por_nome(self, nome: str) -> tuple[bool, list, str]:
        """
        Busca clientes por nome.
        
        Args:
            nome: Nome do cliente para buscar
            
        Returns:
            tuple: (sucesso, lista_clientes, mensagem_erro)
        """
        if not nome or not nome.strip():
            return False, [], 'Nome não pode ser vazio'
        
        sucesso, dados, erro = self.get('/cliente', params={'Nome': nome.strip()})
        return self._processar_resposta_lista(sucesso, dados, erro)
    
    def buscar_cliente_por_cpf(self, cpf: str) -> tuple[bool, Dict, str]:
        """
        Busca cliente por CPF.
        
        Args:
            cpf: CPF do cliente (com ou sem formatação)
            
        Returns:
            tuple: (sucesso, dados_cliente, mensagem_erro)
        """
        if not cpf or not cpf.strip():
            return False, {}, 'CPF não pode ser vazio'
        
        # Remover formatação do CPF
        cpf_limpo = cpf.strip().replace(".", "").replace("-", "").replace(" ", "")
        
        if len(cpf_limpo) != 11 or not cpf_limpo.isdigit():
            return False, {}, 'CPF inválido'
        
        sucesso, dados, erro = self.get(f'/cliente/cpf/{cpf_limpo}')
        return self._processar_resposta_objeto(sucesso, dados, erro)
    
    def buscar_clientes_por_estado(self, estado: str) -> tuple[bool, list, str]:
        """
        Busca clientes por estado.
        
        Args:
            estado: Sigla ou nome do estado
            
        Returns:
            tuple: (sucesso, lista_clientes, mensagem_erro)
        """
        if not estado or not estado.strip():
            return False, [], 'Estado não pode ser vazio'
        
        sucesso, dados, erro = self.get('/endereco', params={'Estado': estado.strip().upper()})
        return self._processar_resposta_lista(sucesso, dados, erro)
    
    # ==================== Métodos de Consulta de Livros ====================
    
    def buscar_livro_por_nome(self, nome: str) -> tuple[bool, list, str]:
        """
        Busca livros por nome.
        
        Args:
            nome: Nome do livro para buscar
            
        Returns:
            tuple: (sucesso, lista_livros, mensagem_erro)
        """
        if not nome or not nome.strip():
            return False, [], 'Nome do livro não pode ser vazio'
        
        sucesso, dados, erro = self.get('/livro', params={'NomeLivro': nome.strip()})
        return self._processar_resposta_lista(sucesso, dados, erro)
    
    def buscar_livros_por_autor(self, autor: str) -> tuple[bool, list, str]:
        """
        Busca livros por autor.
        
        Args:
            autor: Nome do autor
            
        Returns:
            tuple: (sucesso, lista_livros, mensagem_erro)
        """
        if not autor or not autor.strip():
            return False, [], 'Nome do autor não pode ser vazio'
        
        sucesso, dados, erro = self.get('/livro/autor', params={'NomeAutor': autor.strip()})
        return self._processar_resposta_lista(sucesso, dados, erro)
    
    def buscar_livros_por_genero(self, genero: str) -> tuple[bool, list, str]:
        """
        Busca livros por gênero.
        
        Args:
            genero: Nome do gênero
            
        Returns:
            tuple: (sucesso, lista_livros, mensagem_erro)
        """
        if not genero or not genero.strip():
            return False, [], 'Gênero não pode ser vazio'
        
        sucesso, dados, erro = self.get('/genero', params={'NomeGenero': genero.strip()})
        return self._processar_resposta_lista(sucesso, dados, erro)

    def listar_generos(self) -> tuple[bool, list, str]:
        """Lista os gêneros existentes no banco.

        Usa GET /genero sem query string para obter {GeneroID, NomeGenero}.

        Returns:
            tuple: (sucesso, lista_generos, mensagem_erro)
        """
        sucesso, dados, erro = self.get('/genero')
        if sucesso:
            resultado = dados.get('data', dados.get('dados', []))
            if resultado is None:
                return True, [], ''
            generos = resultado if isinstance(resultado, list) else [resultado]
            return True, generos, ''

        return False, [], erro
    
    def buscar_livro_por_id(self, livro_id: str) -> tuple[bool, Dict, str]:
        """
        Busca livro por ID.
        
        Args:
            livro_id: ID do livro
            
        Returns:
            tuple: (sucesso, dados_livro, mensagem_erro)
        """
        if not livro_id or not str(livro_id).strip():
            return False, {}, 'ID do livro não pode ser vazio'
        
        sucesso, dados, erro = self.get(f'/livro/{livro_id}')
        return self._processar_resposta_objeto(sucesso, dados, erro)
    
    # ==================== Métodos de Cadastro ====================
    
    def cadastrar_cliente(self, dados_cliente: Dict[str, Any]) -> tuple[bool, str]:
        """
        Cadastra um novo cliente.
        
        Args:
            dados_cliente: Dicionário com dados do cliente
            
        Returns:
            tuple: (sucesso, mensagem)
        """
        if not dados_cliente:
            return False, 'Dados do cliente não podem ser vazios'
        
        # A API espera campos "flat" (não aninhados) em /cliente.
        # A GUI envia parte do endereço dentro de "endereco"; aqui fazemos a
        # compatibilização para manter a tela funcionando.
        payload: Dict[str, Any] = dict(dados_cliente)

        endereco = payload.pop('endereco', None)
        if isinstance(endereco, dict):
            for chave, valor in endereco.items():
                payload.setdefault(chave, valor)

        # Normalizações e tipos: a API valida strings (usa .trim() no Node).
        if 'CPF' in payload and payload['CPF'] is not None:
            cpf_str = str(payload['CPF']).strip()
            payload['CPF'] = cpf_str.replace('.', '').replace('-', '')

        for campo in ('CEP', 'Rua', 'Numero', 'Bairro', 'Cidade', 'Estado'):
            if campo in payload and payload[campo] is not None:
                payload[campo] = str(payload[campo]).strip()

        campos_obrigatorios = [
            'Nome',
            'Sobrenome',
            'CPF',
            'DataNascimento',
            'DataAfiliacao',
            'CEP',
            'Rua',
            'Numero',
            'Bairro',
            'Cidade',
            'Estado',
        ]

        for campo in campos_obrigatorios:
            valor = payload.get(campo)
            if valor is None or (isinstance(valor, str) and not valor.strip()):
                return False, f'Campo obrigatório ausente: {campo}'

        sucesso, dados, erro = self.post('/cliente', json=payload)
        
        if sucesso:
            return True, 'Cliente cadastrado com sucesso!'
        return False, erro or 'Erro ao cadastrar cliente'
    
    def cadastrar_livro(self, dados_livro: Dict[str, Any]) -> tuple[bool, str]:
        """
        Cadastra um novo livro.
        
        Args:
            dados_livro: Dicionário com dados do livro
            
        Returns:
            tuple: (sucesso, mensagem)
        """
        if not dados_livro:
            return False, 'Dados do livro não podem ser vazios'
        
        # Validações básicas (alinhadas com a GUI e a API)
        campos_obrigatorios = [
            'NomeLivro',
            'Autor',
            'Editora',
            'DataPublicacao',
            'Idioma',
            'QuantidadePaginas',
            'NomeGenero',
            'QuantidadeDisponivel',
        ]
        for campo in campos_obrigatorios:
            valor = dados_livro.get(campo)
            if valor is None or (isinstance(valor, str) and not valor.strip()):
                return False, f'Campo obrigatório ausente: {campo}'

        # Normalizações leves
        for campo_str in ('NomeLivro', 'Autor', 'Editora', 'Idioma', 'NomeGenero'):
            if campo_str in dados_livro and dados_livro[campo_str] is not None:
                dados_livro[campo_str] = str(dados_livro[campo_str]).strip()

        try:
            dados_livro['QuantidadePaginas'] = int(dados_livro['QuantidadePaginas'])
        except (TypeError, ValueError):
            return False, 'QuantidadePaginas deve ser um número inteiro'

        try:
            dados_livro['QuantidadeDisponivel'] = int(dados_livro['QuantidadeDisponivel'])
        except (TypeError, ValueError):
            return False, 'QuantidadeDisponivel deve ser um número inteiro'
        
        sucesso, dados, erro = self.post('/livro', json=dados_livro)
        
        if sucesso:
            return True, 'Livro cadastrado com sucesso!'
        return False, erro or 'Erro ao cadastrar livro'
    
    def cadastrar_reserva(self, dados_reserva: Dict[str, Any]) -> tuple[bool, str]:
        """
        Cadastra uma nova reserva.
        
        Args:
            dados_reserva: Dicionário com dados da reserva
            
        Returns:
            tuple: (sucesso, mensagem)
        """
        if not dados_reserva:
            return False, 'Dados da reserva não podem ser vazios'
        
        # A API espera: CPFReserva, NomeLivro, LivroID, DataRetirada, DataVolta, Entrega, QntdLivro, Observacao
        # Enviamos o payload direto como montado na GUI
        
        sucesso, dados, erro = self.post('/reservas', json=dados_reserva)
        
        if sucesso:
            return True, 'Reserva cadastrada com sucesso!'
        return False, erro or 'Erro ao cadastrar reserva'
    
    def criar_reserva(self, dados_reserva: Dict[str, Any]) -> tuple[bool, str]:
        """
        Alias para cadastrar_reserva - cria uma nova reserva.
        Mantido para compatibilidade com código existente.
        
        Args:
            dados_reserva: Dicionário com dados da reserva
            
        Returns:
            tuple: (sucesso, mensagem)
        """
        return self.cadastrar_reserva(dados_reserva)
    
    # ==================== Métodos de Reservas ====================
    
    def listar_reservas_ativas(self) -> tuple[bool, list, str]:
        """
        Lista todas as reservas ativas.
        
        Returns:
            tuple: (sucesso, lista_reservas, mensagem_erro)
        """
        sucesso, dados, erro = self.get('/reservas', params={'status': 'ativa'})
        return self._processar_resposta_lista(sucesso, dados, erro)
    
    def registrar_devolucao(self, reserva_id: int, data_devolucao: str) -> tuple[bool, str]:
        """
        Registra devolução de um livro.
        
        Args:
            reserva_id: ID da reserva
            data_devolucao: Data da devolução (formato: YYYY-MM-DD)
            
        Returns:
            tuple: (sucesso, mensagem)
        """
        if not reserva_id or reserva_id <= 0:
            return False, 'ID da reserva inválido'
        
        if not data_devolucao or not data_devolucao.strip():
            return False, 'Data de devolução não pode ser vazia'
        
        dados = {
            'reserva_id': reserva_id,
            'data_devolucao_real': data_devolucao.strip()
        }
        
        sucesso, resposta, erro = self.post('/devolucoes', json=dados)
        
        if sucesso:
            return True, 'Devolução registrada com sucesso!'
        return False, erro or 'Erro ao registrar devolução'
    
    def listar_reservas(self, filtro_status: str = 'todas') -> tuple[bool, list, str]:
        """
        Lista reservas com filtro opcional.
        
        Args:
            filtro_status: 'todas', 'ativas', 'finalizadas' ou 'canceladas'
            
        Returns:
            tuple: (sucesso, lista_reservas, mensagem_erro)
        """
        params = {}
        if filtro_status and filtro_status != 'todas':
            params['status'] = filtro_status
        
        sucesso, dados, erro = self.get('/reservas', params=params)
        return self._processar_resposta_lista(sucesso, dados, erro)
    
    def obter_reserva_por_id(self, reserva_id: int) -> tuple[bool, Dict, str]:
        """
        Obtém detalhes de uma reserva específica.
        
        Args:
            reserva_id: ID da reserva
            
        Returns:
            tuple: (sucesso, dados_reserva, mensagem_erro)
        """
        if not reserva_id or reserva_id <= 0:
            return False, {}, 'ID da reserva inválido'
        
        sucesso, dados, erro = self.get(f'/reservas/{reserva_id}')
        return self._processar_resposta_objeto(sucesso, dados, erro)
    
    def atualizar_reserva(self, reserva_id: int, dados_atualizacao: Dict[str, Any]) -> tuple[bool, str]:
        """
        Atualiza todos os dados de uma reserva.
        
        Args:
            reserva_id: ID da reserva
            dados_atualizacao: Dicionário com dados a atualizar
            
        Returns:
            tuple: (sucesso, mensagem)
        """
        if not reserva_id or reserva_id <= 0:
            return False, 'ID da reserva inválido'
        
        if not dados_atualizacao:
            return False, 'Nenhum dado para atualizar'
        
        sucesso, resposta, erro = self.put(f'/reservas/{reserva_id}', json=dados_atualizacao)
        
        if sucesso:
            return True, 'Reserva atualizada com sucesso!'
        return False, erro or 'Erro ao atualizar reserva'
    
    def alterar_status_reserva(self, reserva_id: int, novo_status: str, 
                              data_entrega: str = None) -> tuple[bool, str]:
        """
        Altera o status de uma reserva (finalizada, cancelada, etc).
        
        Args:
            reserva_id: ID da reserva
            novo_status: 'ativa', 'finalizada' ou 'cancelada'
            data_entrega: Data de entrega real (opcional)
            
        Returns:
            tuple: (sucesso, mensagem)
        """
        if not reserva_id or reserva_id <= 0:
            return False, 'ID da reserva inválido'
        
        if novo_status not in ['ativa', 'finalizada', 'cancelada']:
            return False, f'Status inválido: {novo_status}'
        
        dados = {'status': novo_status}
        if data_entrega:
            dados['DataEntrega'] = data_entrega
        
        sucesso, resposta, erro = self.patch(f'/reservas/{reserva_id}', json=dados)
        
        if sucesso:
            return True, f'Reserva marcada como {novo_status}!'
        return False, erro or 'Erro ao alterar status da reserva'
    
    def cancelar_reserva(self, reserva_id: int) -> tuple[bool, str]:
        """
        Cancela uma reserva.
        
        Args:
            reserva_id: ID da reserva
            
        Returns:
            tuple: (sucesso, mensagem)
        """
        if not reserva_id or reserva_id <= 0:
            return False, 'ID da reserva inválido'
        
        sucesso, resposta, erro = self.delete(f'/reservas/{reserva_id}')
        
        if sucesso:
            return True, 'Reserva cancelada com sucesso!'
        return False, erro or 'Erro ao cancelar reserva'
    
    def finalizar_reserva(self, reserva_id: int, data_entrega: str) -> tuple[bool, str]:
        """
        Finaliza uma reserva marcando como devolvida.
        
        Args:
            reserva_id: ID da reserva
            data_entrega: Data de entrega real (formato: DD/MM/YYYY ou YYYY-MM-DD)
            
        Returns:
            tuple: (sucesso, mensagem)
        """
        if not reserva_id or reserva_id <= 0:
            return False, 'ID da reserva inválido'
        
        if not data_entrega or not data_entrega.strip():
            return False, 'Data de entrega não pode ser vazia'
        
        # A API faz a conversão internamente
        return self.alterar_status_reserva(reserva_id, 'finalizada', data_entrega.strip())
    
    # ==================== Métodos de Multas ====================
    
    def listar_multas(self,
                      cliente_id: Optional[int] = None,
                      status: Optional[str] = None,
                      vencidas: bool = False,
                      reserva_id: Optional[int] = None,
                      multa_id: Optional[int] = None) -> tuple[bool, list, str]:
        """Lista multas com filtros opcionais."""
        params: Dict[str, Any] = {}

        if cliente_id is not None:
            try:
                id_cliente = int(cliente_id)
            except (TypeError, ValueError):
                return False, [], 'ID do cliente inválido'
            if id_cliente <= 0:
                return False, [], 'ID do cliente inválido'
            params['clienteId'] = str(id_cliente)

        if reserva_id is not None:
            try:
                id_reserva = int(reserva_id)
            except (TypeError, ValueError):
                return False, [], 'ID da reserva inválido'
            if id_reserva <= 0:
                return False, [], 'ID da reserva inválido'
            params['reservaId'] = str(id_reserva)

        if multa_id is not None:
            try:
                id_multa = int(multa_id)
            except (TypeError, ValueError):
                return False, [], 'ID da multa inválido'
            if id_multa <= 0:
                return False, [], 'ID da multa inválido'
            params['multaId'] = str(id_multa)

        if status:
            params['status'] = str(status).lower()

        if vencidas:
            params['vencidas'] = 'true'

        sucesso, dados, erro = self.get('/multas', params=params or None)

        if sucesso:
            resultado = dados.get('data', dados.get('dados', []))
            if resultado is None:
                return True, [], ''
            multas = resultado if isinstance(resultado, list) else [resultado]
            return True, multas, ''

        return False, [], erro

    def listar_multas_por_cliente(self, cliente_id: int) -> tuple[bool, list, str]:
        """Lista multas de um cliente específico."""
        return self.listar_multas(cliente_id=cliente_id)

    def listar_multas_pendentes(self) -> tuple[bool, list, str]:
        """Lista todas as multas pendentes."""
        return self.listar_multas(status='pendente')

    def criar_multa(self, reserva_id: int, valor: float, data_vencimento: str) -> tuple[bool, str]:
        """Registra manualmente uma multa vinculada a uma reserva."""
        if not reserva_id or reserva_id <= 0:
            return False, 'ID da reserva inválido'

        try:
            valor_float = float(valor)
        except (TypeError, ValueError):
            return False, 'Valor inválido'

        if valor_float <= 0:
            return False, 'Valor deve ser maior que zero'

        if not data_vencimento or not data_vencimento.strip():
            return False, 'Data de vencimento é obrigatória'

        payload = {
            'ReservaID': int(reserva_id),
            'Valor': valor_float,
            'DataVencimento': normalizar_data_para_api(data_vencimento.strip()),
        }

        sucesso, resposta, erro = self.post('/multas', json=payload)

        if sucesso:
            return True, 'Multa registrada com sucesso!'

        return False, erro or 'Erro ao registrar multa'

    def pagar_multa(self, multa_id: int, data_pagamento: Optional[str] = None) -> tuple[bool, str]:
        """Registra pagamento de uma multa."""
        if not multa_id or multa_id <= 0:
            return False, 'ID da multa inválido'

        data_pagamento_norm = normalizar_data_para_api(
            (data_pagamento or datetime.now().strftime('%d/%m/%Y')).strip()
        )

        payload = {'DataPagamento': data_pagamento_norm}

        sucesso, resposta, erro = self.patch(f'/multas/{int(multa_id)}/pagar', json=payload)

        if sucesso:
            return True, 'Multa marcada como paga!'

        return False, erro or 'Erro ao registrar pagamento da multa'
    
    # ==================== Métodos de Atualização ====================
    
    def atualizar_cliente(self, cliente_id: int, dados_cliente: Dict[str, Any]) -> tuple[bool, str]:
        """
        Atualiza dados de um cliente.
        
        Args:
            cliente_id: ID do cliente
            dados_cliente: Dicionário com dados atualizados
            
        Returns:
            tuple: (sucesso, mensagem)
        """
        if not cliente_id or cliente_id <= 0:
            return False, 'ID do cliente inválido'
        
        if not dados_cliente:
            return False, 'Dados para atualização não podem ser vazios'
        
        sucesso, dados, erro = self.put(f'/cliente/{cliente_id}', json=dados_cliente)
        
        if sucesso:
            return True, 'Cliente atualizado com sucesso!'
        return False, erro or 'Erro ao atualizar cliente'
    
    def atualizar_livro(self, livro_id: int, dados_livro: Dict[str, Any]) -> tuple[bool, str]:
        """
        Atualiza dados de um livro.
        
        Args:
            livro_id: ID do livro
            dados_livro: Dicionário com dados atualizados
            
        Returns:
            tuple: (sucesso, mensagem)
        """
        if not livro_id or livro_id <= 0:
            return False, 'ID do livro inválido'
        
        if not dados_livro:
            return False, 'Dados para atualização não podem ser vazios'
        
        sucesso, dados, erro = self.put(f'/livro/{livro_id}', json=dados_livro)
        
        if sucesso:
            return True, 'Livro atualizado com sucesso!'
        return False, erro or 'Erro ao atualizar livro'
    
    # ==================== Métodos de Exclusão ====================
    
    def deletar_cliente(self, cliente_id: int) -> tuple[bool, str]:
        """
        Deleta um cliente.
        
        Args:
            cliente_id: ID do cliente
            
        Returns:
            tuple: (sucesso, mensagem)
        """
        if not cliente_id or cliente_id <= 0:
            return False, 'ID do cliente inválido'
        
        sucesso, dados, erro = self.delete(f'/cliente/{cliente_id}')
        
        if sucesso:
            return True, 'Cliente deletado com sucesso!'
        return False, erro or 'Erro ao deletar cliente'
    
    def deletar_livro(self, livro_id: int) -> tuple[bool, str]:
        """
        Deleta um livro.
        
        Args:
            livro_id: ID do livro
            
        Returns:
            tuple: (sucesso, mensagem)
        """
        if not livro_id or livro_id <= 0:
            return False, 'ID do livro inválido'
        
        sucesso, dados, erro = self.delete(f'/livro/{livro_id}')
        
        if sucesso:
            return True, 'Livro deletado com sucesso!'
        return False, erro or 'Erro ao deletar livro'


# Instância global do cliente
api_client = APIClient()
