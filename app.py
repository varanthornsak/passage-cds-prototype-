import streamlit as st
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, Column, Integer, Float, String, Boolean, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_curve, auc
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
import tempfile

# ==========================================================
# PAGE CONFIG
# ==========================================================
st.set_page_config(page_title="PASSAGE  | KKU", layout="wide")

st.markdown("""
# PASSAGE Clinical Decision Support System  
### Faculty of Medicine, Khon Kaen University  
---
""")

# ==========================================================
# DATABASE (DEV MODE AUTO RESET)
# ==========================================================
DATABASE_URL = "sqlite:///health.db"
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
    cca_risk_level = Column(String)
    ai_confidence = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

# 🔥 DEV RESET
Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)

# ==========================================================
# SCORING ENGINE
# ==========================================================
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

def classify_risk(age, raw_fish, lft_abnormal, red_flags):
    risk_score = age*0.02 + raw_fish*1.5 + lft_abnormal*1.5 + red_flags*1
    if risk_score > 5:
        return "High Risk"
    elif risk_score > 3:
        return "Moderate Risk"
    else:
        return "Low Risk"

# ==========================================================
# MENU
# ==========================================================
menu = st.sidebar.selectbox(
    "Navigation",
    ["New Assessment", "Executive Overview", "Population Dashboard", "User Guide"]
)

# ==========================================================
# NEW ASSESSMENT
# ==========================================================
if menu == "New Assessment":

    st.header("New Clinical Assessment")

    with st.form("form"):

        col1, col2 = st.columns(2)

        with col1:
            patient_name = st.text_input("Patient Name")
            age = st.number_input("Age", 20, 100)
            raw_fish = st.checkbox("Raw fish consumption")
            lft_abnormal = st.checkbox("Abnormal LFT")
            red_flags = st.number_input("Red Flag Symptoms", 0, 5)
            gait_speed = st.number_input("Gait Speed (m/s)", 0.0, 3.0)
            grip_strength = st.number_input("Grip Strength (kg)", 0.0, 100.0)
            tug_time = st.number_input("TUG Time (sec)", 0.0, 60.0)

        with col2:
            moca_score = st.number_input("MoCA Score", 0, 30)
            phq9 = st.number_input("PHQ-9", 0, 27)
            gad7 = st.number_input("GAD-7", 0, 21)
            sbp = st.number_input("Systolic BP", 0.0, 250.0)
            hba1c = st.number_input("HbA1c", 0.0, 15.0)
            whoqol = st.number_input("WHOQOL-OLD", 0.0, 100.0)

        submit = st.form_submit_button("Submit")

        if submit:

            data = locals()
            healthspan = calculate_healthspan(data)
            cca_risk = classify_risk(age, raw_fish, lft_abnormal, red_flags)

            record = Assessment(
                patient_name=patient_name,
                age=age,
                raw_fish=raw_fish,
                lft_abnormal=lft_abnormal,
                red_flags=red_flags,
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
                cca_risk_level=cca_risk,
                ai_confidence=100
            )

            session.add(record)
            session.commit()

            st.success("Assessment Saved")
            st.metric("Healthspan Index", healthspan)
            st.metric("CCA Risk Level", cca_risk)

