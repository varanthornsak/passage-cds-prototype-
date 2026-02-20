import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, Float, String, Boolean, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(page_title="PASSAGE Healthspan CDS", layout="wide")

# -----------------------------
# DATABASE
# -----------------------------
DATABASE_URL = "sqlite:///health.db"

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()

class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True)
    patient_name = Column(String)
    gait_speed = Column(Float)
    grip_strength = Column(Float)
    tug_time = Column(Float)
    moca_score = Column(Integer)
    phq9 = Column(Integer)
    gad7 = Column(Integer)
    sbp = Column(Float)
    hba1c = Column(Float)
    whoqol = Column(Float)
    healthspan_index = Column(Float)
    ai_confidence = Column(Float)
    consent = Column(Boolean)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(engine)

# -----------------------------
# SCORING ENGINE
# -----------------------------
def calculate_healthspan(data):
    score = 0
    score += min(data["gait_speed"] / 1.2, 1) * 15
    score += min(data["grip_strength"] / 35, 1) * 10
    score += (1 - min(data["tug_time"] / 20, 1)) * 10
    score += (data["moca_score"] / 30) * 15
    score += (1 - data["phq9"] / 27) * 10
    score += (1 - data["gad7"] / 21) * 5
    score += (1 - min(data["sbp"] / 180, 1)) * 10
    score += (1 - min(data["hba1c"] / 10, 1)) * 10
    score += (data["whoqol"] / 100) * 15
    return round(score, 2)

def calculate_confidence(data):
    filled = sum(1 for v in data.values() if v is not None)
    total = len(data)
    return round((filled / total) * 100, 2)

# -----------------------------
# UI
# -----------------------------
st.title("🧠 PASSAGE Healthspan Clinical Decision Support")

menu = st.sidebar.selectbox(
    "Navigation",
    ["New Assessment", "Population Dashboard", "User Guide"]
)

# -----------------------------
# NEW ASSESSMENT
# -----------------------------
if menu == "New Assessment":
    st.header("New Clinical Assessment")

    with st.form("assessment_form"):
        col1, col2 = st.columns(2)

        with col1:
            patient_name = st.text_input("Patient Name")
            gait_speed = st.number_input("Gait Speed (m/s)", 0.0, 3.0)
            grip_strength = st.number_input("Grip Strength (kg)", 0.0, 100.0)
            tug_time = st.number_input("TUG Time (sec)", 0.0, 60.0)
            moca_score = st.number_input("MoCA Score", 0, 30)

        with col2:
            phq9 = st.number_input("PHQ-9 Score", 0, 27)
            gad7 = st.number_input("GAD-7 Score", 0, 21)
            sbp = st.number_input("Systolic BP", 0.0, 250.0)
            hba1c = st.number_input("HbA1c (%)", 0.0, 15.0)
            whoqol = st.number_input("WHOQOL-OLD Score (0-100)", 0.0, 100.0)

        consent = st.checkbox("I consent to PDPA-compliant data processing")
        submitted = st.form_submit_button("Submit Assessment")

        if submitted:
            if not consent:
                st.warning("Consent required")
            else:
                data = {
                    "gait_speed": gait_speed,
                    "grip_strength": grip_strength,
                    "tug_time": tug_time,
                    "moca_score": moca_score,
                    "phq9": phq9,
                    "gad7": gad7,
                    "sbp": sbp,
                    "hba1c": hba1c,
                    "whoqol": whoqol,
                }

                healthspan = calculate_healthspan(data)
                confidence = calculate_confidence(data)

                record = Assessment(
                    patient_name=patient_name,
                    gait_speed=gait_speed,
                    grip_strength=grip_strength,
                    tug_time=tug_time,
                    moca_score=moca_score,
                    phq9=phq9,
                    gad7=gad7,
                    sbp=sbp,
                    hba1c=hba1c,
                    whoqol=whoqol,
                    healthspan_index=healthspan,
                    ai_confidence=confidence,
                    consent=True
                )

                session.add(record)
                session.commit()

                st.success("Assessment saved successfully")
                st.metric("Healthspan Index", healthspan)
                st.metric("AI Confidence (%)", confidence)

# -----------------------------
# DASHBOARD
# -----------------------------
if menu == "Population Dashboard":
    st.header("Population Health Dashboard")

    records = session.query(Assessment).all()

    if records:
        df = pd.DataFrame([{
            "Healthspan": r.healthspan_index,
            "Confidence": r.ai_confidence,
            "Date": r.created_at
        } for r in records])

        st.line_chart(df.set_index("Date")["Healthspan"])
        st.metric("Population Average", round(df["Healthspan"].mean(), 2))
        st.metric("Average AI Confidence", round(df["Confidence"].mean(), 2))
    else:
        st.info("No data available yet.")

# -----------------------------
# USER GUIDE PAGE
# -----------------------------
if menu == "User Guide":
    st.header("User Guide – Detailed Instructions")

    st.markdown("""
### Overview
PASSAGE Healthspan CDS integrates functional, cognitive, mental health, cardiometabolic,
and quality-of-life measures into a unified Healthspan Index.

### New Assessment
1. Enter patient name.
2. Input functional metrics (Gait Speed, Grip Strength, TUG).
3. Enter cognitive score (MoCA).
4. Enter mental health scores (PHQ-9, GAD-7).
5. Enter cardiometabolic indicators (SBP, HbA1c).
6. Enter WHOQOL-OLD score.
7. Confirm PDPA consent.
8. Click Submit.

### Healthspan Index
Composite score (0–100) derived from all domains.
Higher scores indicate better overall healthspan.

### AI Confidence
Represents percentage of completed input variables.
Does not represent predictive certainty.

### Population Dashboard
Displays:
- Time-series Healthspan trend
- Population average score
- Average confidence level

### Intended Use
This tool is designed for research, preventive screening,
and population health analytics. It is not a replacement
for physician clinical judgment.
""")
