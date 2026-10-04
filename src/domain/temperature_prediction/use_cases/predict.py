import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from domain.temperature_prediction.models.temperature import Temperature

FEATURES = ["hour", "day", "month", "year", "out/in"]
DEFAULT_MODEL_PATH = Path(__file__).resolve().parents[3] / "models" / "temperature_model.joblib"


@lru_cache(maxsize=1)
def load_model(path: str | None = None) -> Any:
    """Load the trained regressor once per process."""
    return joblib.load(path or os.environ.get("MODEL_PATH", str(DEFAULT_MODEL_PATH)))


def predict_temperature(features: Temperature, model: Any | None = None) -> float:
    """Predict the temperature in degrees Celsius for one reading."""
    estimator = model if model is not None else load_model()
    row = pd.DataFrame(
        [[features.hour, features.day, features.month, features.year, features.out_in]],
        columns=FEATURES,
    )
    return float(estimator.predict(row)[0])
