from datetime import date
from typing import Optional

from ninja import Schema


class PlanoOut(Schema):
    id: int
    nome: str
    descricao: str
    duracao_dias: int
    preco_centavos: int


class AssinaturaOut(Schema):
    id: int
    plano: PlanoOut
    inicio: date
    fim: date
    ativa: bool
    esta_vigente: bool


class StatusPremiumOut(Schema):
    tem_premium_ativo: bool
    assinatura: Optional[AssinaturaOut] = None
