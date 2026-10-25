"""Cyclense - make sense of your cycle.  Run:  streamlit run app.py"""
from datetime import date
import pandas as pd
import streamlit as st

import engine, charts, report, sample, storage

st.set_page_config(page_title="Cyclense", page_icon="🌙", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 1.5rem; max-width: 1100px;}
.hero h1 {color:#5B2E91; margin-bottom:0}
.hero p {color:#6E5A8C; margin-top:0; font-size:1.05rem}
.card {border-radius:12px; padding:14px 16px; margin-bottom:12px; border-left:6px solid;}
.card h4 {margin:0 0 4px 0; font-size:1.05rem}
.card .tag {font-size:.75rem; font-weight:700; letter-spacing:.04em; text-transform:uppercase}
.card ul {margin:6px 0 0 0; padding-left:18px; font-size:.9rem}
.good {background:#EAF6EE; border-color:#2E8B57} .good .tag {color:#2E8B57}
.watch {background:#FFF5E0; border-color:#D98E04} .watch .tag {color:#B07300}
.doctor {background:#FDECEC; border-color:#C93C3C} .doctor .tag {color:#C93C3C}
</style>
""", unsafe_allow_html=True)

# ---------------- state ----------------
if "df" not in st.session_state:
    st.session_state.df = storage.load()
if "flash" not in st.session_state:
    st.session_state.flash = None


def commit(df):
    st.session_state.df = df.reset_index(drop=True)
    storage.save(st.session_state.df)


def add_entry():
    s = st.session_state
    start, end = s["f_start"], s["f_end"]
    if end < start:
        s.flash = ("error", "Period end date can't be before the start date.")
        return
    df = s.df
    existing = pd.to_datetime(df["start"]).dt.date.tolist() if len(df) else []
    if start in existing:
        s.flash = ("error", "You've already logged a period starting on that date.")
        return
    if any(abs((start - e).days) < 10 for e in existing):
        s.flash = ("warning", "Saved, but it's within 10 days of another entry. "
                              "Double-check the dates.")
    else:
        s.flash = ("success", "Period saved. Your insights have been updated.")
    row = dict(start=start, end=end, flow=s["f_flow"], pain=s["f_pain"], mood=s["f_mood"],
               symptoms=";".join(s["f_sym"]), notes=s["f_notes"])
    commit(pd.concat([df, pd.DataFrame([row])], ignore_index=True))


def delete_entry():
    idx = st.session_state.get("del_idx")
    if idx is not None and idx < len(st.session_state.df):
        d = engine.prepare(st.session_state.df)
        commit(d.drop(index=idx)[storage.COLUMNS])
        st.session_state.flash = ("success", "Entry deleted.")


def load_demo():
    commit(sample.build(st.session_state["demo_choice"]))
    st.session_state.flash = ("success", "Demo data loaded.")


def clear_all():
    commit(pd.DataFrame(columns=storage.COLUMNS))
    st.session_state.flash = ("success", "All data cleared.")


# ---------------- sidebar ----------------
with st.sidebar:
    st.header("🌙 Cyclense")
    st.caption("Make sense of your cycle.")
    st.subheader("Your profile")
    name = st.text_input("Name (for the report)", key="p_name")
    age = st.text_input("Age", key="p_age")
    st.divider()
    st.subheader("Demo data")
    st.selectbox("Sample profile", list(sample.PROFILES), key="demo_choice")
    st.button("Load demo data", on_click=load_demo, width="stretch")
    st.divider()
    if len(st.session_state.df):
        st.download_button("⬇ Export my data (CSV)",
                           st.session_state.df.to_csv(index=False),
                           "cyclense_data.csv", "text/csv", width="stretch")
        st.button("Clear all data", on_click=clear_all, width="stretch")
    st.info("Cyclense is a screening and awareness tool, **not a diagnosis**. "
            "Always consult a qualified doctor about health concerns.")

# ---------------- header ----------------
st.markdown('<div class="hero"><h1>🌙 Cyclense</h1>'
            '<p>Log your cycle. Spot warning patterns early. Take a clear summary to your doctor.</p>'
            '</div>', unsafe_allow_html=True)

if st.session_state.flash:
    kind, msg = st.session_state.flash
    getattr(st, kind)(msg)
    st.session_state.flash = None

df = st.session_state.df
d = engine.prepare(df)
a = engine.analyze(df)

tab_dash, tab_log, tab_ins, tab_rep = st.tabs(
    ["📊 Dashboard", "➕ Log a period", "💡 Insights", "📄 Doctor report"])

# ---------------- dashboard ----------------
with tab_dash:
    if a.n_periods == 0:
        st.info("No data yet. Use **Log a period** or load a sample profile from the sidebar.")
    else:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Average cycle", f"{a.avg_cycle} days" if a.avg_cycle else "—")
        c2.metric("Average period", f"{a.avg_period_days} days")
        c3.metric("Average pain", f"{a.avg_pain} / 10")
        c4.metric("Next period (est.)", f"{a.next_start:%d %b}" if a.next_start else "—")
        flagged = [i for i in a.insights if i.level != "good"]
        if flagged:
            st.warning(f"Cyclense found **{len(flagged)}** pattern(s) worth a look. "
                       "See the **Insights** tab.")
        else:
            st.success("No unusual patterns found in your logged data.")
        st.pyplot(charts.cycle_chart(d), width="stretch")
        l, r = st.columns(2)
        l.pyplot(charts.pain_chart(d), width="stretch")
        r.pyplot(charts.symptom_chart(a.symptom_counts), width="stretch")

# ---------------- log ----------------
with tab_log:
    st.subheader("Log a period")
    with st.form("log_form", clear_on_submit=False):
        c1, c2 = st.columns(2)
        c1.date_input("First day of period", value=date.today(), max_value=date.today(),
                      key="f_start")
        c2.date_input("Last day of period", value=date.today(), max_value=date.today(),
                      key="f_end")
        c3, c4 = st.columns(2)
        c3.radio("Flow", engine.FLOWS, index=1, horizontal=True, key="f_flow")
        c4.selectbox("Mood", engine.MOODS, index=1, key="f_mood")
        st.slider("Pain level (0 = none, 10 = worst imaginable)", 0, 10, 3, key="f_pain")
        st.multiselect("Symptoms you had", engine.SYMPTOMS, key="f_sym",
                       help="Pick everything that applies, even if it seems unrelated.")
        st.text_area("Notes (optional)", key="f_notes", height=70)
        st.form_submit_button("Save period", type="primary", on_click=add_entry)

    if len(d):
        st.subheader("Your entries")
        show = d[["start", "end", "cycle_length", "period_days", "flow", "pain", "mood"]].copy()
        show["symptoms"] = d["symptom_list"].apply(", ".join)
        show.columns = ["Start", "End", "Cycle (days)", "Period (days)", "Flow", "Pain",
                        "Mood", "Symptoms"]
        st.dataframe(show.iloc[::-1], width="stretch", hide_index=True)
        dc1, dc2 = st.columns([3, 1])
        dc1.selectbox("Delete an entry", options=list(d.index),
                      format_func=lambda i: f"{d.loc[i, 'start']:%d %b %Y}", key="del_idx")
        dc2.write("")
        dc2.write("")
        dc2.button("Delete", on_click=delete_entry)

# ---------------- insights ----------------
with tab_ins:
    st.subheader("What Cyclense noticed")
    st.caption("Every flag comes from a simple, transparent rule, shown under each card. "
               "No black-box AI.")
    for i in a.insights:
        ev = "".join(f"<li>{e}</li>" for e in i.evidence)
        st.markdown(
            f'<div class="card {i.level}"><span class="tag">{engine.LEVEL_LABEL[i.level]}</span>'
            f'<h4>{i.title}</h4><div>{i.message}</div>'
            f'{"<ul>" + ev + "</ul>" if ev else ""}</div>', unsafe_allow_html=True)
    with st.expander("How do these rules work?"):
        st.markdown(f"""
- **Cycle length** is counted from one period start to the next. Typical: **{engine.CYCLE_MIN}-{engine.CYCLE_MAX} days**.
- **Irregular**: 2+ of the last 6 cycles outside that range, or cycles varying by more than 7 days.
- **Prolonged period**: bleeding for more than **{engine.MAX_PERIOD_DAYS} days**.
- **Severe pain**: **{engine.SEVERE_PAIN}+/10** in 2 of the last 3 periods.
- **PCOS-type pattern**: irregular cycles + 2 or more of acne, excess hair, hair thinning, weight gain.
- **Anemia-type pattern**: heavy/long periods + 2 or more of fatigue, dizziness, pale skin, breathlessness.
- **Thyroid-type pattern**: irregular cycles + 3 or more of fatigue, weight gain, hair thinning, feeling cold.
- A symptom counts as *recurring* if it appears in at least 2 recent periods.
""")

# ---------------- report ----------------
with tab_rep:
    st.subheader("Doctor-ready summary")
    st.write("A one-page PDF with your cycle history, flagged patterns and suggested "
             "questions, so you don't have to remember everything in the appointment.")
    if a.n_periods == 0:
        st.info("Log at least one period to generate a report.")
    else:
        pdf = report.build_pdf(df, name, age)
        st.download_button("⬇ Download PDF report", pdf, "cyclense_report.pdf",
                           "application/pdf", type="primary")
        st.markdown("**Questions to ask your doctor**")
        for q in engine.doctor_questions(a):
            st.write("• " + q)
