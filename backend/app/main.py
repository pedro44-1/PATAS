import logging
from contextlib import asynccontextmanager
from sqlalchemy import text
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import engine, Base, SessionLocal
from app.api.v1 import router as api_v1
from app.models import *
from app.services.cache import cache
from app.core.logging_config import setup_logging

setup_logging()

logger = logging.getLogger("patas")

MAX_BODY_SIZE = 5 * 1024 * 1024
RATE_LIMIT_MAX = 100
RATE_LIMIT_WINDOW = 60


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    _seed_permissions()
    await cache.init()
    yield
    await cache.close()


def _seed_permissions():
    from scripts.seed_permissions import seed_permissions
    db = SessionLocal()
    try:
        seed_permissions(db)
    finally:
        db.close()


app = FastAPI(
    title="PATAS API",
    description="Veterinary clinic management SaaS",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS_LIST,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin"],
)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    if request.url.path.startswith("/health"):
        return await call_next(request)

    client_ip = request.client.host
    key = f"ratelimit:{client_ip}"
    allowed, count = await cache.check_rate_limit(key, RATE_LIMIT_MAX, RATE_LIMIT_WINDOW)
    if not allowed:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": f"Rate limit exceeded. Max {RATE_LIMIT_MAX} requests per {RATE_LIMIT_WINDOW}s"},
            headers={"Retry-After": str(RATE_LIMIT_WINDOW)},
        )

    response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = str(RATE_LIMIT_MAX)
    response.headers["X-RateLimit-Remaining"] = str(max(0, RATE_LIMIT_MAX - count))
    response.headers["X-RateLimit-Reset"] = str(RATE_LIMIT_WINDOW)
    return response


@app.middleware("http")
async def limit_body_size(request: Request, call_next):
    content_length = request.headers.get("Content-Length")
    if content_length and int(content_length) > MAX_BODY_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Corpo da requisição demasiado grande (máximo 5MB)",
        )
    return await call_next(request)


@app.middleware("http")
async def global_exception_handler(request: Request, call_next):
    try:
        return await call_next(request)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Erro interno do servidor"},
        )


app.include_router(api_v1, prefix="/api/v1")


@app.get("/health")
async def health():
    db_ok = False
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        pass

    redis_ok = False
    try:
        if cache.client:
            await cache.client.ping()
            redis_ok = True
    except Exception:
        pass

    all_ok = db_ok and redis_ok
    return {
        "status": "ok" if all_ok else "degraded",
        "app": "PATAS",
        "checks": {
            "database": "ok" if db_ok else "error",
            "redis": "ok" if redis_ok else "error",
        },
    }