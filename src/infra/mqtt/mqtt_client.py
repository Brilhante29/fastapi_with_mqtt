import logging
import os
import threading
from collections import defaultdict, deque

import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)


class MQTTClientManager:
    """Keeps one MQTT connection, publishes messages, and buffers what it receives.

    Received payloads are kept in bounded per-topic buffers so that a chatty topic cannot grow
    memory without limit.
    """

    def __init__(
        self,
        broker: str | None = None,
        port: int | None = None,
        subscription: str | None = None,
        max_messages_per_topic: int = 1000,
    ) -> None:
        self.broker = broker or os.environ.get("MQTT_BROKER", "localhost")
        self.port = port or int(os.environ.get("MQTT_PORT", "1883"))
        self.subscription = subscription or os.environ.get("MQTT_SUBSCRIPTION", "#")
        self._max_messages = max_messages_per_topic
        self._messages: dict[str, deque[str]] = defaultdict(lambda: deque(maxlen=self._max_messages))
        self._lock = threading.Lock()
        self.connected = False

        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message
        self.client.reconnect_delay_set(min_delay=1, max_delay=30)

    def on_connect(self, client, userdata, flags, reason_code, properties) -> None:
        if reason_code.is_failure:
            logger.warning("MQTT connection refused: %s", reason_code)
            return
        self.connected = True
        client.subscribe(self.subscription)
        logger.info("Connected to %s:%s, subscribed to %s", self.broker, self.port, self.subscription)

    def on_disconnect(self, client, userdata, flags, reason_code, properties) -> None:
        self.connected = False
        logger.warning("MQTT disconnected: %s", reason_code)

    def on_message(self, client, userdata, msg) -> None:
        payload = msg.payload.decode("utf-8", errors="replace")
        with self._lock:
            self._messages[msg.topic].append(payload)

    def connect(self) -> None:
        """Connect in the background; paho retries until the broker is reachable."""
        self.client.connect_async(self.broker, self.port, keepalive=60)
        self.client.loop_start()

    def disconnect(self) -> None:
        self.client.disconnect()
        self.client.loop_stop()

    def publish(self, topic: str, payload: str) -> bool:
        info = self.client.publish(topic, payload, qos=1)
        return info.rc == mqtt.MQTT_ERR_SUCCESS

    def get_all_messages(self) -> dict[str, list[str]]:
        with self._lock:
            return {topic: list(messages) for topic, messages in self._messages.items()}

    def get_messages_by_topic(self, topic: str) -> list[str]:
        with self._lock:
            return list(self._messages.get(topic, ()))
