# Insights de Casos Reais — Backlog de Ações para o CRM

Documento vivo. Cada caso novo do site PBK que revelar uma capacidade ausente
no CRM entra aqui como **anexo** + **ações priorizadas**. O objetivo é fechar
o ciclo entre "o que aconteceu no site" e "o que o CRM precisa fazer com isso".

Atualizar a tabela de prioridades no topo conforme os itens forem implementados.

---

## Tabela-mestra de ações (visão geral)

Prioridade segue a lógica: **maior valor por hora de implementação · primeiro**.
Multiplicador = (impacto receita) × (frequência do caso) ÷ (esforço).

| # | Ação | Prioridade | Caso que motiva | Status |
|---|---|---|---|---|
| A1 | Sync inicial de clientes a partir do `User` do PBK | 🔴 P0 | #1 Gisele | aberto |
| A2 | Normalização de telefone E.164 BR (`55 + DDD + número`) | 🔴 P0 | #1 Gisele | aberto |
| A3 | Evento `cliente_iniciou_checkout` (PBK Order `PENDING_PAYMENT`) | 🟠 P1 | #1 Gisele | aberto |
| A4 | Evento `cliente_abandonou_checkout` (PENDING_PAYMENT > 2h) | 🟠 P1 | #1 Gisele | aberto |
| A5 | Evento `cliente_cadastrou_no_site` (PBK `User.createdAt` hoje) | 🟠 P1 | #1 Gisele | aberto |
| A6 | Growth Agent: template de recuperação de checkout abandonado | 🟠 P1 | #1 Gisele | aberto |
| A7 | Painel "Pra falar HOJE" (operadora) com priorização automática | 🟡 P2 | #1 Gisele | aberto |
| A8 | Hot-Lead score baseado em sinais (login + endereço + telefone + sem pedido) | 🟡 P2 | #1 Gisele | aberto |
| A9 | Welcome flow (mensagem 5min após cadastro novo) | 🟡 P2 | #1 Gisele | aberto |
| A10 | Webhook PBK → CRM (em vez de polling do DB) | 🟢 P3 | #1 Gisele | aberto |

---

## Caso #1 — Gisele Sobral · 2026-06-06

### Dados brutos (PBK `public` schema)

```
User
  email:        gisele.sobral2018@gmail.com
  name:         Gisele Sobral
  phone:        11986696489          ← capturado pelo gate do AddressStep
  role:         RETAIL
  createdAt:    2026-06-06 11:32:36 BRT
  lastLoginAt:  2026-06-06 11:32:37 BRT (1s após cadastro)
  updatedAt:    2026-06-06 11:33:55 BRT (~80s depois — completou endereço)

Address (1)
  city:         Diadema / SP
  isDefault:    true

Order
  (nenhum)
```

### Pixel (mesma janela)

Eventos `AddToCart`, `InitiateCheckout` e `Purchase` da Gisele **não chegaram
ao Events Manager** dentro da janela observada (delay típico 30–60min após
o evento). Pendência: cruzar com a CAPI quando ela tiver `external_id`
hasheado pra confirmar profundidade do funil.

### O que isso revela

1. **A Gisele é o caso canônico de "lead pronto sem CRM agir"**. Ela:
   - Cadastrou, logou, completou Address Step (capturou telefone+CEP)
   - Não clicou em "Pagar"
   - Tem **TODOS os sinais** (intent + canal + perfil) pra um outbound
     manual converter — provavelmente em uma janela curta (24h de recência)
   - Sem o CRM rodando, esse intent **decai e morre**

2. **A integração com PBK precisa de granularidade que o spec atual não
   cobre.** O spec fala em ler `ultima_compra_em` do PBK, mas não em:
   - Detectar cadastro recente (`User.createdAt`)
   - Detectar último login (`User.lastLoginAt`)
   - Detectar carrinho/checkout iniciado (`Order` em `PENDING_PAYMENT`)
   - Detectar mudanças de estado (PROCESSING → SHIPPED → DELIVERED)

   Esses são **sinais comportamentais distintos de "compra confirmada"**, e
   formam a base do scoring de Hot Lead.

