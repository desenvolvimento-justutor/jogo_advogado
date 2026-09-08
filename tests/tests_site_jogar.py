from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.casos.choices import Duracao, TipoAcesso, TipoCaso
from apps.casos.models import Caso, Disciplina
from apps.contas.models import Perfil
from apps.jogo.models import Alternativa, Jogada, Pergunta

User = get_user_model()


class JogarHtmlTests(TestCase):
    """Cobre o fluxo de jogo servido em HTML puro (apps/site/views.jogar)."""

    def setUp(self):
        self.user = User.objects.create_user(username="aluno1", password="senha12345")
        self.perfil = Perfil.objects.create(usuario=self.user, nome_jogador="Aluno 1")

        disciplina = Disciplina.objects.create(nome="Direito Civil")
        self.caso = Caso.objects.create(
            nome="Caso HTML",
            texto_curto="curto",
            texto_detalhado="detalhado",
            disciplina=disciplina,
            tipo_acesso=TipoAcesso.GRATIS,
            tipo_caso=TipoCaso.COMPLETO,
            duracao=Duracao.CURTA,
        )
        self.p1 = Pergunta.objects.create(
            caso=self.caso, ordem=1, tipo=Pergunta.Tipo.INFORMATIVA, texto="intro"
        )
        self.p2 = Pergunta.objects.create(
            caso=self.caso,
            ordem=2,
            tipo=Pergunta.Tipo.ALTERNATIVAS,
            texto="pergunta",
            tempo_resposta_segundos=20,
        )
        self.alt_certa = Alternativa.objects.create(
            pergunta=self.p2, texto="certa", correta=True, pontos=15, ordem=1
        )
        self.alt_errada = Alternativa.objects.create(
            pergunta=self.p2, texto="errada", correta=False, pontos=-5, ordem=2
        )
        self.p3 = Pergunta.objects.create(
            caso=self.caso, ordem=3, tipo=Pergunta.Tipo.PONTUACAO, texto="fim", pontos_fixos=30
        )
        self.url = f"/jogar/{self.caso.id}/"

    def _login(self):
        self.client.login(username="aluno1", password="senha12345")

    def test_exige_login(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/accounts/login/", resp.headers["Location"])

    def test_get_inicial_mostra_primeira_tela(self):
        self._login()
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "intro")

    def test_post_avanca_para_proxima_tela(self):
        self._login()
        self.client.post(self.url, {})  # avança a informativa
        resp = self.client.get(self.url)
        self.assertContains(resp, "certa")
        self.assertContains(resp, "errada")

    def test_responder_alternativa_soma_pontos(self):
        self._login()
        self.client.post(self.url, {})
        self.client.post(self.url, {"alternativa_id": self.alt_certa.id})
        jogada = Jogada.objects.get(aluno=self.user, caso=self.caso)
        self.assertEqual(jogada.pontuacao, 15)

    def test_percorrer_ate_o_fim_finaliza_e_soma_ao_perfil(self):
        self._login()
        self.client.post(self.url, {})
        self.client.post(self.url, {"alternativa_id": self.alt_certa.id})
        self.client.post(self.url, {})  # tela de pontuação final

        jogada = Jogada.objects.get(aluno=self.user, caso=self.caso)
        self.perfil.refresh_from_db()
        self.assertTrue(jogada.finalizada)
        self.assertEqual(jogada.pontuacao, 45)
        self.assertEqual(self.perfil.pontuacao_total, 45)

    def test_get_apos_finalizar_mostra_resultado_sem_criar_nova_tentativa(self):
        self._login()
        self.client.post(self.url, {})
        self.client.post(self.url, {"alternativa_id": self.alt_certa.id})
        self.client.post(self.url, {})

        resp = self.client.get(self.url)
        self.assertContains(resp, "45")
        self.assertEqual(
            Jogada.objects.filter(aluno=self.user, caso=self.caso).count(), 1
        )

    def test_jogar_de_novo_cria_nova_tentativa_que_nao_conta_pro_ranking(self):
        self._login()
        self.client.post(self.url, {})
        self.client.post(self.url, {"alternativa_id": self.alt_certa.id})
        self.client.post(self.url, {})

        self.client.post(f"/jogar/{self.caso.id}/reiniciar/")
        resp = self.client.get(self.url)
        self.assertContains(resp, "intro")

        nova = Jogada.objects.filter(aluno=self.user, caso=self.caso, finalizada=False).first()
        self.assertIsNotNone(nova)
        self.assertFalse(nova.conta_para_ranking)

    def test_nao_permite_jogar_caso_premium_pelo_site(self):
        caso_premium = Caso.objects.create(
            nome="Caso Premium",
            texto_curto="curto",
            texto_detalhado="detalhado",
            disciplina=self.caso.disciplina,
            tipo_acesso=TipoAcesso.PREMIUM,
            tipo_caso=TipoCaso.COMPLETO,
            duracao=Duracao.CURTA,
        )
        self._login()
        resp = self.client.get(f"/jogar/{caso_premium.id}/")
        self.assertEqual(resp.status_code, 404)
