import pytest


@pytest.mark.asyncio(loop_scope="session")
async def test_ping_returns_pong(client):
    rsp = await client.post("/ping")

    assert rsp.status_code == 200
    assert rsp.json() == "pong"
