# Jogo do Advogado — API

Backend em **Django + Django Ninja**, com autenticação **JWT** (via
`django-ninja-jwt`), pronto para servir um app **Flutter**.

## Estrutura

```
config/            settings, urls, agregador da API (config/api.py)
apps/
  contas/          usuário/perfil, instituições de ensino, cadastro, login
  casos/           Disciplina, Caso, Avaliação
  jogo/            motor do jogo: Pergunta (tela), Alternativa,
                   ConteudoExtra, Jogada, RespostaJogada
  ranking/         Nível e rankings (geral, por faculdade, por caso)
  premium/         PlanoPremium, Assinatura
```

## Setup rápido

```bash
uv venv
uv sync
cp .env.example .env   # ajuste as variáveis, principalmente as do banco
uv run manage.py makemigrations
uv run manage.py migrate
uv run manage.py createsuperuser
uv run manage.py runserver
```

Documentação interativa da API (Swagger, gerado pelo Ninja):
`http://localhost:8000/api/docs`

## Fluxo de autenticação (Flutter)

1. `POST /api/auth/login/` → `{access, refresh}`
2. Enviar `Authorization: Bearer <access>` nas demais chamadas
3. Quando o access expirar (401), `POST /api/auth/refresh/` com o `refresh`

## Fluxo de uma partida (Jogada)

1. `GET /api/casos/` — lista de casos (com filtros: disciplina, tipo de
   acesso, tipo de caso, duração, busca, ordenação, `apenas_nao_iniciados`)
2. `POST /api/jogo/casos/{id}/iniciar/` — cria ou retoma a Jogada em
   andamento e retorna a tela atual
3. `POST /api/jogo/jogadas/{id}/responder/` — envia a resposta da tela
   atual (alternativa, texto, número ou vazio para telas informativas) e
   recebe a próxima tela + pontuação
4. Quando não há próxima tela, a Jogada é finalizada automaticamente e a
   pontuação é somada ao perfil do aluno **apenas se for a primeira
   tentativa** (`conta_para_ranking`)
5. `POST /api/jogo/casos/{id}/reiniciar/` — cria uma nova tentativa (não
   conta para ranking)

## Decisões e pontos em aberto (para você revisar)

- **Perfil x gênero para Nível**: o model `Nivel` já guarda nome
  masculino/feminino, mas o `Perfil` ainda não tem campo de gênero — hoje
  `ranking/api.py` sempre retorna o nome masculino. Ajuste quando decidir
  como/se vai coletar essa informação do aluno.
- **Conteúdo extra em `PONTUACAO_EXTRA`**: o ícone de conteúdo extra
  aparece condicionado a `pergunta.conteudos_extra.exists()`. Você
  cadastra os itens de `ConteudoExtra` no Admin, vinculados à Pergunta.
  Um mesmo `ConteudoExtra` pode ser reaproveitado por várias perguntas se
  você quiser (hoje é 1 pra 1 — avise se precisar de reuso).
- **Rankings**: `ranking_geral` e `ranking_faculdades` são calculados a
  partir de `Perfil.pontuacao_total` (desnormalizado, recalculado a cada
  Jogada finalizada). Se a base crescer muito, isso pode virar uma tarefa
  assíncrona/cacheada.
- **Pagamento Premium**: os models de `premium` só guardam
  plano/assinatura; a integração de cobrança (Mercado Pago, por
  exemplo) ainda não está aqui — me avise quando for a hora de plugar.
- Migrations não foram commitadas: rode `makemigrations` no seu ambiente
  (Postgres) antes do primeiro `migrate`.
