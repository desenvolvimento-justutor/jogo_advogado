from django.conf import settings
from django.db import models


class InstituicaoEnsino(models.Model):
    nome = models.CharField(max_length=255)
    estado = models.CharField(max_length=2, help_text="UF, ex.: SP, RJ, TO")

    class Meta:
        verbose_name = "Instituição de Ensino"
        verbose_name_plural = "Instituições de Ensino"
        unique_together = ("nome", "estado")
        ordering = ["nome"]

    def __str__(self):
        return f"{self.nome} ({self.estado})"


class Perfil(models.Model):
    """
    Perfil de jogador, associado 1-a-1 ao usuário Django.
    Guarda os dados específicos do Jogo do Advogado (nome de jogador,
    avatar, instituição, pontuação acumulada etc.).
    """

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="perfil"
    )
    nome_jogador = models.CharField(max_length=100)
    avatar = models.ImageField(upload_to="avatares/", blank=True, null=True)
    instituicao = models.ForeignKey(
        InstituicaoEnsino,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="alunos",
    )
    endereco = models.CharField(max_length=255, blank=True)

    # Preferências
    receber_notificacoes = models.BooleanField(default=True)
    receber_newsletter = models.BooleanField(default=True)

    # Pontuação total, recalculada a partir das Jogadas (ver apps.jogo).
    # Mantida desnormalizada aqui por performance (ranking geral é lido com frequência).
    pontuacao_total = models.PositiveIntegerField(default=0)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Perfil"
        verbose_name_plural = "Perfis"

    def __str__(self):
        return self.nome_jogador or self.usuario.get_username()
