# CRM Playbekids — Status, Pendências e Melhorias

**Atualizado em**: 2026-05-28  
**Branch**: `001-crm-ia-loja-infantil`  
**Stack**: Python 3.11 + FastAPI + SQLAlchemy 2.0 | React 18 + Vite 8 + Tailwind v4  
**Banco**: PostgreSQL — schema `crm` (dados CRM) + schema `public` (Playbekids, read-only)

---

## 1. Funcionalidades Implementadas

### Infraestrutura
| Item | Arquivo | Status |
|---|---|---|
| Docker Compose (postgres + backend + frontend) | `docker-compose.yml` | ✅ |
| Alembic + migration completa (8 tabelas no schema `crm`) | `alembic/versions/001_create_crm_tables.py` | ✅ |
| Event bus assíncrono in-process | `src/events/bus.py` | ✅ |
| Subscriptions no startup (segmentacao + growth) | `src/events/handlers.py` | ✅ |
| Logging middleware (método, path, status, ms) | `src/main.py` | ✅ |
| Global exception handler JSON padronizado | `src/main.py` | ✅ |
| CORS configurado para `localhost:5173` | `src/main.py` | ✅ |
| Pydantic Settings lendo `.env` | `src/config.py` | ✅ |

### Backend — Endpoints
| Endpoint | Descrição | Status |
|---|---|---|
| `POST /auth/login` | Valida email+senha, retorna JWT | ✅ |
| `POST /auth/invite` | Gera token de convite (48h TTL) | ✅ |
| `POST /auth/register` | Registra operador via token | ✅ |
| `POST /webhooks/nino/mensagem` | Recebe mensagens do Nino (idempotente) | ✅ |
| `POST /conversas/{id}/handoff` | Operador assume conversa (lock) | ✅ |
| `DELETE /conversas/{id}/handoff` | Libera conversa | ✅ |
| `GET /clientes` | Listagem paginada com filtros | ✅ |
| `GET /clientes/{id}` | Perfil + timeline | ✅ |
| `GET /segmentos` | Segmentos com contagem de clientes | ✅ |
| `GET /acoes` | Ações sugeridas pelos agentes | ✅ |
| `POST /acoes/{id}/aprovar` | Aprova + executa ação | ✅ |
| `POST /acoes/{id}/rejeitar` | Rejeita ação | ✅ |
| `POST /campanhas/gerar` | Aciona Ads Agent | ✅ |
| `GET /campanhas` | Lista campanhas | ✅ |
| `PATCH /campanhas/{id}` | Edita copy/orçamento | ✅ |
| `POST /campanhas/{id}/aprovar` | Aprova campanha | ✅ |
| `POST /campanhas/{id}/rejeitar` | Rejeita campanha | ✅ |
| `GET /metricas/dashboard` | 7 métricas em tempo real | ✅ |
| `GET /conversas` | Listagem de conversas ativas | ✅ |

### Backend — Serviços e Agentes
| Item | Status |
|---|---|
| `ClienteService` — get_or_create, update_classification, sync_from_playbekids | ✅ |
| `ConversaService` — get_or_create_active, start_handoff, end_handoff | ✅ |
| `EventoService` — evaluate_and_emit baseado em sentimento | ✅ |
| `SegmentacaoService` — evaluate_client (6 regras) | ✅ |
| `AcaoAgenteService` — approve (→ executada), reject | ✅ |
| `CampanhaService` — edit, approve, reject (state machine) | ✅ |
| `AuthService` — JWT, bcrypt, invite token | ✅ |
| `GrowthAgent` — sugere ação baseada em evento, respeita janela 24h | ✅ |
| `AdsAgent` — gera campanha com copy + público + orçamento | ✅ |
| `PlaybekidsDB` — get_ultima_compra_by_phone, get_all_purchases (read-only) | ✅ |

### Frontend — Telas
| Rota | Tela | Status |
|---|---|---|
| `/login` | Formulário de login com JWT | ✅ |
| `/dashboard` | 7 cards de métricas + links | ✅ |
| `/clientes` | Tabela paginada + filtro por segmento | ✅ |
| `/clientes/:id` | Perfil + timeline mensagens/compras | ✅ |
| `/conversas` | Lista conversas + handoff | ✅ |
| `/campanhas` | Lista + aprovar/rejeitar | ✅ |
| `/clientes/:id` (insights + ações) | Painel de insights agregados + ações sugeridas inline no perfil | ✅ |
| `/acoes` | Fila global de ações sugeridas pelos agentes | ✅ |

