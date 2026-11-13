from lib.util import get_datetime

from .util import make_service


def test_generate_expiry_offsets_current_time_by_configured_seconds():
    service = make_service(jwt_expiry_secs=120)

    before = int(get_datetime().timestamp())
    expiry = service._generate_expiry()
    after = int(get_datetime().timestamp())

    assert before + 120 <= expiry <= after + 120


def test_generate_expiry_uses_configured_expiry():
    service = make_service(jwt_expiry_secs=60)
    other = make_service(jwt_expiry_secs=3600)

    now = int(get_datetime().timestamp())

    assert service._generate_expiry() - now in (59, 60)
    assert other._generate_expiry() - now in (3599, 3600)
