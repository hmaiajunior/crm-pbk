"""Run the growth sync job once, on demand.

Usage:
    cd backend/
    python -m src.scripts.run_sync
"""
import asyncio
from src.database import AsyncSessionLocal
from src.services.sync_service import run_growth_sync


async def main() -> None:
    async with AsyncSessionLocal() as db:
        stats = await run_growth_sync(db)
        print(f"[ok] growth sync: {stats}")


if __name__ == "__main__":
    asyncio.run(main())
