import pytest
import pandas as pd
import tempfile
import shutil
from unittest.mock import patch
from src.embed_parts import PartEmbedder
import atexit

@pytest.fixture
def temp_chroma_dir():
    d = tempfile.mkdtemp()
    atexit.register(lambda: shutil.rmtree(d, ignore_errors=True))
    yield d
    # Try immediate cleanup too
    try:
        shutil.rmtree(d)
    except Exception:
        pass  # Final cleanup will happen at exit

@pytest.fixture
def small_test_df():
    return pd.DataFrame({
        "Part Description": [
            "Aluminum bracket, 100x50x5 mm, drilling, anodized",
            "Steel gear, 30x30x10 mm, milling, painted"
        ],
        "Material": ["Aluminum", "Steel"],
        "Size": ["100x50x5", "30x30x10"],
        "Operations": ["Drilling", "Milling"],
        "Finish": ["Anodized", "Painted"],
        "Target Price (CHF)": [60, 80]
    })

def dummy_get_embedding(text, model=None):
    # Returns a unique (but fixed-size) vector for each text
    return [1.0] * 10 if "Aluminum" in text else [0.0] * 10

def test_embedding_and_storage(temp_chroma_dir, small_test_df):
    # Patch PartEmbedder.get_embedding with dummy version
    with patch.object(PartEmbedder, "get_embedding", staticmethod(dummy_get_embedding)):
        embedder = PartEmbedder(
            chroma_dir=temp_chroma_dir,
            collection_name="test_parts"
        )
        embedder.process_dataframe(small_test_df)

        # ChromaDB: check the number of documents
        # Query all docs back
        results = embedder.collection.get(include=['documents', 'metadatas'])
        assert len(results['documents']) == len(small_test_df)
        assert all(isinstance(doc, str) for doc in results['documents'])

    print("test_embedding_and_storage passed.")

def test_metadata_integrity(temp_chroma_dir, small_test_df):
    """
    Test that metadata is saved and matches input DataFrame.
    """
    # Patch PartEmbedder.get_embedding with dummy version
    with patch.object(PartEmbedder, "get_embedding", staticmethod(dummy_get_embedding)):
        embedder = PartEmbedder(
            chroma_dir=temp_chroma_dir,
            collection_name="test_parts"
        )
        embedder.process_dataframe(small_test_df)

        # ChromaDB: check the number of documents
        # Query all docs back
        results = embedder.collection.get(include=['documents', 'metadatas'])

        for meta in results['metadatas']:
            assert 'Material' in meta
            assert 'Size' in meta
            assert 'Operations' in meta
            assert 'Finish' in meta
            assert 'Target Price (CHF)' in meta

def test_query_by_similarity(temp_chroma_dir, small_test_df):
    """
    Test that querying by similar text returns the expected part.
    """

    with patch.object(PartEmbedder, "get_embedding", staticmethod(dummy_get_embedding)):
        embedder = PartEmbedder(
            chroma_dir=temp_chroma_dir,
            collection_name="test_parts"
        )
        embedder.process_dataframe(small_test_df)
        result = embedder.query('Aluminum',n_results=1)

        returned_doc = result['documents'][0][0]
        assert 'Aluminum' in returned_doc


def test_batch_add_and_duplicate_handling(temp_chroma_dir, small_test_df):
    """
    Test adding parts in batches and handling duplicate IDs gracefully.
    When using hash-based IDs, adding the same data again should not create duplicates.
    """
    with patch.object(PartEmbedder, "get_embedding", staticmethod(dummy_get_embedding)):
        embedder = PartEmbedder(
            chroma_dir=temp_chroma_dir,
            collection_name="test_parts"
        )
        # Add first batch
        embedder.process_dataframe(small_test_df)
        count1 = len(embedder.collection.get(include=['documents'])['documents'])
        # Add second batch (identical data, same IDs!)
        embedder.process_dataframe(small_test_df)
        count2 = len(embedder.collection.get(include=['documents'])['documents'])
        # Should NOT increase, as entries are updated, not duplicated
        assert count2 == count1

def test_edge_cases_empty_dataframe(temp_chroma_dir):
    """
    Test handling of empty DataFrame (should not crash, returns 0 docs).
    """
    df_empty = pd.DataFrame({
        "Part Description": [],
        "Material": [],
        "Size": [],
        "Operations": [],
        "Finish": [],
        "Target Price (CHF)": []
    })

    with patch.object(PartEmbedder, "get_embedding", staticmethod(dummy_get_embedding)):
        embedder = PartEmbedder(
            chroma_dir=temp_chroma_dir,
            collection_name="test_empty"
        )
        embedder.process_dataframe(df_empty)
        results = embedder.collection.get(include=['documents'])
        assert len(results['documents']) == 0

def test_chromadb_persistence(temp_chroma_dir, small_test_df):
    """
    Test that embeddings and metadata persist across reloads of the PartEmbedder.
    """
    # src/embed_parts.py

import chromadb
import hashlib

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

def test_query_returns_all_metadata_fields(temp_chroma_dir, small_test_df):
    """
    Test that all metadata fields are present in query results.
    """
    with patch.object(PartEmbedder, "get_embedding", staticmethod(dummy_get_embedding)):
        embedder = PartEmbedder(
            chroma_dir=temp_chroma_dir,
            collection_name="meta_fields_test"
        )
        embedder.process_dataframe(small_test_df)
        result = embedder.query('Aluminum', n_results=1)
        meta = result['metadatas'][0][0]
        expected_keys = {"Material", "Size", "Operations", "Finish", "Target Price (CHF)"}
        assert set(meta.keys()) == expected_keys

def test_error_handling_bad_input(temp_chroma_dir):
    """
    Test robust error handling for missing columns or badly formatted data.
    """
    # DataFrame missing 'Part Description'
    bad_df = pd.DataFrame({
        "Material": ["Steel"],
        "Size": ["30x30x10"]
    })
    with patch.object(PartEmbedder, "get_embedding", staticmethod(dummy_get_embedding)):
        embedder = PartEmbedder(
            chroma_dir=temp_chroma_dir,
            collection_name="error_input_test"
        )
        with pytest.raises(KeyError):
            embedder.process_dataframe(bad_df)