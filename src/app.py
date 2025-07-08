import streamlit as st
import pandas as pd

st.set_page_config(page_title="Quoting Assistant", layout="centered")

st.title("🛠️ Quoting Assistant")
st.write(
    "Welcome! This app helps you quote manufacturing parts by learning from your past jobs.\n\n"
    "Start by uploading a CSV file of your manufacturing parts below."
)

uploaded_file = st.file_uploader("Upload your manufacturing parts CSV", type=["csv"])
