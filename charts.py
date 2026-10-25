"""Matplotlib charts, used both in the app and in the PDF report."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from engine import CYCLE_MIN, CYCLE_MAX

PURPLE, PINK, GREEN, RED, GREY = "#7B3FB5", "#E0457B", "#CFE8D5", "#D64545", "#8A7F96"


def cycle_chart(d, figsize=(7, 3)):
    cd = d.dropna(subset=["cycle_length"])
    fig, ax = plt.subplots(figsize=figsize)
    if cd.empty:
        ax.text(0.5, 0.5, "Log at least 2 periods to see cycle lengths",
                ha="center", va="center", color=GREY)
        ax.axis("off")
        return fig
    labels = [s.strftime("%d %b") for s in cd["start"]]
    vals = cd["cycle_length"].astype(int).tolist()
    ax.axhspan(CYCLE_MIN, CYCLE_MAX, color=GREEN, alpha=0.6, label="Typical range (21-35 days)")
    cols = [RED if (v < CYCLE_MIN or v > CYCLE_MAX) else PURPLE for v in vals]
    bars = ax.bar(labels, vals, color=cols, width=0.55)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.6, str(v), ha="center", fontsize=9)
    ax.set_ylabel("Days in cycle")
    ax.set_ylim(0, max(max(vals) + 8, 42))
    ax.set_title("Cycle length (days between period starts)", fontsize=11, loc="left")
    ax.legend(loc="upper left", fontsize=8, frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    plt.setp(ax.get_xticklabels(), fontsize=8)
    fig.tight_layout()
    return fig


def pain_chart(d, figsize=(4, 2.6)):
    fig, ax = plt.subplots(figsize=figsize)
    labels = [s.strftime("%d %b") for s in d["start"]]
    ax.plot(labels, d["pain"], marker="o", color=PINK, lw=2)
    ax.axhline(7, color=RED, ls="--", lw=1)
    ax.text(0, 7.25, "Severe (7+)", color=RED, fontsize=8)
    ax.set_ylim(0, 10.5)
    ax.set_ylabel("Pain (0-10)")
    ax.set_title("Pain level per period", fontsize=11, loc="left")
    ax.spines[["top", "right"]].set_visible(False)
    plt.setp(ax.get_xticklabels(), fontsize=7)
    fig.tight_layout()
    return fig


def symptom_chart(counts, figsize=(4, 2.6)):
    fig, ax = plt.subplots(figsize=figsize)
    items = list(counts.items())[:7][::-1]
    if not items:
        ax.text(0.5, 0.5, "No symptoms logged", ha="center", va="center", color=GREY)
        ax.axis("off")
        return fig
    ax.barh([k for k, _ in items], [v for _, v in items], color=PURPLE)
    ax.set_title("Most frequent symptoms (recent periods)", fontsize=11, loc="left")
    ax.xaxis.get_major_locator().set_params(integer=True)
    ax.spines[["top", "right"]].set_visible(False)
    plt.setp(ax.get_yticklabels(), fontsize=8)
    fig.tight_layout()
    return fig
