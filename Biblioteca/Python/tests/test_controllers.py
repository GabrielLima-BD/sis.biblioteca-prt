"""
Testes para os Controllers
Testa a lógica de negócio sem dependências de API
"""

import sys
import os
from pathlib import Path

# Setup paths
PROJETO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJETO_ROOT))

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.controllers.consulta_controller import ConsultaController
from src.controllers.cadastro_controller import CadastroController


class TestConsultaController:
    """Testes para ConsultaController"""
    
    @patch('src.controllers.consulta_controller.APIClient.get')
    def test_buscar_cliente_por_nome_sucesso(self, mock_get):
        """Testa busca de cliente por nome com sucesso"""
        # Arrange
        mock_get.return_value = (True, [{"Nome": "João", "CPF": "123.456.789-00"}], None)
        
        # Act
        sucesso, dados, erro = ConsultaController.buscar_cliente_por_nome("João")
        
        # Assert
        assert sucesso is True
        assert len(dados) > 0
        assert erro is None
    
    @patch('src.controllers.consulta_controller.APIClient.get')
    def test_buscar_cliente_por_nome_erro(self, mock_get):
        """Testa busca de cliente com erro da API"""
        # Arrange
        mock_get.return_value = (False, [], "Erro de conexão")
        
        # Act
        sucesso, dados, erro = ConsultaController.buscar_cliente_por_nome("João")
        
        # Assert
        assert sucesso is False
        assert dados == []
        assert erro is not None
    
    @patch('src.controllers.consulta_controller.APIClient.get')
    def test_buscar_cliente_por_nome_vazio(self, mock_get):
        """Testa busca de cliente com nome vazio"""
        # Arrange
        mock_get.return_value = (True, [], None)
        
        # Act
        sucesso, dados, erro = ConsultaController.buscar_cliente_por_nome("")
        
        # Assert
        assert sucesso is True
        assert len(dados) == 0
    
    @patch('src.controllers.consulta_controller.APIClient.get')
    def test_buscar_clientes_por_estado_sucesso(self, mock_get):
        """Testa busca de clientes por estado"""
        # Arrange
        mock_get.return_value = (
            True, 
            [{"Nome": "João", "Estado": "SP"}, {"Nome": "Maria", "Estado": "SP"}],
            None
        )
        
        # Act
        sucesso, dados, erro = ConsultaController.buscar_clientes_por_estado("SP")
        
        # Assert
        assert sucesso is True
        assert len(dados) == 2
        assert all(d["Estado"] == "SP" for d in dados)
    
    @patch('src.controllers.consulta_controller.APIClient.get')
    def test_buscar_clientes_por_estado_nao_encontrado(self, mock_get):
        """Testa busca de estado inexistente"""
        # Arrange
        mock_get.return_value = (True, [], None)
        
        # Act
        sucesso, dados, erro = ConsultaController.buscar_clientes_por_estado("XX")
        
        # Assert
        assert sucesso is True
        assert len(dados) == 0
    
    @patch('src.controllers.consulta_controller.APIClient.get')
    def test_buscar_livro_por_nome_sucesso(self, mock_get):
        """Testa busca de livro por nome"""
        # Arrange
        mock_get.return_value = (
            True,
            [{"NomeLivro": "Dom Casmurro", "Autor": "Machado de Assis"}],
            None
        )
        
        # Act
        sucesso, dados, erro = ConsultaController.buscar_livro_por_nome("Dom Casmurro")
        
        # Assert
        assert sucesso is True
        assert len(dados) > 0
        assert dados[0]["NomeLivro"] == "Dom Casmurro"
    
    @patch('src.controllers.consulta_controller.APIClient.get')
    def test_buscar_livro_por_autor_sucesso(self, mock_get):
        """Testa busca de livros por autor"""
        # Arrange
        mock_get.return_value = (
            True,
            [
                {"NomeLivro": "Dom Casmurro", "Autor": "Machado de Assis"},
                {"NomeLivro": "Quincas Borba", "Autor": "Machado de Assis"}
            ],
            None
        )
        
        # Act
        sucesso, dados, erro = ConsultaController.buscar_livro_por_autor("Machado de Assis")
        
        # Assert
        assert sucesso is True
        assert len(dados) == 2
        assert all(d["Autor"] == "Machado de Assis" for d in dados)
    
    @patch('src.controllers.consulta_controller.APIClient.get')
    def test_buscar_livros_por_genero_sucesso(self, mock_get):
        """Testa busca de livros por gênero"""
        # Arrange
        mock_get.return_value = (
            True,
            [{"NomeLivro": "Dom Casmurro", "Genero": "Romance"}],
            None
        )
        
        # Act
        sucesso, dados, erro = ConsultaController.buscar_livros_por_genero("Romance")
        
        # Assert
        assert sucesso is True
        assert len(dados) > 0


