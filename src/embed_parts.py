# src/embed_parts.py

import chromadb
import hashlib
import openai
import os

class PartEmbedder:
    def __init__(self, chroma_dir, collection_name):
        self.chroma_dir = chroma_dir
        self.collection_name = collection_name
        self.client = chromadb.PersistentClient(path=chroma_dir)
        # Delete collection if exists (for clean start in tests)
        if collection_name in [c.name for c in self.client.list_collections()]:
            self.client.delete_collection(collection_name)
        self.collection = self.client.create_collection(collection_name)

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
        documents = df["Part Description"].tolist()
        ids = [self.generate_id(row) for _, row in df.iterrows()]
        metadatas = df.drop(columns=["Part Description"]).to_dict(orient='records')
        embeddings = self.get_embeddings(documents)
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )

    def query(self, query_text, n_results=1):
        emb = self.get_embedding(query_text)
        return self.collection.query(
            query_embeddings=[emb],
            n_results=n_results
        )

