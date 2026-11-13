import pytest
from sqlalchemy import delete

from community.model import Community
from core.db.session import get_db_session

from .util import make_create


async def _clear_communities():
    async with get_db_session() as db_sess:
        await db_sess.execute(delete(Community))
        await db_sess.commit()


async def _seed_communities(community_service, community_user_id, count):
    communities = []
    async with get_db_session() as db_sess:
        for index in range(count):
            communities.append(
                await community_service.create(
                    make_create(community_id=f"seed-{index}"),
                    community_user_id,
                    db_sess,
                )
            )
        await db_sess.commit()
    return communities


@pytest.mark.asyncio(loop_scope="session")
async def test_list_returns_page_and_signals_next_page(
    community_service, create_user
):
    community_user_id = create_user()
    await _clear_communities()
    communities = await _seed_communities(
        community_service, community_user_id, 3
    )
    expected_ids = {community.id for community in communities}

    async with get_db_session() as db_sess:
        page, has_next = await community_service.list(community_user_id, db_sess, page=1, limit=2)

    assert len(page) == 2
    assert {community.id for community in page} <= expected_ids
    assert has_next is True


@pytest.mark.asyncio(loop_scope="session")
async def test_list_returns_second_page_without_overlap(
    community_service, create_user
):
    community_user_id = create_user()
    await _clear_communities()
    communities = await _seed_communities(
        community_service, community_user_id, 3
    )
    expected_ids = {community.id for community in communities}

    async with get_db_session() as db_sess:
        first, _ = await community_service.list(community_user_id, db_sess, page=1, limit=2)

    async with get_db_session() as db_sess:
        second, has_next = await community_service.list(community_user_id, db_sess, page=2, limit=2)

    first_ids = {community.id for community in first}
    second_ids = {community.id for community in second}

    assert first_ids | second_ids == expected_ids
    assert first_ids.isdisjoint(second_ids)
    assert has_next is False


@pytest.mark.asyncio(loop_scope="session")
async def test_list_returns_everything_when_under_limit(
    community_service, create_user
):
    community_user_id = create_user()
    await _clear_communities()
    communities = await _seed_communities(
        community_service, community_user_id, 2
    )
    expected_ids = {community.id for community in communities}

    async with get_db_session() as db_sess:
        page, has_next = await community_service.list(community_user_id, db_sess, page=1, limit=5)

    assert {community.id for community in page} == expected_ids
    assert has_next is False


@pytest.mark.asyncio(loop_scope="session")
async def test_list_returns_empty_page_when_no_communities(
    community_service, create_user
):
    community_user_id = create_user()
    await _clear_communities()

    async with get_db_session() as db_sess:
        page, has_next = await community_service.list(community_user_id, db_sess, page=1, limit=5)

    assert page == []
    assert has_next is False
