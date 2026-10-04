from types import SimpleNamespace

from infra.mqtt.mqtt_client import MQTTClientManager


def message(topic, payload):
    return SimpleNamespace(topic=topic, payload=payload)


def test_received_messages_are_buffered_per_topic_with_a_bound():
    manager = MQTTClientManager(broker="localhost", port=1883, max_messages_per_topic=2)
    for value in (b"1", b"2", b"3"):
        manager.on_message(None, None, message("sensors/a", value))
    manager.on_message(None, None, message("sensors/b", b"\xff"))

    assert manager.get_messages_by_topic("sensors/a") == ["2", "3"]
    assert manager.get_messages_by_topic("sensors/b") == ["�"]
    assert manager.get_messages_by_topic("missing") == []
    assert manager.get_all_messages() == {"sensors/a": ["2", "3"], "sensors/b": ["�"]}


def test_configuration_comes_from_the_environment(monkeypatch):
    monkeypatch.setenv("MQTT_BROKER", "mosquitto")
    monkeypatch.setenv("MQTT_PORT", "1884")
    monkeypatch.setenv("MQTT_SUBSCRIPTION", "sensors/#")
    manager = MQTTClientManager()
    assert (manager.broker, manager.port, manager.subscription) == ("mosquitto", 1884, "sensors/#")
