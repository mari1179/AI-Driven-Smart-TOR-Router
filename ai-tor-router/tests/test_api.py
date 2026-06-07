from src.api.dashboard import create_app


class MockTor:
    pass


class MockCircuit:
    pass


class MockTraffic:
    pass


class MockDetector:
    pass


class MockHealth:
    pass


def test_dashboard():
    app = create_app(
        MockTor(),
        MockCircuit(),
        MockTraffic(),
        MockDetector(),
        MockHealth()
    )

    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200