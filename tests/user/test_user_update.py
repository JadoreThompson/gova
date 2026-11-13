import uuid

import pytest

from core.db.session import get_db_session
from user.exception import UserAlreadyExistsException, UserNotFoundException
from user.model import User
from user.schema import UserEmailUpdate, UserPasswordUpdate, UserUpdate

from .util import make_create


@pytest.mark.asyncio(loop_scope="session")
async def test_update_changes_username(user_service):
    async with get_db_session() as db_sess:
        user = await user_service.create(make_create(), db_sess)
        await db_sess.commit()

    new_username = f"updated-{uuid.uuid4().hex}"
    async with get_db_session() as db_sess:
        result = await user_service.update(
            user.id, UserUpdate(username=new_username), db_sess
        )
        await db_sess.commit()

    assert result.id == user.id
    assert result.username == new_username

    async with get_db_session() as db_sess:
        stored = await db_sess.get(User, user.id)

    assert stored.username == new_username


@pytest.mark.asyncio(loop_scope="session")
async def test_update_does_not_change_email_or_password(user_service):
    req = make_create()
    async with get_db_session() as db_sess:
        user = await user_service.create(req, db_sess)
        await db_sess.commit()

    original_password = user.password
    async with get_db_session() as db_sess:
        result = await user_service.update(
            user.id,
            UserUpdate(username=f"updated-{uuid.uuid4().hex}"),
            db_sess,
        )
        await db_sess.commit()

    assert result.email == req.email
    assert result.password == original_password
    assert user_service.verify_password(result, req.password)


@pytest.mark.asyncio(loop_scope="session")
async def test_update_keeps_username_when_not_provided(user_service):
    req = make_create()
    async with get_db_session() as db_sess:
        user = await user_service.create(req, db_sess)
        await db_sess.commit()

    async with get_db_session() as db_sess:
        result = await user_service.update(user.id, UserUpdate(), db_sess)
        await db_sess.commit()

    assert result.username == req.username
    assert result.email == req.email


@pytest.mark.asyncio(loop_scope="session")
async def test_update_raises_when_user_missing(user_service):
    with pytest.raises(UserNotFoundException):
        async with get_db_session() as db_sess:
            await user_service.update(
                uuid.uuid4(),
                UserUpdate(username=f"updated-{uuid.uuid4().hex}"),
                db_sess,
            )


@pytest.mark.asyncio(loop_scope="session")
async def test_update_raises_when_username_taken(user_service):
    first = make_create()
    second = make_create()

    async with get_db_session() as db_sess:
        await user_service.create(first, db_sess)
        other = await user_service.create(second, db_sess)
        await db_sess.commit()

    with pytest.raises(UserAlreadyExistsException):
        async with get_db_session() as db_sess:
            await user_service.update(
                other.id, UserUpdate(username=first.username), db_sess
            )
            await db_sess.commit()


@pytest.mark.asyncio(loop_scope="session")
async def test_update_trims_username_whitespace(user_service):
    async with get_db_session() as db_sess:
        user = await user_service.create(make_create(), db_sess)
        await db_sess.commit()

    expected = f"spaced-{uuid.uuid4().hex}"
    async with get_db_session() as db_sess:
        result = await user_service.update(
            user.id, UserUpdate(username=f"  {expected}  "), db_sess
        )
        await db_sess.commit()

    assert result.username == expected


@pytest.mark.asyncio(loop_scope="session")
async def test_update_password_hashes_new_password(user_service):
    req = make_create()
    async with get_db_session() as db_sess:
        user = await user_service.create(req, db_sess)
        await db_sess.commit()
    original_password = user.password

    async with get_db_session() as db_sess:
        result = await user_service.update_password(user.id, "new-password", db_sess)
        await db_sess.commit()

    assert result.password != original_password
    assert result.password != "new-password"
    assert user_service.verify_password(result, "new-password")
    assert not user_service.verify_password(result, req.password)


@pytest.mark.asyncio(loop_scope="session")
async def test_update_password_raises_when_user_missing(user_service):
    with pytest.raises(UserNotFoundException):
        async with get_db_session() as db_sess:
            await user_service.update_password(uuid.uuid4(), "new-password", db_sess)


@pytest.mark.asyncio(loop_scope="session")
async def test_update_email_changes_email(user_service):
    req = make_create()
    async with get_db_session() as db_sess:
        user = await user_service.create(req, db_sess)
        await db_sess.commit()

    async with get_db_session() as db_sess:
        result = await user_service.update_email(user.id, "new@example.com", db_sess)
        await db_sess.commit()

    assert result.email == "new@example.com"

    async with get_db_session() as db_sess:
        stored = await db_sess.get(User, user.id)

    assert stored.email == "new@example.com"


@pytest.mark.asyncio(loop_scope="session")
async def test_update_email_raises_when_email_taken(user_service):
    first = make_create()
    second = make_create()

    async with get_db_session() as db_sess:
        await user_service.create(first, db_sess)
        other = await user_service.create(second, db_sess)
        await db_sess.commit()

    with pytest.raises(UserAlreadyExistsException):
        async with get_db_session() as db_sess:
            await user_service.update_email(other.id, first.email, db_sess)
            await db_sess.commit()


@pytest.mark.asyncio(loop_scope="session")
async def test_update_email_raises_when_user_missing(user_service):
    with pytest.raises(UserNotFoundException):
        async with get_db_session() as db_sess:
            await user_service.update_email(uuid.uuid4(), "new@example.com", db_sess)


def test_update_does_not_raise_for_single_character_username():
    request = UserUpdate(username="a")

    assert request.username == "a"


def test_update_raises_validation_error_when_username_is_blank():
    with pytest.raises(ValueError):
        UserUpdate(username="   ")


def test_password_update_does_not_raise_for_single_character_password():
    request = UserPasswordUpdate(password="a")

    assert request.password == "a"


def test_password_update_raises_validation_error_when_password_is_empty():
    with pytest.raises(ValueError):
        UserPasswordUpdate(password="")


def test_email_update_raises_validation_error_when_email_is_empty():
    with pytest.raises(ValueError):
        UserEmailUpdate(email="")
