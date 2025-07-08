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
    
 # ---------  QUERY UI ---------

    st.header("Quote a New Part")
    query = st.text_input(
        "Describe your new part (e.g., 'Aluminum bracket, 100x50x5 mm, drilling, anodized')"
    )

    if st.button("Get Quote"):
        if query.strip() == "":
            st.warning("Please enter a part description to quote.")
        else:
            with st.spinner("Searching for the most similar part..."):
                embedder = PartEmbedder(
                    chroma_dir=CHROMA_DIR,
                    collection_name=COLLECTION_NAME
                )
                result = embedder.query(query, n_results=1)
                if not result["documents"][0]:
                    st.error("No similar parts found. Try indexing data or refining your query.")
                else:
                    st.success("Closest past part found!")
                    st.subheader("Closest Past Part Description:")
                    st.write(result["documents"][0][0])
                    st.subheader("Metadata:")
                    st.json(result["metadatas"][0][0])
                    st.metric(
                        "Estimated Price (CHF)",
                        result["metadatas"][0][0].get("Target Price (CHF)", "N/A"),
                    )
                    st.caption("Price is taken from the most similar past part in your data.")