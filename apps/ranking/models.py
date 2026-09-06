from django.db import models


class Nivel(models.Model):
    """
    Classificação atribuída ao jogador de acordo com sua pontuação total
    (soma de todos os casos jogados). Configurável via Admin.
    """

    nome_masculino = models.CharField(max_length=50)
    nome_feminino = models.CharField(max_length=50)
    pontuacao_minima = models.PositiveIntegerField(
        help_text="Pontuação mínima para atingir este nível."
    )

    class Meta:
        verbose_name = "Nível"
        verbose_name_plural = "Níveis"
        ordering = ["pontuacao_minima"]

    def __str__(self):
        return f"{self.nome_masculino}/{self.nome_feminino} (>= {self.pontuacao_minima} pts)"

    @classmethod
    def para_pontuacao(cls, pontuacao: int):
        """Retorna o maior Nível cuja pontuacao_minima seja <= pontuacao."""
        return (
            cls.objects.filter(pontuacao_minima__lte=pontuacao)
            .order_by("-pontuacao_minima")
            .first()
        )
