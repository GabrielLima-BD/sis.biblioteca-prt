"""Funções de formatação de dados."""

import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Iterable, Optional, Union


GUI_DATA_FORMATS = ('%d/%m/%y', '%d/%m/%Y')
API_DATA_FORMATS = ('%d/%m/%Y', '%d/%m/%y', '%Y-%m-%d')
DB_DATA_FORMATS = ('%Y-%m-%d', '%d/%m/%Y', '%d/%m/%y')
DISPLAY_DATA_FORMAT = '%d/%m/%Y'
API_OUTPUT_FORMAT = '%d/%m/%Y'
DB_OUTPUT_FORMAT = '%Y-%m-%d'


def interpretar_data(data_str: str, formatos: Optional[Iterable[str]] = None) -> Optional[datetime]:
    """Tenta converter string em ``datetime`` usando formatos informados."""
    if not data_str:
        return None
    formatos_validos = list(formatos) if formatos else list(set(GUI_DATA_FORMATS + API_DATA_FORMATS + DB_DATA_FORMATS))
    valor = data_str.strip()
    for formato in formatos_validos:
        try:
            return datetime.strptime(valor, formato)
        except ValueError:
            continue
    return None


def formatar_data_para_db(data_str: str,
                         formatos_entrada: Optional[Iterable[str]] = None,
                         formato_saida: str = DB_OUTPUT_FORMAT) -> str:
    """Normaliza data para formato ISO (YYYY-MM-DD) ao persistir."""
    data = interpretar_data(data_str, formatos_entrada or (GUI_DATA_FORMATS + API_DATA_FORMATS + ('%Y-%m-%d',)))
    if not data:
        return data_str
    return data.strftime(formato_saida)


def normalizar_data_para_api(data_str: str,
                             formatos_entrada: Optional[Iterable[str]] = None,
                             formato_saida: str = API_OUTPUT_FORMAT) -> str:
    """Normaliza data para o padrão aceito pela API (DD/MM/YYYY)."""
    data = interpretar_data(data_str, formatos_entrada or (GUI_DATA_FORMATS + DB_DATA_FORMATS))
    if not data:
        return data_str
    return data.strftime(formato_saida)


def formatar_cpf(cpf: str) -> str:
    """
    Formata CPF para XXX.XXX.XXX-XX
    
    Args:
        cpf: CPF com apenas números
    
    Returns:
        str: CPF formatado
    """
    cpf = re.sub(r'\D', '', cpf)
    if len(cpf) == 11:
        return f'{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}'
    return cpf


def formatar_cep(cep: str) -> str:
    """
    Formata CEP para XXXXX-XXX
    
    Args:
        cep: CEP com apenas números
    
    Returns:
        str: CEP formatado
    """
    cep = re.sub(r'\D', '', cep)
    if len(cep) == 8:
        return f'{cep[:5]}-{cep[5:]}'
    return cep


def remover_formatacao(valor: str) -> str:
    """
    Remove formatação de números e mantém apenas dígitos
    
    Args:
        valor: String com formatação
    
    Returns:
        str: String com apenas dígitos
    """
    return re.sub(r'\D', '', valor)


def formatar_data_para_exibicao(data_str: str,
                                formatos_entrada: Optional[Iterable[str]] = None,
                                formato_saida: str = DISPLAY_DATA_FORMAT) -> str:
    """Converte data para exibição amigável na GUI."""
    data = interpretar_data(data_str, formatos_entrada or (DB_DATA_FORMATS + API_DATA_FORMATS))
    if not data:
        return data_str or ''
    return data.strftime(formato_saida)


def formatar_valor_monetario(valor: Union[str, float, int, Decimal, None]) -> str:
    """Formata números para o padrão monetário brasileiro."""
    if valor in (None, ''):
        return 'R$ 0,00'

    try:
        quantia = Decimal(str(valor))
    except (InvalidOperation, ValueError):
        return str(valor)

    quantia = quantia.quantize(Decimal('0.01'))
    inteiro, centavos = f"{quantia:.2f}".split('.')
    inteiro_formatado = f"{int(inteiro):,}".replace(',', '.')
    return f"R$ {inteiro_formatado},{centavos}"


def interpretar_valor_monetario(valor: str) -> Optional[Decimal]:
    """Converte string monetária brasileira em ``Decimal``."""
    if not valor or not valor.strip():
        return None

    convertido = valor.replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')

    try:
        return Decimal(convertido)
    except (InvalidOperation, ValueError):
        return None