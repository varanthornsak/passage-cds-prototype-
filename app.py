import streamlit as st
import pandas as pd
import uuid
from datetime import datetime

# --------------------------------------------------
# Page Configuration
# --------------------------------------------------
st.set_page_config(
    page_title="PASSAGE-CDS | CCA Risk Stratification",
    page_icon="🩺",
    layout="wide"
)

# --------------------------------------------------
# Session State Initialization
# --------------------------------------------------
if "registry" not in st.session_state:
    st.session_state.registry = []

# --------------------------------------------------
# Risk Calculation Logic (Clinical Layer)
# --------------------------------------------------
def calculate_cca_risk(age, raw_fish, lft_abnormal, red_flags, frailty_score):
    score = 0

    if age >= 40:
        score += 1
    if raw_fish:
        score += 2
    if lft_abnormal:
        score += 2
    if red_flags >= 2:
        score += 3
    if frailty_score >= 2:
        score += 1

    if score >= 6:
        return "High Risk"
    elif score >= 3:
        return "Moderate Risk"
    else:
        return "Low Risk"

# --------------------------------------------------
# Sidebar Navigation
# --------------------------------------------------
st.sidebar.title("PASSAGE-CDS")
page = st.sidebar.radio(
    "Navigation",
    ["Home", "New Assessment", "Patient Registry", "Analytics Dashboard", "About"]
)

# --------------------------------------------------
# Global Clinical Disclaimer
# --------------------------------------------------
st.sidebar.warning(
    "Clinical Decision Support Prototype.\n"
    "Not a replacement for physician diagnosis or imaging confirmation."
)

# --------------------------------------------------
# HOME PAGE
# --------------------------------------------------
if page == "Home":

    st.title("PASSAGE-CDS")
    st.subheader("Cholangiocarcinoma Risk Stratification & Functional Screening")

    st.markdown("""
    PASSAGE-CDS integrates:
    - Epidemiologic risk factors
    - Symptom-based red flags
    - Liver function indicators
    - Functional frailty markers
    
    Purpose:
    Enhance early referral for hepatobiliary imaging.
    """)

    st.info("Designed for research and pilot clinical deployment (2026).")

# --------------------------------------------------
# NEW ASSESSMENT PAGE
# --------------------------------------------------
elif page == "New Assessment":

    st.title("New Patient Assessment")

    col1, col2 = st.columns(2)

    with col1:
        age = st.number_input("Age", 18, 100)
        raw_fish = st.checkbox("History of raw fish consumption")
        lft_abnormal = st.checkbox("Abnormal Liver Function Test")
    
    with col2:
        red_flags = st.slider("Number of Red Flag Symptoms", 0, 5)
        frailty_score = st.slider("Frailty Indicators (0–3)", 0, 3)

    if st.button("Calculate Risk"):

        risk_level = calculate_cca_risk(
            age, raw_fish, lft_abnormal, red_flags, frailty_score
        )

        patient_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

        record = {
            "Patient ID": patient_id,
            "Timestamp": timestamp,
            "Age": age,
            "Raw Fish": raw_fish,
            "LFT Abnormal": lft_abnormal,
            "Red Flags": red_flags,
            "Frailty Score": frailty_score,
            "Risk Level": risk_level
        }

        st.session_state.registry.append(record)

        st.subheader("Risk Stratification Result")

        if risk_level == "High Risk":
            st.error("HIGH RISK – Recommend Ultrasound & Hepatobiliary Referral")
        elif risk_level == "Moderate Risk":
            st.warning("MODERATE RISK – Monitor & Consider Imaging")
        else:
            st.success("LOW RISK – Routine Follow-up")

        df_single = pd.DataFrame([record])

        st.download_button(
            "Download This Assessment (CSV)",
            df_single.to_csv(index=False),
            "assessment.csv",
            "text/csv"
        )

# --------------------------------------------------
# PATIENT REGISTRY
# --------------------------------------------------
elif page == "Patient Registry":

    st.title("Patient Registry")

    if len(st.session_state.registry) == 0:
        st.info("No assessments recorded yet.")
    else:
        df_registry = pd.DataFrame(st.session_state.registry)
        st.dataframe(df_registry, use_container_width=True)

        st.download_button(
            "Download Full Registry (CSV)",
            df_registry.to_csv(index=False),
            "registry.csv",
            "text/csv"
        )

# --------------------------------------------------
# ANALYTICS DASHBOARD
# --------------------------------------------------
elif page == "Analytics Dashboard":

    st.title("Analytics Dashboard")

    if len(st.session_state.registry) == 0:
        st.info("No data available.")
    else:
        df = pd.DataFrame(st.session_state.registry)

        st.subheader("Risk Distribution")
        st.bar_chart(df["Risk Level"].value_counts())

        st.subheader("Age Distribution")
        st.bar_chart(df["Age"])

# --------------------------------------------------
# ABOUT PAGE
# --------------------------------------------------
elif page == "About":

    st.title("About PASSAGE-CDS")

    st.markdown("""
    PASSAGE-CDS is a research-grade clinical decision support prototype 
    designed to enhance early detection pathways for cholangiocarcinoma.

    Framework:
    - Risk stratification model
    - Symptom trigger system
    - Functional decline assessment
    - Clinical referral recommendation layer

    Intended for:
    - Research deployment
    - Pilot screening programs
    - Digital health innovation studies
    """)

    st.markdown("---")
    st.caption("PASSAGE-CDS Prototype | 2026 | Research Use Only")
