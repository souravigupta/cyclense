"""Tiny CSV persistence layer."""
import os
import pandas as pd

COLUMNS = ["start", "end", "flow", "pain", "mood", "symptoms", "notes"]
PATH = os.path.join(os.path.dirname(__file__), "data", "logs.csv")


def load() -> pd.DataFrame:
    if os.path.exists(PATH):
        try:
            df = pd.read_csv(PATH)
            for c in COLUMNS:
                if c not in df.columns:
                    df[c] = ""
            return df[COLUMNS]
        except Exception:
            pass
    return pd.DataFrame(columns=COLUMNS)


def save(df: pd.DataFrame) -> None:
    os.makedirs(os.path.dirname(PATH), exist_ok=True)
    df[COLUMNS].to_csv(PATH, index=False)
