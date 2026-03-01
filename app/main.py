"""
main.py – FastAPI application entry point.

Initialises the MSSQL database, mounts static files, registers all routers
(including auth), adds SessionMiddleware for cookie-based auth, and
starts/stops the APScheduler on application lifecycle events.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from app.database import init_db
from app.scheduler.jobs import create_scheduler, get_notifications
from app.routers import tasks, logs, habits, users, analytics, dashboard
from app.routers import auth as auth_router


# ─── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ─── Lifespan ─────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup:  initialise DB tables → start scheduler
    Shutdown: stop scheduler gracefully
    """
    logger.info("🧠 Mind Flayer starting up...")
    await init_db()

    # Start background scheduler
    scheduler = create_scheduler()
    scheduler.start()
    app.state.scheduler = scheduler
    logger.info("✅ Scheduler started.")

    yield  # Application runs here

    # Shutdown
    scheduler.shutdown(wait=False)
    logger.info("Mind Flayer shut down cleanly.")


# ─── App ──────────────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=settings.APP_DESCRIPTION,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)


# ─── Session Middleware (required for cookie-based auth) ──────────────────────
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SESSION_SECRET_KEY,
    session_cookie="mf_session",
    max_age=60 * 60 * 24 * 7,   # 7 days
    https_only=False,          # Set True in production (HTTPS)
    same_site="lax",
)


# ─── Static Files ─────────────────────────────────────────────────────────────
app.mount("/static", StaticFiles(directory="app/static"), name="static")


# ─── Routers ──────────────────────────────────────────────────────────────────
app.include_router(auth_router.router)   # Unauthenticated routes first

app.include_router(dashboard.router)
app.include_router(tasks.router)
app.include_router(logs.router)
app.include_router(habits.router)
app.include_router(users.router)
app.include_router(analytics.router)


# ─── Notification polling endpoint ────────────────────────────────────────────
@app.get("/api/notifications", tags=["System"])
async def poll_notifications():
    """Frontend polls this to get pending scheduler notifications."""
    return {"notifications": get_notifications()}


# ─── Health check ─────────────────────────────────────────────────────────────
@app.get("/api/health", tags=["System"])
async def health():
    return {
        "status": "operational",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


# ─── HTTP Exception Handler (Type-Safe – Fixes Pylance Error) ─────────────────
@app.exception_handler(HTTPException)
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Handles FastAPI & Starlette HTTP exceptions properly.
    """

    # Handle 303 redirect (used in auth flow)
    if exc.status_code == 303:
        location = exc.headers.get("Location", "/login") if exc.headers else "/login"
        return RedirectResponse(url=location, status_code=302)

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


# ─── Generic Exception Handler ────────────────────────────────────────────────
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """
    Catches any unhandled exceptions.
    """
    logger.error(f"Unhandled exception at {request.url}: {exc}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Check server logs."},
    )


# ─── Run Server ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info",
    )