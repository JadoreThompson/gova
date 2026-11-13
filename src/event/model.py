import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from core.db.model import Base
from core.db.util import datetime_tz, uuid_pk


class EventOutbox(Base):
    __tablename__ = "event_outbox"

    id: Mapped[uuid.UUID] = uuid_pk()
    topic: Mapped[str] = mapped_column(sa.String, nullable=False)
    payload: Mapped[str] = mapped_column(sa.Text, nullable=False)
    message_key: Mapped[str | None] = mapped_column(sa.String, nullable=True)
    created_at: Mapped[datetime] = datetime_tz()
