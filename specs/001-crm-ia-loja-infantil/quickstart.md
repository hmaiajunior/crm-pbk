# Quickstart: CRM Inteligente — Loja Infantil

**Branch**: `001-crm-ia-loja-infantil`
**Objetivo**: Subir o ambiente de desenvolvimento local e validar a integração com Nino e Playbekids.

---

## Pré-requisitos

- Python 3.11+
- Node.js 20+
- PostgreSQL 15 rodando (mesmo servidor que o Playbekids)
- Acesso à variável `PLAYBEKIDS_DB_URL` (solicitar ao time Playbekids)
- Variável `NINO_WEBHOOK_KEY` (compartilhada com o time do Nino)

---

## 1. Backend (FastAPI)

```bash
# Clonar e entrar no diretório
cd backend/

# Criar ambiente virtual
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com:
#   DATABASE_URL=postgresql+asyncpg://crm_user:senha@localhost/playbekids_db
#   PLAYBEKIDS_DB_URL=postgresql+asyncpg://crm_reader:senha@localhost/playbekids_db
#   NINO_WEBHOOK_KEY=<chave compartilhada com Nino>
#   JWT_SECRET=<gerar com: python -c "import secrets; print(secrets.token_hex(32))">

# Criar schema CRM e rodar migrações
alembic upgrade head

# Inicializar segmentos padrão (seed)
python -m src.scripts.seed_segmentos

# Iniciar servidor
uvicorn src.main:app --reload --port 8000
```

**Verificar**: `http://localhost:8000/docs` — OpenAPI UI deve carregar.

---

## 2. Frontend (React)

```bash
cd frontend/

# Instalar dependências
npm install

# Configurar
cp .env.example .env.local
# Editar:
#   VITE_API_URL=http://localhost:8000/api/v1

# Iniciar servidor de desenvolvimento
npm run dev
```

**Verificar**: `http://localhost:5173` — Tela de login deve aparecer.

---

## 3. Criar primeiro operador

```bash
# Via script (primeiro admin — sem convite necessário)
cd backend/
python -m src.scripts.create_admin --email admin@playbekids.com --nome "Admin"
# Senha será solicitada interativamente
```

---

## 4. Testar webhook do Nino (mock)

```bash
curl -X POST http://localhost:8000/api/v1/webhooks/nino/mensagem \
  -H "Content-Type: application/json" \
  -H "X-Nino-Key: <NINO_WEBHOOK_KEY>" \
  -d '{
    "mensagem_id": "550e8400-e29b-41d4-a716-446655440000",
    "telefone": "+5511999990001",
    "conteudo": "Olá, quero saber sobre tênis rosa",
    "direcao": "entrada",
    "sentimento": "positivo",
    "tema": "produto",
    "timestamp": "2026-05-03T14:00:00Z"
  }'
```

**Esperado**: `{"status": "ok", "mensagem_id": "550e8400-..."}`

Verificar no painel `http://localhost:5173/clientes` que o cliente `+5511999990001` aparece na lista.

---

## 5. Testar leitura do Playbekids

```bash
cd backend/
python -m src.scripts.test_playbekids_connection
```

**Esperado**: Lista de clientes com `ultima_compra_em` ou mensagem `"Nenhum pedido encontrado — OK"`.

---

## 6. Validação Golden Path

1. **Login**: acessar `http://localhost:5173`, fazer login com o admin criado.
2. **Dashboard**: verificar se métricas carregam (podem ser zero no início).
3. **Webhook**: enviar mock acima, verificar cliente na lista.
4. **Filtro de segmento**: clicar em "Clientes Novos" — cliente recém-criado deve aparecer.
5. **Perfil do cliente**: abrir perfil, verificar timeline com a mensagem.
6. **Handoff**: clicar "Assumir conversa" → confirmar → status muda para "em handoff".

---

## Troubleshooting

| Problema | Causa provável | Solução |
|----------|---------------|---------|
| `asyncpg.exceptions.InvalidPasswordError` | Credenciais DB erradas | Verificar `DATABASE_URL` no `.env` |
| `401` no webhook | `NINO_WEBHOOK_KEY` diferente | Sincronizar chave com time do Nino |
| Segmentos não aparecendo | Seed não foi executado | Rodar `python -m src.scripts.seed_segmentos` |
| Frontend não conecta na API | `VITE_API_URL` errado | Verificar `.env.local` |