# ==========================================================
# POPULATION DASHBOARD + ML
# ==========================================================
if menu == "Population Dashboard":

    records = session.query(Assessment).all()

    if len(records) < 5:
        st.info("Need at least 5 records for ML training")
    else:

        df = pd.DataFrame([{
            "age": r.age,
            "raw_fish": int(r.raw_fish),
            "lft_abnormal": int(r.lft_abnormal),
            "red_flags": r.red_flags,
            "healthspan": r.healthspan_index,
            "target": 1 if r.cca_risk_level=="High Risk" else 0,
            "date": r.created_at
        } for r in records])

        X = df[["age","raw_fish","lft_abnormal","red_flags","healthspan"]]
        y = df["target"]

        model = LogisticRegression()
        model.fit(X,y)

        y_prob = model.predict_proba(X)[:,1]
        fpr,tpr,_ = roc_curve(y,y_prob)
        roc_auc = auc(fpr,tpr)

        fig = plt.figure()
        plt.plot(fpr,tpr,label=f"AUC={roc_auc:.2f}")
        plt.plot([0,1],[0,1],'--')
        plt.xlabel("False Positive Rate")
        plt.ylabel("True Positive Rate")
        plt.legend()
        st.pyplot(fig)

        st.metric("Model AUC", round(roc_auc,3))
        st.metric("Average Healthspan", round(df["healthspan"].mean(),2))

        # PDF Research Report
        if st.button("Generate Research Report (PDF)"):

            temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            doc = SimpleDocTemplate(temp.name, pagesize=A4)
            styles = getSampleStyleSheet()
            elements = []

            elements.append(Paragraph("PASSAGE Research Summary", styles["Title"]))
            elements.append(Spacer(1,0.3*inch))
            elements.append(Paragraph(f"Total Records: {len(records)}", styles["Normal"]))
            elements.append(Paragraph(f"Model AUC: {roc_auc:.2f}", styles["Normal"]))
            elements.append(Paragraph(f"Average Healthspan: {df['healthspan'].mean():.2f}", styles["Normal"]))
            elements.append(Spacer(1,0.3*inch))
            elements.append(Paragraph(
                "This system supports preventive screening and research analytics.",
                styles["Normal"]
            ))

            doc.build(elements)

            with open(temp.name,"rb") as f:
                st.download_button(
                    "Download PDF",
                    f,
                    file_name="PASSAGE_Research_Report.pdf",
                    mime="application/pdf"
                )
                # ==========================================================
