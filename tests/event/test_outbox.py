import asyncio
import uuid

import pytest
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from sqlalchemy import select

from config import KAFKA_BOOTSTRAP_SERVERS
from core.db.session import get_db_session
from event.model import EventOutbox
from event.poller import OutboxPoller
from event.publisher import AIOKafkaEventPublisher
from moderator.event import ModeratorPingEvent


@pytest.mark.asyncio(loop_scope="session")
async def test_publisher_outbox_poller_emits_event_to_kafka_and_removes_it():
    topic = f"outbox-test-{uuid.uuid4().hex}"
    event = ModeratorPingEvent(moderator_id=uuid.uuid4())
    publisher = AIOKafkaEventPublisher()
    producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
    consumer = AIOKafkaConsumer(
        topic,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id=f"outbox-test-{uuid.uuid4().hex}",
        auto_offset_reset="earliest",
    )
    await producer.start()
    await consumer.start()
    try:
        async with get_db_session() as db_sess:
            await publisher.publish(event, topic, db_sess)

        assert await OutboxPoller(producer, batch_size=10, interval=1).poll_once() == 1
        message = await asyncio.wait_for(consumer.getone(), timeout=15)

        assert message.topic == topic
        assert message.value == event.model_dump_json().encode("utf-8")
        assert message.key == str(event.moderator_id).encode("utf-8")

        async with get_db_session() as db_sess:
            remaining = await db_sess.scalar(
                select(EventOutbox.id).where(EventOutbox.topic == topic)
            )
        assert remaining is None
    finally:
        await consumer.stop()
        await producer.stop()


@pytest.mark.asyncio(loop_scope="session")
async def test_poller_skips_rows_locked_by_another_process():
    topic = f"outbox-lock-test-{uuid.uuid4().hex}"
    event = ModeratorPingEvent(moderator_id=uuid.uuid4())
    async with get_db_session() as db_sess:
        await AIOKafkaEventPublisher().publish(event, topic, db_sess)

    send_started = asyncio.Event()
    continue_send = asyncio.Event()

    class BlockingProducer:
        async def send_and_wait(self, *_args, **_kwargs):
            send_started.set()
            await continue_send.wait()

    poller = OutboxPoller(BlockingProducer(), batch_size=1, interval=1)
    first_poll = asyncio.create_task(poller.poll_once())
    try:
        await asyncio.wait_for(send_started.wait(), timeout=10)
        assert await poller.poll_once() == 0
    finally:
        continue_send.set()
    assert await first_poll == 1
