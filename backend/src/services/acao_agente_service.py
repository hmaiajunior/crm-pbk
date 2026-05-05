import uuid
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.acao_agente import AcaoAgente, StatusAcao
from src.models.operador import Operador


async def get_pending(db: AsyncSession) -> list[AcaoAgente]:
    result = await db.execute(
        select(AcaoAgente)
        .where(AcaoAgente.status == StatusAcao.sugerida)
        .order_by(AcaoAgente.criado_em.desc())
    )
    return list(result.scalars().all())


async def approve(db: AsyncSession, acao_id: uuid.UUID, operador: Operador) -> AcaoAgente:
    result = await db.execute(select(AcaoAgente).where(AcaoAgente.id == acao_id))
    acao = result.scalar_one_or_none()
    if not acao:
        raise KeyError(f"Ação {acao_id} não encontrada")
    if acao.status != StatusAcao.sugerida:
        raise ValueError(f"Ação não está pendente (status={acao.status})")
    acao.status = StatusAcao.executada
    acao.aprovada_por = operador.id
    acao.executada_em = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(acao)
    return acao


async def reject(db: AsyncSession, acao_id: uuid.UUID, operador: Operador) -> AcaoAgente:
    result = await db.execute(select(AcaoAgente).where(AcaoAgente.id == acao_id))
    acao = result.scalar_one_or_none()
    if not acao:
        raise KeyError(f"Ação {acao_id} não encontrada")
    if acao.status != StatusAcao.sugerida:
        raise ValueError(f"Ação não está pendente (status={acao.status})")
    acao.status = StatusAcao.rejeitada
    await db.commit()
    await db.refresh(acao)
    return acao
