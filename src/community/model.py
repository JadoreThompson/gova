import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from community.enums import CommunityPlatform
from core.db.model import Base
from core.db.util import uuid_pk


class Community(Base):
    __tablename__ = "communities"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    platform: Mapped[CommunityPlatform] = mapped_column(sa.String, nullable=False)
    community_id: Mapped[str] = mapped_column(sa.String, nullable=False)
    policy: Mapped[str] = mapped_column(sa.String, nullable=False)

    user: Mapped["User"] = relationship(
        back_populates="communities", passive_deletes=True
    )
    moderators: Mapped[list["Moderators"]] = relationship(
        back_populates="community", passive_deletes=True
    )

    __table_args__ = (
        sa.CheckConstraint(
            "length(trim(policy)) > 0",
            name="ck_policy_not_empty",
        ),
    )
