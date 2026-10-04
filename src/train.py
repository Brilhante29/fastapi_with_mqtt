"""Train the temperature regressor and report honest evaluation metrics.

Readings are a time series, so a random train/test split puts neighbouring readings on both sides
and flatters the model. This script reports that number for comparison, evaluates on a
chronological holdout (the latest 20% of readings), then fits the served model on all data.

Usage: python train.py [--data PATH] [--output PATH]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split

from domain.temperature_prediction.use_cases.predict import DEFAULT_MODEL_PATH, FEATURES

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "data" / "dataset" / "IOT-temp.csv"
SEED = 42


def load_dataset(path: Path) -> pd.DataFrame:
    data = pd.read_csv(path)
    data["noted_date"] = pd.to_datetime(data["noted_date"], format="%d-%m-%Y %H:%M")
    data = data.sort_values("noted_date", kind="stable").reset_index(drop=True)
    data["hour"] = data["noted_date"].dt.hour
    data["day"] = data["noted_date"].dt.day
    data["month"] = data["noted_date"].dt.month
    data["year"] = data["noted_date"].dt.year
    data["out/in"] = data["out/in"].map({"In": 0, "Out": 1})
    return data


def build_model() -> RandomForestRegressor:
    return RandomForestRegressor(n_estimators=100, min_samples_leaf=5, random_state=SEED, n_jobs=-1)


def chronological_split(data: pd.DataFrame, test_fraction: float = 0.2):
    cut = int(len(data) * (1 - test_fraction))
    return data.iloc[:cut], data.iloc[cut:]


def evaluate(data: pd.DataFrame) -> dict[str, float | int | str]:
    features, target = data[FEATURES], data["temp"]

    x_train, x_test, y_train, y_test = train_test_split(features, target, test_size=0.2, random_state=SEED)
    random_mae = mean_absolute_error(y_test, build_model().fit(x_train, y_train).predict(x_test))

    train, test = chronological_split(data)
    chrono_model = build_model().fit(train[FEATURES], train["temp"])
    chrono_mae = mean_absolute_error(test["temp"], chrono_model.predict(test[FEATURES]))

    return {
        "rows": len(data),
        "random_split_mae_celsius": round(float(random_mae), 3),
        "chronological_holdout_mae_celsius": round(float(chrono_mae), 3),
        "holdout_starts_at": str(test["noted_date"].iloc[0]),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--output", type=Path, default=DEFAULT_MODEL_PATH)
    args = parser.parse_args()

    data = load_dataset(args.data)
    print(json.dumps(evaluate(data), indent=2))

    model = build_model().fit(data[FEATURES], data["temp"])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, args.output, compress=3)
    print(f"model={args.output} size_bytes={args.output.stat().st_size}")


if __name__ == "__main__":
    main()
