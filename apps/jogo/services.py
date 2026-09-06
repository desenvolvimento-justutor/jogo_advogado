from django.db import transaction
from django.utils import timezone

from apps.casos.models import Caso
from apps.contas.models import Perfil

from .models import Alternativa, Jogada, Pergunta, RespostaJogada
from .schemas import AlternativaOut, TelaOut


def montar_tela_out(pergunta: Pergunta) -> TelaOut:
    alternativas = []
    if pergunta.tipo in (Pergunta.Tipo.ALTERNATIVAS, Pergunta.Tipo.COLETA_ALTERNATIVAS):
        alternativas = [
            AlternativaOut(id=a.id, texto=a.texto, ordem=a.ordem)
            for a in pergunta.alternativas.all().order_by("ordem")
        ]

    return TelaOut(
        id=pergunta.id,
        ordem=pergunta.ordem,
        tipo=pergunta.tipo,
        titulo=pergunta.titulo,
        texto=pergunta.texto,
        imagem=pergunta.imagem.url if pergunta.imagem else None,
        tempo_exibicao_segundos=pergunta.tempo_exibicao_segundos,
        tempo_resposta_segundos=pergunta.tempo_resposta_segundos,
        permite_multipla_escolha=(pergunta.tipo == Pergunta.Tipo.COLETA_ALTERNATIVAS),
        tem_conteudo_extra=pergunta.conteudos_extra.exists(),
        alternativas=alternativas,
    )


@transaction.atomic
def iniciar_ou_retomar_jogada(aluno, caso: Caso, forcar_reinicio: bool = False) -> Jogada:
    jogada_em_andamento = (
        Jogada.objects.filter(aluno=aluno, caso=caso, finalizada=False)
        .order_by("-iniciada_em")
        .first()
    )
    if jogada_em_andamento and not forcar_reinicio:
        return jogada_em_andamento

    primeira_pergunta = caso.perguntas.order_by("ordem").first()
    jogada = Jogada.objects.create(aluno=aluno, caso=caso, pergunta_atual=primeira_pergunta)
    return jogada


def _proxima_pergunta(jogada: Jogada) -> Pergunta | None:
    if jogada.pergunta_atual is None:
        return None
    return (
        jogada.caso.perguntas.filter(ordem__gt=jogada.pergunta_atual.ordem)
        .order_by("ordem")
        .first()
    )


@transaction.atomic
def finalizar_jogada(jogada: Jogada):
    jogada.finalizada = True
    jogada.finalizada_em = timezone.now()
    jogada.pergunta_atual = None
    jogada.save(update_fields=["finalizada", "finalizada_em", "pergunta_atual"])

    if jogada.conta_para_ranking:
        perfil = Perfil.objects.filter(usuario=jogada.aluno).first()
        if perfil:
            perfil.pontuacao_total = models_sum_pontuacao(jogada.aluno)
            perfil.save(update_fields=["pontuacao_total"])


def models_sum_pontuacao(aluno) -> int:
    total = (
        Jogada.objects.filter(aluno=aluno, conta_para_ranking=True, finalizada=True)
        .values_list("pontuacao", flat=True)
    )
    return sum(total)


@transaction.atomic
def processar_resposta(
    jogada: Jogada,
    alternativa_ids: list[int],
    texto_resposta: str,
    numero_resposta: float | None,
    tempo_esgotado: bool,
) -> tuple[int, "Pergunta | None"]:
    """
    Registra a resposta na tela atual da jogada, calcula pontos, avança
    para a próxima tela (ou finaliza a jogada). Retorna (pontos_ganhos, proxima_pergunta).
    """
    if jogada.finalizada:
        raise ValueError("Esta jogada já foi finalizada.")

    pergunta = jogada.pergunta_atual
    if pergunta is None:
        raise ValueError("Jogada sem tela atual.")

    pontos_ganhos = 0
    resposta = RespostaJogada.objects.create(
        jogada=jogada,
        pergunta=pergunta,
        texto_resposta=texto_resposta,
        numero_resposta=numero_resposta,
        tempo_esgotado=tempo_esgotado,
    )

    if pergunta.tipo == Pergunta.Tipo.ALTERNATIVAS and not tempo_esgotado and alternativa_ids:
        alternativa = Alternativa.objects.filter(
            id=alternativa_ids[0], pergunta=pergunta
        ).first()
        if alternativa:
            resposta.alternativas_selecionadas.add(alternativa)
            pontos_ganhos = alternativa.pontos

    elif pergunta.tipo == Pergunta.Tipo.COLETA_ALTERNATIVAS and alternativa_ids:
        alternativas = Alternativa.objects.filter(id__in=alternativa_ids, pergunta=pergunta)
        resposta.alternativas_selecionadas.set(alternativas)

    elif pergunta.tipo in (Pergunta.Tipo.PONTUACAO, Pergunta.Tipo.PONTUACAO_EXTRA):
        pontos_ganhos = pergunta.pontos_fixos or 0

    resposta.pontos_ganhos = pontos_ganhos
    resposta.save(update_fields=["pontos_ganhos"])

    jogada.pontuacao += pontos_ganhos

    proxima = _proxima_pergunta(jogada)
    jogada.pergunta_atual = proxima
    jogada.save(update_fields=["pontuacao", "pergunta_atual"])

    if proxima is None:
        finalizar_jogada(jogada)

    return pontos_ganhos, proxima
