import json

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.contas.models import Perfil
from apps.jogo.models import Jogada
from tests.utils import bearer_header

from apps.casos.models import Caso, Disciplina

User = get_user_model()


class CasosApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="aluno1", password="senha12345")
        Perfil.objects.create(usuario=self.user, nome_jogador="Aluno 1")

        self.civil = Disciplina.objects.create(nome="Direito Civil")
        self.penal = Disciplina.objects.create(nome="Direito Penal")

        self.caso_civil = Caso.objects.create(
            nome="Danos Morais",
            texto_curto="curto",
            texto_detalhado="detalhado",
            disciplina=self.civil,
            tipo_acesso=Caso.TipoAcesso.GRATIS,
            tipo_caso=Caso.TipoCaso.COMPLETO,
            duracao=Caso.Duracao.MEDIA,
        )
        self.caso_penal = Caso.objects.create(
            nome="Furto Qualificado",
            texto_curto="curto",
            texto_detalhado="detalhado",
            disciplina=self.penal,
            tipo_acesso=Caso.TipoAcesso.PREMIUM,
            tipo_caso=Caso.TipoCaso.PARCIAL,
            duracao=Caso.Duracao.CURTA,
        )

    def test_listar_sem_filtro_retorna_todos_ativos(self):
        resp = self.client.get("/api/casos/", **bearer_header(self.user))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 2)

    def test_filtrar_por_disciplina(self):
        resp = self.client.get(
            f"/api/casos/?disciplina_id={self.civil.id}", **bearer_header(self.user)
        )
        nomes = [c["nome"] for c in resp.json()]
        self.assertEqual(nomes, ["Danos Morais"])

    def test_filtrar_por_tipo_acesso(self):
        resp = self.client.get("/api/casos/?tipo_acesso=premium", **bearer_header(self.user))
        nomes = [c["nome"] for c in resp.json()]
        self.assertEqual(nomes, ["Furto Qualificado"])

    def test_busca_por_texto(self):
        resp = self.client.get("/api/casos/?busca=danos", **bearer_header(self.user))
        nomes = [c["nome"] for c in resp.json()]
        self.assertEqual(nomes, ["Danos Morais"])

    def test_detalhar_caso_retorna_total_de_perguntas(self):
        resp = self.client.get(
            f"/api/casos/{self.caso_civil.id}/", **bearer_header(self.user)
        )
        self.assertEqual(resp.json()["total_perguntas"], 0)

    def test_avaliar_caso_sem_ter_finalizado_retorna_erro(self):
        resp = self.client.post(
            f"/api/casos/{self.caso_civil.id}/avaliar/",
            data=json.dumps({"nota": 5}),
            content_type="application/json",
            **bearer_header(self.user),
        )
        self.assertEqual(resp.status_code, 400)

    def test_avaliar_caso_apos_finalizar_funciona(self):
        Jogada.objects.create(
            aluno=self.user, caso=self.caso_civil, finalizada=True, pergunta_atual=None
        )
        resp = self.client.post(
            f"/api/casos/{self.caso_civil.id}/avaliar/",
            data=json.dumps({"nota": 4}),
            content_type="application/json",
            **bearer_header(self.user),
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["nota"], 4)