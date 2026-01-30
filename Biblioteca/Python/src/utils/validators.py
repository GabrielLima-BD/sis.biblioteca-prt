"""
Validadores para entrada de dados
"""
import re
from datetime import datetime
from typing import Iterable, Optional


def validar_cpf(cpf: str) -> bool:
    """
    Valida CPF usando algoritmo de dígitos verificadores
    
    Args:
        cpf: String com CPF no formato XXX.XXX.XXX-XX ou apenas números
    
    Returns:
        bool: True se CPF válido, False caso contrário
    """
    if not isinstance(cpf, str):
        return False

    cpf = re.sub(r'\D', '', cpf)
    
    if len(cpf) != 11:
        return False
    
    if cpf == cpf[0] * 11:
        return False
    
    # Primeiro dígito verificador
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    resto = soma % 11
    dv1 = 0 if resto < 2 else 11 - resto
    
    if int(cpf[9]) != dv1:
        return False
    
    # Segundo dígito verificador
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    resto = soma % 11
    dv2 = 0 if resto < 2 else 11 - resto
    
    return int(cpf[10]) == dv2


def validar_email(email: str) -> bool:
    """
    Valida formato de email
    
    Args:
        email: String com endereço de email
    
    Returns:
        bool: True se email válido, False caso contrário
    """
    if not isinstance(email, str):
        return False

    padrao = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(padrao, email))


def validar_data(data_str: str,
                 formatos: Optional[Iterable[str]] = None) -> bool:
    """Valida se string representa uma data válida."""
    if not isinstance(data_str, str) or not data_str:
        return False

    candidatos = list(formatos) if formatos else ['%d/%m/%y', '%d/%m/%Y']
    for formato in candidatos:
        try:
            datetime.strptime(data_str.strip(), formato)
            return True
        except ValueError:
            continue
    return False


def validar_cep(cep: str) -> bool:
    """
    Valida CEP brasileiro
    
    Args:
        cep: String com CEP no formato XXXXX-XXX ou apenas números
    
    Returns:
        bool: True se CEP válido, False caso contrário
    """
    if not isinstance(cep, str):
        return False

    valor = cep.strip()
    if re.fullmatch(r'\d{8}', valor):
        return True
    if re.fullmatch(r'\d{5}-\d{3}', valor):
        return True
    return False


def validar_campo_obrigatorio(valor: str, nome_campo: str = 'Campo') -> tuple[bool, str]:
    """
    Valida se campo não está vazio
    
    Args:
        valor: Valor a validar
        nome_campo: Nome do campo para mensagem de erro
    
    Returns:
        tuple: (é_válido, mensagem_erro)
    """
    if not valor or not str(valor).strip():
        return False, f'{nome_campo} é obrigatório'
    return True, ''


def sanitizar_entrada(texto: str) -> str:
    """
    Remove caracteres perigosos da entrada
    
    Args:
        texto: Texto a sanitizar
    
    Returns:
        str: Texto sanitizado
    """
    # Remove caracteres especiais perigosos para SQL injection
    caracteres_perigosos = ['--', ';', '/*', '*/', 'xp_', 'sp_']
    texto_sanitizado = texto
    
    for char in caracteres_perigosos:
        texto_sanitizado = texto_sanitizado.replace(char, '')
    
    return texto_sanitizado.strip()


def sanitizar_sql_injection(texto: Optional[str]) -> str:
    """Sanitiza entrada contra padrões comuns de SQL injection.

    Observação: isto é um *hardening* básico para entradas de UI; não substitui
    consultas parametrizadas no banco.
    """
    if texto is None:
        return ""

    if not isinstance(texto, str):
        texto = str(texto)

    # Escapa aspas (forma compatível com SQL padrão)
    texto_sanitizado = texto.replace("'", "''").replace('"', '""')

    # Remove sequências e delimitadores comuns em injection
    for token in ("--", ";", "/*", "*/"):
        texto_sanitizado = texto_sanitizado.replace(token, "")

    # Remove keywords perigosas como palavras inteiras (case-insensitive)
    texto_sanitizado = re.sub(
        r"\b(drop|union|select|insert|delete|update|alter|create|truncate)\b",
        "",
        texto_sanitizado,
        flags=re.IGNORECASE,
    )

    return texto_sanitizado.strip()


class Validators:
    """API estável de validação usada pelos testes.

    Mantém métodos como `@staticmethod` para facilitar uso em UI.
    """

    @staticmethod
    def validar_cpf(cpf: object) -> bool:
        return validar_cpf(cpf)  # type: ignore[arg-type]

    @staticmethod
    def validar_email(email: object) -> bool:
        return validar_email(email)  # type: ignore[arg-type]

    @staticmethod
    def validar_data(data_str: object) -> bool:
        if not isinstance(data_str, str) or not data_str.strip():
            return False

        # Aceita DD/MM/AAAA (preferencial) e também DD/MM/AA
        for fmt in ("%d/%m/%Y", "%d/%m/%y"):
            try:
                dt = datetime.strptime(data_str.strip(), fmt)
                # Regra de negócio nos testes: anos muito antigos são inválidos
                return dt.year >= 1900
            except ValueError:
                continue
        return False

    @staticmethod
    def validar_cep(cep: object) -> bool:
        return validar_cep(cep)  # type: ignore[arg-type]

    @staticmethod
    def validar_campo_obrigatorio(valor: object) -> bool:
        return bool(valor is not None and str(valor).strip())

    @staticmethod
    def sanitizar_sql_injection(texto: object) -> str:
        return sanitizar_sql_injection(texto if isinstance(texto, str) or texto is None else str(texto))
