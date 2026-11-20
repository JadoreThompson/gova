import uuid

import pytest


@pytest.mark.asyncio(loop_scope="session")
async def test_register_creates_moderator_with_manager(
    client, worker, moderator_manager_service, db_sess
):
    moderator_id = uuid.uuid4()

    rsp = await client.post("/register", json={"moderator_id": str(moderator_id)})

    assert rsp.status_code == 200
    moderator_manager_service.create.assert_awaited_once_with(
        moderator_id, worker.id, db_sess
    )
    db_sess.commit.assert_awaited_once()


@pytest.mark.asyncio(loop_scope="session")
async def test_register_rejects_invalid_moderator_id(
    client, moderator_manager_service, db_sess
):
    rsp = await client.post("/register", json={"moderator_id": "not-a-uuid"})

    assert rsp.status_code == 422
    moderator_manager_service.create.assert_not_awaited()
    db_sess.commit.assert_not_awaited()
