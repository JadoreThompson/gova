import uuid

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, VerifyMismatchError
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from .exception import UserAlreadyExistsException, UserNotFoundException
from .model import User
from .schema import UserCreate, UserUpdate


class UserService:
    def __init__(self, password_hasher: PasswordHasher) -> None:
        self._pw_hasher = password_hasher

    async def create(self, request: UserCreate, db_sess: AsyncSession) -> User:
        existing = await db_sess.scalar(
            select(User).where(
                or_(
                    User.username == request.username,
                    User.email == request.email,
                )
            )
        )
        if existing is not None:
            raise UserAlreadyExistsException()

        user = User(
            username=request.username,
            email=request.email,
            password=self._pw_hasher.hash(request.password),
        )
        db_sess.add(user)
        await db_sess.flush()
        await db_sess.refresh(user)
        return user

    async def get(self, id: uuid.UUID, db_sess: AsyncSession) -> User:
        user = await db_sess.get(User, id)
        if user is None:
            raise UserNotFoundException()
        return user

    async def find_by_email(self, email: str, db_sess: AsyncSession) -> User | None:
        return await db_sess.scalar(select(User).where(User.email == email))

    async def get_by_email(self, email: str, db_sess: AsyncSession) -> User:
        user = await self.find_by_email(email, db_sess)
        if user is None:
            raise UserNotFoundException()
        return user

    async def list(
        self, db_sess: AsyncSession, *, page: int = 1, limit: int = 50
    ) -> tuple[list[User], bool]:
        result = await db_sess.execute(
            select(User)
            .order_by(User.created_at.desc())
            .offset((page - 1) * limit)
            .limit(limit + 1)
        )
        users = list(result.scalars().all())
        has_next = len(users) > limit
        return users[:limit], has_next

    async def update(
        self, id: uuid.UUID, request: UserUpdate, db_sess: AsyncSession
    ) -> User:
        user = await self.get(id, db_sess)

        if request.username is not None and request.username != user.username:
            await self._ensure_username_available(request.username, user.id, db_sess)
            user.username = request.username

        await db_sess.flush()
        await db_sess.refresh(user)
        return user

    async def update_password(
        self, id: uuid.UUID, password: str, db_sess: AsyncSession
    ) -> User:
        user = await self.get(id, db_sess)
        user.password = self._pw_hasher.hash(password)
        await db_sess.flush()
        await db_sess.refresh(user)
        return user

    async def update_email(
        self, id: uuid.UUID, email: str, db_sess: AsyncSession
    ) -> User:
        user = await self.get(id, db_sess)

        if email != user.email:
            existing = await db_sess.scalar(
                select(User.id).where(User.email == email, User.id != user.id).limit(1)
            )
            if existing is not None:
                raise UserAlreadyExistsException()
            user.email = email

        await db_sess.flush()
        await db_sess.refresh(user)
        return user

    change_password = update_password
    change_email = update_email

    def verify_password(self, user: User, password: str) -> bool:
        try:
            return self._pw_hasher.verify(user.password, password)
        except (VerifyMismatchError, VerificationError):
            return False

    async def delete(self, id: uuid.UUID, db_sess: AsyncSession) -> None:
        user = await self.get(id, db_sess)
        await db_sess.delete(user)

    async def _ensure_username_available(
        self, username: str, user_id: uuid.UUID, db_sess: AsyncSession
    ) -> None:
        existing = await db_sess.scalar(
            select(User.id)
            .where(User.username == username, User.id != user_id)
            .limit(1)
        )
        if existing is not None:
            raise UserAlreadyExistsException()
