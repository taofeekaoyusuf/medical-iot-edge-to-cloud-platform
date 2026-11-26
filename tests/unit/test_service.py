import asyncio

import pytest
from httpx import ASGITransport, AsyncClient

from medical_iot.service import create_app


def get(app, path):
    async def request():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            return await client.get(path)

    return asyncio.run(request())


@pytest.mark.parametrize(
    "name", ["gateway", "registry", "processor", "health", "notifications", "api"]
)
def test_scaffold_is_live_but_explicitly_not_ready(name):
    app = create_app(name)
    assert get(app, "/health/live").json() == {"service": name, "status": "alive"}
    response = get(app, "/health/ready")
    assert response.status_code == 503
    assert response.json()["reason"] == "domain_service_not_implemented"
    assert get(app, "/v1/devices").status_code == 404


def test_service_name_cannot_silently_select_unknown_service(monkeypatch):
    monkeypatch.setenv("MEDICAL_IOT_SERVICE", "typo")
    with pytest.raises(ValueError, match="Unknown service"):
        create_app()


def test_service_selection_uses_environment(monkeypatch):
    monkeypatch.setenv("MEDICAL_IOT_SERVICE", "registry")
    assert get(create_app(), "/health/live").json()["service"] == "registry"
