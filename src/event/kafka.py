from aiokafka import AIOKafkaProducer

from config import KAFKA_BOOTSTRAP_SERVERS


class AIOKafkaProducerFactory:
    _producer: AIOKafkaProducer | None = None

    @classmethod
    def create(cls):
        if cls._producer is not None:
            return cls._producer
        cls._producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
        return cls._producer
