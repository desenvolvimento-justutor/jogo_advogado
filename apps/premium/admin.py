from django.contrib import admin

from .models import Assinatura, PlanoPremium


@admin.register(PlanoPremium)
class PlanoPremiumAdmin(admin.ModelAdmin):
    list_display = ("nome", "duracao_dias", "preco_centavos", "ativo")
    list_filter = ("ativo",)


@admin.register(Assinatura)
class AssinaturaAdmin(admin.ModelAdmin):
    list_display = ("aluno", "plano", "inicio", "fim", "ativa", "esta_vigente")
    list_filter = ("ativa", "plano")
    search_fields = ("aluno__username",)
