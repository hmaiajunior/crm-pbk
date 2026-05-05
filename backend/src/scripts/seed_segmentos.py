"""Seed default segments.

Usage:
    cd backend/
    python -m src.scripts.seed_segmentos
"""
import asyncio
from sqlalchemy import select
from src.database import AsyncSessionLocal
from src.models.segmento import Segmento

SEGMENTOS = [
    {"nome": "Clientes Novos", "descricao": "Leads criados nos últimos 7 dias"},
    {"nome": "Clientes Ativos", "descricao": "Interação nos últimos 30 dias"},
    {"nome": "Clientes Inativos", "descricao": "Sem interação há mais de 30 dias"},
    {"nome": "Engajados sem Compra", "descricao": "Opt-in ativo, sem compra registrada"},
    {"nome": "Sentimento Negativo Recorrente", "descricao": "3 ou mais mensagens com sentimento negativo"},
    {"nome": "Lead Quente", "descricao": "Lead com opt-in ativo e alto engajamento"},
]


async def seed() -> None:
    async with AsyncSessionLocal() as db:
        for data in SEGMENTOS:
            existing = await db.execute(select(Segmento).where(Segmento.nome == data["nome"]))
            if existing.scalar_one_or_none():
                print(f"[skip] {data['nome']}")
                continue
            db.add(Segmento(nome=data["nome"], descricao=data["descricao"]))
            print(f"[ok]   {data['nome']}")
        await db.commit()


if __name__ == "__main__":
    asyncio.run(seed())
