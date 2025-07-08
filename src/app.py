import streamlit as st
import pandas as pd
from embed_parts import PartEmbedder

st.set_page_config(page_title="Quoting Assistant", layout="centered")

st.title("🛠️ Quoting Assistant")
st.write(
    "Welcome! This app helps you quote manufacturing parts by learning from your past jobs.\n\n"
    "Start by uploading a CSV file of your manufacturing parts below."
)

uploaded_file = st.file_uploader("Upload your manufacturing parts CSV", type=["csv"])

# Directory to store ChromaDB files
CHROMA_DIR = "data/chroma_db"
COLLECTION_NAME = "parts_db"

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.success("CSV uploaded successfully! Here is a preview of your data:")
    st.dataframe(df)

    if st.button("Embed & Index All Parts"):
        with st.spinner("Indexing and embedding parts..."):
            embedder = PartEmbedder(
                chroma_dir=CHROMA_DIR,
                collection_name=COLLECTION_NAME
            )
            embedder.process_dataframe(df)
        st.success("All parts have been embedded and indexed!")
    
