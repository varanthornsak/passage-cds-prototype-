# ==========================================================
# PASSAGE v5.0 – FULL MERGED PLATFORM
# Faculty of Medicine, Khon Kaen University
# ==========================================================

import streamlit as st
import pandas as pd
import numpy as np
try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
import seaborn as sns
import matplotlib.pyplot as plt
import io

from sqlalchemy import create_engine, Column, Integer, Float, String, Boolean, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.metrics import (
    roc_curve, auc, roc_auc_score,
    confusion_matrix, brier_score_loss
)

# ==========================================================
# CONFIG
# ==========================================================
st.set_page_config(page_title="PASSAGE v5.0 | KKU", layout="wide")
st.title("PASSAGE v5.0 – Integrated CCA Screening & AI Platform")

# ==========================================================
# DATABASE
# ==========================================================
DATABASE_URL = "sqlite:///passage_master.db"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()

# ==========================================================
# TABLES
# ==========================================================

class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True)
    patient_name = Column(String)
    age = Column(Integer)

    # Risk factors
    raw_fish = Column(Boolean)
    lft_abnormal = Column(Boolean)
    red_flags = Column(Integer)

    # Biomarkers
    ca19_9 = Column(Float)
    cea = Column(Float)
    alp = Column(Float)
    bilirubin = Column(Float)
    platelet = Column(Float)

    # Imaging
    bile_duct_dilation = Column(Boolean)
    liver_mass = Column(Boolean)

    # Healthspan
    healthspan_index = Column(Float)

    # Registry
    confirmed_cca = Column(Boolean)

    model_version = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_log"
    id = Column(Integer, primary_key=True)
    action = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)


Base.metadata.create_all(engine)

# ==========================================================
# HEALTHSPAN ENGINE (Original Logic Preserved)
# ==========================================================

def calculate_healthspan(age, red_flags):
    score = 100
    score -= age * 0.4
    score -= red_flags * 3
    return round(max(score,0),2)

# ==========================================================
# SIDEBAR
# ==========================================================

menu = st.sidebar.selectbox(
    "Navigation",
    ["New Assessment", "Population Dashboard", "Executive Overview"]
)

subscription = st.sidebar.selectbox(
    "Subscription Plan",
    ["Starter", "Professional", "Enterprise"]
)

# ==========================================================
# NEW ASSESSMENT
# ==========================================================

if menu == "New Assessment":

    st.header("New CCA Screening Entry")

    with st.form("form"):

        patient_name = st.text_input("Patient Name")
        age = st.number_input("Age", 20, 100)

        raw_fish = st.checkbox("Raw Fish Consumption")
        lft_abnormal = st.checkbox("Abnormal LFT")
        red_flags = st.slider("Red Flag Symptoms", 0, 5)

        st.subheader("Biomarkers")
        ca19_9 = st.number_input("CA19-9", 0.0)
        cea = st.number_input("CEA", 0.0)
        alp = st.number_input("ALP", 0.0)
        bilirubin = st.number_input("Total Bilirubin", 0.0)
        platelet = st.number_input("Platelet Count", 0.0)

        st.subheader("Imaging")
        bile_duct_dilation = st.checkbox("Bile Duct Dilation")
        liver_mass = st.checkbox("Liver Mass")

        confirmed_cca = st.checkbox("Confirmed CCA (Registry)")

        submit = st.form_submit_button("Save")

        if submit:

            healthspan = calculate_healthspan(age, red_flags)

            record = Assessment(
                patient_name=patient_name,
                age=age,
                raw_fish=raw_fish,
                lft_abnormal=lft_abnormal,
                red_flags=red_flags,
                ca19_9=ca19_9,
                cea=cea,
                alp=alp,
                bilirubin=bilirubin,
                platelet=platelet,
                bile_duct_dilation=bile_duct_dilation,
                liver_mass=liver_mass,
                healthspan_index=healthspan,
                confirmed_cca=confirmed_cca,
                model_version="v5.0"
            )

            session.add(record)
            session.add(AuditLog(action=f"Added {patient_name}"))
            session.commit()

            st.success("Saved Successfully")
            st.metric("Healthspan Index", healthspan)

