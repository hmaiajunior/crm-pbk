# Data Model: CRM Inteligente com Agentes de IA — Loja Infantil

**Branch**: `001-crm-ia-loja-infantil` | **Date**: 2026-05-03
**Schema PostgreSQL**: `crm` (isolado do schema `public` do Playbekids)

## Diagrama de Entidades

```
operador ──────────────────────────────────────────────────────────┐
    │ aprova                                                         │
    ▼                                                                │
campanha ◄── gerada por ── ads_agent                               │
    │                                                                │
    │                                                            aprova
    ▼                                                                │
segmento ◄── recalculado por ── segmentacao_service           acao_agente
    │                                               ◄── gerada por ── growth_agent
    │ agrupa                                             │
    ▼                                                    │
cliente ◄──────────────────────────────────────────────┘
    │ 1:N
    ▼
conversa ──► operador (quando em handoff)
    │ 1:N
    ▼
mensagem ──► classificacao (sentimento + tema, via Nino async)
    │
    ▼ gera
evento ──► aciona ──► growth_agent / ads_agent
```

---

## Entidades

### `crm.operador`

Usuários com acesso ao painel administrativo.

| Campo | Tipo | Constraints | Descrição |
|-------|------|-------------|-----------|
| id | UUID | PK, DEFAULT gen_random_uuid() | |
| email | VARCHAR(255) | UNIQUE NOT NULL | Usado para login |
| nome | VARCHAR(255) | NOT NULL | Nome exibido na UI |
| senha_hash | VARCHAR(255) | NOT NULL | bcrypt hash |
| ativo | BOOLEAN | DEFAULT true | false = conta desativada |
| criado_em | TIMESTAMPTZ | DEFAULT now() | |

**State transitions**: `ativo=true` → `ativo=false` (desativação manual pelo admin)

---

### `crm.cliente`

Registro central de cada cliente identificado pelo número de WhatsApp.

| Campo | Tipo | Constraints | Descrição |
|-------|------|-------------|-----------|
| id | UUID | PK, DEFAULT gen_random_uuid() | |
| telefone | VARCHAR(20) | UNIQUE NOT NULL | Número WhatsApp (E.164: +5511999999999) |
| nome | VARCHAR(255) | NULLABLE | Pode ser desconhecido inicialmente |
| classificacao | ENUM | NOT NULL | `lead`, `cliente`, `cliente_recorrente`, `inativo` |
| opt_in | BOOLEAN | DEFAULT true | Consentimento para mensagens |
| opt_in_registrado_em | TIMESTAMPTZ | NOT NULL | Registro formal do consentimento (LGPD) |
| primeira_interacao_em | TIMESTAMPTZ | NOT NULL | Preenchido no cadastro automático |
| ultima_interacao_em | TIMESTAMPTZ | NOT NULL | Atualizado após cada mensagem |
| ultima_compra_em | TIMESTAMPTZ | NULLABLE | Lido do Playbekids DB |
| criado_em | TIMESTAMPTZ | DEFAULT now() | |

**Regras de classificação automática**:
- `lead`: sem compras registradas
- `cliente`: 1 compra confirmada
- `cliente_recorrente`: 2+ compras confirmadas
- `inativo`: sem interação ou compra há mais de 30 dias (sobrescreve as demais)

**Índices**: `telefone` (UNIQUE), `classificacao`, `ultima_interacao_em`

---

### `crm.conversa`

Agrupamento de mensagens de um cliente em uma sessão de atendimento.

| Campo | Tipo | Constraints | Descrição |
|-------|------|-------------|-----------|
| id | UUID | PK, DEFAULT gen_random_uuid() | |
| cliente_id | UUID | FK → crm.cliente NOT NULL | |
| canal | ENUM | DEFAULT 'whatsapp' | `whatsapp` (único canal v1) |
| status | ENUM | NOT NULL | `ativa`, `em_handoff`, `encerrada` |
| operador_id | UUID | FK → crm.operador NULLABLE | Preenchido durante handoff |
| handoff_iniciado_em | TIMESTAMPTZ | NULLABLE | Timestamp do início do handoff |
| iniciada_em | TIMESTAMPTZ | DEFAULT now() | |
| encerrada_em | TIMESTAMPTZ | NULLABLE | |

