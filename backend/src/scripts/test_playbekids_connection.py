"""Test read-only connection to the Playbekids database."""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.integrations.playbekids_db import get_ultima_compra_by_phone


async def main() -> None:
    test_phone = input("Telefone para teste (ex: 11999999999): ").strip()
    if not test_phone:
        test_phone = "11999999999"

    print(f"\nTestando conexão Playbekids DB para telefone: {test_phone}")
    try:
        ultima_compra_em, total_compras = await get_ultima_compra_by_phone(test_phone)
        if ultima_compra_em:
            print(f"✓ Conexão OK — Última compra: {ultima_compra_em} | Total de compras: {total_compras}")
        else:
            print("✓ Conexão OK — Nenhuma compra encontrada para este telefone")
    except Exception as e:
        print(f"✗ Erro na conexão: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
