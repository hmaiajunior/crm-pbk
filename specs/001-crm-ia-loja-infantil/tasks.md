---
description: "Task list for CRM Inteligente com Agentes de IA — Loja Infantil"
---

# Tasks: CRM Inteligente com Agentes de IA — Loja Infantil

**Input**: Design documents from `specs/001-crm-ia-loja-infantil/`
**Prerequisites**: plan.md ✅ | spec.md ✅ | data-model.md ✅ | contracts/ ✅ | research.md ✅

**Stack**: Python 3.11 + FastAPI + SQLAlchemy 2.0 (backend) | React 18 + TypeScript + shadcn/ui (frontend)
**Database**: PostgreSQL — schema `crm` (CRM tables) + schema `public` (Playbekids read-only)

---

## Phase 1: Setup

**Purpose**: Initialize project structure and tooling for both backend and frontend.

- [x] T001 Create backend/ directory structure (src/models, src/services, src/agents, src/api, src/events, src/integrations, src/scripts, tests/unit, tests/integration, alembic/versions) per plan.md
- [x] T002 Initialize backend Python project with requirements.txt: fastapi==0.111.*, sqlalchemy[asyncio]==2.0.*, alembic, asyncpg, pydantic-settings, pyjwt, bcrypt, httpx
- [x] T003 [P] Configure Alembic with async support in backend/alembic.ini and backend/alembic/env.py (asyncpg driver)
- [x] T004 [P] Create backend/.env.example with DATABASE_URL, PLAYBEKIDS_DB_URL, NINO_WEBHOOK_KEY, JWT_SECRET, SMTP_HOST, SMTP_PORT
- [x] T005 [P] Scaffold frontend/ with Vite + React 18 + TypeScript: `npm create vite@latest frontend -- --template react-ts`
- [x] T006 [P] Install and configure TailwindCSS v3 and shadcn/ui in frontend/ (tailwind.config.ts, components.json)
- [x] T007 [P] Create docker-compose.yml with services: backend (FastAPI), frontend (Vite dev), postgres
- [x] T008 Create backend/src/config.py with Pydantic BaseSettings loading from .env (all vars from .env.example)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core models, database schema, and shared infrastructure that ALL user stories depend on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T009 Create crm.operador SQLAlchemy model in backend/src/models/operador.py (id UUID PK, email UNIQUE, nome, senha_hash, ativo bool, criado_em)
- [x] T010 [P] Create crm.cliente SQLAlchemy model in backend/src/models/cliente.py (id, telefone UNIQUE, nome nullable, classificacao enum, opt_in, timestamps) per data-model.md
- [x] T011 [P] Create crm.conversa SQLAlchemy model in backend/src/models/conversa.py (id, cliente_id FK, canal enum, status enum, operador_id FK nullable, handoff timestamps) per data-model.md
- [x] T012 [P] Create crm.mensagem SQLAlchemy model in backend/src/models/mensagem.py (id, conversa_id FK, conteudo, direcao enum, sentimento enum nullable, tema enum nullable, timestamps) per data-model.md
- [x] T013 [P] Create crm.segmento and crm.cliente_segmento models in backend/src/models/segmento.py (segmento: id, nome UNIQUE, descricao, criterios JSONB; cliente_segmento: PK composite) per data-model.md
- [x] T014 [P] Create crm.evento SQLAlchemy model in backend/src/models/evento.py (id, tipo enum, cliente_id FK, payload JSONB, processado bool, criado_em) per data-model.md
- [x] T015 [P] Create crm.campanha SQLAlchemy model in backend/src/models/campanha.py (id, segmento_id FK nullable, copy, publico_alvo JSONB, orcamento_sugerido, status enum, aprovada_por FK nullable, timestamps) per data-model.md
- [x] T016 [P] Create crm.acao_agente SQLAlchemy model in backend/src/models/acao_agente.py (id, tipo enum, agente enum, cliente_id FK, evento_id FK nullable, conteudo_sugerido, status enum, aprovada_por FK nullable, timestamps) per data-model.md
- [x] T017 Write Alembic migration for crm schema + all 8 tables in backend/alembic/versions/001_create_crm_tables.py (depends on T009–T016)
- [x] T018 Configure FastAPI app with asynccontextmanager lifespan, CORS, and router includes in backend/src/main.py
- [x] T019 [P] Implement async database session factory (AsyncSession, get_db dependency) in backend/src/database.py
- [x] T020 [P] Implement in-process async event bus (subscribe/publish with asyncio.gather) in backend/src/events/bus.py
- [x] T021 [P] Implement Playbekids DB reader (read-only SQLAlchemy engine, get_ultima_compra_by_phone query) in backend/src/integrations/playbekids_db.py per contracts/playbekids-db.md
- [x] T022 [P] Create frontend/src/services/api.ts (fetch wrapper with base URL, Bearer JWT header injection, 401 redirect to login)

