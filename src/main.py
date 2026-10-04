from collections.abc import Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status

from domain.mqtt.models.message import Message
from domain.temperature_prediction.models.temperature import Temperature
from domain.temperature_prediction.use_cases.predict import predict_temperature
from infra.mqtt.mqtt_client import MQTTClientManager

Predictor = Callable[[Temperature], float]


def create_app(mqtt_manager: MQTTClientManager, predictor: Predictor = predict_temperature) -> FastAPI:
    """Build the API around an MQTT manager and a temperature predictor (both replaceable in tests)."""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        mqtt_manager.connect()
        yield
        mqtt_manager.disconnect()

    app = FastAPI(
        title="IoT Telemetry Gateway",
        description="Publish and read MQTT messages over HTTP, and predict sensor temperature.",
        version="2.0.0",
        lifespan=lifespan,
    )

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "mqtt_connected": mqtt_manager.connected}

    @app.post("/publish", status_code=status.HTTP_202_ACCEPTED)
    def publish_message(message: Message) -> dict:
        if not mqtt_manager.publish(message.topic, message.payload):
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "MQTT broker unavailable")
        return {"message": f"Message published to {message.topic}"}

    @app.get("/messages")
    def get_all_messages() -> dict[str, list[str]]:
        return mqtt_manager.get_all_messages()

    @app.get("/messages/{topic:path}")
    def get_messages_by_topic(topic: str) -> dict:
        messages = mqtt_manager.get_messages_by_topic(topic)
        if not messages:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "No messages found for this topic.")
        return {"topic": topic, "messages": messages}

    @app.post("/predict")
    def predict_endpoint(features: Temperature) -> dict:
        return {"prediction_celsius": round(predictor(features), 2)}

    return app


app = create_app(MQTTClientManager())
