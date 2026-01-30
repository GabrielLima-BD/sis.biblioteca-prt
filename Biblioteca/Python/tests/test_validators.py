"""
Testes para os Validadores Python
Testa algoritmos de validação
"""

import sys
import os
from pathlib import Path

# Setup paths
PROJETO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJETO_ROOT))

import pytest
from src.utils.validators import Validators


class TestValidadorCPF:
    """Testes para validação de CPF"""
    
    def test_cpf_valido_formatado(self):
        """Testa CPF válido com formatação"""
        assert Validators.validar_cpf("123.456.789-09") is True
    
    def test_cpf_valido_sem_formatacao(self):
        """Testa CPF válido sem formatação"""
        assert Validators.validar_cpf("12345678909") is True
    
    def test_cpf_todos_zeros(self):
        """Testa CPF com todos zeros"""
        assert Validators.validar_cpf("000.000.000-00") is False
    
    def test_cpf_todos_noves(self):
        """Testa CPF com todos noves"""
        assert Validators.validar_cpf("999.999.999-99") is False
    
    def test_cpf_tamanho_incorreto(self):
        """Testa CPF com tamanho incorreto"""
        assert Validators.validar_cpf("123.456.789") is False
    
    def test_cpf_com_letras(self):
        """Testa CPF com letras"""
        assert Validators.validar_cpf("12A.456.789-09") is False
    
    def test_cpf_vazio(self):
        """Testa CPF vazio"""
        assert Validators.validar_cpf("") is False
    
    def test_cpf_digitos_invalidos(self):
        """Testa CPF com dígitos verificadores inválidos"""
        assert Validators.validar_cpf("123.456.789-00") is False
    
    def test_cpf_exemplo_real(self):
        """Testa com CPF exemplo conhecido como válido"""
        # Calcular CPF válido baseado em 12345678
        # Este é um exemplo hipotético
        assert Validators.validar_cpf("000.000.001-91") is True
    
    def test_cpf_nao_string(self):
        """Testa CPF que não é string"""
        assert Validators.validar_cpf(None) is False
        assert Validators.validar_cpf(12345678909) is False


class TestValidadorEmail:
    """Testes para validação de email"""
    
    def test_email_valido_simples(self):
        """Testa email válido simples"""
        assert Validators.validar_email("teste@email.com") is True
    
    def test_email_valido_com_ponto(self):
        """Testa email válido com ponto no usuário"""
        assert Validators.validar_email("teste.usuario@email.com") is True
    
    def test_email_valido_com_numero(self):
        """Testa email válido com números"""
        assert Validators.validar_email("usuario123@email.com") is True
    
    def test_email_invalido_sem_arroba(self):
        """Testa email sem @ (inválido)"""
        assert Validators.validar_email("testeemail.com") is False
    
    def test_email_invalido_sem_dominio(self):
        """Testa email sem domínio"""
        assert Validators.validar_email("teste@") is False
    
    def test_email_invalido_usuario_vazio(self):
        """Testa email com usuário vazio"""
        assert Validators.validar_email("@email.com") is False
    
    def test_email_invalido_multiplos_arrobas(self):
        """Testa email com múltiplos @"""
        assert Validators.validar_email("teste@@email.com") is False
    
    def test_email_vazio(self):
        """Testa email vazio"""
        assert Validators.validar_email("") is False
    
    def test_email_com_espacos(self):
        """Testa email com espaços"""
        assert Validators.validar_email("teste @email.com") is False
    
    def test_email_nao_string(self):
        """Testa email que não é string"""
        assert Validators.validar_email(None) is False


class TestValidadorData:
    """Testes para validação de data"""
    
    def test_data_valida_simples(self):
        """Testa data válida"""
        assert Validators.validar_data("01/01/2024") is True
    
    def test_data_valida_ultimo_dia_mes(self):
        """Testa último dia do mês"""
        assert Validators.validar_data("31/01/2024") is True
    
    def test_data_valida_fevereiro_nao_bissexto(self):
        """Testa Fevereiro em ano não bissexto"""
        assert Validators.validar_data("28/02/2023") is True
    
    def test_data_valida_fevereiro_bissexto(self):
        """Testa Fevereiro 29 em ano bissexto"""
        assert Validators.validar_data("29/02/2024") is True
    
    def test_data_invalida_fevereiro_nao_bissexto(self):
        """Testa Fevereiro 29 em ano não bissexto"""
        assert Validators.validar_data("29/02/2023") is False
    
    def test_data_invalida_mes_invalido(self):
        """Testa mês inválido"""
        assert Validators.validar_data("01/13/2024") is False
    
    def test_data_invalida_dia_invalido(self):
        """Testa dia inválido"""
        assert Validators.validar_data("32/01/2024") is False
    
    def test_data_invalida_dia_zero(self):
        """Testa dia zero"""
        assert Validators.validar_data("00/01/2024") is False
    
    def test_data_invalida_mes_zero(self):
        """Testa mês zero"""
        assert Validators.validar_data("01/00/2024") is False
    
    def test_data_invalida_ano_invalido(self):
        """Testa ano inválido (muito antigo)"""
        assert Validators.validar_data("01/01/1800") is False
    
    def test_data_invalida_formato(self):
        """Testa formato inválido"""
        assert Validators.validar_data("01-01-2024") is False
        assert Validators.validar_data("2024/01/01") is False
    
    def test_data_vazia(self):
        """Testa data vazia"""
        assert Validators.validar_data("") is False
    
    def test_data_nao_string(self):
        """Testa data que não é string"""
        assert Validators.validar_data(None) is False
    
    def test_data_bissexto_multiplo_400(self):
        """Testa ano bissexto (múltiplo de 400)"""
        assert Validators.validar_data("29/02/2000") is True
    
    def test_data_nao_bissexto_multiplo_100(self):
        """Testa ano não bissexto (múltiplo de 100 mas não de 400)"""
        assert Validators.validar_data("29/02/1900") is False


