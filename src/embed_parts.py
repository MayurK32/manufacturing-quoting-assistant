# src/embed_parts.py

import chromadb
import hashlib
import openai
import os
from dotenv import load_dotenv

load_dotenv() 

class PartEmbedder:
    def __init__(self, chroma_dir, collection_name):
        self.chroma_dir = chroma_dir
        self.collection_name = collection_name
        self.client = chromadb.PersistentClient(path=chroma_dir)
        self.collection = self.client.get_or_create_collection(collection_name)
    
    def row_to_embedding_text(self,row):
    # Join with clear labels for each field for LLM-style embeddings
        return (
            f"Material: {row['Material']} | "
            f"Size: {row['Size']} | "
            f"Operations: {row['Operations']} | "
            f"Finish: {row['Finish']} | "
            f"Description: {row['Part Description']}"
        )

    @staticmethod
    def get_embeddings(texts, model="text-embedding-3-small"):
        """
        Get embeddings for a list of texts (batch mode).
        """
        openai.api_key = os.getenv("OPENAI_API_KEY")
        if not openai.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set!")

        try:
            response = openai.embeddings.create(
                input=texts,
                model=model
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            print(f"Error generating batch embeddings.\nError: {e}")
            raise
    
    @staticmethod
    def generate_id(row):
        text = row["Part Description"]
        return hashlib.md5(text.encode("utf-8")).hexdigest()

    
    def process_dataframe(self, df):
        if df.empty:
            return
        # Compose rich strings for embedding input
        documents = [self.row_to_embedding_text(row) for _, row in df.iterrows()]
        ids = [self.generate_id(row) for _, row in df.iterrows()]
        # Keep metadatas as before
        metadatas = df.drop(columns=["Part Description"]).to_dict(orient='records')
        embeddings = self.get_embeddings(documents)
        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )

    def query(self, query_text, n_results=1):
        emb = self.get_embeddings([query_text])[0]   # <-- Extract just the single embedding
        return self.collection.query(
            query_embeddings=[emb],
            n_results=n_results
        )

