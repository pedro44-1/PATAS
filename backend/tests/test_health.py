def test_health_is_unavailable_when_database_probe_fails(client, monkeypatch):
    from src import main

    def fail_connect():
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(main.engine, "connect", fail_connect)

    response = client.get("/health")

    assert response.status_code == 503
    assert response.json()["status"] == "degraded"
    assert response.json()["checks"]["database"] == "error"


def test_health_is_unavailable_when_redis_probe_fails(client, monkeypatch):
    from src import main

    class UnavailableRedis:
        async def ping(self):
            raise RuntimeError("redis unavailable")

    monkeypatch.setattr(main.cache, "_redis", UnavailableRedis())

    response = client.get("/health")

    assert response.status_code == 503
    assert response.json()["checks"]["redis"] == "error"
