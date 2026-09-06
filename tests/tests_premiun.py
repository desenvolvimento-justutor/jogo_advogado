import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.contas.models import Perfil
from tests.utils import bearer_header

from apps.premium.models import Assinatura, PlanoPremium

User = get_user_model()


class AssinaturaTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="aluno1", password="senha12345")
        Perfil.objects.create(usuario=self.user, nome_jogador="Aluno 1")
        self.plano = PlanoPremium.objects.create(
            nome="Mensal", duracao_dias=30, preco_centavos=2990
        )

    def _criar_assinatura(self, inicio, fim, ativa=True):
        return Assinatura.objects.create(
            aluno=self.user, plano=self.plano, inicio=inicio, fim=fim, ativa=ativa
        )

    def test_esta_vigente_dentro_do_periodo(self):
        hoje = timezone.now().date()
        assinatura = self._criar_assinatura(
            hoje - datetime.timedelta(days=1), hoje + datetime.timedelta(days=29)
        )
        self.assertTrue(assinatura.esta_vigente)

    def test_nao_esta_vigente_apos_o_fim(self):
        hoje = timezone.now().date()
        assinatura = self._criar_assinatura(
            hoje - datetime.timedelta(days=40), hoje - datetime.timedelta(days=10)
        )
        self.assertFalse(assinatura.esta_vigente)

    def test_nao_esta_vigente_se_inativa(self):
        hoje = timezone.now().date()
        assinatura = self._criar_assinatura(
            hoje - datetime.timedelta(days=1), hoje + datetime.timedelta(days=29), ativa=False
        )
        self.assertFalse(assinatura.esta_vigente)

    def test_status_api_sem_assinatura(self):
        resp = self.client.get("/api/premium/status/", **bearer_header(self.user))
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.json()["tem_premium_ativo"])

    def test_status_api_com_assinatura_vigente(self):
        hoje = timezone.now().date()
        self._criar_assinatura(hoje, hoje + datetime.timedelta(days=29))
        resp = self.client.get("/api/premium/status/", **bearer_header(self.user))
        data = resp.json()
        self.assertTrue(data["tem_premium_ativo"])
        self.assertEqual(data["assinatura"]["plano"]["nome"], "Mensal")