3. **Telefone PBK ↔ CRM tem formato diferente.**
   - PBK salva: `11986696489` (11 dígitos, sem código de país)
   - CRM exige: `+5511986696489` (E.164) como chave única (`crm.cliente.telefone`)
   - Sem helper de normalização, **o match falha**: o CRM cria duplicado
     ou ignora a Gisele quando o WhatsApp dela chegar via Nino.

4. **O telefone agora é obrigatório no PBK** (commit `619e847` de 04/06).
   A partir dessa data, todo novo cliente que fechar o `AddressStep` tem
   telefone garantido — o CRM pode confiar nesse sinal pra **outbound
   automatizado** (sob aprovação humana, conforme FR-018).

5. **Janela 24h do WhatsApp ainda não foi aberta com a Gisele.** Como
   o cliente nunca mandou DM, qualquer outbound do Growth Agent precisa
   usar **template aprovado** (FR-019). Implica:
   - Cadastrar um template `recuperacao_checkout_v1` no Meta antes
   - Esperar a Meta aprovar (24-48h)
   - Documentar quais variáveis o template aceita (`{{nome}}`, `{{produto}}`)

---

## Ações priorizadas (detalhe)

### 🔴 P0 — Fundação da integração com PBK

#### A1. Sync inicial de clientes a partir do `User` do PBK

**Por quê**: Sem isso, o CRM nem sabe que a Gisele existe.

**O quê**: Job de bootstrap (ou contínuo) que lê `public.User` do PBK e
materializa em `crm.cliente`. Mantém em sincronia o `nome`, `email` (campo
novo? hoje o CRM identifica só por `telefone`) e `ultima_compra_em` (derivado
de `Order` confirmado).

**Onde mexer**:
- `backend/src/integrations/playbekids_sync.py` (novo)
- Job agendado: a cada 5min OU webhook (ver A10)
- Decidir: `crm.cliente` ganha `email` como índice secundário? ou
  mantém `telefone` como única chave e ignora clientes sem telefone?

**Decisão pendente** (D1 abaixo).

#### A2. Normalização de telefone E.164 BR

**Por quê**: Sem isso, identidade entre PBK e CRM quebra.

**O quê**: Helper `backend/src/utils/phone.py`:
```python
def to_e164_br(digits: str) -> str | None:
    """11986696489 → +5511986696489; rejeita o que não bate com BR mobile/fixo."""
```

Espelhar a validação do PBK (`src/lib/phone.ts:isValidBrazilianPhone`):
DDD 11..99 + 10 ou 11 dígitos + leading 9 em mobile.

**Onde mexer**:
- `backend/src/utils/phone.py`
- Aplicar em `crm.cliente.telefone` (validação no upsert)
- Aplicar quando Nino entregar telefone do remetente WhatsApp (já em E.164)
- Aplicar no sync do PBK (A1) ao copiar `User.phone`

### 🟠 P1 — Captura de intent do site

#### A3. Evento `cliente_iniciou_checkout`

**Trigger**: criação de `Order` no PBK com `status = PENDING_PAYMENT`.

**Dados no payload**:
```json
{
  "cliente_telefone": "+5511986696489",
  "order_id": "cmp...",
  "total": 128.73,
  "payment_method": "credit_card",
  "items": [{"product_id": "...", "name": "TSHIRT DO BRASIL", "qty": 2}],
  "criado_em": "2026-06-06T14:32:00Z"
}
```

**Ação no Growth Agent**: ainda nenhuma (aguarda confirmação de pagamento OU timeout — A4).

**Por que registrar mesmo sem ação imediata**: histórico/score do cliente,
auditoria futura, base pra "abandonou checkout 3×" como tag.

#### A4. Evento `cliente_abandonou_checkout`

