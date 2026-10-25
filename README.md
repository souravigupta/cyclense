# 🌙 Cyclense: make sense of your cycle

> Built for **recHERsion 2026** (ACM-W, NITK Surathkal) · Problem Statement 1: Women's Healthcare

Many women wait years for a diagnosis of conditions like PCOS, thyroid disorders, endometriosis or anemia,
because symptoms are dismissed and nobody has clear data. **Cyclense** turns everyday period tracking into
something useful: it spots warning patterns early and produces a one-page summary a doctor can act on.

## How it works (end-to-end flow)
1. **Log**: period dates, flow, pain (0-10), mood and symptoms.
2. **Track**: dashboard shows cycle lengths vs the typical 21-35 day range, pain trend, frequent symptoms, next-period estimate.
3. **Understand**: a transparent **rule-based** engine flags patterns (irregular cycles, prolonged periods, recurring severe pain, PCOS-, anemia- and thyroid-type patterns, late period, mood changes) and shows the *evidence* behind every flag.
4. **Act**: download a **doctor-ready PDF** with stats, chart, flagged patterns and suggested questions to ask.

## Why rule-based (no AI/ML)?
Health screening needs to be **explainable and safe**. Every flag comes from a simple, published threshold that the user (and doctor) can see, and the app works offline with no API dependency. See `engine.py`.

| Rule | Trigger |
|---|---|
| Irregular cycles | 2+ of last 6 cycles outside 21-35 days, or spread > 7 days |
| Prolonged period | > 7 days of bleeding in 2+ periods |
| Severe pain | pain ≥ 7/10 in 2 of last 3 periods |
| PCOS-type pattern | irregular cycles + 2 or more of acne, excess hair, hair thinning, weight gain |
| Anemia-type pattern | heavy/long periods + 2 or more of fatigue, dizziness, pale skin, breathlessness |
| Thyroid-type pattern | irregular cycles + 3 or more of fatigue, weight gain, hair thinning, feeling cold |
| Late period | > avg cycle + 7 days (watch) / > 45 days (see doctor) |

> ⚠️ Cyclense is an awareness and screening tool, **not a medical diagnosis**.

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```
Open the sidebar → **Load demo data** to try the *Irregular cycles (PCOS-like)* or *Typical cycles* profile.

## Project structure
| File | Purpose |
|---|---|
| `app.py` | Streamlit UI (dashboard, logging, insights, report) |
| `engine.py` | Rule-based screening engine |
| `charts.py` | Matplotlib charts (app + PDF) |
| `report.py` | One-page doctor-ready PDF (fpdf2) |
| `sample.py` | Synthetic demo profiles |
| `storage.py` | CSV persistence (`data/logs.csv`) |

## Tech stack & credits
Python, [Streamlit](https://streamlit.io), pandas, Matplotlib, [fpdf2](https://github.com/py-pdf/fpdf2). All demo data is synthetic. Clinical thresholds follow commonly cited adult ranges (e.g. 21-35 day cycles); they are simplified for screening only.

## Privacy
Data stays in a local CSV on the device/server running the app. Users can export or clear all data from the sidebar.

## Future scope
Regional-language UI, reminders, wearable/BBT integration, clinician review mode, anonymised population insights for public-health teams.
