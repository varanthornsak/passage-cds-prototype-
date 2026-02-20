import streamlit as st

st.title("PASSAGE-CDS Prototype")

age = st.number_input("Age", 40, 100)
adl = st.slider("ADL Score", 0, 6)

risk = 0
if age > 75:
    risk += 2
if adl < 4:
    risk += 2

if risk <= 2:
    st.success("Low Risk")
else:
    st.error("High Risk")
