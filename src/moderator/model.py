import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB

from core.db.model import Base
from core.db.util import datetime_tz, uuid_pk
from moderator.enums import ModeratorStatus


class Moderators(Base):
    __tablename__ = "moderators"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    community_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("communities.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(sa.String, nullable=False)
    action_config: Mapped[dict[str, dict]] = mapped_column(JSONB, nullable=False)
    status: Mapped[ModeratorStatus] = mapped_column(
        sa.String, default=ModeratorStatus.OFFLINE, nullable=False
    )
    created_at: Mapped[datetime] = datetime_tz()

    # relationships
    user: Mapped["User"] = relationship(
        back_populates="moderators", passive_deletes=True
    )
    community: Mapped["Community"] = relationship(back_populates="moderators")
