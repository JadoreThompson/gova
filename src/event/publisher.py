from abc import ABC, abstractmethod
import uuid

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from event.model import EventOutbox


class EventPublisher(ABC):
    @abstractmethod
    async def publish(
        self, event: BaseModel, topic: str, db_sess: AsyncSession
    ) -> None: ...


class AIOKafkaEventPublisher(EventPublisher):
    async def publish(
        self, event: BaseModel, topic: str, db_sess: AsyncSession
    ) -> None:
        moderator_id = getattr(event, "moderator_id", None)
        db_sess.add(
            EventOutbox(
                id=uuid.uuid4(),
                topic=topic,
                payload=event.model_dump_json(),
                message_key=str(moderator_id) if moderator_id is not None else None,
            )
        )
