# Research: CRM Inteligente com Agentes de IA — Loja Infantil

**Branch**: `001-crm-ia-loja-infantil` | **Date**: 2026-05-03

## Decisões Técnicas

---

### 1. Linguagem e Framework Backend

**Decision**: Python 3.11 + FastAPI 0.111

**Rationale**:
- Nino já é um sistema multi-agêntico de IA — Python é a linguagem dominante no ecossistema de IA/LLM (LangChain, LangGraph, Anthropic SDK).
- Manter a mesma linguagem do Nino reduz fragmentação e facilita integrações internas.
- FastAPI oferece suporte nativo a async/await (necessário para webhook Nino e eventos), validação automática com Pydantic v2 e geração de documentação OpenAPI sem custo adicional.

**Alternatives considered**:
- Node.js/Express: descartado por afastar-se do ecossistema Python do Nino.
- Django + DRF: mais pesado que o necessário para a escala do projeto (~50 clientes); FastAPI entrega mais produtividade com menos overhead.

---

### 2. Frontend CRM UI

**Decision**: React 18 + TypeScript 5.4 + TailwindCSS + shadcn/ui

**Rationale**:
- React é o padrão de mercado para painéis administrativos com o maior ecossistema de componentes.
- TypeScript elimina classes inteiras de bugs de runtime, especialmente em formulários de aprovação (campanhas, handoff).
- shadcn/ui entrega componentes acessíveis e prontos (tabelas, modais, formulários) sem lock-in, reduzindo tempo de desenvolvimento do painel para operadores não-técnicos.

**Alternatives considered**:
- Vue.js: válido, mas ecossistema menor para painéis admin complexos.
- Next.js: descartado por adicionar complexidade de SSR desnecessária para um painel interno.

---

### 3. Banco de Dados e ORM

**Decision**: PostgreSQL 15 (schema `crm` separado no banco compartilhado com Playbekids) + SQLAlchemy 2.0 + Alembic

**Rationale**:
- Banco compartilhado com Playbekids (decisão confirmada na clarification). Usar um schema PostgreSQL separado (`crm`) isola as tabelas do CRM das do e-commerce, mantendo acesso direto sem duplicar infraestrutura.
- SQLAlchemy 2.0 com suporte async nativo (asyncpg driver) alinha com FastAPI async.
- Alembic para versionamento de migrações — essencial quando dois sistemas compartilham o mesmo servidor PostgreSQL.

**Alternatives considered**:
- Banco de dados separado: descartado pela decisão de compartilhamento com Playbekids para leitura de compras.
- Tortoise ORM: menos maduro; SQLAlchemy tem ecossistema mais amplo.

---

### 4. Integração com Playbekids (Leitura de Compras)

**Decision**: Leitura direta via SQLAlchemy (conexão read-only ao schema do Playbekids)

**Rationale**:
- Decisão confirmada na clarification: banco compartilhado, mesmo time de desenvolvimento.
- Uma connection string com usuário PostgreSQL read-only ao schema `public` do Playbekids garante que o CRM nunca escreva no e-commerce.
- Query mapeada: `SELECT telefone_cliente, MAX(criado_em) FROM pedidos WHERE status = 'confirmado' GROUP BY telefone_cliente`.

**Constraint documentado**: O CRM DEVE usar um usuário PostgreSQL separado com permissão apenas `SELECT` nas tabelas do Playbekids. Nenhuma escrita deve ser permitida.

---

### 5. Sistema de Eventos Internos

**Decision**: Event bus in-process com asyncio (padrão Observer/Publisher-Subscriber)

**Rationale**:
- Volume de ~50 mensagens/dia não justifica infraestrutura de message queue (Redis, RabbitMQ, Kafka).
- Um event bus simples em Python asyncio (classe `EventBus` com `subscribe`/`publish`) é suficiente, testável e sem dependências externas.
- Se o volume escalar para centenas/dia, a interface do bus pode ser reimplementada com Redis Pub/Sub sem alterar o código consumidor.

**Alternatives considered**:
- Redis Pub/Sub: descartado pela escala atual; adiciona dependência de infraestrutura sem benefício real.
- Celery: overkill para volume de 50 eventos/dia.

---

### 6. Autenticação

**Decision**: JWT (PyJWT) + bcrypt + convite por e-mail (SMTP)

**Rationale**:
- Decisão confirmada na clarification: email + senha com convite.
- JWT stateless integra nativamente com FastAPI via `fastapi-security`.
- bcrypt para hash de senhas é o padrão de segurança atual.
- Fluxo de convite: operador admin envia e-mail com token de registro único (TTL 48h).

**Alternatives considered**:
- Sessions com Redis: descartado por adicionar estado e dependência de infraestrutura.
- OAuth2/Google SSO: descartado (equipe não usa Google Workspace como requisito).

---

### 7. Integração com Nino (Webhook Receiver)

**Decision**: FastAPI endpoint POST `/webhooks/nino/mensagem` com validação Pydantic + chave de API compartilhada

**Rationale**:
- Nino já processa mensagens e gera classificações. O CRM precisa apenas de um endpoint para receber os resultados.
- Autenticação do webhook via header `X-Nino-Key` (chave compartilhada em variável de ambiente) — simples e adequado para comunicação interna.
- Processamento assíncrono: o endpoint persiste a mensagem e dispara eventos internos sem bloquear o retorno ao Nino.

---

### 8. Deployment

**Decision**: Docker Compose (backend + frontend + banco) para desenvolvimento; deploy simples em VPS Linux

**Rationale**:
- Escala atual (50 clientes, 1-5 operadores) não requer Kubernetes ou orquestração complexa.
- Docker Compose facilita onboarding de novos desenvolvedores e paridade com produção.
- Frontend servido como build estático via Nginx (mesmo container ou CDN simples).

---

## Mapa de Dependências Resolvidas

| Área | NEEDS CLARIFICATION | Resolução |
|------|--------------------|--------------------|
| Auth CRM UI | Como operadores autenticam? | Email + senha + JWT + convite |
| Integração Playbekids | Mecanismo de leitura? | Banco compartilhado, schema separado, usuário read-only |
| Handoff simultâneo | Conflito de dois operadores? | Lock por conversa, nome do operador ativo visível |
| Escala | Volume esperado? | ~50 clientes, ~50 mensagens/dia |
| Classificação | Sync ou async? | Async, gerada pelo Nino, CRM armazena resultado |
