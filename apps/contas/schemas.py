from typing import Optional

from ninja import Schema


class InstituicaoOut(Schema):
    id: int
    nome: str
    estado: str


class CadastroIn(Schema):
    username: str
    email: str
    password: str
    nome_jogador: str
    instituicao_id: Optional[int] = None


class PerfilOut(Schema):
    usuario_id: int
    nome_jogador: str
    avatar: Optional[str] = None
    instituicao: Optional[InstituicaoOut] = None
    pontuacao_total: int
    receber_notificacoes: bool
    receber_newsletter: bool


class PerfilUpdateIn(Schema):
    nome_jogador: Optional[str] = None
    instituicao_id: Optional[int] = None
    endereco: Optional[str] = None
    receber_notificacoes: Optional[bool] = None
    receber_newsletter: Optional[bool] = None
