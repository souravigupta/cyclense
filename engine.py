"""Cyclense screening engine: transparent, rule-based (no AI / no ML).

Every flag comes from a simple, explainable threshold so users and doctors
can see exactly WHY something was flagged.
"""
from dataclasses import dataclass, field
from datetime import date, timedelta
import pandas as pd

SYMPTOMS = [
    "Cramps", "Bloating", "Fatigue", "Headache", "Acne", "Excess facial/body hair",
    "Hair thinning", "Weight gain", "Dizziness", "Pale skin", "Shortness of breath",
    "Feeling unusually cold", "Pain during intercourse", "Pelvic pain between periods",
    "Bowel/urinary pain during period", "Breast tenderness", "Nausea",
]
FLOWS = ["Light", "Medium", "Heavy"]
MOODS = ["Happy / calm", "Neutral", "Irritable", "Anxious", "Low / sad"]

# Symptom groups used by the rules
PCOS_SIGNS = {"Acne", "Excess facial/body hair", "Hair thinning", "Weight gain"}
ANEMIA_SIGNS = {"Fatigue", "Dizziness", "Pale skin", "Shortness of breath"}
THYROID_SIGNS = {"Fatigue", "Weight gain", "Hair thinning", "Feeling unusually cold"}
ENDO_SIGNS = {"Pain during intercourse", "Pelvic pain between periods",
              "Bowel/urinary pain during period"}

# Thresholds (commonly cited ranges for adults)
CYCLE_MIN, CYCLE_MAX = 21, 35      # days between period starts
MAX_PERIOD_DAYS = 7                # bleeding longer than this is "prolonged"
SEVERE_PAIN = 7                    # on a 0-10 scale

LEVEL_LABEL = {
    "good": "Looks typical",
    "watch": "Keep an eye on this",
    "doctor": "Worth discussing with a doctor",
}


@dataclass
class Insight:
    level: str            # good | watch | doctor
    title: str
    message: str
    evidence: list = field(default_factory=list)


@dataclass
class Analysis:
    n_periods: int
    cycle_lengths: list
    avg_cycle: float | None
    min_cycle: int | None
    max_cycle: int | None
    avg_period_days: float | None
    avg_pain: float | None
    last_start: date | None
    next_start: date | None
    days_since_last: int | None
    symptom_counts: dict
    insights: list


def prepare(df: pd.DataFrame) -> pd.DataFrame:
    """Sort, parse dates and add cycle_length + period_days columns."""
    if df.empty:
        return df.assign(cycle_length=pd.Series(dtype="float"),
                         period_days=pd.Series(dtype="int"))
    d = df.copy()
    d["start"] = pd.to_datetime(d["start"]).dt.date
    d["end"] = pd.to_datetime(d["end"]).dt.date
    d = d.sort_values("start").reset_index(drop=True)
    starts = pd.to_datetime(d["start"])
    d["cycle_length"] = starts.diff().dt.days          # NaN for first row
    d["period_days"] = [(e - s).days + 1 for s, e in zip(d["start"], d["end"])]
    d["symptom_list"] = d["symptoms"].fillna("").apply(
        lambda s: [x for x in str(s).split(";") if x])
    return d


def _recurring(recent: pd.DataFrame) -> dict:
    """Symptoms that show up in at least 2 of the recent periods."""
    counts: dict = {}
    for lst in recent["symptom_list"]:
        for s in set(lst):
            counts[s] = counts.get(s, 0) + 1
    need = min(2, len(recent))
    return {s: c for s, c in counts.items() if c >= need}