**Checkpoint**: Foundation ready — all user story phases can now begin.

---

## Phase 3: User Story 1 — Atendimento Contextualizado via WhatsApp (Priority: P1) 🎯 MVP

**Goal**: O sistema recebe mensagens do Nino via webhook, persiste com classificação, cria/atualiza clientes, suporta handoff de operador.

**Independent Test**: Enviar payload do Nino para POST /webhooks/nino/mensagem → verificar cliente criado + mensagem persistida com sentimento/tema + evento gerado para sentimento negativo.

- [x] T023 [US1] Implement JWTService (create_token, decode_token, get_current_operador dependency) in backend/src/services/auth_service.py (PyJWT + bcrypt)
- [x] T024 [US1] Implement POST /auth/login endpoint in backend/src/api/auth.py per contracts/api.md (validate email+password, return JWT)
- [x] T025 [US1] Implement POST /auth/invite and POST /auth/register endpoints in backend/src/api/auth.py (invite token with 48h TTL, register from token)
- [x] T026 [US1] Create backend/src/scripts/create_admin.py (interactive CLI to create first admin operador without invite)
- [x] T027 [US1] Implement ClienteService.get_or_create_by_phone() in backend/src/services/cliente_service.py (lookup by telefone, create if new, set opt_in + primeira_interacao_em)
- [x] T028 [US1] Implement ConversaService.get_or_create_active() in backend/src/services/conversa_service.py (return open conversa or create new for cliente)
- [x] T029 [US1] Implement POST /webhooks/nino/mensagem in backend/src/api/webhooks.py per contracts/nino-webhook.md (validate X-Nino-Key, idempotency on mensagem_id, persist mensagem, trigger async post-processing)
- [x] T030 [US1] Implement async post-processing after webhook: update cliente.ultima_interacao_em + call EventoService.evaluate_and_emit() in backend/src/api/webhooks.py
- [x] T031 [US1] Implement EventoService.evaluate_and_emit() in backend/src/services/evento_service.py (generate evento based on sentimento: negativo → cliente_insatisfeito; positivo recorrente → cliente_interessado)
- [x] T032 [US1] Implement POST /conversas/{id}/handoff and DELETE /conversas/{id}/handoff in backend/src/api/conversas.py per contracts/api.md (lock on first operator, 409 if already in handoff)
- [ ] T033 [US1] Validate US1 golden path: run quickstart.md step 4 (Nino webhook mock) → confirm cliente created, mensagem persisted, event generated for sentimento=negativo

**Checkpoint**: US1 complete — webhook receiver, customer creation, and handoff fully functional.

---

## Phase 4: User Story 2 — Gestão Centralizada de Clientes (Priority: P2)

**Goal**: Operadora acessa lista e perfil completo de cada cliente com timeline atualizada automaticamente.

**Independent Test**: Após webhook do Nino (US1 complete), acessar GET /clientes → ver cliente criado; GET /clientes/{id} → ver timeline com mensagem, sentimento e data.

- [x] T034 [P] [US2] Implement ClienteService.update_classification() in backend/src/services/cliente_service.py (recalculate lead/cliente/cliente_recorrente/inativo based on purchases + last interaction per data-model.md rules)
- [x] T035 [P] [US2] Implement ClienteService.sync_from_playbekids() in backend/src/services/cliente_service.py (query integrations/playbekids_db.py, update ultima_compra_em + recalculate classification)
- [x] T036 [US2] Implement GET /clientes (paginated, segmento_id + classificacao filters) in backend/src/api/clientes.py per contracts/api.md
- [x] T037 [US2] Implement GET /clientes/{id} with assembled timeline (mensagens + compras + eventos ordered by timestamp) in backend/src/api/clientes.py per contracts/api.md
- [x] T038 [US2] Create frontend/src/services/clientes.ts (typed API client: getClientes, getCliente, getTimeline)
- [x] T039 [P] [US2] Create frontend Auth/Login page in frontend/src/pages/Auth/ (email+password form, store JWT in localStorage, redirect to dashboard on success)
- [x] T040 [P] [US2] Create frontend Clientes page in frontend/src/pages/Clientes/ (paginated table with nome, telefone, classificacao, ultima_interacao_em columns)
- [x] T041 [US2] Create frontend ClienteDetalhe page in frontend/src/pages/ClienteDetalhe/ (profile header + ConversaTimeline component showing mensagens/sentimentos/compras in chronological order)
- [ ] T042 [US2] Validate US2 independently: login → open /clientes → click client → verify timeline shows message from US1 webhook with sentimento and tema