# ==========================================================
# POPULATION DASHBOARD + ADVANCED AI
# ==========================================================

if menu == "Population Dashboard":

    records = session.query(Assessment).all()

    if len(records) < 10:
        st.info("Need ≥10 records with confirmed outcomes")
    else:

        df = pd.DataFrame([{
            "age": r.age,
            "raw_fish": int(r.raw_fish),
            "lft_abnormal": int(r.lft_abnormal),
            "red_flags": r.red_flags,
            "ca19_9": r.ca19_9,
            "cea": r.cea,
            "alp": r.alp,
            "bilirubin": r.bilirubin,
            "platelet": r.platelet,
            "bile_duct_dilation": int(r.bile_duct_dilation),
            "liver_mass": int(r.liver_mass),
            "healthspan": r.healthspan_index,
            "target": int(r.confirmed_cca)
        } for r in records])

        X = df.drop(columns=["target"])
        y = df["target"]

        model = LogisticRegression(max_iter=1000)

        skf = StratifiedKFold(n_splits=5)
        cv_auc = cross_val_score(model, X, y, cv=skf, scoring="roc_auc").mean()

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.3, stratify=y, random_state=42
        )

        model.fit(X_train, y_train)
        y_prob = model.predict_proba(X_test)[:,1]
        y_pred = model.predict(X_test)

        auc_score = roc_auc_score(y_test, y_prob)
        brier = brier_score_loss(y_test, y_prob)

        col1, col2, col3 = st.columns(3)
        col1.metric("Test AUC", round(auc_score,3))
        col2.metric("Cross-Validated AUC", round(cv_auc,3))
        col3.metric("Brier Score", round(brier,3))

        # ROC
        fpr,tpr,_ = roc_curve(y_test,y_prob)
        fig = plt.figure()
        plt.plot(fpr,tpr,label=f"AUC={auc_score:.2f}")
        plt.plot([0,1],[0,1],'--')
        plt.legend()
        st.pyplot(fig)

        # Confusion Matrix
        cm = confusion_matrix(y_test,y_pred)
        fig_cm = plt.figure()
        sns.heatmap(cm, annot=True, fmt="d")
        st.pyplot(fig_cm)
# =============================
# SHAP
# =============================
if SHAP_AVAILABLE:
    st.subheader("Model Explainability (SHAP)")

    explainer = shap.LinearExplainer(model, X_train)
    shap_values = explainer.shap_values(X_test)

    fig_shap = plt.figure()
    shap.summary_plot(shap_values, X_test, show=False)
    st.pyplot(fig_shap)

else:
    st.warning("SHAP not installed. Explainability module disabled.")


# =============================
# RECALL LIST (ต้องไม่ indent)
# =============================
st.subheader("High Risk Recall List (Prob > 0.7)")
recall_df = X_test[y_prob > 0.7]
st.dataframe(recall_df)

# ==========================================================
# EXECUTIVE OVERVIEW
# ==========================================================

if menu == "Executive Overview":

    records = session.query(Assessment).all()

    if len(records) == 0:
        st.info("No Data")
    else:
        df = pd.DataFrame([{
            "risk": r.confirmed_cca,
            "healthspan": r.healthspan_index
        } for r in records])

        st.metric("Total Patients", len(df))
        st.metric("Confirmed CCA %", round(df["risk"].mean()*100,1))
        st.metric("Average Healthspan", round(df["healthspan"].mean(),2))

# ==========================================================
# AUDIT LOG
# ==========================================================

st.markdown("---")
st.subheader("Audit Log")
logs = session.query(AuditLog).all()
log_df = pd.DataFrame([{
    "Action": l.action,
    "Time": l.timestamp
} for l in logs])
st.dataframe(log_df)

st.markdown("---")
st.caption("PASSAGE v5.0 | Fully Integrated AI CCA Platform | KKU")
