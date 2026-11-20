from abc import ABC, abstractmethod


class IngestionPipeline(ABC):

    @abstractmethod
    async def run(self): ...

    @abstractmethod
    def set_worker_id(self, worker_id: str): ...