**Trigger**: `Order` está em `PENDING_PAYMENT` há mais de 2h E não foi
cancelado pelo cron de PBK.

**Implementação**:
- Job a cada 15min que varre `public.Order WHERE status='PENDING_PAYMENT'
  AND createdAt < now() - INTERVAL '2 hours'`
- Para cada hit, emite o evento (idempotente — não emite duas vezes para
  o mesmo `order_id`).

**Ação no Growth Agent**: gera sugestão de mensagem usando template
`recuperacao_checkout_v1` (com fallback se janela 24h aberta).

#### A5. Evento `cliente_cadastrou_no_site`

**Trigger**: `User.createdAt` dentro de 30min e ainda sem `Order` confirmado.

**Por que importa**: a Gisele tinha 80s de vida no site quando cadastrou
o endereço. Janela de calor real.

**Ação no Growth Agent**: **opcional** — pode ser intrusivo. Default: só
registra no perfil; só dispara mensagem se for combinado com A4 (cadastrou
+ tentou checkout).

#### A6. Growth Agent: template `recuperacao_checkout_v1`

**Por quê**: Sem template aprovado pela Meta, FR-019 nos impede de mandar
mensagem fora da janela 24h. Cliente recém-cadastrado **nunca** está na
janela 24h (ele nunca mandou DM antes).

**O quê**: criar e submeter à Meta um template como:
> "Oi {{1}}! 👋 Vimos que você tava de olho na PlayBeKids hoje. Posso te
> ajudar com alguma dúvida sobre tamanho, frete ou desconto? — Equipe PBK"

**Onde**:
- `backend/src/agents/growth/templates/` registrar versão local
- Cadastrar no Meta Business Manager → Templates de mensagem
- Documentar `template_id` em variável de ambiente

### 🟡 P2 — Operação e priorização

#### A7. Painel "Pra falar HOJE"

Lista de clientes ordenados por **prioridade de outbound manual**, na home
do CRM. Default da operadora ao logar.

**Ranking** (rascunho):
```
score = (
  10  if `cliente_abandonou_checkout` em <24h
   8  if `cliente_iniciou_checkout` em <2h (ainda PENDING)
   6  if `cliente_cadastrou_no_site` em <24h sem pedido
   4  if `lastLoginAt` em <24h sem pedido
  -2  if já recebeu outbound manual nas últimas 48h
)
```

Mostra: foto/avatar, nome, telefone, valor do carrinho (se houver), CTA
"Abrir conversa" + "Marcar como contatado".

#### A8. Hot-Lead score automatizado

Atualizar `crm.cliente.classificacao` pra incluir `lead_quente` quando o
score de A7 ≥ 6 por mais de 1h. Move de volta pra `lead` quando o score
cai abaixo de 4.

Mexer em: tabela `cliente_segmento` + service `segmentacao` (já no spec).

#### A9. Welcome flow automático

Após `cliente_cadastrou_no_site` + 5min sem ação, Growth Agent sugere
mensagem leve de boas-vindas (template).

**Cuidado**: pra não saturar com mensagem automatizada, regra **dupla**:
- Limite: 1 welcome por cliente
- Bloqueia se o cliente já fechou pedido nesse meio tempo

### 🟢 P3 — Infra

#### A10. Webhook PBK → CRM (substituir polling)

Hoje a integração é "CRM lê DB do PBK" (acoplamento direto, conforme
clarification Q2 do spec). Funciona, mas:

- Latência depende do intervalo de polling (1–5min)
- Mudanças "rápidas" (cadastro + checkout em 80s) ficam fora de fase
- DB cresce, queries de varredura ficam mais caras

**Alternativa**: PBK ganha um endpoint `POST /api/crm/webhook` que dispara
eventos pra um endpoint do CRM com HMAC. Eventos:

```
user.created
user.address_added
user.phone_added
order.created   (PENDING_PAYMENT)
order.approved
order.cancelled
```

CRM responde 2xx ou retry com backoff. PBK guarda fila de envios falhos.

