from allauth.account.signals import user_signed_up
from django.dispatch import receiver

from apps.contas.models import Perfil


@receiver(user_signed_up)
def criar_perfil_ao_cadastrar(request, user, **kwargs):
    """
    Garante que todo usuário criado pelo site (e-mail/senha ou Google)
    já tenha um Perfil de jogador, necessário para pontuação e ranking.
    """
    if not user.email:
        nome_padrao = user.get_username()
    else:
        nome_padrao = user.email.split("@")[0]

    Perfil.objects.get_or_create(usuario=user, defaults={"nome_jogador": nome_padrao})