class TestValidadorCEP:
    """Testes para validação de CEP"""
    
    def test_cep_valido_formatado(self):
        """Testa CEP válido com formatação"""
        assert Validators.validar_cep("12345-678") is True
    
    def test_cep_valido_sem_formatacao(self):
        """Testa CEP válido sem formatação"""
        assert Validators.validar_cep("12345678") is True
    
    def test_cep_tamanho_incorreto(self):
        """Testa CEP com tamanho incorreto"""
        assert Validators.validar_cep("12345-67") is False
    
    def test_cep_com_letras(self):
        """Testa CEP com letras"""
        assert Validators.validar_cep("1234A-678") is False
    
    def test_cep_vazio(self):
        """Testa CEP vazio"""
        assert Validators.validar_cep("") is False
    
    def test_cep_todos_zeros(self):
        """Testa CEP com todos zeros"""
        assert Validators.validar_cep("00000-000") is True  # Formato válido, só zeros
    
    def test_cep_nao_string(self):
        """Testa CEP que não é string"""
        assert Validators.validar_cep(None) is False
    
    def test_cep_formatacao_incorreta(self):
        """Testa CEP com formatação incorreta"""
        assert Validators.validar_cep("123456-78") is False


class TestValidadorCampoObrigatorio:
    """Testes para validação de campo obrigatório"""
    
    def test_campo_obrigatorio_com_valor(self):
        """Testa campo obrigatório com valor"""
        assert Validators.validar_campo_obrigatorio("João") is True
    
    def test_campo_obrigatorio_vazio(self):
        """Testa campo obrigatório vazio"""
        assert Validators.validar_campo_obrigatorio("") is False
    
    def test_campo_obrigatorio_apenas_espacos(self):
        """Testa campo obrigatório com apenas espaços"""
        assert Validators.validar_campo_obrigatorio("   ") is False
    
    def test_campo_obrigatorio_none(self):
        """Testa campo obrigatório None"""
        assert Validators.validar_campo_obrigatorio(None) is False


class TestSanitizarSQLInjection:
    """Testes para sanitização de SQL Injection"""
    
    def test_sanitizar_aspas_simples(self):
        """Testa sanitização de aspas simples"""
        resultado = Validators.sanitizar_sql_injection("João's")
        assert "'" not in resultado or "\\'" in resultado or "''" in resultado
    
    def test_sanitizar_aspas_duplas(self):
        """Testa sanitização de aspas duplas"""
        resultado = Validators.sanitizar_sql_injection('João"s')
        assert '"' not in resultado or '\\"' in resultado or '""' in resultado
    
    def test_sanitizar_sql_drop(self):
        """Testa sanitização de comando DROP"""
        entrada = "João'; DROP TABLE clientes; --"
        resultado = Validators.sanitizar_sql_injection(entrada)
        # Deve remover ou escapar caracteres perigosos
        assert resultado != entrada or "drop" not in resultado.lower()
    
    def test_sanitizar_sql_union(self):
        """Testa sanitização de UNION"""
        entrada = "' UNION SELECT * FROM --"
        resultado = Validators.sanitizar_sql_injection(entrada)
        assert resultado != entrada
    
    def test_sanitizar_valor_limpo(self):
        """Testa sanitização de valor limpo"""
        entrada = "João Silva"
        resultado = Validators.sanitizar_sql_injection(entrada)
        # Valor limpo deve ser mantido
        assert "Silva" in resultado
    
    def test_sanitizar_vazio(self):
        """Testa sanitização de valor vazio"""
        resultado = Validators.sanitizar_sql_injection("")
        assert resultado == ""
    
    def test_sanitizar_none(self):
        """Testa sanitização de None"""
        resultado = Validators.sanitizar_sql_injection(None)
        assert resultado == ""


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
