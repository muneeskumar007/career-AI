import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.v1.router import api_router
from app.config.settings import settings
from app.database.mongodb import close_mongo_connection, connect_to_mongo
from app.middleware.error_handler import register_error_handlers
from app.middleware.rate_limiter import limiter

logging.basicConfig(
    level=logging.INFO if settings.is_production else logging.DEBUG,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s in %s mode", settings.APP_NAME, settings.APP_ENV)
    await connect_to_mongo()
    yield
    await close_mongo_connection()
    logger.info("Shutdown complete")


app = FastAPI(
    title=settings.APP_NAME,
    description="AI Resume Screening + AI Interview Coach platform API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,  # required so the httpOnly refresh cookie is sent
    allow_methods=["*"],
    allow_headers=["*"],
)

register_error_handlers(app)
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/api/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "service": settings.APP_NAME}
