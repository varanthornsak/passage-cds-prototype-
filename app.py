import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="PASSAGE-CDS", layout="wide")

st.title("PASSAGE-CDS")
st.subheader("Clinical Decision Support for Aging Risk Stratification")

st.markdown("---")

# ===============================
# Sidebar
# ===============================
st.sidebar.header("About")
st.sidebar.info(
    """
PASSAGE-CDS Prototype  
Clinical Decision Support Tool  
For Geriatric Risk Stratification  

⚠️ Prototype only  
Not for real clinical use
"""
)

# ===============================
# Input Section
# ===============================

st.header("Patient Information")

col1, col2 = st.columns(2)

with col1:
    age = st.number_input("Age", 40, 100, 65)
    gender = st.selectbox("Gender", ["Male", "Female"])
    bmi = st.number_input("BMI", 10.0, 45.0, 23.0)
    adl = st.slider("ADL Score (0-6)", 0, 6, 6)

with col2:
    comorbidity = st.selectbox(
        "Comorbidity",
        ["None", "1 Disease", "≥2 Diseases"]
    )
    smoking = st.selectbox("Smoking", ["No", "Yes"])
    exercise = st.selectbox(
        "Exercise Frequency",
        ["None", "1-2 times/week", "≥3 times/week"]
    )
    qol = st.slider("Quality of Life Score (0-100)", 0, 100, 70)

st.markdown("---")

# ===============================
# Risk Engine
# ===============================

def calculate_risk():
    score = 0

    # Age
    if age >= 80:
        score += 3
    elif age >= 70:
        score += 2
    elif age >= 60:
        score += 1

    # ADL
    if adl <= 3:
        score += 3
    elif adl <= 4:
        score += 2

    # BMI
    if bmi < 18.5 or bmi >= 30:
        score += 1

    # Comorbidity
    if comorbidity == "1 Disease":
        score += 1
    elif comorbidity == "≥2 Diseases":
        score += 2

    # Smoking
    if smoking == "Yes":
        score += 1

    # Exercise
    if exercise == "None":
        score += 2
    elif exercise == "1-2 times/week":
        score += 1

    # QoL
    if qol < 50:
        score += 2
    elif qol < 70:
        score += 1

    return score

risk_score = calculate_risk()

# ===============================
# Risk Stratification
# ===============================

if risk_score <= 3:
    risk_level = "Low Risk"
    color = "green"
elif risk_score <= 7:
    risk_level = "Moderate Risk"
    color = "orange"
else:
    risk_level = "High Risk"
    color = "red"

# ===============================
# Output Section
# ===============================

st.header("Risk Assessment Result")

col3, col4 = st.columns(2)

with col3:
    st.metric("Total Risk Score", risk_score)

with col4:
    if risk_level == "Low Risk":
        st.success("Low Risk")
    elif risk_level == "Moderate Risk":
        st.warning("Moderate Risk")
    else:
        st.error("High Risk")

st.markdown("---")

# ===============================
# Recommendation Engine
# ===============================

st.header("Clinical Recommendation")

if risk_level == "Low Risk":
    st.info("""
- Continue healthy lifestyle
- Annual screening
- Encourage regular exercise
""")

elif risk_level == "Moderate Risk":
    st.warning("""
- Follow-up in 3–6 months
- Assess frailty formally
- Nutrition counseling
- Review medication list
""")

else:
    st.error("""
- Refer to geriatric clinic
- Comprehensive geriatric assessment
- Fall risk evaluation
- Medication reconciliation
- Close follow-up
""")

st.markdown("---")

# ===============================
# Visualization Section
# ===============================

st.header("Risk Factor Breakdown")

risk_data = {
    "Factor": [
        "Age", "ADL", "BMI", "Comorbidity",
        "Smoking", "Exercise", "QoL"
    ],
    "Score Contribution": [
        3 if age >= 80 else 2 if age >= 70 else 1 if age >= 60 else 0,
        3 if adl <= 3 else 2 if adl <= 4 else 0,
        1 if bmi < 18.5 or bmi >= 30 else 0,
        2 if comorbidity == "≥2 Diseases" else 1 if comorbidity == "1 Disease" else 0,
        1 if smoking == "Yes" else 0,
        2 if exercise == "None" else 1 if exercise == "1-2 times/week" else 0,
        2 if qol < 50 else 1 if qol < 70 else 0,
    ]
}

df = pd.DataFrame(risk_data)

st.bar_chart(df.set_index("Factor"))

st.markdown("---")

# ===============================
# Audit & Disclaimer
# ===============================

st.caption("""
This tool is a prototype Clinical Decision Support system.
It is intended for innovation demonstration only.
Final clinical decisions must be made by licensed physicians.
""")
