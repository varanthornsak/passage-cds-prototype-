# ==========================================================
# PASSAGE Hospital Edition
# Role-Based | Recall | PDF | Audit | PostgreSQL
# ==========================================================

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
import tempfile
import bcrypt

# ==========================================================
# CONFIG
# ==========================================================

st.set_page_config(page_title="PASSAGE Hospital Edition", layout="wide")

DATABASE_URL = st.secrets["DATABASE_URL"]
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()

# ==========================================================
# MODELS
# ==========================================================

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)
    password = Column(String)
    role = Column(String)

class Assessment(Base):
    __tablename__ = "assessments"
    id = Column(Integer, primary_key=True)
    patient_name = Column(String)
    age = Column(Integer)
    red_flags = Column(Integer)
    ca19_9 = Column(Float)
    risk_level = Column(String)
    followup_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True)
    user_email = Column(String)
    action = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(engine)

# ==========================================================
# LOGIN SYSTEM
# ==========================================================

def authenticate(email, password):
    user = session.query(User).filter_by(email=email).first()
    if user and bcrypt.checkpw(password.encode(), user.password.encode()):
        return user
    return None

if "user" not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:

    st.title("PASSAGE Login")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = authenticate(email, password)
        if user:
            st.session_state.user = user
            session.add(AuditLog(user_email=email, action="Login"))
            session.commit()
            st.rerun()
        else:
            st.error("Invalid credentials")

    st.stop()

user = st.session_state.user
st.sidebar.success(f"{user.email} ({user.role})")

# ==========================================================
# RISK ENGINE
# ==========================================================

def calculate_risk(age, red_flags, ca19_9):
    score = age * 0.03 + red_flags * 2 + (3 if ca19_9 > 100 else 0)
    if score >= 10:
        return "High Risk"
    elif score >= 6:
        return "Moderate Risk"
    return "Low Risk"

# ==========================================================
# NAVIGATION
# ==========================================================

menu = st.sidebar.selectbox(
    "Navigation",
    ["New Screening", "Recall List", "Dashboard"]
)

# ==========================================================
# NEW SCREENING
# ==========================================================

if menu == "New Screening":

    st.header("New CCA Screening")

    patient_name = st.text_input("Patient Name")
    age = st.number_input("Age", 20, 100)
    red_flags = st.slider("Red Flag Symptoms", 0, 5)
    ca19_9 = st.number_input("CA19-9", 0.0)

    if st.button("Evaluate"):

        risk = calculate_risk(age, red_flags, ca19_9)

        followup = None
        if risk == "Moderate Risk":
            followup = datetime.utcnow() + timedelta(days=90)
        elif risk == "Low Risk":
            followup = datetime.utcnow() + timedelta(days=365)

        assessment = Assessment(
            patient_name=patient_name,
            age=age,
            red_flags=red_flags,
            ca19_9=ca19_9,
            risk_level=risk,
            followup_date=followup
        )

        session.add(assessment)
        session.add(AuditLog(user_email=user.email,
                             action=f"New assessment for {patient_name}"))
        session.commit()

        if risk == "High Risk":
            st.error("Urgent referral required")
        elif risk == "Moderate Risk":
            st.warning("Ultrasound within 3 months")
        else:
            st.success("Routine follow-up")

        # PDF Referral (High Risk Only)
        if risk == "High Risk":

            temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            doc = SimpleDocTemplate(temp.name, pagesize=A4)
            styles = getSampleStyleSheet()
            elements = []

            elements.append(Paragraph("CCA Referral Letter", styles["Title"]))
            elements.append(Spacer(1, 0.3 * inch))
            elements.append(Paragraph(f"Patient: {patient_name}", styles["Normal"]))
            elements.append(Paragraph(f"Age: {age}", styles["Normal"]))
            elements.append(Paragraph("Risk Level: HIGH RISK", styles["Normal"]))
            elements.append(Paragraph("Recommendation: Urgent hepatobiliary evaluation.", styles["Normal"]))

            doc.build(elements)

            with open(temp.name, "rb") as f:
                st.download_button(
                    "Download Referral PDF",
                    f,
                    file_name="CCA_Referral.pdf",
                    mime="application/pdf"
                )

# ==========================================================
# RECALL LIST
# ==========================================================

if menu == "Recall List":

    st.header("Recall Scheduler")

    today = datetime.utcnow()

    recalls = session.query(Assessment).filter(
        Assessment.followup_date != None,
        Assessment.followup_date <= today
    ).all()

    if len(recalls) == 0:
        st.success("No patients due for recall today")
    else:
        df = pd.DataFrame([{
            "Patient": r.patient_name,
            "Risk": r.risk_level,
            "Follow-up Date": r.followup_date
        } for r in recalls])

        st.dataframe(df)

# ==========================================================
# DASHBOARD
# ==========================================================

if menu == "Dashboard":

    records = session.query(Assessment).all()

    if len(records) == 0:
        st.info("No data available")
    else:
        df = pd.DataFrame([{
            "risk": r.risk_level
        } for r in records])

        col1, col2 = st.columns(2)
        col1.metric("Total Screenings", len(df))
        col2.metric("High Risk %",
                    round((df["risk"]=="High Risk").mean()*100,1))

        st.bar_chart(df["risk"].value_counts())

# ==========================================================
# AUDIT VIEW (Admin Only)
# ==========================================================

if user.role == "admin":

    st.markdown("---")
    st.subheader("Audit Log")

    logs = session.query(AuditLog).all()

    df_logs = pd.DataFrame([{
        "User": l.user_email,
        "Action": l.action,
        "Time": l.timestamp
    } for l in logs])

    st.dataframe(df_logs)

st.markdown("---")
st.caption("PASSAGE Hospital Edition | Secure Clinical Platform")
