# API Contract: CRM Backend REST API

**Base URL**: `/api/v1`
**Auth**: Bearer JWT em todos os endpoints (exceto `/auth/login` e `/auth/register`)
**Content-Type**: `application/json`

---

## Auth

### POST `/auth/login`
Autentica operador e retorna JWT.

**Request**:
```json
{ "email": "operador@playbekids.com", "senha": "string" }
```

**Response 200**:
```json
{
  "token": "eyJ...",
  "operador": { "id": "uuid", "nome": "string", "email": "string" }
}
```

**Errors**: `401 Credenciais inválidas`

---

### POST `/auth/invite`
Admin envia convite para novo operador.

**Request**: `{ "email": "novo@playbekids.com", "nome": "string" }`
**Response 201**: `{ "message": "Convite enviado" }`

---

### POST `/auth/register`
Completa o cadastro a partir do token de convite.

**Request**: `{ "token": "string", "senha": "string" }`
**Response 201**: `{ "operador": { "id": "uuid", "nome": "string", "email": "string" } }`
**Errors**: `400 Token inválido ou expirado`

---

## Clientes

### GET `/clientes`
Lista paginada de clientes com filtro opcional por segmento.

**Query params**: `segmento_id`, `classificacao`, `page` (default 1), `limit` (default 20)

**Response 200**:
```json
{
  "total": 50,
  "page": 1,
  "items": [
    {
      "id": "uuid",
      "telefone": "+5511999999999",
      "nome": "string | null",
      "classificacao": "lead | cliente | cliente_recorrente | inativo",
      "ultima_interacao_em": "ISO8601",
      "segmentos": ["Clientes Ativos"]
    }
  ]
}
```

---

### GET `/clientes/{id}`
Perfil completo do cliente com timeline.

**Response 200**:
```json
{
  "id": "uuid",
  "telefone": "string",
  "nome": "string | null",
  "classificacao": "string",
  "opt_in": true,
  "primeira_interacao_em": "ISO8601",
  "ultima_interacao_em": "ISO8601",
  "ultima_compra_em": "ISO8601 | null",
  "segmentos": ["string"],
  "timeline": [
    {
      "tipo": "mensagem | compra | evento",
      "timestamp": "ISO8601",
      "dados": {}
    }
  ]
}
```

---

## Conversas

### GET `/conversas`
Lista conversas com filtro por status.

**Query params**: `status` (ativa | em_handoff | encerrada), `page`, `limit`

**Response 200**:
```json
{
  "total": 5,
  "items": [
    {
      "id": "uuid",
      "cliente": { "id": "uuid", "nome": "string", "telefone": "string" },
      "status": "ativa",
      "operador_ativo": null,
      "ultima_mensagem_em": "ISO8601"
    }
  ]
}
```

---

### POST `/conversas/{id}/handoff`
Operador assume a conversa. Falha se outro operador já estiver em handoff.

**Response 200**: `{ "status": "em_handoff", "operador_id": "uuid" }`
**Errors**:
- `409 Conversa já em handoff por {nome do operador}`
- `404 Conversa não encontrada`

---

### DELETE `/conversas/{id}/handoff`
Operador libera a conversa (retorna ao Nino).

**Response 200**: `{ "status": "ativa" }`
**Errors**: `403 Você não é o operador ativo desta conversa`

---

## Campanhas

### GET `/campanhas`
Lista campanhas com filtro por status.

**Query params**: `status`, `page`, `limit`

**Response 200**:
```json
{
  "total": 3,
  "items": [
    {
      "id": "uuid",
      "status": "aguardando_aprovacao",
      "copy": "string",
      "segmento": { "id": "uuid", "nome": "string" },
      "orcamento_sugerido": 150.00,
      "criado_em": "ISO8601"
    }
  ]
}
```

---

### POST `/campanhas/gerar`
Solicita ao Ads Agent a geração de uma nova campanha.

**Request**: `{ "segmento_id": "uuid", "instrucoes_adicionais": "string | null" }`
**Response 202**: `{ "campanha_id": "uuid", "status": "rascunho" }`

---

### PATCH `/campanhas/{id}`
Edita campos da campanha (apenas em status `rascunho` ou `aguardando_aprovacao`).

**Request**: `{ "copy": "string", "orcamento_sugerido": 200.00 }`
**Response 200**: campanha atualizada
**Errors**: `409 Campanha não pode ser editada no status atual`

---

### POST `/campanhas/{id}/aprovar`
Aprova campanha para publicação.

**Response 200**: `{ "status": "aprovada", "aprovada_por": "uuid", "aprovada_em": "ISO8601" }`
**Errors**: `409 Campanha não está aguardando aprovação`

---

### POST `/campanhas/{id}/rejeitar`
Rejeita campanha.

**Request**: `{ "motivo": "string | null" }`
**Response 200**: `{ "status": "rejeitada" }`

---

## Ações de Agentes

### GET `/acoes`
Lista ações sugeridas pelos agentes aguardando aprovação.

**Query params**: `status` (default: sugerida), `agente`, `page`, `limit`

**Response 200**:
```json
{
  "items": [
    {
      "id": "uuid",
      "tipo": "convite_vip | oferta | follow_up",
      "agente": "growth_agent",
      "cliente": { "id": "uuid", "nome": "string" },
      "conteudo_sugerido": "string",
      "status": "sugerida",
      "criado_em": "ISO8601"
    }
  ]
}
```

---

### POST `/acoes/{id}/aprovar`
Aprova e executa ação do agente.

**Response 200**: `{ "status": "executada", "executada_em": "ISO8601" }`
**Errors**: `409 Ação não está no status sugerida`

---

### POST `/acoes/{id}/rejeitar`
Rejeita ação sem executar.

**Response 200**: `{ "status": "rejeitada" }`

---

## Métricas

### GET `/metricas/dashboard`
Métricas gerais para o painel principal.

**Response 200**:
```json
{
  "clientes_total": 50,
  "clientes_novos_7d": 3,
  "clientes_ativos": 35,
  "clientes_inativos": 12,
  "atendimentos_hoje": 8,
  "acoes_pendentes": 2,
  "campanhas_pendentes": 1
}
```

---

## Segmentos

### GET `/segmentos`
Lista todos os segmentos ativos.

**Response 200**: `{ "items": [{ "id": "uuid", "nome": "string", "total_clientes": 15 }] }`

---

## Erros Padrão

| Status | Código | Descrição |
|--------|--------|-----------|
| 400 | BAD_REQUEST | Dados inválidos na requisição |
| 401 | UNAUTHORIZED | Token ausente ou expirado |
| 403 | FORBIDDEN | Sem permissão para esta ação |
| 404 | NOT_FOUND | Recurso não encontrado |
| 409 | CONFLICT | Estado inválido para a operação |
| 500 | INTERNAL_ERROR | Erro interno do servidor |
