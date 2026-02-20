
        import streamlit as st
import pandas as pd
import numpy as np
import datetime
import os

st.set_page_config(
    page_title="PASSAGE Health Platform",
    page_icon="🧠",
    layout="wide"
)

DATA_FILE = "passage_startup_db.csv"

# ===============================
# DATABASE
# ===============================
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    else:
        df = pd.DataFrame(columns=[
            "PatientID","Age","ClinicalScore",
            "FunctionalScore","SocialScore",
            "TotalRiskPercent","RiskLevel",
            "AIConfidence","Timestamp"
        ])
        df.to_csv(DATA_FILE, index=False)
        return df

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

df = load_data()

# ===============================
# STARTUP UI
# ===============================
st.markdown("""
<style>
.main {background-color:#f7f9fc;}
h1,h2,h3 {color:#0f172a;}
.metric-card {background:#ffffff;padding:20px;border-radius:15px;box-shadow:0 2px 10px rgba(0,0,0,0.05);}
.low {color:#16a34a;font-weight:600;}
.moderate {color:#ca8a04;font-weight:600;}
.high {color:#dc2626;font-weight:600;}
</style>
""", unsafe_allow_html=True)

st.title("PASSAGE Health")
st.caption("Digital Frailty & Hospitalization Risk Platform")

menu = st.sidebar.radio("Navigation", [
    "New Assessment",
    "Patient Registry",
    "Population Dashboard"
])

# ===============================
# RISK ENGINE
# ===============================
def logistic(x):
    return 1 / (1 + np.exp(-x))

def calculate_risk(age, comorbidity, qol,
                   gait_speed, frailty_score,
                   living_alone, fall_history):

    # Clinical Layer
    clinical = 0
    if age >= 75: clinical += 2
    if comorbidity == "Multiple": clinical += 3
    if qol < 60: clinical += 2

    # Functional Layer
    functional = 0
    if gait_speed < 0.8: functional += 2
    if frailty_score >= 3: functional += 3

    # Social Layer
    social = 0
    if living_alone: social += 1
    if fall_history: social += 2

    total_raw = clinical + functional + social
    probability = logistic((total_raw - 4) * 0.9)

    confidence = min(0.95, 0.6 + (total_raw * 0.03))

    return clinical, functional, social, probability, confidence

# ===============================
# NEW ASSESSMENT
# ===============================
if menu == "New Assessment":

    st.header("New Patient Assessment")

    col1, col2, col3 = st.columns(3)

    with col1:
        patient_id = st.text_input("Patient ID")
        age = st.number_input("Age", 40, 100, 70)
        comorbidity = st.selectbox("Comorbidity",
                                   ["None","Single","Multiple"])
        qol = st.slider("Quality of Life (0-100)",0,100,70)

    with col2:
        gait_speed = st.number_input("Gait Speed (m/s)",0.1,2.0,1.0)
        frailty_score = st.slider("Frailty Phenotype (0-5)",0,5,1)

    with col3:
        living_alone = st.checkbox("Living Alone")
        fall_history = st.checkbox("Fall in past 12 months")

    if st.button("Generate Risk Profile"):

        if patient_id == "":
            st.warning("Enter Patient ID")
        else:

            clinical, functional, social, risk, confidence = calculate_risk(
                age, comorbidity, qol,
                gait_speed, frailty_score,
                living_alone, fall_history
            )

            if risk < 0.2:
                level = "Low"
                css = "low"
            elif risk < 0.5:
                level = "Moderate"
                css = "moderate"
            else:
                level = "High"
                css = "high"

            st.markdown("---")
            st.subheader("Risk Overview")

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Clinical Score", clinical)
            c2.metric("Functional Score", functional)
            c3.metric("Social Score", social)
            c4.metric("Total Risk", f"{risk*100:.1f}%")

            st.progress(risk)
            st.markdown(f"<p class='{css}'>Risk Level: {level}</p>",
                        unsafe_allow_html=True)

            st.subheader("AI Confidence")
            st.metric("Model Confidence", f"{confidence*100:.1f}%")
            st.progress(confidence)

            # Save
            new_row = pd.DataFrame([{
                "PatientID": patient_id,
                "Age": age,
                "ClinicalScore": clinical,
                "FunctionalScore": functional,
                "SocialScore": social,
                "TotalRiskPercent": risk*100,
                "RiskLevel": level,
                "AIConfidence": confidence*100,
                "Timestamp": datetime.datetime.now()
            }])

            df = pd.concat([df, new_row], ignore_index=True)
            save_data(df)

            st.success("Assessment saved successfully")

# ===============================
# PATIENT REGISTRY
# ===============================
elif menu == "Patient Registry":

    st.header("Patient Registry")

    if df.empty:
        st.info("No data available")
    else:
        selected = st.selectbox("Select Patient",
                                df["PatientID"].unique())
        patient_df = df[df["PatientID"] == selected]
        st.dataframe(patient_df.sort_values("Timestamp"))

        st.line_chart(patient_df.set_index("Timestamp")["TotalRiskPercent"])

# ===============================
# POPULATION DASHBOARD
# ===============================
elif menu == "Population Dashboard":

    st.header("Population Health Insights")

    if df.empty:
        st.info("No data available")
    else:
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Patients", df["PatientID"].nunique())
        col2.metric("Avg Risk %",
                    round(df["TotalRiskPercent"].mean(),1))
        col3.metric("High Risk %",
                    round((df["RiskLevel"]=="High").mean()*100,1))

        st.subheader("Risk Distribution")
        st.bar_chart(df["RiskLevel"].value_counts())

        st.subheader("Risk vs Age")
        st.scatter_chart(df[["Age","TotalRiskPercent"]])

st.markdown("---")
st.caption("PASSAGE Health | Digital Health Risk Intelligence Platform")
