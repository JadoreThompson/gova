from abc import ABC, abstractmethod

from aiokafka import AIOKafkaProducer
from pydantic import BaseModel


class EventPublisher(ABC):
    @abstractmethod
    async def publish(self, event: BaseModel, topic: str): ...


class AIOKafkaEventPublisher(EventPublisher):
    def __init__(self, kafka_producer: AIOKafkaProducer):
        self._kafka_producer = kafka_producer

    async def publish(self, event: BaseModel, topic: str):
        encoded_payload = event.model_dump_json().encode("utf-8")
        moderator_id = getattr(event, "moderator_id", None)
        if moderator_id is None:
            await self._kafka_producer.send_and_wait(topic, encoded_payload)
            return

        await self._kafka_producer.send_and_wait(
            topic, encoded_payload, key=str(moderator_id).encode("utf-8")
        )
