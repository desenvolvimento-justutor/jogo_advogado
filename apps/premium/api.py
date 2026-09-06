from ninja import Router
from ninja_jwt.authentication import JWTAuth

from .models import Assinatura, PlanoPremium
from .schemas import PlanoOut, StatusPremiumOut

router = Router(tags=["premium"], auth=JWTAuth())


@router.get("/planos/", response=list[PlanoOut])
def listar_planos(request):
    return list(PlanoPremium.objects.filter(ativo=True))


@router.get("/status/", response=StatusPremiumOut)
def meu_status_premium(request):
    assinatura = (
        Assinatura.objects.filter(aluno=request.user, ativa=True)
        .order_by("-fim")
        .select_related("plano")
        .first()
    )
    if assinatura and assinatura.esta_vigente:
        return StatusPremiumOut(tem_premium_ativo=True, assinatura=assinatura)
    return StatusPremiumOut(tem_premium_ativo=False, assinatura=None)
