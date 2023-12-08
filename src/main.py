from fastapi import FastAPI, HTTPException, BackgroundTasks
from domain.models.message import Message
from domain.models.topic_data import TopicData
from infra.mqtt.mqtt_client import MQTTClientManager

app = FastAPI()
mqtt_manager = MQTTClientManager()

@app.on_event("startup")
async def startup_event():
    mqtt_manager.connect()

@app.post("/publish")
async def publish_message(topic_data: TopicData, message: Message):
    mqtt_manager.publish(topic_data.topic, message.payload)
    return {"message": f"Message published to {topic_data.topic}"}

@app.get("/messages/all")
def get_all_messages():
    return mqtt_manager.get_all_messages()

@app.get("/messages/{topic_name}")
def get_messages_by_topic(topic_name: str):
    messages = mqtt_manager.get_messages_by_topic(topic_name)
    if messages:
        return {"topic": topic_name, "messages": messages}
    raise HTTPException(status_code=404, detail="No messages found for this topic.")