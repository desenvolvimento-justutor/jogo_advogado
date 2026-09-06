import json

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.casos.models import Caso, Disciplina
from apps.contas.models import Perfil
from tests.utils import bearer_header

from .. import services
from ..models import Alternativa, Jogada, Pergunta

User = get_user_model()


class BaseJogoTestCase(TestCase):
    """
    Monta um caso mínimo com 3 telas (informativa -> alternativas -> pontuação)
    suficiente para exercitar o motor do jogo sem depender do seed_dados.
    """

    def setUp(self):
        self.user = User.objects.create_user(username="aluno1", password="senha12345")
        self.perfil = Perfil.objects.create(usuario=self.user, nome_jogador="Aluno 1")

        disciplina = Disciplina.objects.create(nome="Direito Civil")
        self.caso = Caso.objects.create(
            nome="Caso de Teste",
            texto_curto="curto",
            texto_detalhado="detalhado",
            disciplina=disciplina,
            tipo_acesso=Caso.TipoAcesso.GRATIS,
            tipo_caso=Caso.TipoCaso.COMPLETO,
            duracao=Caso.Duracao.CURTA,
        )

        self.p1 = Pergunta.objects.create(
            caso=self.caso, ordem=1, tipo=Pergunta.Tipo.INFORMATIVA, texto="intro"
        )
        self.p2 = Pergunta.objects.create(
            caso=self.caso,
            ordem=2,
            tipo=Pergunta.Tipo.ALTERNATIVAS,
            texto="pergunta",
            tempo_resposta_segundos=30,
        )
        self.alt_certa = Alternativa.objects.create(
            pergunta=self.p2, texto="certa", correta=True, pontos=20, ordem=1
        )
        self.alt_errada = Alternativa.objects.create(
            pergunta=self.p2, texto="errada", correta=False, pontos=-10, ordem=2
        )
        self.p3 = Pergunta.objects.create(
            caso=self.caso,
            ordem=3,
            tipo=Pergunta.Tipo.PONTUACAO,
            texto="fim",
            pontos_fixos=50,
        )


class IniciarOuRetomarJogadaTests(BaseJogoTestCase):
    def test_cria_jogada_na_primeira_tela(self):
        jogada = services.iniciar_ou_retomar_jogada(self.user, self.caso)
        self.assertEqual(jogada.numero_tentativa, 1)
        self.assertTrue(jogada.conta_para_ranking)
        self.assertEqual(jogada.pergunta_atual_id, self.p1.id)

    def test_retoma_jogada_em_andamento_em_vez_de_criar_outra(self):
        primeira = services.iniciar_ou_retomar_jogada(self.user, self.caso)
        segunda_chamada = services.iniciar_ou_retomar_jogada(self.user, self.caso)
        self.assertEqual(primeira.id, segunda_chamada.id)
        self.assertEqual(Jogada.objects.filter(aluno=self.user, caso=self.caso).count(), 1)

    def test_forcar_reinicio_cria_nova_tentativa_sem_contar_ranking(self):
        primeira = services.iniciar_ou_retomar_jogada(self.user, self.caso)
        primeira.finalizada = True
        primeira.save(update_fields=["finalizada"])

        segunda = services.iniciar_ou_retomar_jogada(self.user, self.caso, forcar_reinicio=True)
        self.assertNotEqual(primeira.id, segunda.id)
        self.assertEqual(segunda.numero_tentativa, 2)
        self.assertFalse(segunda.conta_para_ranking)


