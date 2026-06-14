<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan
at specs/001-crm-ia-loja-infantil/plan.md
<!-- SPECKIT END -->

---

# Estado do projeto (atualizado 2026-06-14)

CRM inteligente para a loja infantil **Playbekids**. Stack: FastAPI + SQLAlchemy async +
PostgreSQL (schema `crm`) no backend; React + Vite + Tailwind no frontend. Tudo roda em
Docker (`docker compose`): containers `crm-pbk-backend-1`, `crm-pbk-frontend-1`,
`crm-pbk-postgres-1`. Backend em `http://localhost:8000` (API em `/api/v1`), frontend em
`http://localhost:5173`. Postgres do CRM exposto em **localhost:5433** (user/senha `crm`/`crm`, db `playbekids`).

## Fontes de dados / ingestão

O CRM tem **duas** entradas de dados:
1. **Webhook do Nino** (`POST /api/v1/webhooks/nino/mensagem`) — cria cliente/conversa/mensagem.
   `NINO_WEBHOOK_KEY` ainda é o placeholder `change-me-shared-secret` (Nino real não plugado).
2. **Leitura READ-ONLY do Playbekids** (banco do e-commerce) via `PLAYBEKIDS_DB_URL`.

### Banco Playbekids = Supabase/Prisma (READ-ONLY, inegociável)
- É um **Supabase** (`aws-1-us-east-2.pooler.supabase.com`), schema `public`, identificadores
  **camelCase entre aspas** (Prisma). User `crm_reader` (somente `SELECT`).
- Tabelas reais: **`"User"`** (role RETAIL/WHOLESALE/ADMIN; `phone` nullable; `email`, `name`,
  `"createdAt"`, `"lastLoginAt"`), **`"Order"`** (compra confirmada = `"paymentStatus"='APPROVED'`,
  liga por `"userId"`), **`"AbandonedCart"`** (liga por `"userId"`; `subtotal`, `"createdAt"`).
  **NÃO existe `public.pedidos`** (o contrato original em `contracts/playbekids-db.md` assumia errado).
- **RLS**: as tabelas têm Row Level Security ligado e sem policies → `crm_reader` precisa de
  `BYPASSRLS` (já aplicado no Supabase via `ALTER ROLE crm_reader BYPASSRLS;`). Sem isso, todo
  `SELECT` volta vazio sem erro.
- Colunas de data são `timestamp without time zone` (UTC naive) → `playbekids_db.py` converte com
  `_naive_utc` (parâmetros) e `_aware_utc` (retornos). NUNCA escrever no Playbekids.

## Feature principal: Growth Sync (gera ações para o operador executar)

Job **pull agendado** (APScheduler no `lifespan` de `main.py`, a cada `SYNC_INTERVAL_MINUTES`=30;
roda 1x no startup). Lê o Playbekids + dados internos e gera `AcaoAgente(status=sugerida)` que
aparecem na tela `/acoes`. Orquestração em **`src/services/sync_service.py:run_growth_sync`**.
Disparo manual: `docker exec crm-pbk-backend-1 python -m src.scripts.run_sync`.

3 cenários (cada um vira uma ação sugerida; conteúdo em `growth_agent._build_conteudo`):
1. **cadastro_sem_pedido**: `User.role='WHOLESALE'` (atacado) sem `Order` APPROVED → ação `boas_vindas`.
2. **checkout_abandonado**: `AbandonedCart` sem compra APPROVED → ação `recuperacao_checkout`.
3. **conversou_sem_acao**: conversou no Nino e sem compra → ação `reengajamento` (só dados internos).

Mais um passo no sync: **enriquecimento** (`_enrich_site_fields`) espelha em `crm.cliente` os
campos do site `cadastrado_site_em`, `ultimo_login_em`, `papel_site` (match por telefone→email).

### Dedup (importante)
`growth_agent.has_open_acao` impede recriar uma ação se já existir UMA do mesmo `(cliente, tipo)`
na janela `ACAO_DEDUP_DAYS` (=7), **independente do status** (sugerida/aprovada/executada/rejeitada).
Ou seja: depois que o operador **aprova ou rejeita**, a ação NÃO reaparece no próximo sync (dentro
de 7 dias). O evento só é emitido quando uma ação nova é de fato criada (não há spam de eventos).

### Aprovar/Rejeitar (lacuna conhecida)
`POST /acoes/{id}/aprovar` apenas muda status `sugerida → executada` (grava `aprovada_por`,
`executada_em`); rejeitar → `rejeitada`. **NÃO envia mensagem real** ao cliente (sem integração de
envio; o `conteudo_sugerido` é texto para o operador enviar manualmente). O estado `aprovada` do
enum não é usado (vai direto pra `executada`).

## Migrations Alembic (rodam SÓ no DB do CRM, `DATABASE_URL`)
- 001: schema/tabelas base.
- 002: `cliente.email` + alarga `acao_agente.tipo` p/ VARCHAR(40).
- 003: `cliente.telefone` **nullable** (leads de site podem ter só email).
- 004: `cliente.cadastrado_site_em`, `ultimo_login_em`, `papel_site`.

## Frontend
- Tela `/acoes`: lista ações `sugerida`, auto-refresh a cada 30s + ao focar a aba + botão "Atualizar".
  Coluna mostra **"Cadastro no site"** (data de registro do cliente no Playbekids, não no CRM).
- Menu (`components/Layout`): **badge vermelho** com contagem de pendentes ao lado de "Ações"
  (polling 45s; endpoint leve `GET /acoes/contador`).
- Tela `/clientes`: visão geral — Tipo (Atacado/Varejo), Classificação, Cadastro no site, Último
  login, Última compra, Última ação. API de detalhe também devolve esses campos (ainda não exibidos
  na tela de perfil `/clientes/:id`).

## Gotchas operacionais
- O `PLAYBEKIDS_DB_URL` é injetado no container via `env_file` na **criação**. Editar `backend/.env`
  exige `docker compose up -d --build backend` (recriar) para o app enxergar o novo valor — e a
  imagem precisa do `apscheduler` (já em `requirements.txt`); sem rebuild, o container novo quebra.
- `python -m src.scripts.run_sync` é processo separado (lê `.env` fresco), mas o engine do Playbekids
  é criado a partir de `settings` (env do processo) — em scripts pontuais ele pega o env do container.

## Pendências / decisões em aberto
- Plugar o **Nino real** (sincronizar `NINO_WEBHOOK_KEY`).
- Decidir se **rejeitada** deve ser permanente (hoje volta após 7 dias) — não implementado.
- Implementar **envio real** ao aprovar (integração Nino / WhatsApp) — hoje é só "marcar como feito".
- `CADASTRO/CHECKOUT_LOOKBACK_DAYS`=7 (capta backlog da semana); reduzir p/ 2 se quiser só "ontem→hoje".
- Exibir os campos de site na tela de perfil do cliente (dados já vêm na API).

> Senha do admin (`admin@playbekids.com`) e connection string do Supabase NÃO ficam aqui (segredos);
> estão na memória local do Claude. Para resetar senha: `python -m src.scripts.reset_senha --email ...`.