**State transitions**:
- `ativa` → `em_handoff` (operador aciona handoff, `operador_id` preenchido)
- `em_handoff` → `ativa` (operador libera conversa, `operador_id` nullificado)
- `ativa` | `em_handoff` → `encerrada`

**Regra de lock**: apenas uma conversa por cliente pode ter `status = 'em_handoff'` com o mesmo `operador_id` ao mesmo tempo. Um segundo operador NÃO pode assumir uma conversa já em handoff.

**Índices**: `cliente_id`, `status`, `operador_id`

---

### `crm.mensagem`

Cada mensagem trocada em uma conversa. Classificação preenchida assincronamente pelo Nino.

| Campo | Tipo | Constraints | Descrição |
|-------|------|-------------|-----------|
| id | UUID | PK, DEFAULT gen_random_uuid() | ID do Nino (idempotente) |
| conversa_id | UUID | FK → crm.conversa NOT NULL | |
| conteudo | TEXT | NOT NULL | |
| direcao | ENUM | NOT NULL | `entrada` (cliente), `saida` (Nino/operador) |
| sentimento | ENUM | NULLABLE | `positivo`, `neutro`, `negativo` |
| tema | ENUM | NULLABLE | `preco`, `produto`, `atendimento`, `qualidade`, `outro` |
| classificado_em | TIMESTAMPTZ | NULLABLE | Preenchido quando Nino envia resultado |
| enviada_em | TIMESTAMPTZ | NOT NULL | |

**Índices**: `conversa_id`, `enviada_em`, `sentimento`

---

### `crm.segmento`

Segmentos pré-definidos com critérios de inclusão automática.

| Campo | Tipo | Constraints | Descrição |
|-------|------|-------------|-----------|
| id | UUID | PK, DEFAULT gen_random_uuid() | |
| nome | VARCHAR(100) | UNIQUE NOT NULL | Ex: "Clientes Inativos" |
| descricao | TEXT | | |
| criterios | JSONB | NOT NULL | Regras de avaliação serializadas |
| ativo | BOOLEAN | DEFAULT true | |

**Segmentos iniciais (seed)**:

| Nome | Critério principal |
|------|-------------------|
| Clientes Novos | `primeira_interacao_em` < 7 dias |
| Clientes Ativos | `ultima_interacao_em` < 30 dias E classificacao != 'inativo' |
| Clientes Inativos | `ultima_interacao_em` > 30 dias OU `ultima_compra_em` > 30 dias |
| Engajados sem Compra | classificacao = 'lead' E múltiplas interações |
| Sentimento Negativo Recorrente | 2+ mensagens com sentimento = 'negativo' em 30 dias |
| Lead Quente | classificacao = 'lead' E sentimento predominante = 'positivo' E 3+ interações |

---

### `crm.cliente_segmento`

Tabela de associação N:N entre clientes e segmentos.

| Campo | Tipo | Constraints |
|-------|------|-------------|
| cliente_id | UUID | FK → crm.cliente |
| segmento_id | UUID | FK → crm.segmento |
| atribuido_em | TIMESTAMPTZ | DEFAULT now() |

**PK**: `(cliente_id, segmento_id)`

---

### `crm.evento`

Eventos de comportamento gerados pelo sistema para acionar agentes.

