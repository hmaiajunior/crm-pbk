"""Reset the password of an existing operator.

Usage:
    cd backend/
    python -m src.scripts.reset_senha --email admin@playbekids.com
    # A nova senha será solicitada interativamente
"""
import asyncio
import argparse
import getpass
from sqlalchemy import select
from src.database import AsyncSessionLocal
from src.models.operador import Operador
from src.services.auth_service import hash_password


async def reset_senha(email: str, senha: str) -> None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Operador).where(Operador.email == email))
        operador = result.scalar_one_or_none()
        if not operador:
            print(f"[erro] Operador com email {email} não encontrado.")
            return
        operador.senha_hash = hash_password(senha)
        await db.commit()
        print(f"[ok] Senha redefinida para: {email}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", required=True)
    args = parser.parse_args()
    senha = getpass.getpass("Nova senha: ")
    asyncio.run(reset_senha(args.email, senha))
