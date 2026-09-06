from django.contrib import admin

from .models import Alternativa, ConteudoExtra, Jogada, Pergunta, RespostaJogada


class AlternativaInline(admin.TabularInline):
    model = Alternativa
    extra = 2


class ConteudoExtraInline(admin.TabularInline):
    model = ConteudoExtra
    extra = 0


@admin.register(Pergunta)
class PerguntaAdmin(admin.ModelAdmin):
    list_display = ("caso", "ordem", "tipo", "titulo")
    list_filter = ("caso", "tipo")
    ordering = ("caso", "ordem")
    inlines = [AlternativaInline, ConteudoExtraInline]


@admin.register(Jogada)
class JogadaAdmin(admin.ModelAdmin):
    list_display = (
        "aluno",
        "caso",
        "numero_tentativa",
        "conta_para_ranking",
        "pontuacao",
        "finalizada",
    )
    list_filter = ("finalizada", "conta_para_ranking", "caso")
    search_fields = ("aluno__username",)


@admin.register(RespostaJogada)
class RespostaJogadaAdmin(admin.ModelAdmin):
    list_display = ("jogada", "pergunta", "pontos_ganhos", "tempo_esgotado", "respondido_em")
    list_filter = ("tempo_esgotado",)
