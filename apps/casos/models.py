from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.casos.choices import TipoAcesso, TipoCaso, Duracao


class Disciplina(models.Model):
    nome = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = "Disciplina"
        verbose_name_plural = "Disciplinas"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Caso(models.Model):

    nome = models.CharField(max_length=150)
    texto_curto = models.CharField(
        max_length=280, help_text="Texto curto exibido na tela principal (lista de casos)."
    )
    texto_detalhado = models.TextField(
        help_text="Texto maior, exibido na tela de detalhamento do caso."
    )
    imagem_capa = models.ImageField(upload_to="casos/capas/", blank=True, null=True)

    disciplina = models.ForeignKey(
        Disciplina, on_delete=models.PROTECT, related_name="casos"
    )
    tipo_acesso = models.CharField(
        max_length=10, choices=TipoAcesso, default=TipoAcesso.GRATIS
    )
    tipo_caso = models.CharField(max_length=10, choices=TipoCaso)
    duracao = models.CharField(max_length=10, choices=Duracao)

    ativo = models.BooleanField(default=True)
    destaque_area_gratuita = models.BooleanField(
        default=False,
        help_text="Aparece na área gratuita do site institucional "
        "(curadoria manual, independente do tipo_acesso).",
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Caso"
        verbose_name_plural = "Casos"
        ordering = ["-criado_em"]

    def __str__(self):
        return self.nome

    @property
    def nota_media(self):
        agg = self.avaliacoes.aggregate(media=models.Avg("nota"))
        return agg["media"] or 0


class Avaliacao(models.Model):
    """Nota dada pelo aluno ao caso, ao finalizá-lo."""

    caso = models.ForeignKey(Caso, on_delete=models.CASCADE, related_name="avaliacoes")
    aluno = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="avaliacoes"
    )
    nota = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Avaliação"
        verbose_name_plural = "Avaliações"
        unique_together = ("caso", "aluno")

    def __str__(self):
        return f"{self.aluno} -> {self.caso} ({self.nota})"
