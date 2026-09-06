from ninja import NinjaAPI

api = NinjaAPI(title="API - Jogo do Advogado", version="1.0.0")

from apps.contas.auth_api import router as auth_router
from apps.contas.api import router as contas_router
from apps.casos.api import router as casos_router
from apps.jogo.api import router as jogo_router
from apps.ranking.api import router as ranking_router
from apps.premium.api import router as premium_router

api.add_router("/auth/", auth_router)
api.add_router("/contas/", contas_router)
api.add_router("/casos/", casos_router)
api.add_router("/jogo/", jogo_router)
api.add_router("/ranking/", ranking_router)
api.add_router("/premium/", premium_router)
