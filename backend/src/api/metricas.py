from datetime import datetime, timedelta, timezone
from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.models.acao_agente import AcaoAgente, StatusAcao
from src.models.campanha import Campanha, StatusCampanha
from src.models.cliente import Cliente
from src.models.conversa import Conversa
from src.services.auth_service import get_current_operador

router = APIRouter(prefix="/metricas", tags=["metricas"])


@router.get("/dashboard")
async def dashboard(
    db: Annotated[AsyncSession, Depends(get_db)],
    _=Depends(get_current_operador),
):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    cutoff_7d = now - timedelta(days=7)
    cutoff_30d = now - timedelta(days=30)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    total = (await db.execute(select(func.count(Cliente.id)))).scalar_one()

    novos_7d = (
        await db.execute(
            select(func.count(Cliente.id)).where(Cliente.primeira_interacao_em >= cutoff_7d)
        )
    ).scalar_one()

    ativos = (
        await db.execute(
            select(func.count(Cliente.id)).where(Cliente.ultima_interacao_em >= cutoff_30d)
        )
    ).scalar_one()

    inativos = (
        await db.execute(
            select(func.count(Cliente.id)).where(Cliente.ultima_interacao_em < cutoff_30d)
        )
    ).scalar_one()

    atendimentos_hoje = (
        await db.execute(
            select(func.count(Conversa.id)).where(Conversa.iniciada_em >= today_start)
        )
    ).scalar_one()

    acoes_pendentes = (
        await db.execute(
            select(func.count(AcaoAgente.id)).where(AcaoAgente.status == StatusAcao.sugerida)
        )
    ).scalar_one()

    campanhas_pendentes = (
        await db.execute(
            select(func.count(Campanha.id)).where(Campanha.status == StatusCampanha.aguardando_aprovacao)
        )
    ).scalar_one()

    return {
        "clientes_total": total,
        "clientes_novos_7d": novos_7d,
        "clientes_ativos": ativos,
        "clientes_inativos": inativos,
        "atendimentos_hoje": atendimentos_hoje,
        "acoes_pendentes": acoes_pendentes,
        "campanhas_pendentes": campanhas_pendentes,
    }
