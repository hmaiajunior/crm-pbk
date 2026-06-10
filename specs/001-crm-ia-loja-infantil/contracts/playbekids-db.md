# Contract: Leitura do Banco Playbekids

**Tipo**: Leitura direta via SQLAlchemy (usuário PostgreSQL read-only `crm_reader`)
**Direção**: CRM lê → Playbekids (sem escrita)
**Schema fonte**: `public` (Playbekids — base **Supabase/Prisma**, identificadores camelCase entre aspas)
**Schema destino**: `crm` (CRM)

> **Atualizado em 2026-06-10:** o banco real é um Supabase (Prisma). As tabelas reais
> são `public."User"`, `public."Order"` e `public."AbandonedCart"` — **não** `public.pedidos`.
> Compra confirmada = `Order."paymentStatus" = 'APPROVED'`. O `crm_reader` precisa de
> `BYPASSRLS` (RLS habilitado nessas tabelas) — rodar no Supabase: `ALTER ROLE crm_reader BYPASSRLS;`.

## Tabelas reais consumidas

| Tabela | Colunas usadas | Uso no CRM |
|--------|----------------|------------|
| `public."User"` | `id`, `name`, `email`, `phone` (nullable), `role` (RETAIL/WHOLESALE/ADMIN), `"createdAt"` | Cadastro de atacado (`role='WHOLESALE'`) → cenário `cadastro_sem_pedido` |
| `public."Order"` | `id`, `"userId"`, `"paymentStatus"` (='APPROVED'), `"createdAt"` | Compra confirmada (`ultima_compra_em`, classificação) |
| `public."AbandonedCart"` | `id`, `"userId"`, `subtotal`, `"createdAt"` | Checkout abandonado → cenário `checkout_abandonado` |

> As colunas de data são `timestamp without time zone` (UTC naive) — a camada
> `playbekids_db.py` converte (`_naive_utc` ao filtrar, `_aware_utc` ao retornar).

---

## Histórico (contrato original — `public.pedidos`)
> O contrato abaixo assumia uma tabela `public.pedidos` que **não existe** no banco real.
> Mantido apenas como registro histórico.

## Descrição

O CRM acessa o banco de dados do Playbekids com um usuário PostgreSQL dedicado, com permissão `SELECT` apenas nas tabelas necessárias. Nenhuma escrita é permitida por esse usuário.

---

## Tabela: `public.pedidos`

Tabela principal de pedidos do e-commerce Playbekids que o CRM consome.

### Campos necessários

| Campo Playbekids | Tipo esperado | Uso no CRM |
|-----------------|---------------|------------|
| `telefone_cliente` | VARCHAR | Match com `crm.cliente.telefone` |
| `status` | VARCHAR | Filtro: apenas `'confirmado'` |
| `criado_em` | TIMESTAMP | `crm.cliente.ultima_compra_em` |

> **AÇÃO ANTES DA IMPLEMENTAÇÃO**: Validar nomes exatos das colunas com o time do Playbekids. Se os nomes divergirem, atualizar este contrato e o arquivo `backend/src/integrations/playbekids_db.py`.

---

## Query Principal

```sql
SELECT
    telefone_cliente,
    MAX(criado_em)  AS ultima_compra_em,
    COUNT(*)        AS total_compras
FROM public.pedidos
WHERE status = 'confirmado'
GROUP BY telefone_cliente;
```

**Frequência de execução**: A cada nova interação de cliente que afete a classificação, ou via job periódico a cada 30 minutos.

---

## Query de Cliente Específico

```sql
SELECT
    MAX(criado_em)  AS ultima_compra_em,
    COUNT(*)        AS total_compras
FROM public.pedidos
WHERE status    = 'confirmado'
  AND telefone_cliente = :telefone;
```

---

## Configuração do Usuário PostgreSQL

```sql
-- Executado uma única vez pelo DBA do Playbekids
CREATE USER crm_reader WITH PASSWORD '<senha>';
GRANT CONNECT ON DATABASE playbekids TO crm_reader;
GRANT USAGE ON SCHEMA public TO crm_reader;
GRANT SELECT ON public.pedidos TO crm_reader;
```

O CRM usa a connection string via variável de ambiente `PLAYBEKIDS_DB_URL`.

---

## Restrições e Garantias

- O usuário `crm_reader` NUNCA tem `INSERT`, `UPDATE` ou `DELETE` no schema do Playbekids.
- O CRM não deve assumir que as tabelas do Playbekids têm um schema estável — mudanças de schema devem ser comunicadas antes de releases.
- Se a query falhar (ex: tabela renomeada), o CRM deve continuar operando sem `ultima_compra_em` (campo nullable) e logar o erro para investigação.

---

## Evolução

Se o Playbekids mudar o schema, o contrato deve ser atualizado aqui antes de alterar o código. A query de leitura está centralizada em `backend/src/integrations/playbekids_db.py` para facilitar mudanças.
