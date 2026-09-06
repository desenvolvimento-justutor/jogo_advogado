from django.conf import settings
from django.db import models


class PlanoPremium(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    duracao_dias = models.PositiveIntegerField(help_text="Duração do plano em dias.")
    preco_centavos = models.PositiveIntegerField(help_text="Preço em centavos.")
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Plano Premium"
        verbose_name_plural = "Planos Premium"

    def __str__(self):
        return self.nome


class Assinatura(models.Model):
    aluno = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="assinaturas"
    )
    plano = models.ForeignKey(PlanoPremium, on_delete=models.PROTECT)
    inicio = models.DateField()
    fim = models.DateField()
    ativa = models.BooleanField(default=True)
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Assinatura"
        verbose_name_plural = "Assinaturas"
        ordering = ["-criada_em"]

    def __str__(self):
        return f"{self.aluno} - {self.plano} ({'ativa' if self.ativa else 'expirada'})"

    @property
    def esta_vigente(self):
        from django.utils import timezone

        hoje = timezone.now().date()
        return self.ativa and self.inicio <= hoje <= self.fim
