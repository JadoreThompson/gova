import asyncio
import json
import logging
import uuid

from fastapi import APIRouter, Depends, Query, WebSocket, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import depends_jwt, get_jwt_service, get_moderator_service
from config import (
    JWT_COOKIE_ALIAS,
    KAFKA_MODERATOR_ACTIONS_TOPIC,
    KAFKA_MODERATOR_EVENTS_TOPIC,
)
from core.db.session import get_db_session
from event.kafka import AIOKafkaConsumerFactory
from moderator.exception import ModeratorNotFoundException
from moderator.schema import ModeratorCreate, ModeratorResponse, ModeratorUpdate
from moderator.service import ModeratorService
from security.jwt.exception import JWTException
from security.jwt.schema import JWTPayload
from security.jwt.service import JWTService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/moderators", tags=["Moderators"])


@router.post("/", response_model=ModeratorResponse, status_code=status.HTTP_201_CREATED)
async def create_moderator(
    body: ModeratorCreate,
    jwt: JWTPayload = Depends(depends_jwt),
    db_sess: AsyncSession = Depends(get_db_session),
    service: ModeratorService = Depends(get_moderator_service),
):
    moderator = await service.create(body, jwt.sub, db_sess)
    return moderator


@router.get("/{id}", response_model=ModeratorResponse)
async def get_moderator(
    id: uuid.UUID,
    jwt: JWTPayload = Depends(depends_jwt),
    db_sess: AsyncSession = Depends(get_db_session),
    service: ModeratorService = Depends(get_moderator_service),
):
    moderator = await service.get(id, jwt.sub, db_sess)
    return moderator


@router.get("/", response_model=list[ModeratorResponse])
async def list_moderators(
    community_id: uuid.UUID | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    jwt: JWTPayload = Depends(depends_jwt),
    db_sess: AsyncSession = Depends(get_db_session),
    service: ModeratorService = Depends(get_moderator_service),
):
    moderators, _ = await service.list(
        jwt.sub, db_sess, community_id=community_id, page=page, limit=limit
    )
    return moderators


@router.patch("/{id}", response_model=ModeratorResponse)
async def update_moderator(
    id: uuid.UUID,
    body: ModeratorUpdate,
    jwt: JWTPayload = Depends(depends_jwt),
    db_sess: AsyncSession = Depends(get_db_session),
    service: ModeratorService = Depends(get_moderator_service),
):
    moderator = await service.update(id, jwt.sub, body, db_sess)
    return moderator


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_moderator(
    id: uuid.UUID,
    jwt: JWTPayload = Depends(depends_jwt),
    db_sess: AsyncSession = Depends(get_db_session),
    service: ModeratorService = Depends(get_moderator_service),
):
    await service.delete(id, jwt.sub, db_sess)


@router.post("/{id}/start", status_code=status.HTTP_202_ACCEPTED)
async def start_moderator(
    id: uuid.UUID,
    jwt: JWTPayload = Depends(depends_jwt),
    db_sess: AsyncSession = Depends(get_db_session),
    service: ModeratorService = Depends(get_moderator_service),
):
    await service.start(id, jwt.sub, db_sess)


@router.post("/{id}/stop", status_code=status.HTTP_202_ACCEPTED)
async def stop_moderator(
    id: uuid.UUID,
    jwt: JWTPayload = Depends(depends_jwt),
    db_sess: AsyncSession = Depends(get_db_session),
    service: ModeratorService = Depends(get_moderator_service),
):
    await service.stop(id, jwt.sub, db_sess)


@router.post("/{id}/ping", status_code=status.HTTP_202_ACCEPTED)
async def ping_moderator(
    id: uuid.UUID,
    jwt: JWTPayload = Depends(depends_jwt),
    db_sess: AsyncSession = Depends(get_db_session),
    service: ModeratorService = Depends(get_moderator_service),
):
    await service.ping(id, jwt.sub, db_sess)


@router.websocket("/{id}/ws")
async def moderator_events(
    websocket: WebSocket,
    id: uuid.UUID,
    db_sess: AsyncSession = Depends(get_db_session),
    moderator_service: ModeratorService = Depends(get_moderator_service),
    jwt_service: JWTService = Depends(get_jwt_service),
):
    token = websocket.cookies.get(JWT_COOKIE_ALIAS)
    if not token:
        await websocket.close(code=1008)
        return

    try:
        jwt = await jwt_service.validate_jwt(token, db_sess)
        await moderator_service.get(id, jwt.sub, db_sess)
    except (JWTException, ModeratorNotFoundException):
        await websocket.close(code=1008)
        return

    consumer = AIOKafkaConsumerFactory.create(
        (KAFKA_MODERATOR_EVENTS_TOPIC, KAFKA_MODERATOR_ACTIONS_TOPIC),
        f"moderator-api-{uuid.uuid4().hex}",
        auto_offset_reset="latest",
    )

    async def consume():
        async for message in consumer:
            try:
                payload = json.loads(message.value)
            except (UnicodeDecodeError, json.JSONDecodeError):
                logger.warning("Ignoring invalid moderator event from Kafka")
                continue

            if isinstance(payload, dict) and payload.get("moderator_id") == str(id):
                await websocket.send_text(message.value.decode("utf-8"))

    async def receive():
        while True:
            message = await websocket.receive()
            if message["type"] == "websocket.disconnect":
                return

    await consumer.start()

    try:
        await websocket.accept()

        async with asyncio.TaskGroup() as tg:
            tg.create_task(consume())
            tg.create_task(receive())

    except* Exception as exc:
        logger.exception("Moderator WebSocket connection failed: %s", exc)
        await websocket.send_json(
            {
                "type": "error",
                "message": "An internal error occurred while processing moderator events.",
            }
        )

    finally:
        await consumer.stop()
