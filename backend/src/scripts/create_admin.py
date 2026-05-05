"""Create the first admin operator without requiring an invite token.

Usage:
    cd backend/
    python -m src.scripts.create_admin --email admin@playbekids.com --nome "Admin"
"""
import asyncio
import argparse
import getpass
from sqlalchemy import select
from src.database import AsyncSessionLocal
from src.models.operador import Operador
from src.services.auth_service import hash_password


async def create_admin(email: str, nome: str, senha: str) -> None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Operador).where(Operador.email == email))
        if result.scalar_one_or_none():
            print(f"[erro] Operador com email {email} já existe.")
            return
        operador = Operador(email=email, nome=nome, senha_hash=hash_password(senha))
        db.add(operador)
        await db.commit()
        print(f"[ok] Admin criado: {email}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", required=True)
    parser.add_argument("--nome", required=True)
    args = parser.parse_args()
    senha = getpass.getpass("Senha: ")
    asyncio.run(create_admin(args.email, args.nome, senha))
