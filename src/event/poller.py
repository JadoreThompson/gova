import asyncio

from aiokafka import AIOKafkaProducer
from sqlalchemy import select

from core.db.session import get_db_session
from event.model import EventOutbox


class OutboxPoller:
    def __init__(
        self, kafka_producer: AIOKafkaProducer, batch_size: int, interval: float
    ) -> None:
        if batch_size < 1:
            raise ValueError("batch_size must be greater than zero")
        if interval <= 0:
            raise ValueError("interval must be greater than zero")

        self._kafka_producer = kafka_producer
        self._batch_size = batch_size
        self._interval = interval

    async def poll_once(self) -> int:
        async with get_db_session() as db_sess:
            result = await db_sess.execute(
                select(EventOutbox)
                .order_by(EventOutbox.created_at, EventOutbox.id)
                .with_for_update(skip_locked=True)
                .limit(self._batch_size)
            )
            events = list(result.scalars().all())

            for event in events:
                await self._kafka_producer.send_and_wait(
                    event.topic,
                    event.payload.encode("utf-8"),
                    key=(
                        event.message_key.encode("utf-8")
                        if event.message_key is not None
                        else None
                    ),
                )
                await db_sess.delete(event)

            return len(events)

    async def run(self) -> None:
        while True:
            await self.poll_once()
            await asyncio.sleep(self._interval)
