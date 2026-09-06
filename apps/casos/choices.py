from django.db import models


class TipoAcesso(models.TextChoices):
    GRATIS = "gratis", "Grátis"
    PREMIUM = "premium", "Premium"


class TipoCaso(models.TextChoices):
    PARCIAL = "parcial", "Parcial"
    COMPLETO = "completo", "Completo"


class Duracao(models.TextChoices):
    CURTA = "curta", "Curta"
    MEDIA = "media", "Média"
    LONGA = "longa", "Longa"
