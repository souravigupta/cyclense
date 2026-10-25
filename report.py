"""One-page, doctor-ready PDF summary."""
import io
from datetime import date
from fpdf import FPDF
import engine
import charts

PURPLE = (91, 46, 145)
LEVEL_COL = {"doctor": (200, 50, 50), "watch": (200, 130, 0), "good": (40, 140, 80)}
LEVEL_TAG = {"doctor": "DISCUSS WITH DOCTOR", "watch": "KEEP AN EYE", "good": "TYPICAL"}


def _t(s) -> str:
    """fpdf core fonts are latin-1 only."""
    return str(s).replace("\u2013", "-").replace("\u2014", "-").replace("\u2019", "'") \
        .encode("latin-1", "replace").decode("latin-1")


def build_pdf(df, name="", age="", today: date | None = None) -> bytes:
    today = today or date.today()
    d = engine.prepare(df)
    a = engine.analyze(df, today)

    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.set_margins(12, 10, 12)
    pdf.add_page()

    # Header
    pdf.set_fill_color(*PURPLE)
    pdf.rect(0, 0, 210, 20, "F")
    pdf.set_xy(12, 5)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(100, 8, "Cyclense - Cycle Health Summary")
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 8, _t(f"Generated {today:%d %b %Y}"), align="R")
    pdf.set_xy(12, 24)
    pdf.set_text_color(40, 30, 60)
    pdf.set_font("Helvetica", "", 10)
    who = f"Patient: {name or '-'}    Age: {age or '-'}    Periods logged: {a.n_periods}"
    pdf.cell(0, 6, _t(who), new_x="LMARGIN", new_y="NEXT")

    # Key stats
    pdf.ln(1)
    stats = [("Avg cycle", f"{a.avg_cycle} d" if a.avg_cycle else "-"),
             ("Shortest / longest", f"{a.min_cycle} / {a.max_cycle} d" if a.cycle_lengths else "-"),
             ("Avg period length", f"{a.avg_period_days} d"),
             ("Avg pain", f"{a.avg_pain} / 10"),
             ("Last period", f"{a.last_start:%d %b %Y}")]
    w = (210 - 24) / len(stats)
    y0 = pdf.get_y()
    for i, (k, v) in enumerate(stats):
        pdf.set_xy(12 + i * w, y0)
        pdf.set_fill_color(245, 239, 250)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(110, 90, 140)
        pdf.cell(w - 2, 5, _t(k), fill=True, new_x="LEFT", new_y="NEXT")
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(40, 30, 60)
        pdf.cell(w - 2, 7, _t(v), fill=True)
    pdf.set_y(y0 + 14)

    # Chart
    fig = charts.cycle_chart(d, figsize=(7.2, 2.4))
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150)
    charts.plt.close(fig)
    buf.seek(0)
    pdf.image(buf, x=12, w=186)
    pdf.ln(1)

    # Flagged patterns
    def heading(txt):
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(*PURPLE)
        pdf.cell(0, 6, _t(txt), new_x="LMARGIN", new_y="NEXT")

    heading("Patterns found by Cyclense")
    for ins in a.insights:
        col = LEVEL_COL[ins.level]
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*col)
        pdf.cell(42, 5, _t(LEVEL_TAG[ins.level]))
        pdf.set_text_color(40, 30, 60)
        pdf.cell(0, 5, _t(ins.title), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 8.5)
        pdf.set_text_color(70, 60, 90)
        for e in ins.evidence:
            pdf.set_x(54)
            pdf.multi_cell(0, 4, _t("- " + e), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)

    # Log table (last 6)
    heading("Recent period log")
    cols = [("Start", 24), ("Cycle", 14), ("Days", 12), ("Flow", 18), ("Pain", 12),
            ("Mood", 28), ("Symptoms", 78)]
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(235, 225, 245)
    pdf.set_text_color(40, 30, 60)
    for n, wd in cols:
        pdf.cell(wd, 5, n, border=0, fill=True)
    pdf.ln(5)
    pdf.set_font("Helvetica", "", 8)
    for _, r in d.tail(6).iloc[::-1].iterrows():
        cl = "-" if r["cycle_length"] != r["cycle_length"] else str(int(r["cycle_length"]))
        sy = ", ".join(r["symptom_list"])
        if len(sy) > 52:
            sy = sy[:50] + ".."
        vals = [f"{r['start']:%d %b %y}", cl, str(r["period_days"]), r["flow"],
                f"{int(r['pain'])}/10", r["mood"], sy]
        for (n, wd), v in zip(cols, vals):
            pdf.cell(wd, 4.6, _t(v))
        pdf.ln(4.6)
    pdf.ln(2)

    # Questions
    heading("Suggested questions for the doctor")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(40, 30, 60)
    for q in engine.doctor_questions(a):
        pdf.multi_cell(0, 4.8, _t("- " + q), new_x="LMARGIN", new_y="NEXT")

    # Disclaimer
    pdf.ln(2)
    pdf.set_font("Helvetica", "I", 7.5)
    pdf.set_text_color(120, 110, 135)
    pdf.multi_cell(0, 3.8, _t(
        "Cyclense is a self-tracking and awareness tool. It uses simple rule-based checks on "
        "data entered by the user and does NOT provide a medical diagnosis. This summary is "
        "meant to help start a conversation with a qualified healthcare professional."))
    return bytes(pdf.output())
