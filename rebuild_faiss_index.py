#!/usr/bin/env python3
"""
Rebuild FAISS Index in LangChain Format
This script converts the custom FAISS index to LangChain-compatible format.
"""

import os
import pickle
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings

def rebuild_faiss_index():
    print("=" * 80)
    print("REBUILDING FAISS INDEX IN LANGCHAIN FORMAT")
    print("=" * 80)
    print()
    
    # Paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    vector_store_path = os.path.join(script_dir, "vector_store")
    
    # Load original data
    print("📥 Loading original data...")
    print("-" * 80)
    
    with open(os.path.join(vector_store_path, "documents.pkl"), 'rb') as f:
        documents_text = pickle.load(f)
    
    with open(os.path.join(vector_store_path, "document_metadata.pkl"), 'rb') as f:
        documents_metadata = pickle.load(f)
    
    print(f"✅ Loaded {len(documents_text)} documents")
    print(f"✅ Loaded {len(documents_metadata)} metadata entries")
    print()
    
    # Create LangChain Document objects
    print("🔨 Creating LangChain Document objects...")
    print("-" * 80)
    
    langchain_docs = []
    for text, metadata in zip(documents_text, documents_metadata):
        doc = Document(
            page_content=text,
            metadata=metadata
        )
        langchain_docs.append(doc)
    
    print(f"✅ Created {len(langchain_docs)} LangChain Document objects")
    print()
    
    # Initialize embedding model (same as orchestrator)
    print("🤖 Initializing embedding model...")
    print("-" * 80)
    print("Model: sentence-transformers/all-MiniLM-L6-v2")
    print("This may take a few minutes on first run (downloading model)...")
    
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )
    
    print("✅ Embedding model initialized")
    print()
    
    # Create FAISS index
    print("🏗️  Creating FAISS index from documents...")
    print("-" * 80)
    print("This will take several minutes to embed all documents...")
    
    faiss_index = FAISS.from_documents(
        documents=langchain_docs,
        embedding=embeddings
    )
    
    print("✅ FAISS index created")
    print()
    
    # Backup old index files
    print("💾 Backing up old index files...")
    print("-" * 80)
    
    old_index_faiss = os.path.join(vector_store_path, "index.faiss")
    old_index_pkl = os.path.join(vector_store_path, "index.pkl")
    
    if os.path.exists(old_index_faiss):
        os.rename(old_index_faiss, os.path.join(vector_store_path, "index.faiss.old"))
        print("✅ Backed up index.faiss → index.faiss.old")
    
    if os.path.exists(old_index_pkl):
        os.rename(old_index_pkl, os.path.join(vector_store_path, "index.pkl.old"))
        print("✅ Backed up index.pkl → index.pkl.old")
    
    print()
    
    # Save new index
    print("💾 Saving new FAISS index...")
    print("-" * 80)
    
    faiss_index.save_local(vector_store_path)
    
    print("✅ Saved to:", vector_store_path)
    print()
    
    # Verify
    print("🔍 Verifying new index...")
    print("-" * 80)
    
    # Test load
    test_index = FAISS.load_local(
        vector_store_path,
        embeddings,
        allow_dangerous_deserialization=True
    )
    
    # Test search
    test_results = test_index.similarity_search("NSAID drug manufacturers", k=3)
    
    print(f"✅ Index loaded successfully")
    print(f"✅ Test search returned {len(test_results)} results")
    print()
    
    if test_results:
        print("📄 Sample search result:")
        print(f"   Content: {test_results[0].page_content[:150]}...")
        print(f"   Metadata: {test_results[0].metadata}")
    
    print()
    print("=" * 80)
    print("✅ REBUILD COMPLETE!")
    print("=" * 80)
    print()
    print("The FAISS index has been successfully rebuilt in LangChain format.")
    print("Your Streamlit app should now be able to search the knowledge base.")
    print()

if __name__ == "__main__":
    rebuild_faiss_index()
