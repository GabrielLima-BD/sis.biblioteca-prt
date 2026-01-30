"""Controller para operações relacionadas a multas."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from src.models.api_client import APIClient
from src.utils.formatters import (
    formatar_data_para_exibicao,
    interpretar_data,
    formatar_valor_monetario,
    interpretar_valor_monetario,
)


class MultasController:
    """Encapsula regras de negócio para gerenciamento de multas."""

    def __init__(self, api_client: APIClient) -> None:
        self.api_client = api_client

    def listar_multas_por_cpf(self, cpf: str) -> Tuple[bool, Dict[str, Any], str]:
        """Busca cliente por CPF e retorna suas multas formatadas."""
        sucesso_cliente, cliente, erro_cliente = self.api_client.buscar_cliente_por_cpf(cpf)
        if not sucesso_cliente:
            return False, {}, erro_cliente or 'Não foi possível localizar o cliente.'

        cliente_id = cliente.get('ClienteID') or cliente.get('cliente_id')
        if not cliente_id:
            return False, {}, 'Cliente sem identificador válido.'

        sucesso_multas, multas, erro_multas = self.api_client.listar_multas_por_cliente(int(cliente_id))
        if not sucesso_multas:
            return False, {}, erro_multas or 'Não foi possível carregar as multas do cliente.'

        multas_formatadas = self._formatar_multas(multas)
        resumo = self.calcular_resumo(multas_formatadas)

        payload = {
            'cliente': cliente,
            'multas': multas_formatadas,
            'resumo': resumo,
        }
        return True, payload, ''

    def listar_multas(self,
                      status: Optional[str] = None,
                      apenas_vencidas: bool = False,
                      cliente_id: Optional[int] = None,
                      reserva_id: Optional[int] = None,
                      multa_id: Optional[int] = None) -> Tuple[bool, List[Dict[str, Any]], str]:
        """Retorna multas com filtros e formatação padronizada."""
        sucesso, multas, erro = self.api_client.listar_multas(
            cliente_id=cliente_id,
            status=status,
            vencidas=apenas_vencidas,
            reserva_id=reserva_id,
            multa_id=multa_id,
        )

        if not sucesso:
            return False, [], erro

        return True, self._formatar_multas(multas), ''

    def listar_multas_pendentes(self, apenas_vencidas: bool = False) -> Tuple[bool, List[Dict[str, Any]], str]:
        """Lista multas pendentes, opcionalmente filtrando apenas vencidas."""
        return self.listar_multas(status='pendente', apenas_vencidas=apenas_vencidas)

    def obter_multa_por_id(self, multa_id: int) -> Tuple[bool, Dict[str, Any], str]:
        """Carrega uma multa específica pelo identificador."""
        sucesso, multas, erro = self.listar_multas(multa_id=multa_id)
        if not sucesso:
            return False, {}, erro
        if not multas:
            return False, {}, 'Multa não encontrada.'
        return True, multas[0], ''

    def registrar_multa(self, reserva_id: int, valor: str, data_vencimento: str) -> Tuple[bool, str]:
        """Registra uma multa manualmente aplicando validações básicas."""
        if not reserva_id or reserva_id <= 0:
            return False, 'Informe um ID de reserva válido.'

        valor_decimal = interpretar_valor_monetario(valor)
        if valor_decimal is None:
            try:
                valor_decimal = Decimal(str(valor).replace(',', '.'))
            except (ValueError, ArithmeticError):
                return False, 'Valor da multa inválido.'

        if valor_decimal <= 0:
            return False, 'Valor da multa deve ser maior que zero.'

        if not data_vencimento or not data_vencimento.strip():
            return False, 'Informe a data de vencimento.'

        sucesso, mensagem = self.api_client.criar_multa(
            reserva_id=int(reserva_id),
            valor=float(valor_decimal),
            data_vencimento=data_vencimento.strip(),
        )
        return sucesso, mensagem

    def registrar_pagamento(self, multa_id: int, data_pagamento: Optional[str] = None) -> Tuple[bool, str]:
        """Efetua o pagamento de uma multa."""
        if not multa_id or multa_id <= 0:
            return False, 'Informe um ID de multa válido.'
        return self.api_client.pagar_multa(int(multa_id), data_pagamento)

    @staticmethod
    def calcular_resumo(multas: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calcula totais financeiros e contagens auxiliares."""
        total = Decimal('0')
        total_pendente = Decimal('0')
        total_pago = Decimal('0')
        total_vencido = Decimal('0')
        pendentes = 0
        pagas = 0
        vencidas = 0

        for multa in multas:
            valor = multa.get('ValorDecimal', Decimal('0'))
            total += valor

            if multa.get('Status') == 'Paga':
                total_pago += valor
                pagas += 1
            elif multa.get('EmAtraso'):
                total_vencido += valor
                total_pendente += valor
                vencidas += 1
            else:
                total_pendente += valor
                pendentes += 1

        return {
            'quantidade_total': len(multas),
            'quantidade_pendentes': pendentes,
            'quantidade_pagas': pagas,
            'quantidade_vencidas': vencidas,
            'total': total,
            'total_formatado': formatar_valor_monetario(total),
            'total_pendente': total_pendente,
            'total_pendente_formatado': formatar_valor_monetario(total_pendente),
            'total_pago': total_pago,
            'total_pago_formatado': formatar_valor_monetario(total_pago),
            'total_vencido': total_vencido,
            'total_vencido_formatado': formatar_valor_monetario(total_vencido),
        }

    def _formatar_multas(self, multas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enriquece dados de multas com informações derivadas."""
        hoje = datetime.now().date()
        resultado: List[Dict[str, Any]] = []

        for multa in multas or []:
            valor_bruto = multa.get('Valor', multa.get('valor', 0))
            try:
                valor_decimal = Decimal(str(valor_bruto)).quantize(Decimal('0.01'))
            except (ValueError, ArithmeticError):
                valor_decimal = Decimal('0')

            data_venc_str = multa.get('DataVencimento') or multa.get('data_vencimento')
            data_pag_str = multa.get('DataPagamento') or multa.get('data_pagamento')

            data_venc = interpretar_data(data_venc_str)
            data_pag = interpretar_data(data_pag_str)

            em_atraso = False
            dias_atraso = 0
            if data_venc and not data_pag:
                diff = (hoje - data_venc.date()).days
                if diff > 0:
                    em_atraso = True
                    dias_atraso = diff

            status_original = multa.get('Status') or multa.get('status')
            status = status_original or ('Paga' if data_pag else ('Vencida' if em_atraso else 'Pendente'))

            reserva = multa.get('reserva') or {}
            cliente_info = reserva.get('cliente') or multa.get('cliente') or {}
            livro_info = reserva.get('livro') or multa.get('livro') or {}

            nome_cliente = ' '.join(filter(None, [cliente_info.get('Nome'), cliente_info.get('Sobrenome')])).strip()

            resultado.append({
                **multa,
                'MultaID': multa.get('MultaID') or multa.get('multa_id'),
                'ReservaID': multa.get('ReservaID') or multa.get('reserva_id') or reserva.get('ReservaID') or reserva.get('reserva_id'),
                'ClienteID': multa.get('ClienteID') or multa.get('cliente_id') or reserva.get('ClienteID') or cliente_info.get('ClienteID'),
                'ValorDecimal': valor_decimal,
                'ValorFormatado': formatar_valor_monetario(valor_decimal),
                'DataVencimentoFormatada': formatar_data_para_exibicao(data_venc_str),
                'DataPagamentoFormatada': formatar_data_para_exibicao(data_pag_str) if data_pag_str else 'N/D',
                'Status': status,
                'StatusCalculado': 'Paga' if data_pag else ('Vencida' if em_atraso else 'Pendente'),
                'EmAtraso': em_atraso,
                'DiasEmAtraso': dias_atraso,
                'ClienteNome': nome_cliente or cliente_info.get('Nome') or '',
                'LivroNome': livro_info.get('NomeLivro') or livro_info.get('Nome') or reserva.get('LivroNome') or livro_info.get('nome'),
            })

        return resultado
