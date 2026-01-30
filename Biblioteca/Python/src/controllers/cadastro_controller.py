"""
Controllers para operações de cadastro
"""
from typing import Tuple, Dict, Optional

from src.models.api_client import api_client
from src.utils.validators import Validators, sanitizar_entrada
from src.utils.formatters import normalizar_data_para_api


class APIClient:
    """Façade para permitir patching nos testes.

    Os testes fazem `@patch('src.controllers.cadastro_controller.APIClient.post')`.
    """

    @staticmethod
    def post(endpoint: str, json: Optional[Dict] = None) -> tuple[bool, Dict, Optional[str]]:
        sucesso, payload, erro = api_client.post(endpoint, json=json)
        if not sucesso:
            return False, {}, erro or 'Erro na requisição'
        return True, payload if isinstance(payload, dict) else {}, None


class CadastroController:
    """Controller para operações de cadastro"""
    
    @staticmethod
    def validar_dados_cliente(dados: Dict[str, str]) -> Tuple[bool, str]:
        """
        Valida dados do cliente antes de enviar para API
        
        Args:
            dados: Dicionário com dados do cliente
        
        Returns:
            tuple: (válido, mensagem_erro)
        """
        nome = str(dados.get('Nome', '')).strip()
        if not nome:
            return False, 'Nome é obrigatório'

        # Ordem escolhida para bater com a suíte de testes (data antes de CPF)
        data_nascimento = str(dados.get('DataNascimento', '')).strip()
        if data_nascimento and not Validators.validar_data(data_nascimento):
            return False, 'Data de nascimento inválida'

        data_afil = str(dados.get('DataAfiliacao', '')).strip()
        if data_afil and not Validators.validar_data(data_afil):
            return False, 'Data de afiliação inválida'

        cpf = str(dados.get('CPF', '')).strip()
        if cpf and not Validators.validar_cpf(cpf):
            return False, 'CPF inválido'

        cep = str(dados.get('CEP', '')).strip()
        if cep and not Validators.validar_cep(cep):
            return False, 'CEP inválido'
        
        return True, ''
    
    @staticmethod
    def cadastrar_cliente(dados: Dict[str, str]) -> Tuple[bool, str]:
        """
        Cadastra um novo cliente
        
        Args:
            dados: Dicionário com dados do cliente
        
        Returns:
            tuple: (sucesso, mensagem)
        """
        # Validar dados
        valido, erro = CadastroController.validar_dados_cliente(dados)
        if not valido:
            return False, erro
        
        dados_formatados = dados.copy()
        if 'DataNascimento' in dados_formatados:
            dados_formatados['DataNascimento'] = normalizar_data_para_api(dados_formatados['DataNascimento'])
        if 'DataAfiliacao' in dados_formatados:
            dados_formatados['DataAfiliacao'] = normalizar_data_para_api(dados_formatados['DataAfiliacao'])
        
        # Sanitizar entrada
        for chave in dados_formatados:
            if isinstance(dados_formatados[chave], str):
                dados_formatados[chave] = sanitizar_entrada(dados_formatados[chave])
        
        # Fazer requisição
        sucesso, _resposta, erro = APIClient.post('/cliente', json=dados_formatados)
        if not sucesso:
            return False, erro or 'Erro ao cadastrar cliente'
        
        return True, 'Cliente cadastrado com sucesso!'
    
    @staticmethod
    def validar_dados_reserva(dados: Dict[str, str]) -> Tuple[bool, str]:
        """
        Valida dados da reserva
        
        Args:
            dados: Dicionário com dados da reserva
        
        Returns:
            tuple: (válido, mensagem_erro)
        """
        nome_livro = str(dados.get('NomeLivro', '')).strip()
        if not nome_livro:
            return False, 'NomeLivro é obrigatório'

        data_retirada = str(dados.get('DataRetirada', '')).strip()
        if data_retirada and not Validators.validar_data(data_retirada):
            return False, 'Data de retirada inválida'

        data_volta = str(dados.get('DataVolta', '')).strip()
        if data_volta and not Validators.validar_data(data_volta):
            return False, 'Data de volta inválida'

        cpf = str(dados.get('CPFReserva', '')).strip()
        if cpf and not Validators.validar_cpf(cpf):
            return False, 'CPF inválido'
        
        # Validar quantidade
        qntd_raw = str(dados.get('QntdLivro', '')).strip()
        if qntd_raw:
            try:
                qntd = int(qntd_raw)
                if qntd <= 0:
                    return False, 'Quantidade deve ser maior que 0'
            except ValueError:
                return False, 'Quantidade deve ser um número'
        
        return True, ''
    
    @staticmethod
    def cadastrar_reserva(dados: Dict[str, str]) -> Tuple[bool, str]:
        """
        Cadastra uma nova reserva
        
        Args:
            dados: Dicionário com dados da reserva
        
        Returns:
            tuple: (sucesso, mensagem)
        """
        # Validar dados
        valido, erro = CadastroController.validar_dados_reserva(dados)
        if not valido:
            return False, erro
        
        dados_formatados = dados.copy()
        if 'DataRetirada' in dados_formatados:
            dados_formatados['DataRetirada'] = normalizar_data_para_api(dados_formatados['DataRetirada'])
        if 'DataVolta' in dados_formatados:
            dados_formatados['DataVolta'] = normalizar_data_para_api(dados_formatados['DataVolta'])
        
        # Sanitizar entrada
        for chave in dados_formatados:
            if isinstance(dados_formatados[chave], str):
                dados_formatados[chave] = sanitizar_entrada(dados_formatados[chave])
        
        # Fazer requisição
        sucesso, _resposta, erro = APIClient.post('/reservas', json=dados_formatados)
        if not sucesso:
            return False, erro or 'Erro ao cadastrar reserva'
        
        return True, 'Reserva cadastrada com sucesso!'
