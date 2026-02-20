import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(
    page_title="PASSAGE Health",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================
# Branding + Custom UI
# ==============================
st.markdown("""
<style>
.main {
    background-color: #f8fafc;
}
h1, h2, h3 {
    color: #0F172A;
}
.metric-card {
    background-color: white;
    padding: 20px;
    border-radius: 16px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.05);
}
.risk-low {
    background-color: #DCFCE7;
    padding: 15px;
    border-radius: 12px;
    font-weight: 600;
}
.risk-moderate {
    background-color: #FEF3C7;
    padding: 15px;
    border-radius: 12px;
    font-weight: 600;
}
.risk-high {
    background-color: #FEE2E2;
    padding: 15px;
    border-radius: 12px;
    font-weight: 600;
}
.footer {
    text-align: center;
    color: gray;
    font-size: 12px;
    padding-top: 40px;
}
</style>
""", unsafe_allow_html=True)

# ==============================
# Mock Login System
# ==============================
users = {
    "doctor": {"password": "1234", "role": "Doctor"},
    "nurse": {"password": "1234", "role": "Nurse"},
    "admin": {"password": "1234", "role": "Admin"},
}

def login():
    st.title("PASSAGE Health")
    st.subheader("Login to Clinical Dashboard")
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

# ==============================
# Sidebar
# ==============================
st.sidebar.title("PASSAGE Health")
st.sidebar.write(f"Role: {st.session_state['role']}")
st.sidebar.info("""
Personalized Adaptive Screening  
System for Geriatric Evaluation  

Startup Prototype Version
""")

# ==============================
# Main Header
# ==============================
st.title("Clinical Decision Support Dashboard")
st.caption("Aging Risk Intelligence Platform")

# ==============================
# Patient Input
# ==============================
st.header("Patient Assessment")

col1, col2, col3 = st.columns(3)

with col1:
    age = st.number_input("Age", 40, 100, 65)
    bmi = st.number_input("BMI", 10.0, 45.0, 23.0)

with col2:
    adl = st.slider("ADL Score (0-6)", 0, 6, 6)
    qol = st.slider("QoL Score (0-100)", 0, 100, 70)

with col3:
    comorbidity = st.selectbox("Comorbidity", ["None", "1 Disease", "≥2 Diseases"])
    exercise = st.selectbox("Exercise", ["≥3 times/week", "1-2 times/week", "None"])

# ==============================
# Risk Engine
# ==============================
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

# Risk Level
if score <= 3:
    level = "Low Risk"
    risk_class = "risk-low"
elif score <= 7:
    level = "Moderate Risk"
    risk_class = "risk-moderate"
else:
    level = "High Risk"
    risk_class = "risk-high"

confidence = np.random.uniform(0.80, 0.95)

# ==============================
# Dashboard Metrics
# ==============================
st.markdown("---")
st.header("Risk Overview")

k1, k2, k3 = st.columns(3)

with k1:
    st.metric("Risk Score", score)

with k2:
    st.metric("Risk Level", level)

with k3:
    st.metric("AI Confidence", f"{round(confidence*100,1)}%")

st.progress(confidence)

st.markdown(f'<div class="{risk_class}">{level}</div>', unsafe_allow_html=True)

# ==============================
# Recommendation
# ==============================
st.header("Clinical Recommendation")

if level == "Low Risk":
    st.success("""
• Annual screening  
• Maintain physical activity  
• Balanced diet  
""")

elif level == "Moderate Risk":
    st.warning("""
• Follow-up in 3–6 months  
• Frailty assessment  
• Medication review  
""")

else:
    st.error("""
• Refer to Geriatric Clinic  
• Comprehensive Geriatric Assessment  
• Close monitoring  
""")

# ==============================
# Multi-Patient Mode
# ==============================
if "patients" not in st.session_state:
    st.session_state["patients"] = []

if st.button("Save Patient Case"):
    st.session_state["patients"].append({
        "Age": age,
        "Risk Score": score,
        "Risk Level": level
    })

st.markdown("---")
st.header("Patient Registry")

if st.session_state["patients"]:
    df_patients = pd.DataFrame(st.session_state["patients"])
    st.dataframe(df_patients)

# ==============================
# Population Dashboard
# ==============================
st.markdown("---")
st.header("Population Analytics")

if st.session_state["patients"]:
    df_pop = pd.DataFrame(st.session_state["patients"])

    risk_counts = df_pop["Risk Level"].value_counts()
    st.subheader("Risk Distribution")
    st.bar_chart(risk_counts)

    avg_score = df_pop["Risk Score"].mean()
    st.metric("Average Population Risk Score", round(avg_score, 2))

# ==============================
# Footer
# ==============================
st.markdown("""
<div class="footer">
PASSAGE Health © 2026  
Clinical Decision Support Startup Prototype  
Not for real clinical use
</div>
""", unsafe_allow_html=True)
