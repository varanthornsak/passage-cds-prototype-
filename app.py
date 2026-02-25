# ==========================================================
# PASSAGE – Stable Production Version
# Integrated CCA Screening + AI Module
# ==========================================================

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from sqlalchemy import create_engine, Column, Integer, Float, String, Boolean, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.metrics import roc_curve, roc_auc_score, confusion_matrix, brier_score_loss

# ==========================================================
# CONFIG
# ==========================================================

st.set_page_config(page_title="PASSAGE CCA Platform", layout="wide")
st.title("PASSAGE – AI CCA Screening Platform")

# ==========================================================
# DATABASE
# ==========================================================

DATABASE_URL = "sqlite:///passage.db"
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

    ca19_9 = Column(Float)
    cea = Column(Float)
    alp = Column(Float)
    bilirubin = Column(Float)

    healthspan_index = Column(Float)
    confirmed_cca = Column(Boolean)

    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(engine)

# ==========================================================
# HEALTHSPAN FUNCTION
# ==========================================================

def calculate_healthspan(age, red_flags):
    score = 100 - (age * 0.4) - (red_flags * 3)
    return max(round(score, 2), 0)

# ==========================================================
# AI MODULE FUNCTION (SAFE SCOPE)
# ==========================================================

def run_ai_module(df):

    X = df.drop(columns=["target"])
    y = df["target"]

    model = LogisticRegression(max_iter=1000)

    # Cross-validation
    skf = StratifiedKFold(n_splits=5)
    cv_auc = cross_val_score(model, X, y, cv=skf, scoring="roc_auc").mean()

    # Train-test split
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

    # ROC Curve
    fpr, tpr, _ = roc_curve(y_test, y_prob)
    fig = plt.figure()
    plt.plot(fpr, tpr)
    plt.plot([0,1],[0,1],'--')
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    st.pyplot(fig)

    # Confusion Matrix
    cm = confusion_matrix(y_test, y_pred)
    st.subheader("Confusion Matrix")
    st.write(cm)

    # Feature Importance (แทน SHAP)
    importance = pd.DataFrame({
        "Feature": X.columns,
        "Coefficient": model.coef_[0]
    }).sort_values(by="Coefficient", ascending=False)

    st.subheader("Feature Importance")
    st.bar_chart(importance.set_index("Feature"))

    # Recall List
    st.subheader("High Risk Recall List (Probability > 0.7)")
    recall_df = X_test[y_prob > 0.7]
    st.dataframe(recall_df)

# ==========================================================
# SIDEBAR
# ==========================================================

menu = st.sidebar.selectbox(
    "Navigation",
    ["New Assessment", "Population Dashboard", "Executive Overview"]
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

        ca19_9 = st.number_input("CA19-9", 0.0)
        cea = st.number_input("CEA", 0.0)
        alp = st.number_input("ALP", 0.0)
        bilirubin = st.number_input("Total Bilirubin", 0.0)

        confirmed_cca = st.checkbox("Confirmed CCA")

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
                healthspan_index=healthspan,
                confirmed_cca=confirmed_cca
            )

            session.add(record)
            session.commit()

            st.success("Saved Successfully")
            st.metric("Healthspan Index", healthspan)

# ==========================================================
# POPULATION DASHBOARD
# ==========================================================

if menu == "Population Dashboard":

    records = session.query(Assessment).all()

    if len(records) < 10:
        st.info("Need at least 10 records with confirmed outcomes")
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
            "healthspan": r.healthspan_index,
            "target": int(r.confirmed_cca)
        } for r in records])

        run_ai_module(df)

# ==========================================================
# EXECUTIVE OVERVIEW
# ==========================================================

if menu == "Executive Overview":

    records = session.query(Assessment).all()

    if len(records) == 0:
        st.info("No Data Available")
    else:

        df = pd.DataFrame([{
            "healthspan": r.healthspan_index,
            "cca": int(r.confirmed_cca)
        } for r in records])

        st.metric("Total Patients", len(df))
        st.metric("Confirmed CCA %", round(df["cca"].mean()*100,1))
        st.metric("Average Healthspan", round(df["healthspan"].mean(),2))

st.markdown("---")
st.caption("PASSAGE Stable Version | AI CCA Screening Platform")
