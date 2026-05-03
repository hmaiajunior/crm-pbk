# Contract: Nino → CRM Webhook

**Endpoint CRM**: `POST /api/v1/webhooks/nino/mensagem`
**Auth**: Header `X-Nino-Key: <shared_secret>` (variável de ambiente `NINO_WEBHOOK_KEY`)
**Direção**: Nino envia → CRM recebe

## Descrição

O Nino envia um payload a cada mensagem processada (entrada ou saída) após classificação assíncrona de sentimento e tema. O CRM persiste a mensagem, atualiza o perfil do cliente e dispara eventos internos quando necessário.

O endpoint deve retornar em menos de 500ms. Todo processamento pesado (eventos, segmentação) é feito de forma assíncrona após o retorno da resposta HTTP.

---

## Request Payload

```json
{
  "mensagem_id": "uuid-gerado-pelo-nino",
  "telefone": "+5511999999999",
  "conteudo": "Olá, quero saber sobre o tênis rosa",
  "direcao": "entrada",
  "sentimento": "positivo",
  "tema": "produto",
  "timestamp": "2026-05-03T14:32:00Z"
}
```

### Campos

| Campo | Tipo | Obrigatório | Valores aceitos |
|-------|------|-------------|-----------------|
| mensagem_id | string (UUID) | Sim | UUID v4 gerado pelo Nino (idempotência) |
| telefone | string | Sim | Formato E.164 (+55DDNNNNNNNNN) |
| conteudo | string | Sim | Conteúdo da mensagem |
| direcao | string | Sim | `entrada` \| `saida` |
| sentimento | string | Não | `positivo` \| `neutro` \| `negativo` \| `null` |
| tema | string | Não | `preco` \| `produto` \| `atendimento` \| `qualidade` \| `outro` \| `null` |
| timestamp | string (ISO8601) | Sim | UTC |

**Nota**: `sentimento` e `tema` podem ser `null` para mensagens de saída (respostas do Nino) ou quando a classificação ainda não está disponível.

---

## Response

### 200 OK — Mensagem processada com sucesso

```json
{ "status": "ok", "mensagem_id": "uuid-gerado-pelo-nino" }
```

### 409 Conflict — Mensagem já processada (idempotência)

```json
{ "status": "duplicate", "mensagem_id": "uuid-gerado-pelo-nino" }
```

O Nino pode reenviar em caso de falha de rede. O CRM deve aceitar reenvios retornando `409` sem processar duplicatas.

### 401 Unauthorized — Chave inválida

```json
{ "error": "UNAUTHORIZED" }
```

### 422 Unprocessable Entity — Payload inválido

```json
{ "error": "VALIDATION_ERROR", "detail": [{ "field": "telefone", "msg": "Invalid E.164 format" }] }
```

---

## Comportamento do CRM após recebimento

1. Valida `X-Nino-Key`
2. Verifica idempotência por `mensagem_id`
3. Cria ou recupera `cliente` pelo `telefone` (cria se novo)
4. Cria ou recupera `conversa` ativa para o cliente
5. Persiste `mensagem` com classificação
6. Atualiza `cliente.ultima_interacao_em`
7. **Assincronamente** (após retornar 200):
   - Avalia se deve gerar eventos internos
   - Recalcula segmentos do cliente
   - Dispara agentes se necessário

---

## Contrato de Evolução

- O CRM deve aceitar campos desconhecidos (ignore extra fields) para compatibilidade futura.
- Versões futuras do contrato devem incrementar a URL: `/webhooks/nino/mensagem/v2`.
