import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(
    page_title="PASSAGE-CDS",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------------
# Custom CSS (Startup Style)
# -------------------------------
st.markdown("""
<style>
.main {
    background-color: #f8fafc;
}
.block-container {
    padding-top: 2rem;
}
h1 {
    color: #0f172a;
}
.metric-card {
    background-color: white;
    padding: 20px;
    border-radius: 16px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.05);
}
.risk-low {
    background-color: #dcfce7;
    padding: 15px;
    border-radius: 12px;
    font-weight: 600;
}
.risk-moderate {
    background-color: #fef3c7;
    padding: 15px;
    border-radius: 12px;
    font-weight: 600;
}
.risk-high {
    background-color: #fee2e2;
    padding: 15px;
    border-radius: 12px;
    font-weight: 600;
}
.footer {
    text-align: center;
    color: gray;
    font-size: 12px;
    padding-top: 30px;
}
</style>
""", unsafe_allow_html=True)

# -------------------------------
# Header
# -------------------------------
st.title("PASSAGE-CDS")
st.caption("Personalized Aging Risk Intelligence Platform")

st.markdown("---")

# -------------------------------
# Sidebar
# -------------------------------
st.sidebar.title("Platform Overview")
st.sidebar.info("""
PASSAGE-CDS v1.0  
Clinical Decision Support Platform  

Built for Community Hospitals  
Startup Prototype Version
""")

# -------------------------------
# Input Section
# -------------------------------
st.subheader("Patient Input")

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

st.markdown("---")

# -------------------------------
# Risk Engine
# -------------------------------
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

# -------------------------------
# Dashboard KPI
# -------------------------------
st.subheader("Risk Dashboard")

k1, k2, k3 = st.columns(3)

with k1:
    st.metric("Total Risk Score", score)

with k2:
    st.metric("Frailty Indicator", "Stable" if score <= 3 else "Monitor")

with k3:
    st.metric("Hospitalization Risk", level)

st.markdown("---")

# -------------------------------
# Risk Display Card
# -------------------------------
st.markdown(f'<div class="{risk_class}">{level}</div>', unsafe_allow_html=True)

# -------------------------------
# Recommendation Section
# -------------------------------
st.subheader("Clinical Recommendation")

if level == "Low Risk":
    st.success("""
• Annual screening  
• Maintain physical activity  
• Balanced nutrition  
""")

elif level == "Moderate Risk":
    st.warning("""
• Follow-up in 3–6 months  
• Frailty assessment  
• Medication review  
• Nutrition counseling  
""")

else:
    st.error("""
• Refer to Geriatric Clinic  
• Comprehensive Geriatric Assessment  
• Fall risk evaluation  
• Close monitoring  
""")

st.markdown("---")

# -------------------------------
# Visualization
# -------------------------------
st.subheader("Risk Factor Contribution")

risk_data = {
    "Factor": ["Age", "ADL", "BMI", "Comorbidity", "Exercise", "QoL"],
    "Score": [
        3 if age >= 80 else 2 if age >= 70 else 1 if age >= 60 else 0,
        3 if adl <= 3 else 2 if adl <= 4 else 0,
        1 if bmi < 18.5 or bmi >= 30 else 0,
        2 if comorbidity == "≥2 Diseases" else 1 if comorbidity == "1 Disease" else 0,
        2 if exercise == "None" else 1 if exercise == "1-2 times/week" else 0,
        2 if qol < 50 else 1 if qol < 70 else 0
    ]
}

df = pd.DataFrame(risk_data)
st.bar_chart(df.set_index("Factor"))

# -------------------------------
# Footer
# -------------------------------
st.markdown("""
<div class="footer">
PASSAGE-CDS © 2026 | HealthTech Startup Prototype  
Not for real clinical use
</div>
""", unsafe_allow_html=True)
