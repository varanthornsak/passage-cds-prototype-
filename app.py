# ==========================================================
# PASSAGE – Clinical CCA Screening Platform
# Institutional Professional Version
# ==========================================================

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, Float, String, Boolean, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

# ==========================================================
# CONFIG
# ==========================================================

st.set_page_config(
    page_title="PASSAGE Clinical Platform",
    layout="wide"
)

st.title("PASSAGE – Cholangiocarcinoma (CCA) Screening Platform")
st.caption("Clinical Decision Support System | Institutional Version")

# ==========================================================
# DATABASE
# ==========================================================

DATABASE_URL = "sqlite:///passage_clinical.db"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()

class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True)
    patient_name = Column(String)
    age = Column(Integer)

    raw_fish = Column(Boolean)
    lft_abnormal = Column(Boolean)
    red_flags = Column(Integer)

    ca19_9 = Column(Float)
    cea = Column(Float)
    alp = Column(Float)
    bilirubin = Column(Float)

    risk_level = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(engine)

# ==========================================================
# RISK ENGINE
# ==========================================================

def calculate_risk(age, raw_fish, lft_abnormal, red_flags, ca19_9):

    score = 0
    score += age * 0.03
    score += 2 if raw_fish else 0
    score += 2 if lft_abnormal else 0
    score += red_flags * 1.5
    score += 3 if ca19_9 > 100 else 0

    if score >= 10:
        return "High Risk"
    elif score >= 6:
        return "Moderate Risk"
    else:
        return "Low Risk"

# ==========================================================
# NAVIGATION
# ==========================================================

menu = st.sidebar.selectbox(
    "Navigation",
    ["New Screening", "Dashboard", "Clinical Interpretation Guide"]
)

# ==========================================================
# NEW SCREENING
# ==========================================================

if menu == "New Screening":

    st.header("New CCA Risk Assessment")

    with st.form("screening_form"):

        col1, col2 = st.columns(2)

        with col1:
            patient_name = st.text_input("Patient Name")
            age = st.number_input("Age", 20, 100)
            raw_fish = st.checkbox("History of Raw Fish Consumption")
            lft_abnormal = st.checkbox("Abnormal Liver Function Test")
            red_flags = st.slider(
                "Red Flag Symptoms (0–5)",
                0, 5,
                help="Jaundice, Weight loss, RUQ pain, Anorexia, Cholangitis"
            )

        with col2:
            ca19_9 = st.number_input("CA19-9 (U/mL)", 0.0)
            cea = st.number_input("CEA (ng/mL)", 0.0)
            alp = st.number_input("ALP (U/L)", 0.0)
            bilirubin = st.number_input("Total Bilirubin (mg/dL)", 0.0)

        submit = st.form_submit_button("Evaluate Risk")

        if submit:

            risk_level = calculate_risk(
                age, raw_fish, lft_abnormal, red_flags, ca19_9
            )

            record = Assessment(
                patient_name=patient_name,
                age=age,
                raw_fish=raw_fish,
                lft_abnormal=lft_abnormal,
                red_flags=red_flags,
                ca19_9=ca19_9,
                cea=cea,
                alp=alp,
                bilirubin=bilirubin,
                risk_level=risk_level
            )

            session.add(record)
            session.commit()

            st.success("Assessment Saved")

            if risk_level == "High Risk":
                st.error("High Risk – Recommend urgent hepatobiliary evaluation")
            elif risk_level == "Moderate Risk":
                st.warning("Moderate Risk – Recommend ultrasound within 3 months")
            else:
                st.success("Low Risk – Routine annual follow-up")

# ==========================================================
# DASHBOARD
# ==========================================================

if menu == "Dashboard":

    st.header("Institutional Dashboard")

    records = session.query(Assessment).all()

    if len(records) == 0:
        st.info("No screening data available.")
    else:

        df = pd.DataFrame([{
            "risk": r.risk_level
        } for r in records])

        col1, col2, col3 = st.columns(3)

        col1.metric("Total Screenings", len(df))
        col2.metric("High Risk %",
                    round((df["risk"]=="High Risk").mean()*100,1))
        col3.metric("Moderate Risk %",
                    round((df["risk"]=="Moderate Risk").mean()*100,1))

        st.bar_chart(df["risk"].value_counts())

# ==========================================================
# CLINICAL INTERPRETATION GUIDE
# ==========================================================

if menu == "Clinical Interpretation Guide":

    st.header("Clinical Interpretation & Reference Guide")

    st.subheader("Tumor Markers")

    marker_table = pd.DataFrame({
        "Marker": ["CA19-9", "CEA", "ALP", "Total Bilirubin"],
        "Normal Range": ["< 37 U/mL", "< 5 ng/mL", "44–147 U/L", "0.1–1.2 mg/dL"],
        "Interpretation": [
            "Elevated in cholangiocarcinoma; >100 U/mL increases suspicion",
            "Non-specific tumor marker; may elevate in GI malignancy",
            "Elevated in biliary obstruction",
            "Elevated in obstructive jaundice"
        ]
    })

    st.table(marker_table)

    st.subheader("Red Flag Symptoms")

    symptom_table = pd.DataFrame({
        "Symptom": [
            "Jaundice",
            "Unintentional Weight Loss",
            "Right Upper Quadrant Pain",
            "Anorexia",
            "Recurrent Cholangitis"
        ],
        "Clinical Concern": [
            "Suggests biliary obstruction",
            "Possible malignancy",
            "Hepatobiliary pathology",
            "Systemic disease indicator",
            "Chronic biliary disease"
        ]
    })

    st.table(symptom_table)

    st.subheader("Risk Interpretation")

    risk_table = pd.DataFrame({
        "Risk Level": ["Low", "Moderate", "High"],
        "Clinical Recommendation": [
            "Routine follow-up annually",
            "Ultrasound within 3 months",
            "Urgent hepatobiliary referral"
        ]
    })

    st.table(risk_table)

st.markdown("---")
st.caption("PASSAGE Clinical Platform | Institutional-Ready Version")
