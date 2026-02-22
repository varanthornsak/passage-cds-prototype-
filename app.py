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
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
import tempfile

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(page_title="PASSAGE 3.0 | KKU", layout="wide")

st.markdown("""
# PASSAGE 3.0 Clinical Decision Support System  
### Faculty of Medicine, Khon Kaen University  
Digital Health Innovation & Preventive Oncology Research Unit
---
""")

# --------------------------------------------------
# DATABASE
# --------------------------------------------------
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

Base.metadata.create_all(engine)

# --------------------------------------------------
# HEALTHSPAN SCORING
# --------------------------------------------------
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

# --------------------------------------------------
# MENU
# --------------------------------------------------
menu = st.sidebar.selectbox(
    "Navigation",
    ["New Assessment", "Population Dashboard"]
)

# --------------------------------------------------
# NEW ASSESSMENT
# --------------------------------------------------
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

# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------
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
        plt.xlabel("FPR")
        plt.ylabel("TPR")
        plt.legend()
        st.pyplot(fig)

        st.metric("Model AUC", round(roc_auc,3))
        st.metric("Average Healthspan", round(df["healthspan"].mean(),2))

        if st.button("Generate Research Report"):

            temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            doc = SimpleDocTemplate(temp.name, pagesize=A4)
            styles = getSampleStyleSheet()
            elements = []

            elements.append(Paragraph("PASSAGE 3.0 Research Summary", styles["Title"]))
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
                st.download_button("Download PDF", f,
                    file_name="PASSAGE_Research_Report.pdf",
                    mime="application/pdf")
