from django.db.models import Sum
from django.shortcuts import get_object_or_404
from ninja import Router
from ninja_jwt.authentication import JWTAuth

from apps.contas.models import InstituicaoEnsino, Perfil

from .models import Nivel
from .schemas import (
    NivelOut,
    RankingAlunosDaFaculdadeItemOut,
    RankingFaculdadeItemOut,
    RankingGeralItemOut,
)

router = Router(tags=["ranking"], auth=JWTAuth())


def _nome_nivel(perfil: Perfil) -> str | None:
    nivel = Nivel.para_pontuacao(perfil.pontuacao_total)
    if not nivel:
        return None
    # Ajuste simples; troque pela lógica de gênero do seu modelo de usuário/perfil.
    return nivel.nome_masculino


@router.get("/geral/", response=list[RankingGeralItemOut])
def ranking_geral(request):
    perfis = Perfil.objects.select_related("usuario").order_by("-pontuacao_total")[:100]
    return [
        RankingGeralItemOut(
            posicao=i,
            aluno_id=p.usuario_id,
            nome_jogador=p.nome_jogador,
            pontuacao_total=p.pontuacao_total,
            nivel=_nome_nivel(p),
        )
        for i, p in enumerate(perfis, start=1)
    ]


@router.get("/faculdades/", response=list[RankingFaculdadeItemOut])
def ranking_faculdades(request):
    instituicoes = (
        InstituicaoEnsino.objects.annotate(pontuacao_total=Sum("alunos__pontuacao_total"))
        .order_by("-pontuacao_total")[:100]
    )
    return [
        RankingFaculdadeItemOut(
            posicao=i,
            instituicao_id=inst.id,
            nome=inst.nome,
            pontuacao_total=inst.pontuacao_total or 0,
        )
        for i, inst in enumerate(instituicoes, start=1)
    ]


@router.get("/faculdades/{instituicao_id}/alunos/", response=list[RankingAlunosDaFaculdadeItemOut])
def ranking_alunos_da_faculdade(request, instituicao_id: int):
    instituicao = get_object_or_404(InstituicaoEnsino, id=instituicao_id)
    perfis = (
        Perfil.objects.filter(instituicao=instituicao)
        .order_by("-pontuacao_total")[:100]
    )
    return [
        RankingAlunosDaFaculdadeItemOut(
            posicao=i,
            aluno_id=p.usuario_id,
            nome_jogador=p.nome_jogador,
            pontuacao_total=p.pontuacao_total,
        )
        for i, p in enumerate(perfis, start=1)
    ]


@router.get("/niveis/", response=list[NivelOut])
def listar_niveis(request):
    return list(Nivel.objects.all())