**Checkpoint**: US2 complete — operators can view client list and individual profiles with full timeline.

---

## Phase 5: User Story 3 — Segmentação Automática de Clientes (Priority: P3)

**Goal**: Clientes são classificados em segmentos automaticamente; operadora filtra por segmento na lista.

**Independent Test**: Criar cliente com ultima_interacao_em = 35 dias atrás → verificar que aparece no segmento "Clientes Inativos" após recálculo automático.

- [x] T043 [US3] Implement SegmentacaoService.evaluate_client() in backend/src/services/segmentacao_service.py (evaluate all 6 segment rules per data-model.md, update crm.cliente_segmento)
- [x] T044 [US3] Subscribe SegmentacaoService to event bus in backend/src/events/bus.py: recalculate after message webhook and after Playbekids sync
- [x] T045 [US3] Create backend/src/scripts/seed_segmentos.py (insert 6 default segments with JSONB criteria per data-model.md seed table)
- [x] T046 [US3] Implement GET /segmentos in backend/src/api/segmentos.py per contracts/api.md (return nome + total_clientes per segment)
- [x] T047 [US3] Wire segmento_id filter into GET /clientes endpoint in backend/src/api/clientes.py (JOIN cliente_segmento WHERE segmento_id = :id)
- [x] T048 [P] [US3] Create SegmentoFiltro component in frontend/src/components/SegmentoFiltro/ (dropdown fetching GET /segmentos, emit selected segmento_id to parent)
- [x] T049 [US3] Wire SegmentoFiltro into frontend Clientes page (pass segmento_id to getClientes API call, re-fetch on change)
- [ ] T050 [US3] Validate US3 independently: run seed_segmentos → send webhook for client with 35-day-old data → verify client appears under "Clientes Inativos" filter in frontend

**Checkpoint**: US3 complete — automatic segmentation running; operators can filter by segment.

---

## Phase 6: User Story 4 — Ativação e Conversão via Growth Agent (Priority: P4)

**Goal**: Growth Agent recebe eventos e sugere ações de conversão que o operador aprova antes do envio.

**Independent Test**: Emitir evento cliente_pronto_compra → verificar que Growth Agent cria acao_agente com status=sugerida → aprovar via POST /acoes/{id}/aprovar → confirmar status=executada.

- [x] T051 [US4] Implement GrowthAgent.process_event() in backend/src/agents/growth_agent.py (call LLM with client context + event, return suggested action type + conteudo_sugerido; respect 24h WhatsApp window rule)
- [x] T052 [US4] Implement AcaoAgenteService (create_suggestion, approve, reject, execute) in backend/src/services/acao_agente_service.py (enforce: no execution without aprovada_por)
- [x] T053 [US4] Subscribe GrowthAgent to event bus in backend/src/events/bus.py (events: cliente_interessado, cliente_pronto_compra → call GrowthAgent.process_event())
- [x] T054 [US4] Implement GET /acoes, POST /acoes/{id}/aprovar, POST /acoes/{id}/rejeitar in backend/src/api/acoes.py per contracts/api.md
- [ ] T055 [US4] Validate US4 independently: emit cliente_pronto_compra via test script → verify acao_agente created with status=sugerida → approve via API → confirm status=executada

**Checkpoint**: US4 complete — Growth Agent suggests actions; operators approve before execution.

---

## Phase 7: User Story 5 — Criação e Aprovação de Campanhas via Ads Agent (Priority: P5)

**Goal**: Ads Agent gera campanha completa (copy + público + orçamento) com aprovação obrigatória do operador antes de publicar.

**Independent Test**: POST /campanhas/gerar com segmento_id → Ads Agent gera rascunho → operador edita copy via PATCH → aprova via POST /campanhas/{id}/aprovar → status = aprovada (nunca publicada automaticamente).

- [x] T056 [US5] Implement AdsAgent.generate_campaign() in backend/src/agents/ads_agent.py (call LLM with segment data, generate copy + publico_alvo JSONB + orcamento_sugerido; status=rascunho on creation)
- [x] T057 [US5] Implement CampanhaService (create, edit fields, approve state machine, reject) in backend/src/services/campanha_service.py (enforce: publicada requires aprovada_por not null per data-model.md invariant)
- [x] T058 [US5] Implement POST /campanhas/gerar, GET /campanhas, PATCH /campanhas/{id}, POST /campanhas/{id}/aprovar, POST /campanhas/{id}/rejeitar in backend/src/api/campanhas.py per contracts/api.md
- [x] T059 [P] [US5] Create frontend/src/services/campanhas.ts (typed API client: getCampanhas, gerarCampanha, editarCampanha, aprovarCampanha, rejeitarCampanha)
- [x] T060 [P] [US5] Create frontend Campanhas page in frontend/src/pages/Campanhas/ (list with status badge; approve/reject with shadcn AlertDialog confirmation)
- [ ] T061 [US5] Validate US5 independently: generate campaign → edit copy → approve → verify status=aprovada and aprovada_por is set; verify no campaign reaches status=publicada without aprovada_por

