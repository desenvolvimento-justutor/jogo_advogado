from ninja import Schema


class NivelOut(Schema):
    id: int
    nome_masculino: str
    nome_feminino: str
    pontuacao_minima: int


class RankingGeralItemOut(Schema):
    posicao: int
    aluno_id: int
    nome_jogador: str
    pontuacao_total: int
    nivel: str | None = None


class RankingFaculdadeItemOut(Schema):
    posicao: int
    instituicao_id: int
    nome: str
    pontuacao_total: int


class RankingAlunosDaFaculdadeItemOut(Schema):
    posicao: int
    aluno_id: int
    nome_jogador: str
    pontuacao_total: int
