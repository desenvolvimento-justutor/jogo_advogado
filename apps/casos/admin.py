from django.contrib import admin

from .models import Avaliacao, Caso, Disciplina


@admin.register(Disciplina)
class DisciplinaAdmin(admin.ModelAdmin):
    list_display = ("nome",)
    search_fields = ("nome",)


@admin.register(Caso)
class CasoAdmin(admin.ModelAdmin):
    list_display = (
        "nome",
        "disciplina",
        "tipo_acesso",
        "tipo_caso",
        "duracao",
        "ativo",
        "nota_media",
    )
    list_filter = ("disciplina", "tipo_acesso", "tipo_caso", "duracao", "ativo")
    search_fields = ("nome", "texto_curto")


@admin.register(Avaliacao)
class AvaliacaoAdmin(admin.ModelAdmin):
    list_display = ("caso", "aluno", "nota", "criado_em")
    list_filter = ("nota",)
