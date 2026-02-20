import streamlit as st
import pandas as pd
import numpy as np
import os
import datetime
import hashlib
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

st.set_page_config(page_title="PASSAGE Health", layout="wide")

# =====================================================
# CONFIG
# =====================================================
DATABASE_URL = os.environ.get("DATABASE_URL")  # ถ้ามีจะใช้ PostgreSQL
LOCAL_FILE = "passage_local_db.csv"
AUDIT_FILE = "audit_log.txt"

# =====================================================
# UTIL
# =====================================================
def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def log_action(user, action):
    with open(AUDIT_FILE, "a") as f:
        f.write(f"{datetime.datetime.now()} | {user} | {action}\n")

def logistic(x):
    return 1 / (1 + np.exp(-x))

# =====================================================
# DATABASE MODE
# =====================================================
if DATABASE_URL:
    engine = create_engine(DATABASE_URL)
    DB_MODE = "PostgreSQL"
else:
    DB_MODE = "Local CSV"

def load_data():
    if DB_MODE == "PostgreSQL":
        try:
            return pd.read_sql("SELECT * FROM patients", engine)
        except:
            return pd.DataFrame()
    else:
        if os.path.exists(LOCAL_FILE):
            return pd.read_csv(LOCAL_FILE)
        else:
            return pd.DataFrame(columns=[
                "PatientID","Age","ClinicalScore",
                "FunctionalScore","SocialScore",
                "RiskPercent","RiskLevel",
                "AIConfidence","Timestamp","User"
            ])

def save_data(df):
    if DB_MODE == "PostgreSQL":
        try:
            df.to_sql("patients", engine, if_exists="append", index=False)
        except SQLAlchemyError as e:
            st.error("Database error")
    else:
        df_existing = load_data()
        df_all = pd.concat([df_existing, df], ignore_index=True)
        df_all.to_csv(LOCAL_FILE, index=False)

# =====================================================
# LOGIN (Simple Secure)
# =====================================================
USERS = {
    "admin": hash_password("admin123"),
    "doctor": hash_password("doctor123")
}

if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("PASSAGE Health Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        if u in USERS and USERS[u] == hash_password(p):
            st.session_state.auth = True
            st.session_state.user = u
            log_action(u, "Login success")
            st.rerun()
        else:
            st.error("Invalid credentials")
    st.stop()

# =====================================================
# MAIN SYSTEM
# =====================================================
st.sidebar.title("PASSAGE Health")
st.sidebar.write(f"User: {st.session_state.user}")
st.sidebar.write(f"Database Mode: {DB_MODE}")

menu = st.sidebar.radio("Menu", [
    "New Assessment",
    "Patient Registry",
    "Population Dashboard"
])

df = load_data()

# =====================================================
# RISK ENGINE
# =====================================================
def calculate_risk(age, comorbidity, qol,
                   gait_speed, frailty,
                   living_alone, fall):

    clinical = 0
    if age >= 75: clinical += 2
    if comorbidity == "Multiple": clinical += 3
    if qol < 60: clinical += 2

    functional = 0
    if gait_speed < 0.8: functional += 2
    if frailty >= 3: functional += 3

    social = 0
    if living_alone: social += 1
    if fall: social += 2

    total = clinical + functional + social
    risk = logistic((total - 4) * 0.9)
    confidence = min(0.95, 0.6 + total*0.03)

    return clinical, functional, social, risk, confidence

# =====================================================
# NEW ASSESSMENT
# =====================================================
if menu == "New Assessment":

    st.title("New Patient Assessment")

    consent = st.checkbox("Patient consent obtained (PDPA required)")
    if not consent:
        st.warning("Consent required before proceeding")
        st.stop()

    col1, col2, col3 = st.columns(3)

    with col1:
        pid = st.text_input("Patient ID")
        age = st.number_input("Age", 40, 100, 70)
        comorbidity = st.selectbox("Comorbidity",
                                   ["None","Single","Multiple"])
        qol = st.slider("Quality of Life",0,100,70)

    with col2:
        gait = st.number_input("Gait Speed (m/s)",0.1,2.0,1.0)
        frailty = st.slider("Frailty Score (0-5)",0,5,1)

    with col3:
        living = st.checkbox("Living Alone")
        fall = st.checkbox("Fall in past year")

    if st.button("Generate Risk"):

        if pid == "":
            st.warning("Enter Patient ID")
        else:
            clinical, functional, social, risk, conf = calculate_risk(
                age, comorbidity, qol,
                gait, frailty,
                living, fall
            )

            if risk < 0.2:
                level = "Low"
            elif risk < 0.5:
                level = "Moderate"
            else:
                level = "High"

            st.metric("Risk %", f"{risk*100:.1f}%")
            st.metric("AI Confidence", f"{conf*100:.1f}%")
            st.progress(risk)

            new_row = pd.DataFrame([{
                "PatientID": pid,
                "Age": age,
                "ClinicalScore": clinical,
                "FunctionalScore": functional,
                "SocialScore": social,
                "RiskPercent": risk*100,
                "RiskLevel": level,
                "AIConfidence": conf*100,
                "Timestamp": datetime.datetime.now(),
                "User": st.session_state.user
            }])

            save_data(new_row)
            log_action(st.session_state.user,
                       f"Created assessment for {pid}")

            st.success("Saved successfully")

# =====================================================
# REGISTRY
# =====================================================
elif menu == "Patient Registry":

    st.title("Patient Registry")

    if df.empty:
        st.info("No data")
    else:
        selected = st.selectbox("Select Patient",
                                df["PatientID"].unique())
        sub = df[df["PatientID"] == selected]
        st.dataframe(sub.sort_values("Timestamp"))
        st.line_chart(sub.set_index("Timestamp")["RiskPercent"])

# =====================================================
# POPULATION DASHBOARD
# =====================================================
elif menu == "Population Dashboard":

    st.title("Population Dashboard")

    if df.empty:
        st.info("No data")
    else:
        st.metric("Total Patients",
                  df["PatientID"].nunique())
        st.metric("High Risk %",
                  round((df["RiskLevel"]=="High").mean()*100,1))

        st.bar_chart(df["RiskLevel"].value_counts())
        st.scatter_chart(df[["Age","RiskPercent"]])

st.markdown("---")
st.caption("PASSAGE Health | Production-Lite Digital Health Platform")
