# src/embed_parts.py

import chromadb

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
    def get_embedding(text, model=None):
        # This will be patched/mocked during tests,
        # but for now, raise NotImplementedError to signal it's a placeholder.
        raise NotImplementedError("get_embedding should be patched or implemented.")

    def process_dataframe(self, df):
        documents = df["Part Description"].tolist()
        ids = [f"part_{i}" for i in range(len(df))]
        metadatas = df.drop(columns=["Part Description"]).to_dict(orient='records')
        embeddings = [self.get_embedding(desc) for desc in documents]
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

