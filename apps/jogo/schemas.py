from typing import Optional

from ninja import Schema


class AlternativaOut(Schema):
    id: int
    texto: str
    ordem: int


class TelaOut(Schema):
    id: int
    ordem: int
    tipo: str
    titulo: str
    texto: str
    imagem: Optional[str] = None
    tempo_exibicao_segundos: Optional[int] = None
    tempo_resposta_segundos: Optional[int] = None
    permite_multipla_escolha: bool = False
    tem_conteudo_extra: bool = False
    alternativas: list[AlternativaOut] = []


class JogadaOut(Schema):
    id: int
    caso_id: int
    numero_tentativa: int
    conta_para_ranking: bool
    pontuacao: int
    finalizada: bool
    tela_atual: Optional[TelaOut] = None


class RespostaIn(Schema):
    alternativa_ids: list[int] = []
    texto_resposta: str = ""
    numero_resposta: Optional[float] = None
    tempo_esgotado: bool = False


class RespostaOut(Schema):
    pontos_ganhos: int
    pontuacao_total: int
    finalizada: bool
    proxima_tela: Optional[TelaOut] = None


class ConteudoExtraOut(Schema):
    id: int
    tipo: str
    texto: str


class ConteudoExtraRespostaOut(Schema):
    id: int
    resposta: str


class RankingCasoItemOut(Schema):
    aluno_id: int
    nome_jogador: str
    pontuacao: int
    posicao: int
