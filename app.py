import streamlit as st
import pandas as pd
import numpy as np
import datetime

st.set_page_config(
    page_title="PASSAGE Health Clinical Platform",
    layout="wide"
)

# ===============================
# Custom Enterprise UI
# ===============================
st.markdown("""
<style>
.main {background-color: #f4f6f9;}
h1,h2,h3 {color:#0F172A;}
.risk-low {background:#DCFCE7;padding:15px;border-radius:12px;font-weight:600;}
.risk-moderate {background:#FEF3C7;padding:15px;border-radius:12px;font-weight:600;}
.risk-high {background:#FEE2E2;padding:15px;border-radius:12px;font-weight:600;}
.footer {text-align:center;color:gray;font-size:12px;padding-top:40px;}
</style>
""", unsafe_allow_html=True)

# ===============================
# Mock Login System
# ===============================
users = {
    "doctor": {"password": "1234", "role": "Doctor"},
    "nurse": {"password": "1234", "role": "Nurse"},
    "admin": {"password": "1234", "role": "Administrator"},
}

def login():
    st.title("PASSAGE Health Clinical Platform")
    st.subheader("Secure Login – Pilot Deployment Version")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username in users and users[username]["password"] == password:
            st.session_state["logged_in"] = True
            st.session_state["role"] = users[username]["role"]
        else:
            st.error("Invalid credentials")

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    login()
    st.stop()

# ===============================
# Sidebar
# ===============================
st.sidebar.title("PASSAGE Health")
st.sidebar.write(f"Role: {st.session_state['role']}")
st.sidebar.markdown("""
Clinical Decision Support – Aging Risk Stratification  
Pilot Implementation Phase
""")
st.sidebar.markdown("### Risk Interpretation")
st.sidebar.write("""
Low Risk: <20%  
Moderate Risk: 20–50%  
High Risk: >50%
""")

# ===============================
# Main Header
# ===============================
st.title("Clinical Decision Support Dashboard")
st.caption("Longitudinal Aging Risk Monitoring System")

# ===============================
# Patient Input
# ===============================
st.header("Patient Assessment")

patient_id = st.text_input("Patient ID")

col1, col2, col3 = st.columns(3)

with col1:
    age = st.number_input("Age", 40, 100, 65)
    bmi = st.number_input("BMI", 10.0, 45.0, 23.0)

with col2:
    adl = st.slider("ADL Score (0-6)", 0, 6, 6)
    qol = st.slider("Quality of Life (0-100)", 0, 100, 70)

with col3:
    comorbidity = st.selectbox("Comorbidity", ["None", "1 Disease", "≥2 Diseases"])
    exercise = st.selectbox("Exercise Frequency", ["≥3 times/week", "1-2 times/week", "None"])

# ===============================
# Risk Engine (Rule-based Score)
# ===============================
score = 0

if age >= 80:
    score += 3
elif age >= 70:
    score += 2
elif age >= 60:
    score += 1

if adl <= 3:
    score += 3
elif adl <= 4:
    score += 2

if bmi < 18.5 or bmi >= 30:
    score += 1

if comorbidity == "1 Disease":
    score += 1
elif comorbidity == "≥2 Diseases":
    score += 2

if exercise == "None":
    score += 2
elif exercise == "1-2 times/week":
    score += 1

if qol < 50:
    score += 2
elif qol < 70:
    score += 1

# ===============================
# Logistic Probability Model
# ===============================
def logistic_probability(score):
    return 1 / (1 + np.exp(-0.8*(score-5)))

probability = logistic_probability(score)

if probability < 0.2:
    level = "Low Risk"
    risk_class = "risk-low"
elif probability < 0.5:
    level = "Moderate Risk"
    risk_class = "risk-moderate"
else:
    level = "High Risk"
    risk_class = "risk-high"

# ===============================
# Dashboard Metrics
# ===============================
st.markdown("---")
st.header("Risk Overview")

k1, k2, k3 = st.columns(3)

with k1:
    st.metric("Risk Score", score)

with k2:
    st.metric("Predicted Hospitalization Risk", f"{probability*100:.1f}%")

with k3:
    st.metric("Risk Category", level)

st.progress(probability)
st.markdown(f'<div class="{risk_class}">{level}</div>', unsafe_allow_html=True)

# ===============================
# Explainable AI
# ===============================
st.header("Risk Explanation")

explanation = []

if age >= 70:
    explanation.append("Advanced age increases frailty-related hospitalization risk.")
if adl <= 4:
    explanation.append("Reduced functional capacity contributes significantly to risk.")
if comorbidity != "None":
    explanation.append("Presence of comorbid conditions elevates risk profile.")
if qol < 70:
    explanation.append("Lower quality of life associated with adverse outcomes.")
if exercise == "None":
    explanation.append("Physical inactivity linked to higher geriatric risk.")

for e in explanation:
    st.write("•", e)

# ===============================
# Clinical Recommendation
# ===============================
st.header("Clinical Recommendation")

if level == "Low Risk":
    st.success("""
• Annual screening  
• Encourage physical activity  
• Preventive lifestyle counseling  
""")

elif level == "Moderate Risk":
    st.warning("""
• Follow-up within 3–6 months  
• Formal frailty assessment  
• Medication review  
""")

else:
    st.error("""
• Refer to Geriatric Clinic  
• Comprehensive Geriatric Assessment  
• Close monitoring and intervention planning  
""")

# ===============================
# Multi-Patient Registry
# ===============================
if "patients" not in st.session_state:
    st.session_state["patients"] = []

if st.button("Save Assessment"):
    if patient_id != "":
        st.session_state["patients"].append({
            "Patient ID": patient_id,
            "Timestamp": datetime.datetime.now(),
            "Risk Score": score,
            "Risk %": probability*100,
            "Risk Level": level
        })

st.markdown("---")
st.header("Patient Registry")

if st.session_state["patients"]:
    df_patients = pd.DataFrame(st.session_state["patients"])
    st.dataframe(df_patients)

    # ===============================
    # Longitudinal Trend
    # ===============================
    st.header("Longitudinal Risk Trend")
    selected_id = st.selectbox("Select Patient ID", df_patients["Patient ID"].unique())
    df_selected = df_patients[df_patients["Patient ID"] == selected_id]
    st.line_chart(df_selected.set_index("Timestamp")["Risk %"])

# ===============================
# Population Analytics
# ===============================
st.markdown("---")
st.header("Population Analytics")

if st.session_state["patients"]:
    df_pop = pd.DataFrame(st.session_state["patients"])
    risk_counts = df_pop["Risk Level"].value_counts()
    st.subheader("Risk Distribution")
    st.bar_chart(risk_counts)

    avg_score = df_pop["Risk %"].mean()
    st.metric("Average Population Risk (%)", round(avg_score, 2))

# ===============================
# Footer
# ===============================
st.markdown("""
<div class="footer">
PASSAGE Health Clinical Platform © 2026  
Pilot Deployment Version 1.0  
For Evaluation Use Only – Not for Independent Clinical Decision Making
</div>
""", unsafe_allow_html=True)