### Scripts Utilitários
| Script | Uso |
|---|---|
| `src/scripts/create_admin.py` | Cria primeiro operador (sem convite) |
| `src/scripts/seed_segmentos.py` | Popula os 6 segmentos default |
| `src/scripts/test_playbekids_connection.py` | Testa conexão com banco Playbekids |

---

## 2. Bugs Confirmados

> Identificados por revisão de código em 2026-05-19. BUG-01, BUG-02 e BUG-03 fechados pelo commit `030cdba`.

### BUG-01 — `GET /conversas` inexistente ✅ RESOLVIDO
Endpoint `GET /api/v1/conversas` implementado em `backend/src/api/conversas.py:16-53` retornando conversas ativas/em_handoff com dados do cliente e operador.

---

### BUG-02 — Tipo errado em `campanhas.ts` ✅ RESOLVIDO
Service corrigido para usar `{ items: Campanha[] }`.

---

### BUG-03 — Comparação de datetime naive vs. aware no `segmentacao_service` ✅ RESOLVIDO
`.replace(tzinfo=None)` removido.

---

### BUG-04 — Mesmo problema de timezone no `growth_agent` ⚠️ MÉDIA — AINDA ABERTO

> **Impacto adicional desde 2026-05-28**: com a nova tela `/acoes` e o bloco "Ações sugeridas" no perfil do cliente (`/clientes/:id`), esse bug fica mais visível — se a sugestão nunca é gerada por causa do `TypeError`, o operador verá a fila sempre vazia. Priorizar a correção.
**Impacto**: `now = datetime.now(timezone.utc).replace(tzinfo=None)` e `window_24h = now - timedelta(hours=24)`. A comparação `last_conv.iniciada_em < window_24h` pode lançar `TypeError` pelo mesmo motivo do BUG-03. O growth agent nunca sugere ações para clientes com conversas recentes.  
**Arquivo**: `backend/src/agents/growth_agent.py:11`.  
**Correção**: Remover o `.replace(tzinfo=None)`.

---

### BUG-05 — Erros no event bus silenciados sem log ⚠️ MÉDIA
**Impacto**: `asyncio.gather(..., return_exceptions=True)` em `bus.py` descarta exceções. Os handlers em `handlers.py` também têm `except Exception: rollback` sem nenhum log. Quando BUG-03 ou BUG-04 ocorrem, não há evidência nos logs — o sistema parece funcionar mas segmentação e sugestões do agente estão quebradas.  
**Arquivo**: `backend/src/events/bus.py:16` e `backend/src/events/handlers.py:20,39`.  
**Correção**: Adicionar `logging.exception(...)` nos blocos `except`.

---

### BUG-06 — N+1 queries em `segmentacao_service` ⚠️ BAIXA
**Impacto**: Para cada cliente avaliado, o serviço faz até 6 queries separadas (`_get_segmento_by_nome` em loop) para buscar segmentos por nome. Com volume de clientes, isso multiplica as queries desnecessariamente.  
**Arquivo**: `backend/src/services/segmentacao_service.py:53-56`.  
**Correção**: Carregar todos os segmentos em uma query `WHERE nome IN (...)` antes do loop.

---

## 3. Funcionalidades Faltando

### F-01 — `GET /conversas` (backend) ✅ RESOLVIDO
Endpoint implementado em `backend/src/api/conversas.py:16-53`.

---

### F-02 — Tela de Ações do Agente (frontend) ✅ RESOLVIDO
- `frontend/src/pages/Acoes/index.tsx` — tela global em `/acoes` listando todas as ações `sugerida`s com botões Aprovar/Rejeitar e link para o cliente.
- `frontend/src/pages/ClienteDetalhe/index.tsx` — bloco "Ações sugeridas" embutido no perfil de cada cliente.
- `frontend/src/services/acoes.ts` — service compartilhado.
- Item no sidebar e link `Ver ações →` no Dashboard.

---

### F-03 — Seed automático de segmentos 🟡 MÉDIA
`seed_segmentos.py` precisa ser executado manualmente após cada `alembic upgrade head`. Se o operador pular essa etapa, a segmentação nunca funciona (nenhum segmento no banco = nenhuma atribuição). 

**Sugestão**: Executar o seed dentro da migration `001` ou em um evento `startup` do lifespan com verificação de idempotência.

---

### F-04 — Nome do cliente nunca preenchido 🟡 MÉDIA
O campo `nome` em `crm.cliente` existe no schema, mas o webhook do Nino não envia esse campo, e não há endpoint `PATCH /clientes/{id}` para atualização manual. A UI exibe o telefone como fallback, mas degradar a experiência do operador que reconhece o cliente pelo nome.

---

