from django.conf import settings
from django.db import models

from apps.casos.models import Caso


class Pergunta(models.Model):
    """
    Representa uma "tela" dentro do caso (nem toda Pergunta é uma pergunta
    de fato — o nome é mantido por simplicidade, mas cobre todos os tipos
    de tela do jogo: informativa, pergunta com alternativas, coleta de
    dados, tela de pontuação etc.)
    """

    class Tipo(models.TextChoices):
        INFORMATIVA = "informativa", "Informativa (texto ou texto + imagem)"
        SO_IMAGEM = "so_imagem", "Somente imagem (com tempo de exibição)"
        ALTERNATIVAS = "alternativas", "Pergunta com alternativas (com timer, pontuada)"
        COLETA_TEXTO = "coleta_texto", "Coleta de dados: texto"
        COLETA_NUMERO = "coleta_numero", "Coleta de dados: número"
        COLETA_ALTERNATIVAS = "coleta_alternativas", "Coleta de dados: alternativas (múltipla escolha, sem timer)"
        PONTUACAO = "pontuacao", "Pontuação sem informações extras"
        PONTUACAO_EXTRA = "pontuacao_extra", "Pontuação com conteúdo extra"

    caso = models.ForeignKey(Caso, on_delete=models.CASCADE, related_name="perguntas")
    ordem = models.PositiveIntegerField(help_text="Posição da tela dentro do caso.")
    tipo = models.CharField(max_length=25, choices=Tipo.choices)

    titulo = models.CharField(max_length=200, blank=True)
    texto = models.TextField(blank=True)
    imagem = models.ImageField(upload_to="jogo/telas/", blank=True, null=True)

    # Usado em SO_IMAGEM (segundos de exibição antes de avançar automaticamente)
    tempo_exibicao_segundos = models.PositiveIntegerField(blank=True, null=True)

    # Usado em ALTERNATIVAS (tempo que o aluno tem para responder)
    tempo_resposta_segundos = models.PositiveIntegerField(blank=True, null=True)

    # Usado em PONTUACAO / PONTUACAO_EXTRA como mensagem fixa (ex.: "Você ganhou $50")
    pontos_fixos = models.IntegerField(
        blank=True,
        null=True,
        help_text="Pontuação fixa atribuída/perdida nesta tela (independente de resposta).",
    )

    class Meta:
        verbose_name = "Pergunta / Tela"
        verbose_name_plural = "Perguntas / Telas"
        ordering = ["caso", "ordem"]
        unique_together = ("caso", "ordem")

    def __str__(self):
        return f"[{self.caso}] #{self.ordem} - {self.get_tipo_display()}"


class Alternativa(models.Model):
    """
    Opção de resposta, usada tanto em telas ALTERNATIVAS (pergunta com
    timer, uma única correta, pontuada) quanto em COLETA_ALTERNATIVAS
    (múltipla escolha livre, sem timer, sem pontuação — apenas dado
    coletado para influenciar textos gerados depois, ex.: sentença).
    """

    pergunta = models.ForeignKey(
        Pergunta, on_delete=models.CASCADE, related_name="alternativas"
    )
    texto = models.CharField(max_length=255)
    correta = models.BooleanField(
        default=False, help_text="Usado apenas em telas do tipo ALTERNATIVAS."
    )
    pontos = models.IntegerField(
        default=0, help_text="Pontos ganhos/perdidos ao escolher esta alternativa."
    )
    ordem = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Alternativa"
        verbose_name_plural = "Alternativas"
        ordering = ["pergunta", "ordem"]

    def __str__(self):
        return f"{self.texto} ({'correta' if self.correta else 'incorreta'})"


class ConteudoExtra(models.Model):
    class Tipo(models.TextChoices):
        SAIBA_MAIS = "saiba_mais", "Saiba mais"
        LEGISLACAO = "legislacao", "Legislação"
        JURISPRUDENCIA = "jurisprudencia", "Jurisprudência"
        QUESTAO_CONCURSO = "questao_concurso", "Questão de concurso"

    pergunta = models.ForeignKey(
        Pergunta, on_delete=models.CASCADE, related_name="conteudos_extra"
    )
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    texto = models.TextField(help_text="Enunciado, texto legal, ementa etc.")
    resposta = models.TextField(
        blank=True,
        help_text="Usado apenas em QUESTAO_CONCURSO: a resposta revelada ao clicar em 'Ver resposta'.",
    )

    class Meta:
        verbose_name = "Conteúdo Extra"
        verbose_name_plural = "Conteúdos Extra"

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.pergunta}"


class Jogada(models.Model):
    """
    Uma "partida" de um aluno em um Caso. O aluno pode reiniciar o caso
    quantas vezes quiser, mas apenas a primeira Jogada finalizada conta
    para pontuação/ranking (conta_para_ranking).
    """

    aluno = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="jogadas"
    )
    caso = models.ForeignKey(Caso, on_delete=models.CASCADE, related_name="jogadas")
    numero_tentativa = models.PositiveIntegerField(default=1)
    conta_para_ranking = models.BooleanField(default=True)

    pergunta_atual = models.ForeignKey(
        Pergunta, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    pontuacao = models.IntegerField(default=0)
    finalizada = models.BooleanField(default=False)

    iniciada_em = models.DateTimeField(auto_now_add=True)
    finalizada_em = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = "Jogada"
        verbose_name_plural = "Jogadas"
        ordering = ["-iniciada_em"]

    def __str__(self):
        return f"{self.aluno} - {self.caso} (tentativa {self.numero_tentativa})"

    def save(self, *args, **kwargs):
        # Define automaticamente se é a primeira tentativa válida para ranking.
        if self._state.adding and self.numero_tentativa == 1:
            ja_jogou = Jogada.objects.filter(aluno=self.aluno, caso=self.caso).exists()
            if ja_jogou:
                ultima = (
                    Jogada.objects.filter(aluno=self.aluno, caso=self.caso)
                    .order_by("-numero_tentativa")
                    .first()
                )
                self.numero_tentativa = ultima.numero_tentativa + 1
                self.conta_para_ranking = False
        super().save(*args, **kwargs)


class RespostaJogada(models.Model):
    """Registro de cada resposta/interação dada pelo aluno em uma Jogada."""

    jogada = models.ForeignKey(
        Jogada, on_delete=models.CASCADE, related_name="respostas"
    )
    pergunta = models.ForeignKey(Pergunta, on_delete=models.CASCADE)

    alternativas_selecionadas = models.ManyToManyField(Alternativa, blank=True)
    texto_resposta = models.TextField(blank=True)
    numero_resposta = models.FloatField(blank=True, null=True)

    tempo_esgotado = models.BooleanField(default=False)
    pontos_ganhos = models.IntegerField(default=0)
    respondido_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Resposta"
        verbose_name_plural = "Respostas"
        ordering = ["respondido_em"]

    def __str__(self):
        return f"{self.jogada} -> {self.pergunta}"
