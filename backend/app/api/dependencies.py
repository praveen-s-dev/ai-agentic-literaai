from contextlib import asynccontextmanager
from typing import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from app.config import settings, Settings
from database.connection import get_session, init_db


def get_settings() -> Settings:
    return settings


def get_db() -> Generator[Session, None, None]:
    with get_session() as db:
        yield db


@asynccontextmanager
async def lifespan(app):
    init_db()
    yield


def get_db_sync() -> Generator[Session, None, None]:
    with get_session() as db:
        yield db