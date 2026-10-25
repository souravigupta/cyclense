"""Demo profiles (synthetic data, generated relative to today)."""
from datetime import date, timedelta
import pandas as pd
from storage import COLUMNS

PROFILES = {
    "Irregular cycles (PCOS-like pattern)": dict(
        gaps=[34, 38, 41, 36, 44, 39], last_ago=20,
        pain=[5, 6, 8, 5, 7, 8, 7],
        flow=["Medium", "Heavy", "Medium", "Heavy", "Heavy", "Medium", "Heavy"],
        days=[5, 6, 5, 8, 8, 6, 8],
        mood=["Neutral", "Irritable", "Low / sad", "Anxious", "Low / sad", "Neutral", "Low / sad"],
        sym=[["Cramps", "Acne", "Fatigue"],
             ["Cramps", "Acne", "Excess facial/body hair", "Fatigue"],
             ["Acne", "Weight gain", "Fatigue", "Dizziness"],
             ["Cramps", "Excess facial/body hair", "Hair thinning", "Dizziness", "Fatigue"],
             ["Acne", "Weight gain", "Excess facial/body hair", "Fatigue", "Dizziness"],
             ["Cramps", "Acne", "Weight gain", "Fatigue"],
             ["Cramps", "Acne", "Excess facial/body hair", "Dizziness", "Fatigue"]]),
    "Typical cycles (healthy pattern)": dict(
        gaps=[28, 29, 27, 28, 30, 28], last_ago=14,
        pain=[3, 4, 3, 2, 4, 3, 3],
        flow=["Medium"] * 7, days=[5, 5, 4, 5, 5, 4, 5],
        mood=["Neutral", "Happy / calm", "Irritable", "Neutral", "Happy / calm", "Neutral", "Neutral"],
        sym=[["Cramps"], ["Bloating"], ["Cramps", "Bloating"], ["Cramps"], ["Breast tenderness"],
             ["Cramps", "Bloating"], ["Cramps"]]),
}


def build(name: str) -> pd.DataFrame:
    p = PROFILES[name]
    n = len(p["pain"])
    last = date.today() - timedelta(days=p["last_ago"])
    starts = [last]
    for g in reversed(p["gaps"]):
        starts.insert(0, starts[0] - timedelta(days=g))
    rows = []
    for i in range(n):
        rows.append(dict(start=starts[i], end=starts[i] + timedelta(days=p["days"][i] - 1),
                         flow=p["flow"][i], pain=p["pain"][i], mood=p["mood"][i],
                         symptoms=";".join(p["sym"][i]), notes=""))
    return pd.DataFrame(rows, columns=COLUMNS)
