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
st.title("PASSAGE Healthspan Clinical Decision Support")

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
# ==========================================================
# PROFESSIONAL HEALTHSPAN UPGRADE MODULE
# Compatible with existing SQLAlchemy database
# ==========================================================

import plotly.express as px
from fpdf import FPDF
import tempfile

# ----------------------------------------------------------
# Healthspan Classification
# ----------------------------------------------------------
def classify_healthspan(score):
    if score >= 80:
        return "Optimal"
    elif score >= 60:
        return "Stable"
    elif score >= 40:
        return "Vulnerable"
    else:
        return "High Risk"

# ----------------------------------------------------------
# Add Classification to Dashboard
# ----------------------------------------------------------
if menu == "Population Dashboard":

    records = session.query(Assessment).all()

    if records:
        df = pd.DataFrame([{
            "Healthspan": r.healthspan_index,
            "Confidence": r.ai_confidence,
            "Date": r.created_at,
            "Category": classify_healthspan(r.healthspan_index)
        } for r in records])

        st.subheader("Healthspan Category Distribution")
        st.bar_chart(df["Category"].value_counts())

        st.subheader("Frailty vs Healthspan")
        fig = px.scatter(
            df,
            x="Confidence",
            y="Healthspan",
            color="Category",
            title="AI Confidence vs Healthspan Index"
        )
        st.plotly_chart(fig, use_container_width=True)

# ----------------------------------------------------------
# PDF Report for Latest Record
# ----------------------------------------------------------
if menu == "New Assessment":

    last_record = session.query(Assessment).order_by(Assessment.id.desc()).first()

    if last_record:

        st.markdown("### Generate Professional PDF Report")

        if st.button("Download Latest Report (PDF)"):

            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", "B", 16)
            pdf.cell(0, 10, "PASSAGE Healthspan Clinical Report", ln=True)

            pdf.set_font("Arial", "", 12)
            pdf.cell(0, 10, f"Patient: {last_record.patient_name}", ln=True)
            pdf.cell(0, 10, f"Date: {last_record.created_at}", ln=True)
            pdf.cell(0, 10, f"Healthspan Index: {last_record.healthspan_index}", ln=True)
            pdf.cell(0, 10, f"Classification: {classify_healthspan(last_record.healthspan_index)}", ln=True)
            pdf.cell(0, 10, f"AI Confidence: {last_record.ai_confidence}%", ln=True)

            pdf.ln(10)
            pdf.multi_cell(0, 8,
                "This report is generated by PASSAGE Healthspan CDS. "
                "This tool supports preventive screening and does not replace physician judgment."
            )

            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            pdf.output(temp_file.name)

            with open(temp_file.name, "rb") as f:
                st.download_button(
                    "Click to Download PDF",
                    f,
                    file_name="PASSAGE_Healthspan_Report.pdf",
                    mime="application/pdf"
                )

# ==========================================================
# ADVANCED AI RESEARCH MODULE – PASSAGE 2.0
# ==========================================================

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_curve, auc
import matplotlib.pyplot as plt

# ----------------------------------------------------------
# Institutional Header
# ----------------------------------------------------------
st.markdown("""
---
# PASSAGE 2.0 Clinical Decision Support System  
### Faculty of Medicine, Khon Kaen University  
Digital Health Innovation & Preventive Oncology Research Unit
---
""")

# ----------------------------------------------------------
# MACHINE LEARNING TRAINING
# ----------------------------------------------------------
def train_logistic_model(records):

    if len(records) < 10:
        return None, None, None

    df = pd.DataFrame([{
        "age": r.age,
        "raw_fish": int(r.raw_fish),
        "lft_abnormal": int(r.lft_abnormal),
        "red_flags": r.red_flags,
        "healthspan": r.healthspan_index,
        "target": 1 if r.cca_risk_level == "High Risk" else 0
    } for r in records])

    X = df[["age", "raw_fish", "lft_abnormal", "red_flags", "healthspan"]]
    y = df["target"]

    model = LogisticRegression()
    model.fit(X, y)

    y_prob = model.predict_proba(X)[:,1]

    fpr, tpr, _ = roc_curve(y, y_prob)
    roc_auc = auc(fpr, tpr)

    return model, (fpr, tpr, roc_auc), df


# ----------------------------------------------------------
# AI DASHBOARD EXTENSION
# ----------------------------------------------------------
if menu == "Population Dashboard":

    records = session.query(Assessment).all()

    model, roc_data, df = train_logistic_model(records)

    if model:

        st.subheader("Machine Learning Model – Logistic Regression")

        st.write("Model trained automatically on available database records.")

        fpr, tpr, roc_auc = roc_data

        fig = plt.figure()
        plt.plot(fpr, tpr, label=f"ROC curve (AUC = {roc_auc:.2f})")
        plt.plot([0,1], [0,1], linestyle='--')
        plt.xlabel("False Positive Rate")
        plt.ylabel("True Positive Rate")
        plt.title("ROC Curve – CCA Risk Prediction")
        plt.legend(loc="lower right")
        st.pyplot(fig)

        st.metric("Model AUC", round(roc_auc, 3))

    else:
        st.info("Need at least 10 records for ML training.")


# ----------------------------------------------------------
# INDIVIDUAL ML PREDICTION
# ----------------------------------------------------------
if menu == "New Assessment":

    records = session.query(Assessment).all()
    model, roc_data, df = train_logistic_model(records)

    latest = session.query(Assessment).order_by(Assessment.id.desc()).first()

    if model and latest:

        X_new = np.array([[
            latest.age,
            int(latest.raw_fish),
            int(latest.lft_abnormal),
            latest.red_flags,
            latest.healthspan_index
        ]])

        prob = model.predict_proba(X_new)[0][1]

        st.subheader("AI Predicted High-Risk Probability")
        st.metric("Predicted Probability", f"{prob*100:.2f} %")


# ----------------------------------------------------------
# AUTOMATIC RESEARCH REPORT EXPORT
# ----------------------------------------------------------
if menu == "Population Dashboard":

    if st.button("Generate Research Summary Report (PDF)"):

        records = session.query(Assessment).all()

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 14)

        pdf.cell(0, 10, "PASSAGE 2.0 Research Report", ln=True)
        pdf.cell(0, 10, "Khon Kaen University – Clinical AI Unit", ln=True)
        pdf.ln(5)

        pdf.set_font("Arial", "", 12)

        pdf.cell(0, 10, f"Total Records: {len(records)}", ln=True)

        if len(records) > 0:
            avg_healthspan = np.mean([r.healthspan_index for r in records])
            pdf.cell(0, 10, f"Average Healthspan Index: {avg_healthspan:.2f}", ln=True)

            high_risk = sum(1 for r in records if r.cca_risk_level == "High Risk")
            pdf.cell(0, 10, f"High Risk Cases: {high_risk}", ln=True)

        pdf.ln(10)
        pdf.multi_cell(0, 8,
            "This report summarizes AI-assisted screening performance "
            "and population health analytics. "
            "This system is intended for research and preventive screening."
        )

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        pdf.output(temp_file.name)

        with open(temp_file.name, "rb") as f:
            st.download_button(
                "Download Research Report",
                f,
                file_name="PASSAGE_Research_Report.pdf",
                mime="application/pdf"
            )
