from django.contrib import admin

from .models import InstituicaoEnsino, Perfil


@admin.register(InstituicaoEnsino)
class InstituicaoEnsinoAdmin(admin.ModelAdmin):
    list_display = ("nome", "estado")
    list_filter = ("estado",)
    search_fields = ("nome",)


@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ("nome_jogador", "usuario", "instituicao", "pontuacao_total")
    search_fields = ("nome_jogador", "usuario__username", "usuario__email")
    list_filter = ("instituicao",)
