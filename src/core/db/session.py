import logging
from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator, Generator

from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql.asyncpg import (
    AsyncAdapt_asyncpg_dbapi as InterfaceError,
)
from sqlalchemy.ext.asyncio import AsyncSession

from .client import POSTGRES_ENGINE, POSTGRES_ENGINE_SYNC

logger = logging.getLogger(__name__)

smaker = sessionmaker(bind=POSTGRES_ENGINE, class_=AsyncSession, expire_on_commit=False)
smaker_sync = sessionmaker(bind=POSTGRES_ENGINE_SYNC, class_=Session, expire_on_commit=False)


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    global smaker

    async with smaker.begin() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            if isinstance(e, InterfaceError):
                logger.info("Received InterfaceError, recreating session maker")
                smaker.configure(
                    bind=POSTGRES_ENGINE, class_=AsyncSession, expire_on_commit=False
                )
            raise


@contextmanager
def get_db_session_sync() -> Generator[Session, None, None]:
    global smaker_sync

    with smaker_sync.begin() as sess:
        try:
            yield sess
        except Exception as e:
            sess.rollback()
            if isinstance(e, InterfaceError):
                logger.info("Received InterfaceError, recreating session maker")
                smaker_sync.configure(
                    bind=POSTGRES_ENGINE_SYNC, class_=Session, expire_on_commit=False
                )
            raise
