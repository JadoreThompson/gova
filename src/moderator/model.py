import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB

from core.db.model import Base
from core.db.util import datetime_tz, uuid_pk
from moderator.enums import ModeratorPlatform, ModeratorStatus, ModeratorWorkerStatus


class Moderator(Base):
    __tablename__ = "moderators"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    platform: Mapped[ModeratorPlatform] = mapped_column(sa.String, nullable=False)
    platform_community_id: Mapped[str] = mapped_column(sa.String, nullable=False)
    community_policy: Mapped[str] = mapped_column(sa.String, nullable=False)
    name: Mapped[str] = mapped_column(sa.String, nullable=False)
    action_config: Mapped[dict[str, dict]] = mapped_column(JSONB, nullable=False)
    status: Mapped[ModeratorStatus] = mapped_column(
        sa.String, default=ModeratorStatus.OFFLINE, nullable=False
    )
    created_at: Mapped[datetime] = datetime_tz()

    __table_args__ = (
        sa.UniqueConstraint(
            "platform",
            "platform_community_id",
            name="uq_moderators_platform_platform_community_id",
        ),
        sa.CheckConstraint(
            "length(trim(community_policy)) > 0",
            name="ck_moderators_community_policy_not_empty",
        ),
    )


class ModeratorWorker(Base):
    __tablename__ = "moderator_workers"

    id: Mapped[str] = mapped_column(sa.String, primary_key=True)
    platform: Mapped[ModeratorPlatform] = mapped_column(sa.String, nullable=False)
    host: Mapped[str] = mapped_column(sa.String, nullable=False)
    port: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    count: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    capacity: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    status: Mapped[ModeratorWorkerStatus] = mapped_column(
        sa.String, nullable=False, default=ModeratorWorkerStatus.OFFLINE
    )
    last_heartbeat: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    last_attempt: Mapped[int] = mapped_column(sa.Integer, nullable=False)


class ModeratorWorkerAssignment(Base):
    __tablename__ = "moderator_worker_assignment"

    id: Mapped[uuid.UUID] = uuid_pk()
    moderator_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("moderators.id"),
        nullable=False,
    )
    worker_id: Mapped[str] = mapped_column(
        sa.String,
        sa.ForeignKey("moderator_workers.id"),
        nullable=False,
    )