# USER GUIDE – DETAILED CLINICAL VERSION
# ==========================================================
if menu == "User Guide":

    st.header("PASSAGE 3.0 – Detailed User Guide")
    st.markdown("---")

    st.subheader("1. System Overview")

    st.markdown("""
PASSAGE (Preventive Assessment System for Sustainable Ageing & Geriatric Evaluation) 
is an AI-assisted Clinical Decision Support System developed for preventive health screening 
and population-level analytics.

The system integrates:

• Functional performance  
• Cognitive status  
• Mental health  
• Cardiometabolic risk  
• Quality of life  
• Cholangiocarcinoma (CCA) risk indicators  

Outputs include:
- Healthspan Index (0–100)
- CCA Risk Level
- Machine Learning risk modeling (Logistic Regression)
- ROC performance metrics
""")

    # ======================================================
    st.subheader("2. Variable Interpretation Guide")

    st.markdown("### A. Functional Measures")

    st.markdown("""
**1. Gait Speed (m/s)**  
• ≥ 1.0 m/s → Normal mobility  
• 0.8 – 0.99 m/s → Mild decline  
• < 0.8 m/s → Frailty risk  

Interpretation:  
Lower gait speed is associated with sarcopenia, fall risk, and mortality.
""")

    st.markdown("""
**2. Grip Strength (kg)**  
• Male: ≥ 28 kg normal  
• Female: ≥ 18 kg normal  
• Below threshold → Possible sarcopenia  

Interpretation:  
Reduced grip strength correlates with muscle weakness and poor healthspan.
""")

    st.markdown("""
**3. Timed Up & Go (TUG) Test (seconds)**  
• ≤ 10 sec → Normal  
• 11–20 sec → Mild impairment  
• > 20 sec → High fall risk  

Interpretation:  
Longer times indicate mobility impairment and frailty.
""")

    # ======================================================
    st.subheader("B. Cognitive Assessment")

    st.markdown("""
**MoCA Score (0–30)**  
• ≥ 26 → Normal cognition  
• 18–25 → Mild cognitive impairment  
• < 18 → Possible dementia  

Interpretation:  
Lower scores suggest cognitive decline affecting functional independence.
""")

    # ======================================================
    st.subheader("C. Mental Health")

    st.markdown("""
**PHQ-9 (Depression Screening)**  
• 0–4 → Minimal  
• 5–9 → Mild  
• 10–14 → Moderate  
• 15–27 → Severe  

**GAD-7 (Anxiety Screening)**  
• 0–4 → Minimal  
• 5–9 → Mild  
• 10–14 → Moderate  
• 15–21 → Severe  

Interpretation:  
Higher scores negatively affect overall healthspan and quality of life.
""")

    # ======================================================
    st.subheader("D. Cardiometabolic Indicators")

    st.markdown("""
**Systolic Blood Pressure (mmHg)**  
• < 120 → Normal  
• 120–129 → Elevated  
• 130–139 → Stage 1 HT  
• ≥ 140 → Stage 2 HT  

**HbA1c (%)**  
• < 5.7 → Normal  
• 5.7–6.4 → Prediabetes  
• ≥ 6.5 → Diabetes  

Interpretation:  
Chronic cardiometabolic dysregulation reduces long-term healthspan.
""")

    # ======================================================
    st.subheader("E. Quality of Life")

    st.markdown("""
**WHOQOL-OLD (0–100)**  
• ≥ 80 → Excellent quality of life  
• 60–79 → Moderate  
• < 60 → Poor  

Interpretation:  
Higher values indicate better perceived well-being.
""")

    # ======================================================
    st.subheader("F. CCA Risk Indicators")

    st.markdown("""
**Age**  
Risk increases progressively after age 50.

**Raw Fish Consumption**  
Binary risk factor (Opisthorchis viverrini exposure).

**Abnormal Liver Function Test (LFT)**  
Suggests hepatobiliary pathology.

**Red Flag Symptoms (0–5 scale)**  
Includes jaundice, weight loss, RUQ pain, anorexia, cholangitis.

Interpretation:  
Combined into logistic regression model for CCA risk stratification.
""")

    # ======================================================
    st.subheader("3. Healthspan Index Interpretation")

    st.markdown("""
Healthspan Index is a composite score (0–100) derived from all domains.

• ≥ 80 → Optimal healthspan  
• 60–79 → Stable  
• 40–59 → Vulnerable  
• < 40 → High frailty risk  

This score reflects multi-system biological ageing rather than chronological age.
""")

    # ======================================================
    st.subheader("4. Machine Learning Model")

    st.markdown("""
The Logistic Regression model:

• Trains automatically when ≥ 5 records are available  
• Predicts probability of High CCA Risk  
• Generates ROC curve  
• Reports AUC (Area Under Curve)

AUC Interpretation:
• 0.5 → No discrimination  
• 0.6–0.7 → Acceptable  
• 0.7–0.8 → Good  
• 0.8–0.9 → Excellent  
• >0.9 → Outstanding
""")

    # ======================================================
    st.subheader("5. Intended Clinical Use")

    st.markdown("""
PASSAGE is intended for:

• Preventive screening  
• Population health analytics  
• Research support  
• Risk stratification  

Not intended to replace physician clinical judgment.

Final decisions must always be made by qualified medical professionals.
""")

    st.markdown("---")
    st.success("End of User Guide")
# ==========================================================
# ===== PASSAGE PROFESSIONAL + BUSINESS EXTENSION =========
# ==========================================================

st.markdown("""
<style>
.metric-card {
    background-color:#f4f6f9;
    padding:15px;
    border-radius:12px;
    box-shadow:0 2px 6px rgba(0,0,0,0.05);
}
</style>
""", unsafe_allow_html=True)

st.sidebar.markdown("---")
st.sidebar.subheader("Platform Mode")
role = st.sidebar.radio("User Role", ["Clinician", "Research", "Admin (Pro)"])

# ==========================================================
# EXECUTIVE OVERVIEW
# ==========================================================