### F-05 — Sincronização periódica com Playbekids 🟡 MÉDIA
`ClienteService.sync_from_playbekids()` existe mas nunca é chamado automaticamente. O `ultima_compra_em` só é atualizado se o operador ou um script acionarem manualmente. A classificação `cliente → cliente_recorrente` depende desse dado.

---

### F-06 — Envio de email de convite 🟢 BAIXA
`POST /auth/invite` retorna o token diretamente na resposta JSON (aceitável em dev). Em produção, o token deveria ser enviado por email. O `.env` já tem `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, mas `auth.py` não usa essas variáveis.

---

### F-07 — Refresh de JWT 🟢 BAIXA
Não há `POST /auth/refresh`. Quando o token expira (padrão: 24h), o operador é redirecionado para `/login` e precisa autenticar novamente. O frontend já detecta 401 e redireciona, mas a experiência pode ser melhorada com silent refresh.

---

### F-08 — Testes automatizados 🟢 BAIXA
Estrutura de pastas `tests/unit/` e `tests/integration/` existe mas está completamente vazia. Não há cobertura de nenhuma função.

---

## 4. Melhorias Sugeridas

### M-01 — LLM real nos agentes 🔴 ALTA (valor de negócio)
`GrowthAgent` e `AdsAgent` usam templates hardcoded com `f-string`. Para o CRM agregar valor real, os agentes deveriam chamar um LLM (Claude API) com contexto do cliente (histórico, classificação, segmento, última compra) para gerar conteúdo personalizado.

**Exemplo de contexto para o GrowthAgent:**
```python
prompt = f"""
Cliente: {cliente.nome}, classificação: {cliente.classificacao}
Última interação: {cliente.ultima_interacao_em}
Última compra: {cliente.ultima_compra_em}
Evento: {tipo_evento}
Gere uma mensagem de {tipo_acao} curta e natural em português.
"""
```

---

### M-02 — Padronização de timezone em todo o backend 🟡 MÉDIA
Vários arquivos misturam datetimes naive e aware:
- `segmentacao_service.py`: `.replace(tzinfo=None)` — **remove** tzinfo (BUG-03)
- `growth_agent.py`: `.replace(tzinfo=None)` — **remove** tzinfo (BUG-04)
- `cliente_service.py`: `datetime.now(timezone.utc)` — **correto** (aware)
- `conversa_service.py`: `datetime.now(timezone.utc)` — **correto** (aware)

**Regra a adotar**: sempre usar `datetime.now(timezone.utc)` sem `.replace(tzinfo=None)`. O PostgreSQL TIMESTAMPTZ + asyncpg sempre devolve datetimes aware.

---

### M-03 — Robustez do `_post_process` no webhook 🟡 MÉDIA
`asyncio.create_task(_post_process(...))` desacopla o processamento da resposta HTTP, mas se o servidor for encerrado enquanto a task está na fila, ela é perdida silenciosamente. Para produção, considerar:
- **Mínimo**: adicionar logging de erro no `_post_process`
- **Ideal**: fila leve com APScheduler ou Redis + ARQ

---

### M-04 — `atualizado_em` em `Campanha` não é atualizado automaticamente 🟡 MÉDIA
O campo `atualizado_em` tem `onupdate=lambda: datetime.now(timezone.utc)` no modelo SQLAlchemy, mas o `campanha_service.edit()` faz `await db.commit()` sem emitir um `UPDATE` explícito com atualização do campo. O SQLAlchemy ORM aciona `onupdate` apenas quando o objeto é marcado como dirty, o que pode não acontecer se o commit não detectar a mudança como um update de coluna no servidor.

**Correção**: `campanha.atualizado_em = datetime.now(timezone.utc)` explícito em `campanha_service.edit()`.

---

### M-05 — Histórico completo de compras na timeline ✅ RESOLVIDO
- `backend/src/integrations/playbekids_db.py` ganhou `get_purchases_by_phone(telefone)` retornando todos os timestamps de pedidos confirmados.
- `backend/src/api/clientes.py` agora monta uma entrada de timeline por compra.
- Pendente: incluir `valor` por pedido — contrato `playbekids-db.md` documenta apenas `criado_em`, `telefone_cliente` e `status`. Quando a coluna de valor for confirmada, atualizar contrato + query.

---

### M-06 — Paginação na tela de Campanhas 🟢 BAIXA
O endpoint `GET /campanhas` suporta `page` e `limit`, mas o frontend não implementa controles de paginação. Com volume de campanhas, a tela pode ficar lenta.

---

### M-07 — Deduplicar subscrições do event bus 🟢 BAIXA
`subscribe_all()` é chamado no lifespan do FastAPI. Em ambientes de desenvolvimento com hot-reload do uvicorn, se o módulo `bus.py` não for recarregado mas o lifespan for executado novamente, os handlers se acumulariam. Adicionar uma flag ou verificar se já existe subscriber antes de adicionar.

---

### M-08 — Proteção de rotas no frontend via `localStorage` 🟢 BAIXA
O JWT é armazenado em `localStorage`, que é vulnerável a XSS. Para uma aplicação de produção, o ideal é usar `httpOnly cookie`. Não é crítico em ambiente interno, mas vale registrar para uma revisão de segurança futura.

---

### M-09 — `App.css` não utilizado 🟢 BAIXA
`frontend/src/App.css` é um resquício do template do Vite com variáveis CSS e classes não utilizadas (`--accent`, `.hero`, `#next-steps`, etc.). Não causa bugs, mas polui o projeto.

