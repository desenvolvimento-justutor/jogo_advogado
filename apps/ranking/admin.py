from django.contrib import admin

from .models import Nivel


@admin.register(Nivel)
class NivelAdmin(admin.ModelAdmin):
    list_display = ("nome_masculino", "nome_feminino", "pontuacao_minima")
    ordering = ("pontuacao_minima",)