**Tradeoff**: dobra a complexidade da integração (precisa manter os 2
caminhos sincronizados ou migrar tudo de uma vez). Valor: real-time + menos
carga no DB. Endereçar quando o volume justificar (acima de ~30 eventos/min).

---

## Decisões pendentes

São perguntas cuja resposta muda a implementação. Precisam do operador
(você) antes de avançar com A1+.

### D1. Chave de identidade no `crm.cliente`

Hoje o spec diz `telefone UNIQUE`. Mas o caso da Gisele revela: muitos
sinais úteis do site chegam **antes** do telefone (cadastro, primeiro
login). E o telefone só vira obrigatório no checkout.

**Opções**:
- **A** Manter `telefone` como única chave. Cliente sem telefone é
  invisível pro CRM até abrir o checkout. **Perde** sinal de cadastro.
- **B** Adicionar `email` como segunda chave de identidade. `cliente` pode
  existir com `telefone = NULL`. **Ganha** sinal de cadastro, mas dobra
  complexidade de match e exige merge quando o cliente preencher telefone
  depois.
- **C** Usar `pbk_user_id` como chave externa. CRM virtualmente espelha o
  `User` do PBK. **Ganha** rastreabilidade clara, mas amarra os dois
  schemas.

Recomendação inicial: **B**. Match por email funciona pra welcome flow
e abandono de checkout sem telefone (rara hoje, mas possível antes da
captura obrigatória). Merge é exercício único quando o telefone aparece.

### D2. Quem é "fonte da verdade" para o nome

Cliente que faz DM no WhatsApp pode dar um apelido. Cliente que cadastra
no site dá o nome formal. Cliente que envia NF-e dá nome civil.

**Opção** simples: `crm.cliente.nome` = último valor recebido de qualquer
fonte; PBK ganha precedência sobre Nino quando há conflito (porque tem
validação CPF).

### D3. Privacidade de outbound automatizado

LGPD: ao puxar `User.phone` do PBK e mandar WhatsApp sem o cliente ter
iniciado contato, estamos usando dado pessoal sem consentimento explícito
pra fim de marketing. Sob a regra de "execução de contrato" (Art. 7º, V),
mensagem **operacional** sobre o pedido em andamento é OK; **promocional**
não.

**Implicação**:
- Template `recuperacao_checkout_v1` deve ser fraseado como "ajuda com o
  seu pedido" (operacional), não "última chance de desconto" (promocional)
- Welcome flow (A9) é cinza — recomenda-se pedir opt-in explícito no
  cadastro do PBK (checkbox marcada por padrão? não — LGPD diz que precisa
  ser opt-in ativo. Adicionar uma checkbox livre é seguro)

### D4. Threshold do "abandono"

Hoje proponho 2h pro A4. Mas pedido pode ficar PENDING_PAYMENT
legitimamente em alguns cenários:
- Pix esperando confirmação do banco (geralmente <5min, mas pode atrasar)
- Cartão com análise de risco (raro)
- Cron de cancelamento do PBK roda a cada X horas (verificar — pode
  estar matando o pedido **antes** do CRM agir)

Decidir após observar uns 10 pedidos PENDING e ver a distribuição de
tempo até a resolução natural.

---

## Próximos casos a documentar

Conforme aparecem, abrir nova seção `Caso #N` com mesma estrutura. Casos
que provavelmente entram no curto prazo:

- **Caso #2** Alcione (05/06) — cliente comprou direto, **fluxo feliz**.
  Insight: ela é candidata a `cliente_satisfeito` + pedido de review +
  cross-sell no WhatsApp em D+7.
- **Caso #3** Belisa (02/06) — comprou sem CPF/telefone preenchido na
  época. Insight: como o CRM lida com clientes pré-feature (legado)?
- **Caso #4** Janaina (29/05) — esposa do dono, perfil "interno".
  Insight: precisa flag pra excluir contas internas das métricas e
  segmentos.