---

## 5. Priorização Sugerida

### Sprint imediata (bugs e funcionalidades bloqueantes)

| # | Item | Tipo | Status |
|---|---|---|---|
| 1 | ~~Implementar `GET /conversas` (BUG-01 + F-01)~~ | Bug + Feature | ✅ |
| 2 | ~~Corrigir type mismatch em `campanhas.ts` (BUG-02)~~ | Bug | ✅ |
| 3 | Corrigir timezone em `growth_agent` (BUG-04) — BUG-03 já resolvido | Bug | ❗ ainda aberto |
| 4 | Adicionar logging nos handlers do event bus (BUG-05) | Bug | 🔲 |
| 5 | ~~Criar tela de Ações do Agente no frontend (F-02)~~ | Feature | ✅ |
| 6 | Seed automático de segmentos no startup (F-03) | Feature | 🔲 |
| 7 | ~~Histórico completo de compras na timeline (M-05)~~ | Feature | ✅ (sem valor por pedido) |

### Sprint seguinte (valor de negócio)

| # | Item | Tipo | Esforço |
|---|---|---|---|
| 7 | LLM real nos agentes (M-01) | Feature | Médio |
| 8 | Campo `nome` editável pelo operador + PATCH /clientes/{id} (F-04) | Feature | Pequeno |
| 9 | Sincronização periódica com Playbekids (F-05) | Feature | Médio |
| 10 | Histórico completo de compras na timeline (M-05) | Feature | Médio |
| 11 | Padronização de timezone + atualizado_em em Campanha (M-02, M-04) | Melhoria | Pequeno |

### Backlog (melhorias não urgentes)

| # | Item |
|---|---|
| 12 | Testes automatizados (F-08) |
| 13 | Envio de email de convite (F-06) |
| 14 | Refresh de JWT (F-07) |
| 15 | Paginação na tela de Campanhas (M-06) |
| 16 | Robustez do `_post_process` com fila (M-03) |
| 17 | Remover `App.css` não utilizado (M-09) |

---

## 6. Como Rodar (Setup Inicial)

```bash
# 1. Criar .env a partir do exemplo (já feito)
cp backend/.env.example backend/.env  # editar conforme necessário

# 2. Subir containers
docker compose up -d

# 3. Rodar migration
docker compose exec backend alembic upgrade head

# 4. Popular segmentos (MANUAL — ver F-03)
docker compose exec backend python -m src.scripts.seed_segmentos

# 5. Criar primeiro admin
docker compose exec backend python -m src.scripts.create_admin \
  --email admin@playbekids.com --nome "Admin"

# 6. Acessar
open http://localhost:5173
```

---

## 7. Contagem de Tarefas Originais

| Fase | Total | ✅ Feito | 🔲 Pendente |
|---|---|---|---|
| Fase 1 — Setup | 8 | 8 | 0 |
| Fase 2 — Fundação | 14 | 14 | 0 |
| Fase 3 — US1 WhatsApp | 11 | 10 | 1 (validação) |
| Fase 4 — US2 Clientes | 9 | 8 | 1 (validação) |
| Fase 5 — US3 Segmentação | 8 | 7 | 1 (validação) |
| Fase 6 — US4 Growth Agent | 5 | 4 | 1 (validação) |
| Fase 7 — US5 Ads Agent | 6 | 5 | 1 (validação) |
| Fase 8 — US6 Painel Admin | 6 | 5 | 1 (validação) |
| Fase 9 — Polish | 5 | 4 | 1 (validação E2E) |
| **Total** | **72** | **65** | **7** |

> As 7 pendências originais são todas validações de golden path (testes manuais com o sistema rodando).  
> Os bugs e funcionalidades faltando listados acima foram identificados em revisão de código e não estavam no plano original.
