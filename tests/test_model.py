from pathlib import Path

import pandas as pd

from domain.temperature_prediction.models.temperature import Temperature
from domain.temperature_prediction.use_cases.predict import FEATURES, predict_temperature
from train import build_model, chronological_split, load_dataset

CSV = """id,room_id/id,noted_date,temp,out/in
c,Room Admin,08-12-2018 09:30,29,In
a,Room Admin,28-07-2018 07:06,31,Out
b,Room Admin,15-09-2018 13:00,33,Out
"""


def test_dataset_is_sorted_and_featurized(tmp_path: Path):
    path = tmp_path / "readings.csv"
    path.write_text(CSV)
    data = load_dataset(path)
    assert list(data["id"]) == ["a", "b", "c"]
    assert data.loc[0, ["hour", "day", "month", "year", "out/in"]].tolist() == [7, 28, 7, 2018, 1]


def test_chronological_split_keeps_the_latest_readings_for_testing(tmp_path: Path):
    path = tmp_path / "readings.csv"
    path.write_text(CSV)
    train, test = chronological_split(load_dataset(path), test_fraction=0.34)
    assert train["noted_date"].max() < test["noted_date"].min()


def test_prediction_uses_the_training_feature_names():
    frame = pd.DataFrame([[h, 1, 1, 2018, h % 2] for h in range(24)] * 5, columns=FEATURES).assign(
        temp=lambda df: 20 + df["out/in"] * 10
    )
    model = build_model().fit(frame[FEATURES], frame["temp"])
    outdoor = predict_temperature(Temperature(hour=3, day=1, month=1, year=2018, out_in=1), model)
    indoor = predict_temperature(Temperature(hour=4, day=1, month=1, year=2018, out_in=0), model)
    assert outdoor > indoor
