import pytest
from pydantic import ValidationError

from core.db.session import get_db_session
from user.exception import UserAlreadyExistsException
from user.model import User
from user.schema import UserResponse

from .util import make_create


@pytest.mark.asyncio(loop_scope="session")
async def test_create_adds_user_and_returns_it(user_service):
    req = make_create()
    async with get_db_session() as db_sess:
        user = await user_service.create(req, db_sess)
        await db_sess.commit()

    assert isinstance(user, UserResponse)
    assert user.username == req.username
    assert user.email == req.email

    async with get_db_session() as db_sess:
        stored = await db_sess.get(User, user.id)

    assert stored is not None
    assert stored.password != req.password
    assert user_service.verify_password(stored.password, req.password)
    assert not user_service.verify_password(stored.password, "not-the-password")


@pytest.mark.asyncio(loop_scope="session")
async def test_create_raises_when_username_already_exists(user_service):
    req = make_create()

    async with get_db_session() as db_sess:
        user = await user_service.create(req, db_sess)
        await db_sess.commit()

    duplicate = make_create(username=req.username)

    with pytest.raises(UserAlreadyExistsException):
        async with get_db_session() as db_sess:
            await user_service.create(duplicate, db_sess)
            await db_sess.commit()

    async with get_db_session() as db_sess:
        stored = await db_sess.get(User, user.id)

    assert stored.email == req.email


@pytest.mark.asyncio(loop_scope="session")
async def test_create_raises_when_email_already_exists(user_service):
    req = make_create()

    async with get_db_session() as db_sess:
        user = await user_service.create(req, db_sess)
        await db_sess.commit()

    duplicate = make_create(email=req.email)

    with pytest.raises(UserAlreadyExistsException):
        async with get_db_session() as db_sess:
            await user_service.create(duplicate, db_sess)
            await db_sess.commit()

    async with get_db_session() as db_sess:
        stored = await db_sess.get(User, user.id)

    assert stored.username == req.username


@pytest.mark.asyncio(loop_scope="session")
async def test_create_allows_distinct_users(user_service):
    first = make_create()
    second = make_create()

    async with get_db_session() as db_sess:
        first_user = await user_service.create(first, db_sess)
        await db_sess.commit()

    async with get_db_session() as db_sess:
        second_user = await user_service.create(second, db_sess)
        await db_sess.commit()

    assert first_user.id != second_user.id
    assert first_user.username != second_user.username
    assert first_user.email != second_user.email


def test_create_does_not_raise_for_single_character_fields():
    request = make_create(username="a", email="a", password="a")

    assert request.username == "a"
    assert request.email == "a"
    assert request.password == "a"


def test_create_raises_validation_error_when_username_is_blank():
    with pytest.raises(ValidationError):
        make_create(username="   ")


def test_create_raises_validation_error_when_email_is_empty():
    with pytest.raises(ValidationError):
        make_create(email="")


def test_create_raises_validation_error_when_password_is_empty():
    with pytest.raises(ValidationError):
        make_create(password="")


def test_create_trims_whitespace():
    request = make_create(username="  alice  ", email="  a@b.c  ")

    assert request.username == "alice"
    assert request.email == "a@b.c"


def test_make_create_generates_distinct_values():
    first = make_create()
    second = make_create()

    assert first.username != second.username
    assert first.email != second.email
