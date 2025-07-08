import streamlit as st
import pandas as pd
from embed_parts import PartEmbedder
import json
import openai
from training_prompt import cnc_training_prompt

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
                    doc = result["documents"][0][0]
                    meta = result["metadatas"][0][0]
                    similar_price = meta.get("Target Price (CHF)", "")
                    similar_features = {
                        "Material": meta.get("Material", ""),
                        "Size": meta.get("Size", ""),
                        "Operations": meta.get("Operations", ""),
                        "Finish": meta.get("Finish", "")
                    }

                    # Build AI prompt for LLM agent
                    prompt = cnc_training_prompt(query,similar_price,doc,similar_features)


                    with st.spinner("Letting the AI agent calculate your quote..."):
                        try:
                            response = openai.chat.completions.create(
                                model="gpt-4o",
                                messages=[{"role": "system", "content": prompt}],
                                temperature=0
                            )
                            ai_output = response.choices[0].message.content.strip()

                            # Clean code fencing if present
                            if ai_output.startswith("```"):
                                ai_output = ai_output.split("```")[-2] if "```" in ai_output else ai_output
                            ai_output = ai_output.strip()
                            if ai_output.startswith("json"):
                                ai_output = ai_output[4:].strip()
                            # Now try to parse
                            try:
                                result_json = json.loads(ai_output)
                                st.success("AI-generated quote breakdown:")
                                st.json(result_json)
                                st.caption(result_json.get("Explanation", ""))
                            except json.JSONDecodeError:
                                st.error("AI response could not be parsed as JSON. Showing raw output:")
                                st.code(ai_output)
                        except Exception as e:
                            st.error(f"OpenAI API call failed: {e}")
