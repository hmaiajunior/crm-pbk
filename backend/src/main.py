import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from src.api import auth, clientes, conversas, webhooks, segmentos, acoes, metricas, campanhas

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def _scheduled_growth_sync() -> None:
    """Wrapper that runs the growth sync with its own DB session."""
    from src.database import AsyncSessionLocal
    from src.services.sync_service import run_growth_sync

    async with AsyncSessionLocal() as db:
        try:
            await run_growth_sync(db)
        except Exception:
            await db.rollback()
            logger.exception("growth sync failed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    from src.events.handlers import subscribe_all
    from src.config import settings

    subscribe_all()
    logger.info("CRM Playbekids starting up")

    scheduler = None
    if settings.SYNC_ENABLED:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler

        scheduler = AsyncIOScheduler()
        scheduler.add_job(
            _scheduled_growth_sync,
            "interval",
            minutes=settings.SYNC_INTERVAL_MINUTES,
            id="growth_sync",
            next_run_time=datetime.now(timezone.utc),  # run once at startup
        )
        scheduler.start()
        logger.info("growth sync scheduled every %d min", settings.SYNC_INTERVAL_MINUTES)

    yield

    if scheduler:
        scheduler.shutdown(wait=False)
    logger.info("CRM Playbekids shutting down")


app = FastAPI(title="CRM Playbekids", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    start = time.monotonic()
    response = await call_next(request)
    duration_ms = round((time.monotonic() - start) * 1000)
    logger.info(
        "%s %s %s %dms",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Erro interno do servidor"})


app.include_router(auth.router, prefix="/api/v1")
app.include_router(clientes.router, prefix="/api/v1")
app.include_router(conversas.router, prefix="/api/v1")
app.include_router(webhooks.router, prefix="/api/v1")
app.include_router(segmentos.router, prefix="/api/v1")
app.include_router(acoes.router, prefix="/api/v1")
app.include_router(metricas.router, prefix="/api/v1")
app.include_router(campanhas.router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok"}