**Checkpoint**: US5 complete — Ads Agent generates campaigns; mandatory human approval enforced.

---

## Phase 8: User Story 6 — Painel Administrativo (CRM UI) (Priority: P6)

**Goal**: Operadora tem visão centralizada de métricas, clientes, conversas e campanhas pendentes em um único painel web.

**Independent Test**: Login → dashboard carrega métricas corretas → filtrar clientes por segmento → abrir perfil → assumir conversa com no máximo 2 cliques → confirmar handoff bloqueado para outros operadores.

- [x] T062 [US6] Implement GET /metricas/dashboard in backend/src/api/metricas.py per contracts/api.md (clientes_total, clientes_novos_7d, clientes_ativos, clientes_inativos, atendimentos_hoje, acoes_pendentes, campanhas_pendentes)
- [x] T063 [P] [US6] Create MetricasPanel component in frontend/src/components/MetricasPanel/ (6 metric cards from GET /metricas/dashboard)
- [x] T064 [P] [US6] Create Dashboard page in frontend/src/pages/Dashboard/ (MetricasPanel + quick links to pending actions and campaigns)
- [x] T065 [US6] Create Conversas page in frontend/src/pages/Conversas/ (list active/handoff conversations; "Assumir" button → shadcn AlertDialog confirm → POST /conversas/{id}/handoff; show operador ativo name when locked)
- [x] T066 [US6] Wire React Router in frontend/src/App.tsx: protected routes (redirect /login if no JWT), define routes for /dashboard, /clientes, /clientes/:id, /conversas, /campanhas
- [ ] T067 [US6] Validate US6 independently: full flow — login → dashboard metrics correct → filter "Clientes Inativos" → open client profile → assume conversation (2 clicks) → verify conversation locked to operator

**Checkpoint**: US6 complete — full admin panel operational for all operator workflows.

---

## Phase 9: Polish & Cross-Cutting Concerns

- [x] T068 [P] Add structured request/response logging middleware to backend/src/main.py (log method, path, status, duration; mask sensitive fields: senha, token)
- [x] T069 [P] Add global exception handler in backend/src/main.py returning standardized JSON error format per contracts/api.md error table
- [x] T070 [P] Add protected route guard in frontend/src/App.tsx (check JWT expiry on each route transition; auto-redirect to /login on 401)
- [ ] T071 Run quickstart.md golden path end-to-end (all 6 steps) and fix any issues found
- [x] T072 [P] Create backend/src/scripts/test_playbekids_connection.py (test read-only connection, run get_ultima_compra query, print result per quickstart.md step 5)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Phase 2 — can start immediately after foundation
- **US2 (Phase 4)**: Depends on Phase 2 + US1 webhook working (client data needed)
- **US3 (Phase 5)**: Depends on Phase 2 + US1 (events needed to trigger segmentation)
- **US4 (Phase 6)**: Depends on Phase 2 + US1 (events) + US3 (segmentation context)
- **US5 (Phase 7)**: Depends on Phase 2 + US3 (segments needed for campaign audience)
- **US6 (Phase 8)**: Depends on Phase 2 + US2 (client data) + auth from US1
- **Polish (Phase 9)**: Depends on all user stories complete

### Parallel Opportunities

- **Phase 1**: T003–T007 can all run in parallel after T001
- **Phase 2**: T009–T016 all run in parallel (separate model files); T018–T022 run in parallel after T017
- **US2**: T034–T035 in parallel; T039–T040 in parallel
- **US5**: T059–T060 in parallel after T057
- **US6**: T063–T064 in parallel after T062

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: US1 (webhook + handoff)
4. **STOP and VALIDATE**: Send Nino mock → verify client + message created

### Incremental Delivery

1. US1 → Webhook receiver functional (Nino integration live)
2. US2 → Client management visible in UI
3. US3 → Segmentation active (marketing intelligence)
4. US4 → Growth Agent live (conversion actions)
5. US5 → Ads Agent live (campaign creation)
6. US6 → Full admin dashboard

---

## Notes

- [P] tasks = different files, no blocking dependencies — safe to run in parallel
- [US#] label maps each task to its user story for traceability
- T029 (webhook) is the most critical task — all data flows from it
- T017 (Alembic migration) blocks all service work — prioritize within Phase 2
- Playbekids integration (T021, T035) should be tested early against real DB schema
