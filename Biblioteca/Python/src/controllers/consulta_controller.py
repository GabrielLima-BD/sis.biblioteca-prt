"""
Controllers para consultas de dados
"""
from typing import Tuple, List, Dict, Optional

from src.models.api_client import api_client
from src.utils.validators import sanitizar_entrada


class APIClient:
    """Façade para permitir patching nos testes.

    Os testes fazem `@patch('src.controllers.consulta_controller.APIClient.get')`.
    """

    @staticmethod
    def get(endpoint: str, params: Optional[Dict] = None) -> tuple[bool, list, Optional[str]]:
        sucesso, payload, erro = api_client.get(endpoint, params=params)
        if not sucesso:
            return False, [], erro or 'Erro na requisição'

        dados = payload.get('data', payload.get('dados', [])) if isinstance(payload, dict) else []
        if isinstance(dados, list):
            return True, dados, None
        if dados:
            return True, [dados], None
        return True, [], None


class ConsultaController:
    """Controller para operações de consulta"""
    
    @staticmethod
    def buscar_cliente_por_nome(nome: str) -> Tuple[bool, List[Dict], Optional[str]]:
        """
        Busca clientes pelo nome
        
        Args:
            nome: Nome do cliente a buscar
        
        Returns:
            tuple: (sucesso, dados, mensagem_erro)
        """
        params = None
        if isinstance(nome, str) and nome.strip():
            params = {'Nome': sanitizar_entrada(nome)}
        return APIClient.get('/cliente', params=params)
    
    @staticmethod
    def buscar_clientes_por_estado(estado: str) -> Tuple[bool, List[Dict], Optional[str]]:
        """
        Busca clientes por estado
        
        Args:
            estado: Nome do estado a buscar
        
        Returns:
            tuple: (sucesso, dados, mensagem_erro)
        """
        params = None
        if isinstance(estado, str) and estado.strip():
            params = {'Estado': sanitizar_entrada(estado)}
        return APIClient.get('/endereco', params=params)
    
    @staticmethod
    def buscar_livro_por_nome(nome_livro: str) -> Tuple[bool, List[Dict], Optional[str]]:
        """
        Busca livros pelo nome
        
        Args:
            nome_livro: Nome do livro a buscar
        
        Returns:
            tuple: (sucesso, dados, mensagem_erro)
        """
        params = None
        if isinstance(nome_livro, str) and nome_livro.strip():
            params = {'NomeLivro': sanitizar_entrada(nome_livro)}
        return APIClient.get('/livro', params=params)
    
    @staticmethod
    def buscar_livro_por_autor(nome_autor: str) -> Tuple[bool, List[Dict], Optional[str]]:
        """
        Busca livros pelo autor
        
        Args:
            nome_autor: Nome do autor a buscar
        
        Returns:
            tuple: (sucesso, dados, mensagem_erro)
        """
        params = None
        if isinstance(nome_autor, str) and nome_autor.strip():
            params = {'NomeAutor': sanitizar_entrada(nome_autor)}
        return APIClient.get('/livro/autor', params=params)
    
    @staticmethod
    def buscar_livros_por_genero(nome_genero: str) -> Tuple[bool, List[Dict], Optional[str]]:
        """
        Busca livros por gênero
        
        Args:
            nome_genero: Nome do gênero a buscar
        
        Returns:
            tuple: (sucesso, dados, mensagem_erro)
        """
        params = None
        if isinstance(nome_genero, str) and nome_genero.strip():
            params = {'NomeGenero': sanitizar_entrada(nome_genero)}
        return APIClient.get('/genero', params=params)
