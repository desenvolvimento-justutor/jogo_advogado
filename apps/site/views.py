from django.shortcuts import render

from apps.casos.models import Caso
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
