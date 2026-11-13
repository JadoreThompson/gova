from collections.abc import Sequence

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from config import KAFKA_BOOTSTRAP_SERVERS


class AIOKafkaProducerFactory:
    _producer: AIOKafkaProducer | None = None

    @classmethod
    def create(cls):
        if cls._producer is not None:
            return cls._producer
        cls._producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
        return cls._producer


class AIOKafkaConsumerFactory:
    @classmethod
    def create(
        cls,
        topic: str | Sequence[str],
        group_id: str,
        *,
        auto_offset_reset: str = "earliest",
    ) -> AIOKafkaConsumer:
        return AIOKafkaConsumer(
            *([topic] if isinstance(topic, str) else topic),
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            group_id=group_id,
            auto_offset_reset=auto_offset_reset,
            enable_auto_commit=False,
        )
