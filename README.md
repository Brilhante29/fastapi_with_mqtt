# IoT Telemetry Gateway: MQTT over HTTP with FastAPI, plus a Temperature Model

A small FastAPI service that bridges HTTP and MQTT: publish messages to a Mosquitto broker, read buffered messages per topic, and predict sensor temperature with a scikit-learn model trained on a public IoT dataset. It also documents an evaluation pitfall: a random train/test split on time-series readings reports a **0.515 °C** MAE, while a chronological holdout shows **4.674 °C**.

[![ci](https://github.com/Brilhante29/fastapi_with_mqtt/actions/workflows/ci.yml/badge.svg)](https://github.com/Brilhante29/fastapi_with_mqtt/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Python 3.12](https://img.shields.io/badge/python-3.12-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white) ![MQTT](https://img.shields.io/badge/MQTT-660066?logo=mqtt&logoColor=white)

## Why this exists

IoT devices speak MQTT; dashboards, back offices, and ML services usually speak HTTP. This gateway lets HTTP clients publish to and read from a broker without an MQTT library, and serves a model next to the telemetry. It started as a 2023 study project and was rebuilt to production habits: pinned dependencies, the paho-mqtt 2 callback API, background reconnection, bounded buffers, input validation, tests, and a model trained reproducibly at build time instead of a binary committed to Git.

## Quickstart

```bash
docker compose -f docker/docker-compose.yaml up --build
```

Open the interactive API docs at [http://localhost:8000/docs](http://localhost:8000/docs), or use [`client.http`](client.http):

```bash
curl -s -X POST localhost:8000/publish -H 'Content-Type: application/json' \
  -d '{"topic": "sensors/room-admin/temperature", "payload": "29.5"}'
curl -s localhost:8000/messages/sensors/room-admin/temperature
curl -s -X POST localhost:8000/predict -H 'Content-Type: application/json' \
  -d '{"hour": 12, "day": 15, "month": 9, "year": 2018, "out_in": 1}'
```

Watch the broker directly: `docker compose -f docker/docker-compose.yaml exec mosquitto mosquitto_sub -t '#' -v`. Stop and remove only this project's containers and volume with `docker compose -f docker/docker-compose.yaml down -v`.

## API

| Method | Path | Behavior |
|---|---|---|
| `GET` | `/health` | Service status and whether the broker connection is up |
| `POST` | `/publish` | Publishes `{"topic", "payload"}` with QoS 1; `202`, or `503` if the broker is unavailable |
| `GET` | `/messages` | All buffered messages, grouped by topic |
| `GET` | `/messages/{topic}` | Messages of one topic (slashes allowed), or `404` |
| `POST` | `/predict` | Validated features (`hour`, `day`, `month`, `year`, `out_in`) to `{"prediction_celsius"}` |

The service subscribes to `MQTT_SUBSCRIPTION` (default `#`) and keeps the latest 1,000 messages per topic in memory.

## The model, and an honest evaluation

The dataset ([Temperature Readings: IoT Devices](https://www.kaggle.com/datasets/atulanandjha/temperature-readings-iot-devices), 97,606 readings from July to December 2018) has a timestamp, the reading, and whether the sensor is indoors or outdoors. [`src/train.py`](src/train.py) builds time features and fits a random forest.

| Evaluation | MAE |
|---|---:|
| Random 80/20 split (what the original notebook reported) | 0.515 °C |
| Chronological holdout: train on readings before 2018-10-23, test on the rest | 4.674 °C |

Neighbouring readings are nearly identical, so a random split puts almost the same sample in train and test; the chronological holdout is the number that predicts behaviour on future data. With only timestamp features, the model has no information about weather, which is the real driver of outdoor temperature. It is a deliberately simple baseline served for demonstration, not a forecasting product. The served model is refit on all readings during the Docker build.

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `MQTT_BROKER` | `localhost` (`mosquitto` in Compose) | Broker host |
| `MQTT_PORT` | `1883` | Broker port |
| `MQTT_SUBSCRIPTION` | `#` | Topic filter buffered by the gateway |
| `MODEL_PATH` | `src/models/temperature_model.joblib` | Trained model file |

## Development

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.lock -r requirements-dev.txt
python -m ruff check src tests
python -m pytest -q
(cd src && python train.py && MQTT_BROKER=localhost uvicorn main:app --reload)
```

The notebook in [`jupyter/notebooks/`](jupyter/notebooks/) holds the original exploration; install `requirements.lock` and `requirements-notebook.txt` to run it.

## Design decisions

| Decision | Why | Rejected |
|---|---|---|
| `create_app(mqtt, predictor)` factory | Tests replace the broker and the model without monkeypatching globals | Module-level singletons only |
| `connect_async` with automatic reconnection | The API starts even if the broker is still booting | Failing at startup |
| Bounded per-topic buffers | A chatty topic cannot exhaust memory | Unbounded lists |
| Train at build time | Reproducible artifact, nothing binary in Git, no scikit-learn pickle incompatibilities | Committing a 29 MB pickle |
| Broker and API bound to `127.0.0.1` | Anonymous MQTT is only acceptable locally | Exposing the demo broker |

## Limitations

- Messages are buffered in memory; restarts lose them, and multiple replicas would not share them.
- The broker allows anonymous clients (local use only); there is no API authentication.
- Timestamp-only features limit the model, as the chronological MAE shows.

## Project structure

```text
src/
  main.py                      FastAPI app factory and routes
  train.py                     training and evaluation script
  domain/                      request models and the prediction use case
  infra/mqtt/mqtt_client.py    paho-mqtt 2 client with bounded buffers
tests/                         API, MQTT client, and model tests
docker/                        Dockerfile, Compose file, Mosquitto configuration
data/dataset/IOT-temp.csv      public IoT temperature dataset
jupyter/notebooks/             exploratory notebook
```

## Related work

- [vision-serving-fastapi](https://github.com/Brilhante29/vision-serving-fastapi): a FastAPI model service that refuses to start on an unverified checkpoint.
- [observability-stack](https://github.com/Brilhante29/observability-stack): one HTTP incident traced across metrics, traces, and logs.
- [model-drift-detector](https://github.com/Brilhante29/model-drift-detector): monitoring a model after deployment.

## Author

**Guilherme Brilhante**, software engineer working on scalable backends and production AI.
[LinkedIn](https://www.linkedin.com/in/guilhermefreirebrilhanteseveriano/) · [GitHub](https://github.com/Brilhante29) · [Publications](https://dblp.org/pid/353/6812.html)

## License

Code: [MIT](LICENSE). The dataset is redistributed from Kaggle for demonstration; check its license on the source page before reuse.