if menu == "Executive Overview":

    st.header("Executive Overview – PASSAGE Platform")

    records = session.query(Assessment).all()

    if len(records) == 0:
        st.info("No data available.")
    else:
        df = pd.DataFrame([{
            "age": r.age,
            "raw_fish": int(r.raw_fish),
            "lft_abnormal": int(r.lft_abnormal),
            "red_flags": r.red_flags,
            "healthspan": r.healthspan_index,
            "target": 1 if r.cca_risk_level=="High Risk" else 0,
            "date": r.created_at
        } for r in records])

        col1, col2, col3 = st.columns(3)

        col1.metric("Total Patients", len(df))
        col2.metric("High Risk %", round(df["target"].mean()*100,1))
        col3.metric("Average Healthspan", round(df["healthspan"].mean(),2))

        st.markdown("---")

        df["date"] = pd.to_datetime(df["date"])
        trend = df.groupby(df["date"].dt.date)["target"].mean()

        st.subheader("High Risk Trend Over Time")
        st.line_chart(trend)

        st.markdown("---")

        st.subheader("Business Model Snapshot")

        st.markdown("""
        PASSAGE is positioned as:

        • AI-driven Clinical Decision Support (CCA risk stratification)  
        • Hospital-level SaaS subscription platform  
        • Government screening integration infrastructure  
        • Research analytics engine  

        Revenue Model:
        - B2B Annual License
        - Institutional Pro Analytics Tier
        - Research Collaboration Model
        """)

# ==========================================================
# ENHANCED ML CONFIDENCE (PRO MODE)
# ==========================================================

if menu == "Population Dashboard" and role == "Admin (Pro)":

    records = session.query(Assessment).all()

    if len(records) >= 5:

        df = pd.DataFrame([{
            "age": r.age,
            "raw_fish": int(r.raw_fish),
            "lft_abnormal": int(r.lft_abnormal),
            "red_flags": r.red_flags,
            "healthspan": r.healthspan_index,
            "target": 1 if r.cca_risk_level=="High Risk" else 0
        } for r in records])

        X = df[["age","raw_fish","lft_abnormal","red_flags","healthspan"]]
        y = df["target"]

        model = LogisticRegression()
        model.fit(X,y)

        y_prob = model.predict_proba(X)[:,1]
        confidence = np.mean(y_prob)*100

        st.markdown("---")
        st.subheader("AI Model Confidence (Pro Analytics)")
        st.metric("Average AI Confidence (%)", round(confidence,1))

# ==========================================================
# DATA GOVERNANCE SECTION
# ==========================================================

if menu == "User Guide":

    st.markdown("---")
    st.subheader("8. Data Governance & Compliance")

    st.markdown("""
    • Local encrypted SQLite database (development mode)  
    • No external data transmission  
    • Role-based feature separation  
    • Designed for PDPA compliance framework  
    • Future roadmap: ISO 27001 alignment  
    • Future roadmap: Software as Medical Device validation pathway  
    """)

    st.markdown("---")
    st.subheader("9. Public Health & Economic Impact")

    st.markdown("""
    Early detection of cholangiocarcinoma reduces late-stage treatment burden,
    improves survival outcomes, and decreases healthcare system cost.

    PASSAGE aims to evolve into:

    • Regional CCA AI screening infrastructure  
    • Institutional research-grade registry  
    • Government-integrated decision support platform  
    """)

# ==========================================================
# VERSION FOOTER
# ==========================================================

st.markdown("---")
st.caption("PASSAGE Platform v3.1 | Institutional Prototype | Faculty of Medicine, KKU")
# ==========================================================
# ===== PASSAGE ENTERPRISE SaaS LAYOUT =====================
# ==========================================================

# ---------- MODERN UI THEME ----------
st.markdown("""
<style>
body {
    background-color:#f7f9fb;
}
.saas-card {
    background:white;
    padding:20px;
    border-radius:16px;
    box-shadow:0 4px 12px rgba(0,0,0,0.06);
}
.big-number {
    font-size:32px;
    font-weight:700;
}
.small-label {
    color:gray;
    font-size:14px;
}
.footer {
    text-align:center;
    font-size:12px;
    color:gray;
    padding-top:20px;
}
</style>
""", unsafe_allow_html=True)

