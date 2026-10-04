from fastapi.testclient import TestClient

from main import create_app


class FakeMQTT:
    def __init__(self, publish_ok=True):
        self.connected = True
        self.publish_ok = publish_ok
        self.published = []
        self.messages = {"sensors/room-admin/temperature": ["29", "30"]}
        self.lifecycle = []

    def connect(self):
        self.lifecycle.append("connect")

    def disconnect(self):
        self.lifecycle.append("disconnect")

    def publish(self, topic, payload):
        self.published.append((topic, payload))
        return self.publish_ok

    def get_all_messages(self):
        return self.messages

    def get_messages_by_topic(self, topic):
        return self.messages.get(topic, [])


def test_lifespan_connects_and_disconnects_the_broker():
    mqtt = FakeMQTT()
    with TestClient(create_app(mqtt)) as client:
        assert client.get("/health").json() == {"status": "ok", "mqtt_connected": True}
    assert mqtt.lifecycle == ["connect", "disconnect"]


def test_publish_accepts_topic_and_payload():
    mqtt = FakeMQTT()
    with TestClient(create_app(mqtt)) as client:
        response = client.post("/publish", json={"topic": "sensors/a", "payload": "21.5"})
    assert response.status_code == 202
    assert mqtt.published == [("sensors/a", "21.5")]


def test_publish_reports_an_unavailable_broker():
    with TestClient(create_app(FakeMQTT(publish_ok=False))) as client:
        response = client.post("/publish", json={"topic": "sensors/a", "payload": "1"})
    assert response.status_code == 503


def test_topics_with_slashes_are_readable():
    with TestClient(create_app(FakeMQTT())) as client:
        found = client.get("/messages/sensors/room-admin/temperature")
        missing = client.get("/messages/unknown/topic")
    assert found.json() == {"topic": "sensors/room-admin/temperature", "messages": ["29", "30"]}
    assert missing.status_code == 404


def test_predict_validates_input_and_rounds_the_prediction():
    with TestClient(create_app(FakeMQTT(), predictor=lambda features: 29.4567)) as client:
        ok = client.post("/predict", json={"hour": 12, "day": 15, "month": 6, "year": 2023, "out_in": 1})
        invalid = client.post("/predict", json={"hour": 25, "day": 15, "month": 6, "year": 2023, "out_in": 1})
    assert ok.json() == {"prediction_celsius": 29.46}
    assert invalid.status_code == 422
