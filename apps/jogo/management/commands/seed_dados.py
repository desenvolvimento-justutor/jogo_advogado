from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.casos.choices import TipoAcesso, TipoCaso, Duracao
from apps.casos.models import Caso, Disciplina
from apps.contas.models import InstituicaoEnsino, Perfil
from apps.jogo.models import Alternativa, ConteudoExtra, Pergunta
from apps.premium.models import PlanoPremium
from apps.ranking.models import Nivel

User = get_user_model()


class Command(BaseCommand):
    help = "Popula o banco com dados de demonstração: disciplinas, instituições, níveis, plano premium, um caso completo e um usuário de teste."

    @transaction.atomic
    def handle(self, *args, **options):
        self._criar_disciplinas()
        self._criar_instituicoes()
        self._criar_niveis()
        self._criar_plano_premium()
        self._criar_usuario_demo()
        self._criar_caso_danos_morais()

        self.stdout.write(self.style.SUCCESS("Dados de demonstração criados com sucesso."))

    def _criar_disciplinas(self):
        nomes = [
            "Direito Civil",
            "Direito Penal",
            "Direito Constitucional",
            "Direito Administrativo",
            "Direito Processual Civil",
        ]
        self.disciplinas = {}
        for nome in nomes:
            disciplina, _ = Disciplina.objects.get_or_create(nome=nome)
            self.disciplinas[nome] = disciplina
        self.stdout.write(f"  {len(nomes)} disciplinas ok")

    def _criar_instituicoes(self):
        dados = [
            ("USP", "SP"),
            ("UFMG", "MG"),
            ("UFT", "TO"),
            ("UERJ", "RJ"),
            ("UFBA", "BA"),
        ]
        for nome, estado in dados:
            InstituicaoEnsino.objects.get_or_create(nome=nome, estado=estado)
        self.stdout.write(f"  {len(dados)} instituições ok")

    def _criar_niveis(self):
        dados = [
            ("Estagiário", "Estagiária", 0),
            ("Advogado Júnior", "Advogada Júnior", 100),
            ("Advogado Pleno", "Advogada Plena", 300),
            ("Advogado Sênior", "Advogada Sênior", 700),
            ("Jurista", "Jurista", 1500),
        ]
        for masc, fem, pontos in dados:
            Nivel.objects.get_or_create(
                pontuacao_minima=pontos,
                defaults={"nome_masculino": masc, "nome_feminino": fem},
            )
        self.stdout.write(f"  {len(dados)} níveis ok")

    def _criar_plano_premium(self):
        PlanoPremium.objects.get_or_create(
            nome="Premium Mensal",
            defaults={
                "descricao": "Acesso a todos os casos premium por 30 dias.",
                "duracao_dias": 30,
                "preco": 2990,
            },
        )
        PlanoPremium.objects.get_or_create(
            nome="Premium Anual",
            defaults={
                "descricao": "Acesso a todos os casos premium por 12 meses.",
                "duracao_dias": 365,
                "preco": 24990,
            },
        )
        self.stdout.write("  2 planos premium ok")

    def _criar_usuario_demo(self):
        user, criado = User.objects.get_or_create(
            username="aluno_demo", defaults={"email": "aluno_demo@example.com"}
        )
        if criado:
            user.set_password("aluno12345")
            user.save()

        Perfil.objects.get_or_create(
            usuario=user,
            defaults={
                "nome_jogador": "Aluno Demo",
                "instituicao": InstituicaoEnsino.objects.filter(estado="TO").first(),
            },
        )
        self.stdout.write("  usuário aluno_demo / senha aluno12345 ok")

    def _criar_caso_danos_morais(self):
        caso, criado = Caso.objects.get_or_create(
            nome="Ação de Indenização por Danos Morais",
            defaults={
                "texto_curto": "Um cliente chega ao seu escritório após ser exposto "
                "publicamente por uma cobrança indevida. Como você conduz o caso?",
                "texto_detalhado": (
                    "O Sr. João procura seu escritório relatando que foi cobrado "
                    "indevidamente por uma dívida já quitada e teve seu nome exposto "
                    "em uma lista pública de devedores no comércio local. Ele quer "
                    "saber se tem direito a indenização e como deve proceder. Conduza "
                    "a análise jurídica do caso, da qualificação dos fatos até a "
                    "eventual propositura da ação."
                ),
                "disciplina": self.disciplinas["Direito Civil"],
                "tipo_acesso": TipoAcesso.GRATIS,
                "tipo_caso": TipoCaso.COMPLETO,
                "duracao": Duracao.MEDIA,
            },
        )
        if not criado:
            self.stdout.write("  caso de demonstração já existia, pulando telas")
            return

        # 1) Informativa
        p1 = Pergunta.objects.create(
            caso=caso,
            ordem=1,
            tipo=Pergunta.Tipo.INFORMATIVA,
            titulo="O caso chega ao escritório",
            texto=(
                "Sr. João, 54 anos, comerciante, procura você relatando que foi "
                "cobrado por um débito já quitado há 8 meses e que seu nome foi "
                "exposto em um mural de devedores em um mercado da cidade."
            ),
        )

        # 2) Alternativas com timer (decisão inicial)
        p2 = Pergunta.objects.create(
            caso=caso,
            ordem=2,
            tipo=Pergunta.Tipo.ALTERNATIVAS,
            titulo="Primeira análise",
            texto="Qual a natureza jurídica mais adequada para o dano sofrido pelo Sr. João?",
            tempo_resposta_segundos=30,
        )
        Alternativa.objects.create(
            pergunta=p2, texto="Dano moral, por exposição vexatória e abalo à honra", correta=True, pontos=20, ordem=1
        )
        Alternativa.objects.create(
            pergunta=p2, texto="Dano exclusivamente material, pela cobrança indevida", correta=False, pontos=-10, ordem=2
        )
        Alternativa.objects.create(
            pergunta=p2, texto="Não há dano indenizável, mero aborrecimento", correta=False, pontos=-20, ordem=3
        )

        # 3) Pontuação com conteúdo extra (legislação + jurisprudência)
        p3 = Pergunta.objects.create(
            caso=caso,
            ordem=3,
            tipo=Pergunta.Tipo.PONTUACAO_EXTRA,
            titulo="Fundamentação",
            texto="Veja os fundamentos legais que sustentam essa análise.",
        )
        ConteudoExtra.objects.create(
            pergunta=p3,
            tipo=ConteudoExtra.Tipo.LEGISLACAO,
            texto="Código Civil, art. 186 c/c art. 927: aquele que, por ação ou "
            "omissão voluntária, negligência ou imprudência, causar dano a "
            "outrem, comete ato ilícito, ficando obrigado a repará-lo.",
        )
        ConteudoExtra.objects.create(
            pergunta=p3,
            tipo=ConteudoExtra.Tipo.JURISPRUDENCIA,
            texto="STJ, Súmula 385: exposição indevida do nome do consumidor em "
            "cadastro de inadimplentes, quando a dívida já foi quitada, gera "
            "dano moral in re ipsa em situações análogas.",
        )

        # 4) Coleta de texto (justificativa do aluno)
        Pergunta.objects.create(
            caso=caso,
            ordem=4,
            tipo=Pergunta.Tipo.COLETA_TEXTO,
            titulo="Sua estratégia",
            texto="Em poucas linhas, como você explicaria ao Sr. João o fundamento do pedido?",
        )

        # 5) Coleta de alternativas (múltipla escolha, sem timer, sem pontuação)
        p5 = Pergunta.objects.create(
            caso=caso,
            ordem=5,
            tipo=Pergunta.Tipo.COLETA_ALTERNATIVAS,
            titulo="Provas a reunir",
            texto="Quais documentos você vai pedir ao Sr. João para instruir a petição inicial?",
        )
        for i, texto in enumerate(
            [
                "Comprovante de quitação do débito",
                "Print ou foto do mural de devedores",
                "Testemunhas que viram a exposição",
                "Boletim de ocorrência",
            ],
            start=1,
        ):
            Alternativa.objects.create(pergunta=p5, texto=texto, ordem=i)

        # 6) Alternativas com timer (prescrição)
        p6 = Pergunta.objects.create(
            caso=caso,
            ordem=6,
            tipo=Pergunta.Tipo.ALTERNATIVAS,
            titulo="Prazo prescricional",
            texto="Qual o prazo prescricional aplicável à pretensão de reparação civil neste caso?",
            tempo_resposta_segundos=30,
        )
        Alternativa.objects.create(pergunta=p6, texto="3 anos, conforme art. 206, §3º, V, do Código Civil", correta=True, pontos=20, ordem=1)
        Alternativa.objects.create(pergunta=p6, texto="10 anos, prazo geral do art. 205 do Código Civil", correta=False, pontos=-10, ordem=2)
        Alternativa.objects.create(pergunta=p6, texto="1 ano, por analogia ao Código de Defesa do Consumidor", correta=False, pontos=-15, ordem=3)

        # 7) Pontuação extra com questão de concurso
        p7 = Pergunta.objects.create(
            caso=caso,
            ordem=7,
            tipo=Pergunta.Tipo.PONTUACAO_EXTRA,
            titulo="Caiu em prova",
            texto="Esse tema já foi cobrado em concurso. Veja só:",
        )
        ConteudoExtra.objects.create(
            pergunta=p7,
            tipo=ConteudoExtra.Tipo.QUESTAO_CONCURSO,
            texto="(Procurador do Estado - AM/2016) A pretensão de reparação civil "
            "por dano moral decorrente de inscrição indevida em cadastro de "
            "inadimplentes prescreve em: (A) 1 ano (B) 3 anos (C) 5 anos (D) 10 anos",
            resposta="Alternativa B - 3 anos, nos termos do art. 206, §3º, V, do Código Civil.",
        )

        # 8) Coleta de número
        Pergunta.objects.create(
            caso=caso,
            ordem=8,
            tipo=Pergunta.Tipo.COLETA_NUMERO,
            titulo="Quantificando o dano",
            texto="Que valor (em R$) você sugeriria pedir a título de indenização por danos morais?",
        )

        # 9) Somente imagem (encerramento)
        Pergunta.objects.create(
            caso=caso,
            ordem=9,
            tipo=Pergunta.Tipo.SO_IMAGEM,
            titulo="Petição protocolada",
            texto="Com os documentos reunidos, a petição inicial é protocolada.",
            tempo_exibicao_segundos=4,
        )

        # 10) Pontuação final (bônus de conclusão)
        Pergunta.objects.create(
            caso=caso,
            ordem=10,
            tipo=Pergunta.Tipo.PONTUACAO,
            titulo="Caso concluído!",
            texto="Você concluiu o caso do Sr. João.",
            pontos_fixos=50,
        )

        self.stdout.write("  caso 'Ação de Indenização por Danos Morais' com 10 telas ok")
