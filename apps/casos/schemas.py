from datetime import datetime
from typing import Optional

from ninja import Schema


class DisciplinaOut(Schema):
    id: int
    nome: str


class CasoListOut(Schema):
    id: int
    nome: str
    texto_curto: str
    imagem_capa: Optional[str] = None
    disciplina: DisciplinaOut
    tipo_acesso: str
    tipo_caso: str
    duracao: str
    nota_media: float
    ja_iniciado: bool = False


class CasoDetailOut(CasoListOut):
    texto_detalhado: str
    total_perguntas: int = 0


class AvaliacaoIn(Schema):
    nota: int


class AvaliacaoOut(Schema):
    id: int
    caso_id: int
    nota: int
    criado_em: datetime