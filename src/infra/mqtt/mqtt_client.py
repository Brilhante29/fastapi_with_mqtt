import paho.mqtt.client as mqtt
from collections import defaultdict

class MQTTClientManager:
    def __init__(self, broker='mosquitto', port=1883):
        self.broker = broker
        self.port = port
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        # Usando defaultdict para acumular mensagens em uma lista por tópico
        self.messages = defaultdict(list)

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connected successfully to MQTT broker.")
            # Subscrever a '#' significa que estamos ouvindo todos os tópicos
            self.client.subscribe("#")
        else:
            print(f"Failed to connect to MQTT broker, return code {rc}\n")

    def on_message(self, client, userdata, msg):
        print(f"Message received on {msg.topic}: {msg.payload.decode()}")
        # Acumula mensagens para o tópico
        self.messages[msg.topic].append(msg.payload.decode())

    def connect(self):
        self.client.connect(self.broker, self.port, 60)
        self.client.loop_start()

    def subscribe(self, topic):
        self.client.subscribe(topic)

    def publish(self, topic, payload):
        self.client.publish(topic, payload)

    def get_all_messages(self):
        return dict(self.messages)

    def get_messages_by_topic(self, topic):
        return self.messages[topic]