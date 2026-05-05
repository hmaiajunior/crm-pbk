# Implementation Plan: CRM Inteligente com Agentes de IA — Loja Infantil

**Branch**: `001-crm-ia-loja-infantil` | **Date**: 2026-05-03 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/001-crm-ia-loja-infantil/spec.md`

## Summary

Sistema de CRM inteligente para a loja infantil Playbekids, integrando atendimento via WhatsApp
(Agent Nino — já existente), gestão centralizada de clientes, segmentação automática por
comportamento, agentes de IA para conversão (Growth Agent) e campanhas (Ads Agent), e painel
administrativo web para operadores.

Stack: Python 3.11 + FastAPI (backend REST API) + React 18 + TypeScript (frontend CRM UI) +
PostgreSQL compartilhado com o e-commerce Playbekids (schema separado `crm`). O sistema recebe
eventos de classificação do Nino via webhook e lê dados de compras diretamente do banco Playbekids
com usuário read-only.

## Technical Context

**Language/Version**: Python 3.11 (backend), TypeScript 5.4 / React 18 (frontend)
**Primary Dependencies**: FastAPI 0.111, SQLAlchemy 2.0, Alembic, Pydantic v2, PyJWT, bcrypt,
asyncpg; React 18, TailwindCSS, shadcn/ui, Vite
**Storage**: PostgreSQL 15 — schema `crm` (tabelas do CRM) + schema `public` do Playbekids
(read-only para compras)
**Testing**: pytest + httpx (backend), Vitest + React Testing Library (frontend)
**Target Platform**: Linux server (VPS ou container Docker)
**Project Type**: Web application (REST API backend + React admin panel frontend)
**Performance Goals**: <500ms p95 para endpoints de API; <30s resposta Agent Nino (SC-007)
**Constraints**: ~50 clientes ativos, ~50 mensagens/dia; suportar crescimento até ~500 clientes
sem redesign
**Scale/Scope**: 50 clientes ativos, 1–5 operadores simultâneos

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Status | Evidência |
|-----------|--------|-----------|
| I. Foco no Cliente | ✅ | CRM centraliza histórico, sentimento e interesses; todas as respostas do Nino usam contexto do cliente |
| II. Simplicidade Operacional | ✅ | React UI com fluxos de no máximo 3 etapas para ações críticas; sem exposição de detalhes técnicos ao operador |
| III. Human-in-the-Loop | ✅ | FR-018 (Growth), FR-022 (Ads), FR-028 (handoff) — toda ação crítica exige aprovação humana explícita |
| IV. Privacidade e Segurança | ✅ | Auth JWT + bcrypt (FR-023); opt-in registrado (FR-007); usuário read-only para Playbekids; LGPD: dados em repouso encriptados via PostgreSQL column encryption ou pgcrypto em `telefone` e `conteudo` |
| V. Comunicação Adequada | ✅ | Nino já implementa tom correto; CRM armazena resultados; copies de campanha revisadas por operador antes de publicação |
| AI: 3 agentes especializados | ✅ | Chat Agent (Nino, existente), Growth Agent, Ads Agent |
| AI: Sem invenção / ações financeiras | ✅ | Agentes geram sugestões; execução requer aprovação do operador |
| AI: Sem mensagens em massa sem consentimento | ✅ | FR-022, opt-in verificado antes de qualquer envio |

**GATE RESULT**: ✅ Aprovado — todos os princípios endereçados no design.

## Project Structure

### Documentation (this feature)

```text
specs/001-crm-ia-loja-infantil/
├── plan.md              # Este arquivo
├── research.md          # Decisões técnicas e alternativas consideradas
├── data-model.md        # Entidades, campos, relações e queries Playbekids
├── quickstart.md        # Setup local e validação golden path
├── contracts/
│   ├── api.md           # REST API endpoints do backend CRM
│   ├── nino-webhook.md  # Contrato webhook Nino → CRM
│   └── playbekids-db.md # Contrato de leitura do banco Playbekids
└── tasks.md             # Gerado pelo /speckit-tasks
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── models/              # SQLAlchemy ORM models (schema crm)
│   │   ├── operador.py
│   │   ├── cliente.py
│   │   ├── conversa.py
│   │   ├── mensagem.py
│   │   ├── segmento.py
│   │   ├── evento.py
│   │   ├── campanha.py
│   │   └── acao_agente.py
│   ├── services/            # Business logic por domínio
│   │   ├── auth_service.py
│   │   ├── cliente_service.py
│   │   ├── conversa_service.py
│   │   ├── segmentacao_service.py
│   │   ├── evento_service.py
│   │   └── campanha_service.py
│   ├── agents/              # Integração com Growth e Ads Agent
│   │   ├── growth_agent.py
│   │   └── ads_agent.py
│   ├── api/                 # FastAPI routers
│   │   ├── auth.py
│   │   ├── clientes.py
│   │   ├── conversas.py
│   │   ├── campanhas.py
│   │   ├── acoes.py
│   │   ├── metricas.py
│   │   ├── segmentos.py
│   │   └── webhooks.py      # Endpoint receptor do Nino
│   ├── events/              # Event bus in-process (asyncio)
│   │   └── bus.py
│   ├── integrations/        # Leituras externas
│   │   └── playbekids_db.py
│   ├── scripts/             # Scripts de setup/seed
│   │   ├── seed_segmentos.py
│   │   ├── create_admin.py
│   │   └── test_playbekids_connection.py
│   ├── config.py
│   └── main.py
├── tests/
│   ├── integration/
│   └── unit/
├── alembic/
│   └── versions/
├── requirements.txt
├── .env.example
└── alembic.ini

frontend/
├── src/
│   ├── components/          # Componentes reutilizáveis
│   │   ├── ClienteCard/
│   │   ├── ConversaTimeline/
│   │   ├── SegmentoFiltro/
│   │   ├── CampanhaCard/
│   │   └── MetricasPanel/
│   ├── pages/               # Páginas do painel
│   │   ├── Dashboard/       # Métricas gerais
│   │   ├── Clientes/        # Lista + filtro por segmento
│   │   ├── ClienteDetalhe/  # Perfil individual + timeline
│   │   ├── Conversas/       # Conversas ativas + handoff
│   │   ├── Campanhas/       # Gerenciamento + aprovação
│   │   └── Auth/            # Login
│   ├── services/            # Clientes HTTP para a API
│   │   ├── api.ts
│   │   ├── clientes.ts
│   │   ├── conversas.ts
│   │   ├── campanhas.ts
│   │   └── auth.ts
│   ├── hooks/               # React hooks customizados
│   └── App.tsx
├── tests/
├── package.json
└── vite.config.ts
```

**Structure Decision**: Web application (backend + frontend separados). Backend FastAPI serve
a API REST; frontend React consome essa API. Separação permite evolução independente de cada
camada e facilita onboarding de desenvolvedores com especialização diferente.

## Complexity Tracking

> Não há violações de princípios constitucionais que exijam justificativa.
