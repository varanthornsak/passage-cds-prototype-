import streamlit as st
import pandas as pd
import numpy as np
import os
import datetime
import plotly.express as px
import hashlib

# ==============================
# CONFIG
# ==============================
st.set_page_config(
    page_title="PASSAGE Clinical Decision Support",
    page_icon="🧠",
    layout="wide"
)

DATA_FILE = "patients_db.csv"
USER_FILE = "users_db.csv"

# ==============================
# UTILS
# ==============================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    if os.path.exists(USER_FILE):
        return pd.read_csv(USER_FILE)
    else:
        df = pd.DataFrame({
            "username": ["admin", "doctor1"],
            "password": [hash_password("admin123"), hash_password("doctor123")],
            "role": ["admin", "clinician"]
        })
        df.to_csv(USER_FILE, index=False)
        return df

def authenticate(username, password):
    users = load_users()
    hashed = hash_password(password)
    user = users[(users.username == username) & (users.password == hashed)]
    if not user.empty:
        return user.iloc[0]["role"]
    return None

def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    else:
        df = pd.DataFrame(columns=[
            "PatientID","Age","ADL","Comorbidity",
            "QoL","RiskScore","RiskPercent",
            "RiskLevel","Timestamp","Clinician"
        ])
        df.to_csv(DATA_FILE, index=False)
        return df

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

def logistic_probability(score):
    prob = 1 / (1 + np.exp(-0.8*(score-5)))
    return round(prob, 3)

def calculate_risk(age, adl, comorbidity, qol):
    score = 0
    if age >= 70: score += 2
    if adl <= 4: score += 3
    if comorbidity == "Multiple": score += 3
    if qol < 70: score += 2
    return score

# ==============================
# LOGIN SYSTEM
# ==============================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("PASSAGE Clinical Decision Support")
    st.subheader("Secure Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        role = authenticate(username, password)
        if role:
            st.session_state.authenticated = True
            st.session_state.role = role
            st.session_state.username = username
            st.success("Login successful")
            st.rerun()
        else:
            st.error("Invalid credentials")

    st.stop()

# ==============================
# MAIN SYSTEM
# ==============================

st.sidebar.title("PASSAGE CDS")
st.sidebar.write(f"User: {st.session_state.username}")
st.sidebar.write(f"Role: {st.session_state.role}")

menu = st.sidebar.radio("Navigation", [
    "Patient Assessment",
    "Patient Registry",
    "Population Dashboard"
])

df = load_data()

# ==============================
# PATIENT ASSESSMENT
# ==============================
if menu == "Patient Assessment":

    st.title("Patient Risk Assessment")

    col1, col2 = st.columns(2)

    with col1:
        patient_id = st.text_input("Patient ID")
        age = st.number_input("Age", 40, 100, 65)
        adl = st.slider("ADL Score (0-6)", 0, 6, 5)

    with col2:
        comorbidity = st.selectbox("Comorbidity",
                                   ["None","Single","Multiple"])
        qol = st.slider("Quality of Life (0-100)", 0, 100, 75)

    if st.button("Calculate Risk"):

        if patient_id == "":
            st.warning("Please enter Patient ID")
        else:
            score = calculate_risk(age, adl, comorbidity, qol)
            probability = logistic_probability(score)

            if probability < 0.2:
                level = "Low"
            elif probability < 0.5:
                level = "Moderate"
            else:
                level = "High"

            st.subheader("Prediction Result")
            st.metric("Hospitalization Risk", f"{probability*100:.1f}%")
            st.progress(probability)
            st.write("Risk Level:", level)

            st.subheader("Risk Explanation")
            explanations = []
            if age >= 70:
                explanations.append("Advanced age increases frailty risk.")
            if adl <= 4:
                explanations.append("Reduced functional status detected.")
            if comorbidity == "Multiple":
                explanations.append("Multiple comorbidities present.")
            if qol < 70:
                explanations.append("Lower quality of life reported.")

            for e in explanations:
                st.write("•", e)

            new_row = pd.DataFrame([{
                "PatientID": patient_id,
                "Age": age,
                "ADL": adl,
                "Comorbidity": comorbidity,
                "QoL": qol,
                "RiskScore": score,
                "RiskPercent": probability*100,
                "RiskLevel": level,
                "Timestamp": datetime.datetime.now(),
                "Clinician": st.session_state.username
            }])

            df = pd.concat([df, new_row], ignore_index=True)
            save_data(df)

            st.success("Assessment saved to system")

# ==============================
# PATIENT REGISTRY
# ==============================
elif menu == "Patient Registry":

    st.title("Patient Registry")

    if df.empty:
        st.info("No patient data available.")
    else:
        selected_id = st.selectbox("Select Patient ID",
                                   df["PatientID"].unique())

        patient_data = df[df["PatientID"] == selected_id]

        st.dataframe(patient_data.sort_values("Timestamp"))

        st.subheader("Risk Trend")
        fig = px.line(patient_data,
                      x="Timestamp",
                      y="RiskPercent",
                      markers=True)
        st.plotly_chart(fig, use_container_width=True)

# ==============================
# POPULATION DASHBOARD
# ==============================
elif menu == "Population Dashboard":

    st.title("Population Health Dashboard")

    if df.empty:
        st.info("No data available.")
    else:

        col1, col2, col3 = st.columns(3)

        col1.metric("Total Patients", df["PatientID"].nunique())
        col2.metric("Total Assessments", len(df))
        col3.metric("High Risk %",
                    f"{(df['RiskLevel']=='High').mean()*100:.1f}%")

        st.subheader("Risk Distribution")
        fig1 = px.histogram(df, x="RiskLevel")
        st.plotly_chart(fig1, use_container_width=True)

        st.subheader("Average Risk by Age")
        fig2 = px.scatter(df,
                          x="Age",
                          y="RiskPercent",
                          trendline="ols")
        st.plotly_chart(fig2, use_container_width=True)

# ==============================
# FOOTER
# ==============================
st.markdown("---")
st.caption("""
PASSAGE Clinical Decision Support System  
Pilot Deployment Version 1.0  
For Clinical Evaluation Use Only
""")
# ==============================
# PRODUCTION DATABASE CONFIG
# ==============================
from sqlalchemy import create_engine
from cryptography.fernet import Fernet
import base64

DB_URL = "postgresql://passage_user:strongpassword@localhost:5432/passage_db"
engine = create_engine(DB_URL)

# ===== Encryption Key =====
SECRET_KEY = os.environ.get("PASSAGE_SECRET_KEY")

if not SECRET_KEY:
    SECRET_KEY = Fernet.generate_key()
    print("WARNING: Store this key securely:", SECRET_KEY)

cipher = Fernet(SECRET_KEY)

def encrypt_data(text):
    return cipher.encrypt(str(text).encode()).decode()

def decrypt_data(text):
    return cipher.decrypt(text.encode()).decode()

def save_to_postgres(row_dict):
    encrypted_row = {
        "patientid": encrypt_data(row_dict["PatientID"]),
        "age": row_dict["Age"],
        "adl": row_dict["ADL"],
        "comorbidity": row_dict["Comorbidity"],
        "qol": row_dict["QoL"],
        "riskscore": row_dict["RiskScore"],
        "riskpercent": row_dict["RiskPercent"],
        "risklevel": row_dict["RiskLevel"],
        "timestamp": row_dict["Timestamp"],
        "clinician": row_dict["Clinician"]
    }
    df = pd.DataFrame([encrypted_row])
    df.to_sql("patient_records", engine, if_exists="append", index=False)
