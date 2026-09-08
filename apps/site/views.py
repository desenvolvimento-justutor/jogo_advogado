from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from apps.casos.choices import TipoAcesso
from apps.casos.models import Caso
from apps.jogo import services as jogo_services
from apps.jogo.models import Jogada, Pergunta
from apps.premium.models import PlanoPremium


def home(request):
    """Página de apresentação do Jogo do Advogado."""
    casos_destaque = (
        Caso.objects.filter(ativo=True)
        .select_related("disciplina")
        .order_by("-criado_em")[:3]
    )
    context = {
        "casos_destaque": casos_destaque,
    }
    return render(request, "site/home.html", context)


def planos(request):
    """Página com os planos Premium disponíveis."""
    planos_ativos = PlanoPremium.objects.filter(ativo=True).order_by("preco")

    planos_formatados = [
        {
            "obj": plano,
            "destaque": i == 1 and len(planos_ativos) > 1,  # plano do meio em destaque
        }
        for i, plano in enumerate(planos_ativos)
    ]

    context = {
        "planos": planos_formatados,
    }
    return render(request, "site/planos.html", context)


def area_gratuita(request):
    """Lista os casos selecionados manualmente para a área gratuita do site."""
    casos = (
        Caso.objects.filter(ativo=True, tipo_acesso=TipoAcesso.GRATIS)
        .select_related("disciplina")
        .order_by("nome")
    )
    context = {"casos": casos}
    return render(request, "site/area_gratuita.html", context)


@login_required
def minha_conta(request):
    """Painel simples pós-login, ponto de partida para o app Flutter mais pra frente."""
    perfil = getattr(request.user, "perfil", None)
    context = {"perfil": perfil}
    return render(request, "site/minha_conta.html", context)


def _extrair_resposta_do_post(pergunta: Pergunta, post):
    """Converte os dados de POST para o formato esperado por services.processar_resposta."""
    alternativa_ids: list[int] = []
    texto_resposta = ""
    numero_resposta = None

    if pergunta.tipo == Pergunta.Tipo.ALTERNATIVAS:
        alt_id = post.get("alternativa_id")
        if alt_id:
            alternativa_ids = [int(alt_id)]
    elif pergunta.tipo == Pergunta.Tipo.COLETA_ALTERNATIVAS:
        alternativa_ids = [int(v) for v in post.getlist("alternativa_ids") if v]
    elif pergunta.tipo == Pergunta.Tipo.COLETA_TEXTO:
        texto_resposta = post.get("texto_resposta", "").strip()
    elif pergunta.tipo == Pergunta.Tipo.COLETA_NUMERO:
        valor = post.get("numero_resposta", "").strip()
        if valor:
            try:
                numero_resposta = float(valor.replace(",", "."))
            except ValueError:
                numero_resposta = None

    tempo_esgotado = post.get("tempo_esgotado") == "1"
    return alternativa_ids, texto_resposta, numero_resposta, tempo_esgotado


@login_required
def jogar(request, caso_id):
    """
    Versão jogável do caso direto no navegador (área gratuita). Reaproveita
    o mesmo motor de jogo (apps/jogo/services.py) usado pela API do app.
    """
    caso = get_object_or_404(
        Caso, id=caso_id, ativo=True, tipo_acesso=TipoAcesso.GRATIS
    )

    # Busca a jogada em andamento; se não houver, mostra o resultado da
    # última finalizada (sem criar uma tentativa nova sozinha — isso só
    # acontece quando o aluno clica em "Jogar de novo").
    jogada = (
        Jogada.objects.filter(aluno=request.user, caso=caso, finalizada=False)
        .order_by("-iniciada_em")
        .first()
    )
    if jogada is None:
        jogada = (
            Jogada.objects.filter(aluno=request.user, caso=caso, finalizada=True)
            .order_by("-iniciada_em")
            .first()
        )
    if jogada is None:
        jogada = jogo_services.iniciar_ou_retomar_jogada(request.user, caso)

    if request.method == "POST" and not jogada.finalizada:
        pergunta = jogada.pergunta_atual
        if pergunta is not None:
            alternativa_ids, texto_resposta, numero_resposta, tempo_esgotado = (
                _extrair_resposta_do_post(pergunta, request.POST)
            )
            try:
                jogo_services.processar_resposta(
                    jogada, alternativa_ids, texto_resposta, numero_resposta, tempo_esgotado
                )
            except ValueError:
                pass
        return redirect("site_publico:jogar", caso_id=caso.id)

    pergunta = jogada.pergunta_atual
    context = {
        "caso": caso,
        "jogada": jogada,
        "pergunta": pergunta,
        "Tipo": Pergunta.Tipo,
    }
    if pergunta and pergunta.tipo in (
        Pergunta.Tipo.ALTERNATIVAS,
        Pergunta.Tipo.COLETA_ALTERNATIVAS,
    ):
        context["alternativas"] = pergunta.alternativas.all().order_by("ordem")
    if pergunta and pergunta.tipo == Pergunta.Tipo.PONTUACAO_EXTRA:
        context["conteudos_extra"] = pergunta.conteudos_extra.all()

    return render(request, "site/jogar.html", context)


@login_required
def jogar_reiniciar(request, caso_id):
    caso = get_object_or_404(
        Caso, id=caso_id, ativo=True, tipo_acesso=TipoAcesso.GRATIS
    )
    ja_jogou = Jogada.objects.filter(aluno=request.user, caso=caso, finalizada=True).exists()
    if ja_jogou:
        jogo_services.iniciar_ou_retomar_jogada(request.user, caso, forcar_reinicio=True)
    return redirect("site_publico:jogar", caso_id=caso.id)
