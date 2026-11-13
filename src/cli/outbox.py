import asyncio

import click

from event.kafka import AIOKafkaProducerFactory
from event.poller import OutboxPoller


async def _run_outbox(batch_size: int, interval: float) -> None:
    producer = AIOKafkaProducerFactory.create()
    await producer.start()
    try:
        await OutboxPoller(producer, batch_size, interval).run()
    finally:
        await producer.stop()


@click.command()
@click.option("--batch-size", type=click.IntRange(min=1), default=100, show_default=True)
@click.option(
    "--interval",
    type=click.FloatRange(min=0, min_open=True),
    default=1.0,
    show_default=True,
)
def outbox(batch_size: int, interval: float) -> None:
    asyncio.run(_run_outbox(batch_size, interval))