| Campo | Tipo | Constraints | Descrição |
|-------|------|-------------|-----------|
| id | UUID | PK, DEFAULT gen_random_uuid() | |
| tipo | ENUM | NOT NULL | `cliente_interessado`, `cliente_inativo`, `cliente_insatisfeito`, `cliente_pronto_compra` |
| cliente_id | UUID | FK → crm.cliente NOT NULL | |
| payload | JSONB | DEFAULT '{}' | Contexto adicional do evento |
| processado | BOOLEAN | DEFAULT false | true = agente já processou |
| criado_em | TIMESTAMPTZ | DEFAULT now() | |

**Índices**: `tipo`, `cliente_id`, `processado`

---

### `crm.campanha`

Campanhas de marketing geradas pelo Ads Agent e aprovadas por operadores.

| Campo | Tipo | Constraints | Descrição |
|-------|------|-------------|-----------|
| id | UUID | PK, DEFAULT gen_random_uuid() | |
| segmento_id | UUID | FK → crm.segmento NULLABLE | Público-alvo |
| copy | TEXT | NOT NULL | Texto da campanha |
| publico_alvo | JSONB | NOT NULL | Descrição do público + filtros |
| orcamento_sugerido | DECIMAL(10,2) | NULLABLE | Sugestão do Ads Agent |
| status | ENUM | NOT NULL | `rascunho`, `aguardando_aprovacao`, `aprovada`, `publicada`, `rejeitada` |
| gerada_por | VARCHAR(50) | DEFAULT 'ads_agent' | |
| aprovada_por | UUID | FK → crm.operador NULLABLE | |
| aprovada_em | TIMESTAMPTZ | NULLABLE | |
| criado_em | TIMESTAMPTZ | DEFAULT now() | |
| atualizado_em | TIMESTAMPTZ | DEFAULT now() | |

**State transitions**:
- `rascunho` → `aguardando_aprovacao` (operador solicita revisão)
- `aguardando_aprovacao` → `aprovada` (operador aprova)
- `aguardando_aprovacao` → `rejeitada` (operador rejeita)
- `aprovada` → `publicada` (publicação confirmada)
- `rascunho` | `aguardando_aprovacao` → `rascunho` (edição)

**Invariante**: Nenhuma campanha PODE ter status `publicada` sem `aprovada_por` preenchido.

---

### `crm.acao_agente`

Ações sugeridas pelos agentes (Growth/Ads) que aguardam aprovação do operador.

| Campo | Tipo | Constraints | Descrição |
|-------|------|-------------|-----------|
| id | UUID | PK, DEFAULT gen_random_uuid() | |
| tipo | ENUM | NOT NULL | `convite_vip`, `oferta`, `follow_up` |
| agente | ENUM | NOT NULL | `growth_agent`, `ads_agent` |
| cliente_id | UUID | FK → crm.cliente NOT NULL | |
| evento_id | UUID | FK → crm.evento NULLABLE | Evento que originou a ação |
| conteudo_sugerido | TEXT | NOT NULL | Mensagem/ação sugerida pelo agente |
| status | ENUM | NOT NULL | `sugerida`, `aprovada`, `executada`, `rejeitada` |
| aprovada_por | UUID | FK → crm.operador NULLABLE | |
| criado_em | TIMESTAMPTZ | DEFAULT now() | |
| executada_em | TIMESTAMPTZ | NULLABLE | |

---

## Leitura do Playbekids (Schema Externo)

O CRM acessa o schema `public` do Playbekids com usuário PostgreSQL **read-only**.

**Query principal** (última compra por cliente):

```sql
SELECT
    telefone_cliente,
    MAX(criado_em) AS ultima_compra_em,
    COUNT(*) AS total_compras
FROM public.pedidos
WHERE status = 'confirmado'
GROUP BY telefone_cliente;
```

**Notas**:
- Campos `telefone_cliente`, `status`, `criado_em` são os únicos necessários do Playbekids.
- Mapeamento exato das colunas deve ser validado com o time do Playbekids antes da implementação.
- O CRM sincroniza `ultima_compra_em` e `total_compras` no perfil do cliente a cada interação ou via job periódico (a definir na fase de tasks).
