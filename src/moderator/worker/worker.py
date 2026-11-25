import asyncio
import logging

import uvicorn
from fastapi import Depends, FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from moderator.enums import ModeratorPlatform
from core.db.session import get_db_session, get_db_session_dep
from moderator.pipeline.base import IngestionPipeline
from moderator.schema import ModeratorWorkerCreate
from moderator.service.manager import ModeratorManagerService
from moderator.service.worker import ModeratorWorkerService
from moderator.worker.schema import RegisterModeratorRequest


class ModeratorWorker:
    def __init__(
        self,
        id: str,
        capacity: int,
        host: str,
        port: int,
        platform: ModeratorPlatform,
        moderator_worker_service: ModeratorWorkerService,
        moderator_manager_service: ModeratorManagerService,
        pipeline: IngestionPipeline,
        heartbeat_interval: int = 5,
    ) -> None:
        self._id = id
        self._capacity = capacity
        self._host = host
        self._port = port
        self._platform = platform
        self._moderator_worker_service = moderator_worker_service
        self._moderator_manager_service = moderator_manager_service
        self._pipeline = pipeline
        self._heartbeat_interval = heartbeat_interval

        self._app = FastAPI()
        config = uvicorn.Config(self._app, host=self._host, port=self._port)
        self._server = uvicorn.Server(config)
        self._is_ready = False
        self._logger = logging.getLogger(self.__class__.__name__)

    @property
    def id(self) -> str:
        return self._id

    @property
    def capacity(self) -> int:
        return self._capacity

    @property
    def host(self) -> str:
        return self._host

    @property
    def port(self) -> int:
        return self._port

    @property
    def platform(self) -> ModeratorPlatform:
        return self._platform

    @property
    def pipeline(self) -> IngestionPipeline:
        return self._pipeline

    @property
    def app(self) -> FastAPI:
        return self._app

    @property
    def server(self) -> uvicorn.Server:
        return self._server

    @property
    def is_ready(self) -> bool:
        return self._is_ready

    async def run(self):
        await self._ensure_worker()
        self._assign_routes()

        async with asyncio.TaskGroup() as tg:
            tg.create_task(self._server.serve())
            tg.create_task(self._heartbeat_loop())

    def _assign_routes(self):
        @self._app.post("/ping")
        async def ping():
            return "pong"

        @self._app.post("/register")
        async def register(
            body: RegisterModeratorRequest,
            db_sess: AsyncSession = Depends(get_db_session_dep),
        ):
            """Create moderator instance with manager. Pipeline picks it up through manager"""
            await self._moderator_manager_service.create(
                body.moderator_id, self._id, db_sess
            )
            await db_sess.commit()

    async def _ensure_worker(self):
        """Creates or refreshes the moderator worker record in the db"""
        async with get_db_session() as db_sess:
            await self._moderator_worker_service.register(
                ModeratorWorkerCreate(
                    id=self._id,
                    host=self._host,
                    port=self._port,
                    capacity=self._capacity,
                    platform=self._platform,
                ),
                db_sess,
            )
            await db_sess.commit()

        self._is_ready = True

    async def _heartbeat_loop(self):
        while not self._server.should_exit:
            try:
                async with get_db_session() as db_sess:
                    await self._moderator_worker_service.heartbeat(self._id, db_sess)
            except Exception:
                self._logger.exception(
                    "Failed to send heartbeat for moderator worker '%s'", self._id
                )
            await asyncio.sleep(self._heartbeat_interval)
