from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db import close_db, init_db
from app.routers import admin, auth, generate, posts
from app.services.scheduler import init_scheduler, shutdown_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    init_scheduler()
    yield
    shutdown_scheduler()
    await close_db()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="LinkedIn AI Agent",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.frontend_origin,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router)
    app.include_router(generate.router)
    app.include_router(posts.router)
    app.include_router(admin.router)

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


app = create_app()
