from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.contas.models import InstituicaoEnsino, Perfil
from tests.utils import bearer_header

from apps.ranking.models import Nivel

User = get_user_model()


class NivelTests(TestCase):
    def setUp(self):
        Nivel.objects.create(nome_masculino="Estagiário", nome_feminino="Estagiária", pontuacao_minima=0)
        Nivel.objects.create(nome_masculino="Júnior", nome_feminino="Júnior", pontuacao_minima=100)
        Nivel.objects.create(nome_masculino="Pleno", nome_feminino="Plena", pontuacao_minima=300)

    def test_para_pontuacao_abaixo_do_primeiro_nivel(self):
        nivel = Nivel.para_pontuacao(0)
        self.assertEqual(nivel.nome_masculino, "Estagiário")

    def test_para_pontuacao_no_meio(self):
        nivel = Nivel.para_pontuacao(150)
        self.assertEqual(nivel.nome_masculino, "Júnior")

    def test_para_pontuacao_acima_do_maior_nivel(self):
        nivel = Nivel.para_pontuacao(10_000)
        self.assertEqual(nivel.nome_masculino, "Pleno")


class RankingApiTests(TestCase):
    def setUp(self):
        self.uft = InstituicaoEnsino.objects.create(nome="UFT", estado="TO")
        self.usp = InstituicaoEnsino.objects.create(nome="USP", estado="SP")

        self.u1 = User.objects.create_user(username="a1", password="x")
        self.u2 = User.objects.create_user(username="a2", password="x")
        self.p1 = Perfil.objects.create(
            usuario=self.u1, nome_jogador="Aluno 1", instituicao=self.uft, pontuacao_total=300
        )
        self.p2 = Perfil.objects.create(
            usuario=self.u2, nome_jogador="Aluno 2", instituicao=self.usp, pontuacao_total=500
        )

    def test_ranking_geral_ordenado_por_pontuacao_desc(self):
        resp = self.client.get("/api/ranking/geral/", **bearer_header(self.u1))
        nomes = [r["nome_jogador"] for r in resp.json()]
        self.assertEqual(nomes, ["Aluno 2", "Aluno 1"])

    def test_ranking_faculdades_soma_pontuacao_dos_alunos(self):
        resp = self.client.get("/api/ranking/faculdades/", **bearer_header(self.u1))
        dados = {r["nome"]: r["pontuacao_total"] for r in resp.json()}
        self.assertEqual(dados["USP"], 500)
        self.assertEqual(dados["UFT"], 300)