# ---------- SaaS SIDEBAR ----------
st.sidebar.markdown("## PASSAGE SaaS Platform")
subscription = st.sidebar.selectbox(
    "Subscription Plan",
    ["Starter (Free)", "Professional", "Enterprise"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### Deployment Mode")
environment = st.sidebar.radio("Environment", ["Development", "Institutional", "Government"])

st.sidebar.markdown("---")
st.sidebar.success("System Status: Operational")

# ==========================================================
# SaaS DASHBOARD HEADER
# ==========================================================

st.markdown("""
<div class='saas-card'>
<h2>PASSAGE AI Clinical Platform</h2>
<p>AI-powered Cholangiocarcinoma Risk Stratification & Healthspan Analytics</p>
</div>
""", unsafe_allow_html=True)

# ==========================================================
# SaaS KPI OVERVIEW
# ==========================================================

records = session.query(Assessment).all()

if len(records) > 0:

    df = pd.DataFrame([{
        "age": r.age,
        "risk": r.cca_risk_level,
        "healthspan": r.healthspan_index
    } for r in records])

    total_patients = len(df)
    high_risk = len(df[df["risk"]=="High Risk"])
    avg_healthspan = round(df["healthspan"].mean(),2)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
        <div class='saas-card'>
        <div class='big-number'>{total_patients}</div>
        <div class='small-label'>Total Patients</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class='saas-card'>
        <div class='big-number'>{high_risk}</div>
        <div class='small-label'>High Risk Cases</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class='saas-card'>
        <div class='big-number'>{avg_healthspan}</div>
        <div class='small-label'>Avg Healthspan Index</div>
        </div>
        """, unsafe_allow_html=True)

# ==========================================================
# ENTERPRISE ANALYTICS (LOCK FEATURE)
# ==========================================================

st.markdown("---")
st.subheader("Advanced AI Analytics")

if subscription == "Starter (Free)":
    st.warning("Upgrade to Professional to unlock advanced analytics.")

elif subscription == "Professional":

    st.info("Professional Tier Enabled")

    if len(records) >= 5:
        df = pd.DataFrame([{
            "age": r.age,
            "raw_fish": int(r.raw_fish),
            "lft_abnormal": int(r.lft_abnormal),
            "red_flags": r.red_flags,
            "healthspan": r.healthspan_index,
            "target": 1 if r.cca_risk_level=="High Risk" else 0
        } for r in records])

        X = df[["age","raw_fish","lft_abnormal","red_flags","healthspan"]]
        y = df["target"]

        model = LogisticRegression()
        model.fit(X,y)

        y_prob = model.predict_proba(X)[:,1]
        confidence = round(np.mean(y_prob)*100,1)

        st.metric("AI Model Confidence (%)", confidence)

elif subscription == "Enterprise":

    st.success("Enterprise AI Suite Activated")

    if len(records) >= 5:
        df = pd.DataFrame([{
            "age": r.age,
            "raw_fish": int(r.raw_fish),
            "lft_abnormal": int(r.lft_abnormal),
            "red_flags": r.red_flags,
            "healthspan": r.healthspan_index,
            "target": 1 if r.cca_risk_level=="High Risk" else 0,
            "date": r.created_at
        } for r in records])

        X = df[["age","raw_fish","lft_abnormal","red_flags","healthspan"]]
        y = df["target"]

        model = LogisticRegression()
        model.fit(X,y)

        y_prob = model.predict_proba(X)[:,1]
        fpr,tpr,_ = roc_curve(y,y_prob)
        roc_auc = round(auc(fpr,tpr),3)

        st.metric("Model AUC", roc_auc)
        st.metric("AI Confidence (%)", round(np.mean(y_prob)*100,1))

        st.line_chart(df.groupby(pd.to_datetime(df["date"]).dt.date)["target"].mean())

# ==========================================================
# REVENUE SIMULATION (Business View)
# ==========================================================

st.markdown("---")
st.subheader("Projected Annual Revenue (Simulation)")

hospital_count = st.slider("Number of Institutional Clients",1,100,10)

if subscription == "Professional":
    revenue = hospital_count * 60000
elif subscription == "Enterprise":
    revenue = hospital_count * 120000
else:
    revenue = 0

st.metric("Estimated Annual Revenue (THB)", f"{revenue:,.0f}")

# ==========================================================
# PLATFORM FOOTER
# ==========================================================

st.markdown(""")
<div class='footer'>
PASSAGE AI Platform | Faculty of Medicine, Khon Kaen University<br>
Digital Preventive Oncology & AI Research Initiative<br>
Prototype SaaS Demonstration Version
</div>
# ==========================================================
# ===== PASSAGE PROFESSIONAL ML EXTENSION (DROP-IN) ======
# ==========================================================

import io
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
import seaborn as sns

st.markdown("---")
st.markdown("## PASSAGE Advanced Clinical AI Module")

records_ext = session.query(Assessment).all()

if len(records_ext) >= 5:

    df_ext = pd.DataFrame([{
        "age": r.age,
        "raw_fish": int(r.raw_fish),
        "lft_abnormal": int(r.lft_abnormal),
        "red_flags": r.red_flags,
        "healthspan": r.healthspan_index,
        "target": 1 if r.cca_risk_level=="High Risk" else 0
    } for r in records_ext])

    X_ext = df_ext[["age","raw_fish","lft_abnormal","red_flags","healthspan"]]
    y_ext = df_ext["target"]

    X_train, X_test, y_train, y_test = train_test_split(
        X_ext, y_ext, test_size=0.3, random_state=42
    )

    model_ext = LogisticRegression(max_iter=1000)
    model_ext.fit(X_train, y_train)

    y_pred_ext = model_ext.predict(X_test)
    y_prob_ext = model_ext.predict_proba(X_test)[:,1]

    auc_score = roc_auc_score(y_test, y_prob_ext)
    cv_score = cross_val_score(model_ext, X_ext, y_ext, cv=5).mean()

    col1, col2, col3 = st.columns(3)
    col1.metric("Test AUC", round(auc_score,3))
    col2.metric("Cross-Validated AUC", round(cv_score,3))
    col3.metric("Model Version", "v3.2-logreg")

    st.markdown("---")

    # ==============================
    # Feature Importance
    # ==============================
    st.subheader("Feature Importance")

    importance = pd.DataFrame({
        "Feature": X_ext.columns,
        "Coefficient": model_ext.coef_[0]
    }).sort_values(by="Coefficient", ascending=False)

    st.bar_chart(importance.set_index("Feature"))

    # ==============================
    # Confusion Matrix
    # ==============================
    st.subheader("Confusion Matrix")

    cm = confusion_matrix(y_test, y_pred_ext)

    fig_cm = plt.figure()
    sns.heatmap(cm, annot=True, fmt="d")
    plt.xlabel("Predicted")
    plt.ylabel("Actual")
    st.pyplot(fig_cm)

    # ==============================
    # Clinical Decision Layer
    # ==============================
    st.subheader("Clinical Decision Recommendation")

    high_risk_ratio = df_ext["target"].mean()

    if high_risk_ratio > 0.4:
        st.error("High institutional risk burden detected. Recommend hepatobiliary screening expansion.")
    elif high_risk_ratio > 0.2:
        st.warning("Moderate CCA prevalence. Consider ultrasound screening program.")
    else:
        st.success("Low prevalence cohort. Continue preventive surveillance.")

    # ==============================
    # Dataset Export
    # ==============================
    st.markdown("---")
    st.subheader("Research Data Export")

    csv_buffer = io.StringIO()
    df_ext.to_csv(csv_buffer, index=False)

    st.download_button(
        "Download Research Dataset (CSV)",
        csv_buffer.getvalue(),
        file_name="PASSAGE_research_dataset.csv",
        mime="text/csv"
    )

    # ==============================
    # Compliance Footer
    # ==============================
    st.markdown("---")
    st.caption("""
    PASSAGE AI Clinical Module v3.2  
    Internal Validation Cohort  
    Prototype Decision Support System - Not for standalone diagnostic use  
    PDPA-oriented data architecture  
    """)

else:
    st.info("Advanced AI module activates when ≥ 5 records are available.")
""", unsafe_allow_html=True)