class TestCadastroController:
    """Testes para CadastroController"""
    
    @patch('src.controllers.cadastro_controller.Validators.validar_cpf')
    @patch('src.controllers.cadastro_controller.Validators.validar_data')
    @patch('src.controllers.cadastro_controller.Validators.validar_cep')
    @patch('src.controllers.cadastro_controller.APIClient.post')
    def test_cadastrar_cliente_sucesso(self, mock_post, mock_cep, mock_data, mock_cpf):
        """Testa cadastro de cliente com sucesso"""
        # Arrange
        mock_cpf.return_value = True
        mock_data.return_value = True
        mock_cep.return_value = True
        mock_post.return_value = (True, {"id": 1}, None)
        
        dados = {
            "Nome": "João",
            "Sobrenome": "Silva",
            "CPF": "123.456.789-00",
            "DataNascimento": "01/01/1990",
            "DataAfiliacao": "01/01/2020",
            "CEP": "12345-678",
            "Rua": "Rua A",
            "Numero": "123",
            "Bairro": "Centro",
            "Cidade": "São Paulo",
            "Estado": "SP",
            "Complemento": ""
        }
        
        # Act
        sucesso, msg = CadastroController.cadastrar_cliente(dados)
        
        # Assert
        assert sucesso is True
        assert "sucesso" in msg.lower() or "cadastrad" in msg.lower()
    
    @patch('src.controllers.cadastro_controller.Validators.validar_cpf')
    def test_cadastrar_cliente_cpf_invalido(self, mock_cpf):
        """Testa cadastro com CPF inválido"""
        # Arrange
        mock_cpf.return_value = False
        
        dados = {
            "Nome": "João",
            "CPF": "000.000.000-00",
            "DataNascimento": "01/01/1990",
        }
        
        # Act
        sucesso, msg = CadastroController.cadastrar_cliente(dados)
        
        # Assert
        assert sucesso is False
        assert "cpf" in msg.lower() or "inválido" in msg.lower()
    
    @patch('src.controllers.cadastro_controller.Validators.validar_data')
    def test_cadastrar_cliente_data_invalida(self, mock_data):
        """Testa cadastro com data inválida"""
        # Arrange
        mock_data.return_value = False
        
        dados = {
            "Nome": "João",
            "CPF": "123.456.789-00",
            "DataNascimento": "32/13/1990",
        }
        
        # Act
        sucesso, msg = CadastroController.cadastrar_cliente(dados)
        
        # Assert
        assert sucesso is False
        assert "data" in msg.lower() or "inválido" in msg.lower()
    
    @patch('src.controllers.cadastro_controller.Validators.validar_cpf')
    @patch('src.controllers.cadastro_controller.Validators.validar_data')
    @patch('src.controllers.cadastro_controller.Validators.validar_cep')
    @patch('src.controllers.cadastro_controller.APIClient.post')
    def test_cadastrar_cliente_nome_obrigatorio(self, mock_post, mock_cep, mock_data, mock_cpf):
        """Testa cadastro sem nome (campo obrigatório)"""
        # Arrange
        mock_cpf.return_value = True
        mock_data.return_value = True
        mock_cep.return_value = True
        
        dados = {
            "Nome": "",  # Nome vazio
            "Sobrenome": "Silva",
            "CPF": "123.456.789-00",
            "DataNascimento": "01/01/1990",
        }
        
        # Act
        sucesso, msg = CadastroController.cadastrar_cliente(dados)
        
        # Assert
        assert sucesso is False
        assert "obrigatório" in msg.lower() or "nome" in msg.lower()
    
    @patch('src.controllers.cadastro_controller.Validators.validar_cpf')
    @patch('src.controllers.cadastro_controller.Validators.validar_data')
    @patch('src.controllers.cadastro_controller.APIClient.post')
    def test_cadastrar_reserva_sucesso(self, mock_post, mock_data, mock_cpf):
        """Testa cadastro de reserva com sucesso"""
        # Arrange
        mock_cpf.return_value = True
        mock_data.return_value = True
        mock_post.return_value = (True, {"id": 1}, None)
        
        dados = {
            "CPFReserva": "123.456.789-00",
            "NomeLivro": "Dom Casmurro",
            "QntdLivro": "1",
            "DataRetirada": "01/01/2024",
            "DataVolta": "15/01/2024",
        }
        
        # Act
        sucesso, msg = CadastroController.cadastrar_reserva(dados)
        
        # Assert
        assert sucesso is True
        assert "sucesso" in msg.lower() or "reserv" in msg.lower()
    
    @patch('src.controllers.cadastro_controller.Validators.validar_cpf')
    def test_cadastrar_reserva_cpf_invalido(self, mock_cpf):
        """Testa reserva com CPF inválido"""
        # Arrange
        mock_cpf.return_value = False
        
        dados = {
            "CPFReserva": "000.000.000-00",
            "NomeLivro": "Dom Casmurro",
        }
        
        # Act
        sucesso, msg = CadastroController.cadastrar_reserva(dados)
        
        # Assert
        assert sucesso is False
        assert "cpf" in msg.lower()
    
    @patch('src.controllers.cadastro_controller.Validators.validar_data')
    def test_cadastrar_reserva_data_invalida(self, mock_data):
        """Testa reserva com datas inválidas"""
        # Arrange
        mock_data.return_value = False
        
        dados = {
            "CPFReserva": "123.456.789-00",
            "NomeLivro": "Dom Casmurro",
            "DataRetirada": "invalid",
            "DataVolta": "invalid",
        }
        
        # Act
        sucesso, msg = CadastroController.cadastrar_reserva(dados)
        
        # Assert
        assert sucesso is False
        assert "data" in msg.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