class ProcessarRespostaTests(BaseJogoTestCase):
    def test_alternativa_correta_soma_pontos_e_avanca(self):
        jogada = services.iniciar_ou_retomar_jogada(self.user, self.caso)
        services.processar_resposta(jogada, [], "", None, False)  # avança a informativa

        pontos, proxima = services.processar_resposta(
            jogada, [self.alt_certa.id], "", None, False
        )
        jogada.refresh_from_db()
        self.assertEqual(pontos, 20)
        self.assertEqual(jogada.pontuacao, 20)
        self.assertEqual(proxima.id, self.p3.id)

    def test_alternativa_errada_desconta_pontos(self):
        jogada = services.iniciar_ou_retomar_jogada(self.user, self.caso)
        services.processar_resposta(jogada, [], "", None, False)

        pontos, _ = services.processar_resposta(jogada, [self.alt_errada.id], "", None, False)
        self.assertEqual(pontos, -10)

    def test_tempo_esgotado_nao_pontua_mesmo_enviando_alternativa(self):
        jogada = services.iniciar_ou_retomar_jogada(self.user, self.caso)
        services.processar_resposta(jogada, [], "", None, False)

        pontos, _ = services.processar_resposta(
            jogada, [self.alt_certa.id], "", None, tempo_esgotado=True
        )
        self.assertEqual(pontos, 0)

    def test_finaliza_jogada_na_ultima_tela_e_soma_ao_perfil(self):
        jogada = services.iniciar_ou_retomar_jogada(self.user, self.caso)
        services.processar_resposta(jogada, [], "", None, False)  # informativa -> alternativas
        services.processar_resposta(jogada, [self.alt_certa.id], "", None, False)  # -> pontuacao
        pontos, proxima = services.processar_resposta(jogada, [], "", None, False)  # pontuacao final

        jogada.refresh_from_db()
        self.perfil.refresh_from_db()
        self.assertIsNone(proxima)
        self.assertTrue(jogada.finalizada)
        self.assertEqual(pontos, 50)
        self.assertEqual(jogada.pontuacao, 70)  # 20 (alternativa certa) + 50 (pontuação fixa)
        self.assertEqual(self.perfil.pontuacao_total, 70)

    def test_responder_apos_finalizada_gera_erro(self):
        jogada = services.iniciar_ou_retomar_jogada(self.user, self.caso)
        for _ in range(3):
            services.processar_resposta(jogada, [], "", None, False)
        jogada.refresh_from_db()
        with self.assertRaises(ValueError):
            services.processar_resposta(jogada, [], "", None, False)


class ReplayNaoContaParaRankingTests(BaseJogoTestCase):
    def test_segunda_tentativa_finalizada_nao_altera_pontuacao_do_perfil(self):
        jogada1 = services.iniciar_ou_retomar_jogada(self.user, self.caso)
        for _ in range(3):
            services.processar_resposta(jogada1, [self.alt_certa.id], "", None, False)
        self.perfil.refresh_from_db()
        pontuacao_apos_primeira = self.perfil.pontuacao_total
        self.assertGreater(pontuacao_apos_primeira, 0)

        jogada2 = services.iniciar_ou_retomar_jogada(self.user, self.caso, forcar_reinicio=True)
        self.assertFalse(jogada2.conta_para_ranking)
        for _ in range(3):
            services.processar_resposta(jogada2, [self.alt_errada.id], "", None, False)

        self.perfil.refresh_from_db()
        self.assertEqual(self.perfil.pontuacao_total, pontuacao_apos_primeira)


class JogoApiTests(BaseJogoTestCase):
    def _post_json(self, url, payload, user):
        return self.client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json",
            **bearer_header(user),
        )

    def test_iniciar_e_percorrer_caso_via_api(self):
        resp = self.client.post(
            f"/api/jogo/casos/{self.caso.id}/iniciar/", **bearer_header(self.user)
        )
        self.assertEqual(resp.status_code, 200)
        jogada_id = resp.json()["id"]
        self.assertEqual(resp.json()["tela_atual"]["tipo"], "informativa")

        resp = self._post_json(f"/api/jogo/jogadas/{jogada_id}/responder/", {}, self.user)
        self.assertEqual(resp.json()["proxima_tela"]["tipo"], "alternativas")

        resp = self._post_json(
            f"/api/jogo/jogadas/{jogada_id}/responder/",
            {"alternativa_ids": [self.alt_certa.id]},
            self.user,
        )
        data = resp.json()
        self.assertEqual(data["pontos_ganhos"], 20)
        self.assertEqual(data["proxima_tela"]["tipo"], "pontuacao")

        resp = self._post_json(f"/api/jogo/jogadas/{jogada_id}/responder/", {}, self.user)
        data = resp.json()
        self.assertTrue(data["finalizada"])
        self.assertIsNone(data["proxima_tela"])

    def test_endpoint_exige_autenticacao(self):
        resp = self.client.post(f"/api/jogo/casos/{self.caso.id}/iniciar/")
        self.assertEqual(resp.status_code, 401)

    def test_ranking_do_caso_ordena_por_pontuacao_desc(self):
        outro_user = User.objects.create_user(username="aluno2", password="senha12345")
        Perfil.objects.create(usuario=outro_user, nome_jogador="Aluno 2")

        jogada1 = services.iniciar_ou_retomar_jogada(self.user, self.caso)
        for _ in range(3):
            services.processar_resposta(jogada1, [self.alt_errada.id], "", None, False)

        jogada2 = services.iniciar_ou_retomar_jogada(outro_user, self.caso)
        for _ in range(3):
            services.processar_resposta(jogada2, [self.alt_certa.id], "", None, False)

        resp = self.client.get(
            f"/api/jogo/casos/{self.caso.id}/ranking/", **bearer_header(self.user)
        )
        ranking = resp.json()
        self.assertEqual(ranking[0]["aluno_id"], outro_user.id)
        self.assertEqual(ranking[0]["posicao"], 1)