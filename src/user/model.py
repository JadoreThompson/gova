import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db.model import Base
from core.db.util import datetime_tz, uuid_pk
from lib.util import get_datetime


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = uuid_pk()
    username: Mapped[str] = mapped_column(sa.String, unique=True, nullable=False)
    email: Mapped[str] = mapped_column(sa.String, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(sa.String, nullable=False)
    jwt_token: Mapped[str | None] = mapped_column(sa.String, nullable=True)
    discord_oauth_payload: Mapped[str | None] = mapped_column(sa.String, nullable=True)
    stripe_customer_id: Mapped[str | None] = mapped_column(
        sa.String, unique=True, nullable=True
    )
    created_at: Mapped[datetime] = datetime_tz()
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        default=get_datetime,
        onupdate=get_datetime,
    )
    verified_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )

    communities: Mapped[list["Community"]] = relationship(
        back_populates="user", passive_deletes=True
    )
    moderators: Mapped[list["Moderators"]] = relationship(
        back_populates="user", passive_deletes=True
    )

    __table_args__ = (
        sa.CheckConstraint(
            "length(trim(username)) > 0",
            name="ck_users_username_not_empty",
        ),
        sa.CheckConstraint(
            "length(trim(email)) > 0",
            name="ck_users_email_not_empty",
        ),
    )