def analyze(df: pd.DataFrame, today: date | None = None) -> Analysis:
    today = today or date.today()
    d = prepare(df)
    n = len(d)
    if n == 0:
        return Analysis(0, [], None, None, None, None, None, None, None, None, {},
                        [Insight("watch", "No data yet",
                                 "Log your first period to start seeing insights.")])

    recent = d.tail(6)
    cycles = [int(c) for c in recent["cycle_length"].dropna()]
    avg_cycle = round(sum(cycles) / len(cycles), 1) if cycles else None
    last_start = d["start"].iloc[-1]
    days_since = (today - last_start).days
    next_start = None
    if cycles:
        next_start = last_start + timedelta(days=round(sum(cycles[-3:]) / len(cycles[-3:])))

    all_counts: dict = {}
    for lst in recent["symptom_list"]:
        for s in lst:
            all_counts[s] = all_counts.get(s, 0) + 1
    recurring = _recurring(recent)

    ins: list[Insight] = []

    # ---- Rule 1: cycle regularity ------------------------------------
    irregular = False
    if len(cycles) < 2:
        ins.append(Insight("watch", "Need a bit more data",
                           "Log at least 3 periods so Cyclense can judge your cycle "
                           "regularity."))
    else:
        short = [c for c in cycles if c < CYCLE_MIN]
        long_ = [c for c in cycles if c > CYCLE_MAX]
        out = short + long_
        spread = max(cycles) - min(cycles)
        ev = [f"Last {len(cycles)} cycle lengths: {', '.join(map(str, cycles))} days",
              f"Typical range is {CYCLE_MIN}-{CYCLE_MAX} days"]
        if len(out) >= 2:
            irregular = True
            kind = ("longer than 35 days" if long_ and not short else
                    "shorter than 21 days" if short and not long_ else
                    "outside the typical 21-35 day range")
            ins.append(Insight("doctor", "Irregular cycles",
                               f"{len(out)} of your last {len(cycles)} cycles were {kind}. "
                               "Repeated irregular cycles are worth checking with a doctor.",
                               ev))
        elif len(out) == 1:
            irregular = True
            ins.append(Insight("watch", "One cycle outside the typical range",
                               "One recent cycle was outside 21-35 days. One-off changes "
                               "are common (stress, illness, travel), but keep tracking.",
                               ev))
        elif spread > 7:
            irregular = True
            ins.append(Insight("watch", "Cycle length varies a lot",
                               f"Your cycles differ by {spread} days. Variation of more "
                               "than about 7 days can be worth mentioning to a doctor.",
                               ev))
        else:
            ins.append(Insight("good", "Regular cycles",
                               f"Your cycles are consistent (average {avg_cycle} days).",
                               ev))

    # ---- Rule 2: late / missed period --------------------------------
    if days_since > 45:
        ins.append(Insight("doctor", "No period for over 45 days",
                           "It has been a long time since your last period. If you are "
                           "not pregnant, this is worth discussing with a doctor.",
                           [f"Last period started {last_start:%d %b %Y} "
                            f"({days_since} days ago)"]))
    elif avg_cycle and days_since > avg_cycle + 7:
        ins.append(Insight("watch", "Period may be late",
                           f"Your period is about {days_since - round(avg_cycle)} days "
                           "later than your usual pattern.",
                           [f"Last period started {days_since} days ago; your average "
                            f"cycle is {avg_cycle} days"]))

    # ---- Rule 3: prolonged bleeding ----------------------------------
    long_periods = recent[recent["period_days"] > MAX_PERIOD_DAYS]
    if len(long_periods) >= 2:
        ins.append(Insight("doctor", "Prolonged periods",
                           "Several periods lasted more than 7 days.",
                           [f"{len(long_periods)} of your last {len(recent)} periods "
                            f"lasted over {MAX_PERIOD_DAYS} days"]))
    elif len(long_periods) == 1:
        ins.append(Insight("watch", "One long period",
                           "One recent period lasted more than 7 days. Keep tracking.",
                           []))

    # ---- Rule 4: severe / recurring pain -----------------------------
    last3 = d.tail(3)
    severe = int((last3["pain"] >= SEVERE_PAIN).sum())
    endo = sorted(ENDO_SIGNS & set(recurring))
    if severe >= 2:
        ev = [f"Pain of {SEVERE_PAIN}+/10 in {severe} of your last {len(last3)} periods"]
        msg = ("Recurring severe period pain is not something you have to just "
               "put up with, and it is worth discussing with a doctor.")
        if endo:
            ev.append("Also recurring: " + ", ".join(endo))
            msg += (" Severe pain together with these symptoms is a pattern doctors "
                    "look at when checking for conditions such as endometriosis.")
        ins.append(Insight("doctor", "Recurring severe pain", msg, ev))
    elif severe == 1:
        ins.append(Insight("watch", "Severe pain once recently",
                           "One recent period had severe pain. If it repeats, "
                           "mention it to a doctor.",
                           [f"Pain {int(last3['pain'].max())}/10"]))

    # ---- Rule 5: PCOS-type pattern -----------------------------------
    pcos = sorted(PCOS_SIGNS & set(recurring))
    if irregular and len(pcos) >= 2:
        ins.append(Insight("doctor", "Pattern sometimes seen with PCOS",
                           "Irregular cycles together with these recurring signs can be "
                           "associated with PCOS (polycystic ovary syndrome). This is not "
                           "a diagnosis, but a doctor can check with simple tests.",
                           ["Irregular cycles", "Recurring: " + ", ".join(pcos)]))
    elif irregular and len(pcos) == 1:
        ins.append(Insight("watch", "Possible hormonal sign",
                           f"Irregular cycles plus recurring '{pcos[0]}'. Keep tracking "
                           "and mention it at your next check-up.",
                           ["Irregular cycles", "Recurring: " + pcos[0]]))

    # ---- Rule 6: anemia-type pattern ---------------------------------
    heavy = int((recent["flow"] == "Heavy").sum())
    anemia = sorted(ANEMIA_SIGNS & set(recurring))
    heavy_pattern = heavy >= 2 or len(long_periods) >= 2
    if heavy_pattern and len(anemia) >= 2:
        ins.append(Insight("doctor", "Pattern sometimes seen with anemia",
                           "Heavy or long bleeding with tiredness-type symptoms can be "
                           "associated with low iron or anemia. A simple blood test "
                           "can check this.",
                           [f"Heavy flow in {heavy} of last {len(recent)} periods",
                            "Recurring: " + ", ".join(anemia)]))
    elif heavy_pattern and len(anemia) == 1:
        ins.append(Insight("watch", "Heavy flow with tiredness",
                           f"Heavy bleeding with recurring '{anemia[0]}'. Consider asking "
                           "about an iron check.",
                           [f"Heavy flow in {heavy} of last {len(recent)} periods"]))

    # ---- Rule 7: thyroid-type pattern --------------------------------
    thy = sorted(THYROID_SIGNS & set(recurring))
    if irregular and len(thy) >= 3:
        ins.append(Insight("watch", "Pattern sometimes seen with thyroid issues",
                           "Irregular cycles with several of these symptoms can be linked "
                           "to the thyroid. A basic thyroid blood test is common and "
                           "inexpensive.",
                           ["Recurring: " + ", ".join(thy)]))

    # ---- Rule 8: mood -------------------------------------------------
    low = int(recent["mood"].isin(["Low / sad", "Anxious"]).sum())
    if low >= 3:
        ins.append(Insight("watch", "Mood changes around your period",
                           "Low or anxious mood showed up in several periods. If it "
                           "affects daily life, talking to a doctor or counsellor helps.",
                           [f"Low/anxious mood in {low} of last {len(recent)} periods"]))

    order = {"doctor": 0, "watch": 1, "good": 2}
    ins.sort(key=lambda i: order[i.level])

    return Analysis(
        n_periods=n, cycle_lengths=cycles, avg_cycle=avg_cycle,
        min_cycle=min(cycles) if cycles else None,
        max_cycle=max(cycles) if cycles else None,
        avg_period_days=round(float(recent["period_days"].mean()), 1),
        avg_pain=round(float(recent["pain"].mean()), 1),
        last_start=last_start, next_start=next_start, days_since_last=days_since,
        symptom_counts=dict(sorted(all_counts.items(), key=lambda x: -x[1])),
        insights=ins,
    )


def doctor_questions(a: Analysis) -> list:
    """Suggested questions to ask, based on flagged patterns."""
    q = []
    titles = " ".join(i.title for i in a.insights if i.level != "good").lower()
    if "irregular" in titles or "varies" in titles or "late" in titles or "45" in titles:
        q.append("Why might my cycles be irregular, and which tests would help?")
    if "pcos" in titles:
        q.append("Should I be checked for PCOS (hormone tests, ultrasound)?")
    if "anemia" in titles or "heavy" in titles or "prolonged" in titles:
        q.append("Can I get my iron / haemoglobin levels checked?")
    if "pain" in titles:
        q.append("What could be causing my severe period pain, and how can it be managed?")
    if "thyroid" in titles:
        q.append("Should I have a thyroid function test?")
    if "mood" in titles:
        q.append("Could my mood changes be linked to my cycle? What support is available?")
    if not q:
        q.append("Is there anything in my cycle history I should keep an eye on?")
    return q
