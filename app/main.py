from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import settings
from app.database import engine


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # startup

    yield
    # shutdown
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
)
