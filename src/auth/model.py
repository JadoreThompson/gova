import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from core.db.model import Base
from core.db.util import datetime_tz, uuid_pk
from lib.util import get_datetime
from moderator.enums import ModeratorPlatform


class PlatformToken(Base):
    __tablename__ = "platform_tokens"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    platform: Mapped[ModeratorPlatform] = mapped_column(sa.String, nullable=False)
    token: Mapped[str] = mapped_column(sa.String, nullable=False)
    refresh_token: Mapped[str | None] = mapped_column(sa.String, nullable=True)
    created_at: Mapped[datetime] = datetime_tz()
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        default=get_datetime,
        onupdate=get_datetime,
    )

    __table_args__ = (
        sa.UniqueConstraint(
            "user_id",
            "platform",
            name="uq_platform_tokens_user_id_platform",
        ),
        sa.CheckConstraint(
            "length(trim(token)) > 0",
            name="ck_platform_tokens_token_not_empty",
        ),
    )
