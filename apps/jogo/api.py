from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from ninja import Router
from ninja.errors import HttpError
from ninja_jwt.authentication import JWTAuth

from apps.casos.models import Caso

from . import services
from .models import ConteudoExtra, Jogada, Pergunta
from .schemas import (
    ConteudoExtraOut,
    ConteudoExtraRespostaOut,
    JogadaOut,
    RankingCasoItemOut,
    RespostaIn,
    RespostaOut,
)

router = Router(tags=["jogo"], auth=JWTAuth())


def _jogada_out(jogada: Jogada) -> JogadaOut:
    tela = services.montar_tela_out(jogada.pergunta_atual) if jogada.pergunta_atual else None
    return JogadaOut(
        id=jogada.id,
        caso_id=jogada.caso_id,
        numero_tentativa=jogada.numero_tentativa,
        conta_para_ranking=jogada.conta_para_ranking,
        pontuacao=jogada.pontuacao,
        finalizada=jogada.finalizada,
        tela_atual=tela,
    )


@router.post("/casos/{caso_id}/iniciar/", response=JogadaOut)
def iniciar_caso(request, caso_id: int):
    caso = get_object_or_404(Caso, id=caso_id, ativo=True)
    jogada = services.iniciar_ou_retomar_jogada(request.user, caso, forcar_reinicio=False)
    return _jogada_out(jogada)


@router.post("/casos/{caso_id}/reiniciar/", response=JogadaOut)
def reiniciar_caso(request, caso_id: int):
    caso = get_object_or_404(Caso, id=caso_id, ativo=True)
    ja_jogou = Jogada.objects.filter(aluno=request.user, caso=caso, finalizada=True).exists()
    if not ja_jogou:
        raise HttpError(400, "Você só pode reiniciar um caso que já jogou até o fim.")
    jogada = services.iniciar_ou_retomar_jogada(request.user, caso, forcar_reinicio=True)
    return _jogada_out(jogada)


@router.get("/jogadas/{jogada_id}/", response=JogadaOut)
def obter_jogada(request, jogada_id: int):
    jogada = get_object_or_404(Jogada, id=jogada_id, aluno=request.user)
    return _jogada_out(jogada)


@router.post("/jogadas/{jogada_id}/responder/", response=RespostaOut)
def responder(request, jogada_id: int, payload: RespostaIn):
    jogada = get_object_or_404(Jogada, id=jogada_id, aluno=request.user)
    try:
        pontos, proxima = services.processar_resposta(
            jogada,
            alternativa_ids=payload.alternativa_ids,
            texto_resposta=payload.texto_resposta,
            numero_resposta=payload.numero_resposta,
            tempo_esgotado=payload.tempo_esgotado,
        )
    except ValueError as exc:
        raise HttpError(400, str(exc))

    jogada.refresh_from_db()
    return RespostaOut(
        pontos_ganhos=pontos,
        pontuacao_total=jogada.pontuacao,
        finalizada=jogada.finalizada,
        proxima_tela=services.montar_tela_out(proxima) if proxima else None,
    )


@router.get("/perguntas/{pergunta_id}/conteudo-extra/", response=list[ConteudoExtraOut])
def listar_conteudo_extra(request, pergunta_id: int):
    pergunta = get_object_or_404(Pergunta, id=pergunta_id)
    return list(pergunta.conteudos_extra.all())


@router.get(
    "/conteudo-extra/{conteudo_id}/revelar-resposta/", response=ConteudoExtraRespostaOut
)
def revelar_resposta_questao(request, conteudo_id: int):
    conteudo = get_object_or_404(
        ConteudoExtra, id=conteudo_id, tipo=ConteudoExtra.Tipo.QUESTAO_CONCURSO
    )
    return ConteudoExtraRespostaOut(id=conteudo.id, resposta=conteudo.resposta)


@router.get("/casos/{caso_id}/ranking/", response=list[RankingCasoItemOut])
def ranking_do_caso(request, caso_id: int):
    User = get_user_model()
    qs = (
        Jogada.objects.filter(caso_id=caso_id, conta_para_ranking=True, finalizada=True)
        .select_related("aluno__perfil")
        .order_by("-pontuacao")[:100]
    )
    resultado = []
    for posicao, jogada in enumerate(qs, start=1):
        nome = getattr(getattr(jogada.aluno, "perfil", None), "nome_jogador", jogada.aluno.get_username())
        resultado.append(
            RankingCasoItemOut(
                aluno_id=jogada.aluno_id,
                nome_jogador=nome,
                pontuacao=jogada.pontuacao,
                posicao=posicao,
            )
        )
    return resultado
