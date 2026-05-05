import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.models.operador import Operador
from src.services import conversa_service
from src.services.auth_service import get_current_operador

router = APIRouter(prefix="/conversas", tags=["conversas"])


@router.post("/{conversa_id}/handoff")
async def assume_conversa(
    conversa_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    operador: Annotated[Operador, Depends(get_current_operador)],
):
    try:
        conversa = await conversa_service.start_handoff(db, conversa_id, operador)
        return {"status": conversa.status, "operador_id": str(conversa.operador_id)}
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.delete("/{conversa_id}/handoff")
async def release_conversa(
    conversa_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    operador: Annotated[Operador, Depends(get_current_operador)],
):
    try:
        conversa = await conversa_service.end_handoff(db, conversa_id, operador)
        return {"status": conversa.status}
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
