from typing import Optional

from django.db.models import Avg, Q
from django.shortcuts import get_object_or_404
from ninja import Query, Router
from ninja.errors import HttpError
from ninja_jwt.authentication import JWTAuth

from apps.jogo.models import Jogada

from .models import Avaliacao, Caso
from .schemas import AvaliacaoIn, AvaliacaoOut, CasoDetailOut, CasoListOut

router = Router(tags=["casos"], auth=JWTAuth())


ORDENACOES = {
    "recentes": "-criado_em",
    "nome": "nome",
    "nota": "-nota_media_calc",
    "duracao": "duracao",
}


@router.get("/", response=list[CasoListOut])
def listar_casos(
    request,
    busca: Optional[str] = Query(None),
    disciplina_id: Optional[int] = Query(None),
    tipo_acesso: Optional[str] = Query(None),
    tipo_caso: Optional[str] = Query(None),
    duracao: Optional[str] = Query(None),
    apenas_nao_iniciados: bool = Query(False),
    ordenar_por: str = Query("recentes"),
):
    qs = Caso.objects.filter(ativo=True).select_related("disciplina").annotate(
        nota_media_calc=Avg("avaliacoes__nota")
    )

    if busca:
        qs = qs.filter(Q(nome__icontains=busca) | Q(texto_curto__icontains=busca))
    if disciplina_id:
        qs = qs.filter(disciplina_id=disciplina_id)
    if tipo_acesso:
        qs = qs.filter(tipo_acesso=tipo_acesso)
    if tipo_caso:
        qs = qs.filter(tipo_caso=tipo_caso)
    if duracao:
        qs = qs.filter(duracao=duracao)

    ids_jogados = set(
        Jogada.objects.filter(aluno=request.user).values_list("caso_id", flat=True)
    )
    if apenas_nao_iniciados:
        qs = qs.exclude(id__in=ids_jogados)

    qs = qs.order_by(ORDENACOES.get(ordenar_por, "-criado_em"))

    resultado = []
    for caso in qs:
        item = CasoListOut.from_orm(caso)
        item.ja_iniciado = caso.id in ids_jogados
        resultado.append(item)
    return resultado


@router.get("/{caso_id}/", response=CasoDetailOut)
def detalhar_caso(request, caso_id: int):
    caso = get_object_or_404(Caso.objects.select_related("disciplina"), id=caso_id, ativo=True)
    ja_iniciado = Jogada.objects.filter(aluno=request.user, caso=caso).exists()
    data = CasoDetailOut.from_orm(caso)
    data.ja_iniciado = ja_iniciado
    data.total_perguntas = caso.perguntas.count()
    return data


@router.post("/{caso_id}/avaliar/", response=AvaliacaoOut)
def avaliar_caso(request, caso_id: int, payload: AvaliacaoIn):
    caso = get_object_or_404(Caso, id=caso_id)

    finalizou = Jogada.objects.filter(
        aluno=request.user, caso=caso, finalizada=True
    ).exists()
    if not finalizou:
        raise HttpError(400, "Você só pode avaliar um caso após finalizá-lo.")

    if not (1 <= payload.nota <= 5):
        raise HttpError(400, "Nota deve estar entre 1 e 5.")

    avaliacao, _ = Avaliacao.objects.update_or_create(
        caso=caso, aluno=request.user, defaults={"nota": payload.nota}
    )
    return avaliacao
