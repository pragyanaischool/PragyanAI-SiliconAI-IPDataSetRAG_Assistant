import os
import streamlit as st
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

@st.cache_resource
def get_embedding_model():
    """Initializes and caches the local HuggingFace embedding model for CPU execution."""
    return HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

def initialize_vector_persistence():
    """Ensures all global session state structures exist for group/IP management."""
    if "ip_databases" not in st.session_state:
        st.session_state.ip_databases = {}  # {ip_name: FAISS_vector_store}
    if "ip_groups" not in st.session_state:
        st.session_state.ip_groups = {}     # {ip_name: group_name}
    if "ip_raw_docs" not in st.session_state:
        st.session_state.ip_raw_docs = {}   # {ip_name: [Document, ...]}
    if "ip_file_registry" not in st.session_state:
        st.session_state.ip_file_registry = {}  # {ip_name: {source_name: metadata}}

def rebuild_and_retain_vector_store(ip_name: str):
    """
    Rebuilds and retains the FAISS CPU vector store for a given IP model 
    using all accumulated raw documents in session state.
    """
    initialize_vector_persistence()
    embeddings = get_embedding_model()
    
    if ip_name in st.session_state.ip_raw_docs and st.session_state.ip_raw_docs[ip_name]:
        # Vectorize and build FAISS vector store on CPU from documents
        vector_store = FAISS.from_documents(
            st.session_state.ip_raw_docs[ip_name], 
            embeddings
        )
        st.session_state.ip_databases[ip_name] = vector_store
    else:
        if ip_name in st.session_state.ip_databases:
            del st.session_state.ip_databases[ip_name]

def add_documents_to_faiss(ip_name: str, new_docs: list):
    """
    Incrementally embeds and appends new documents into an 
    existing FAISS CPU index without rebuilding from scratch.
    """
    initialize_vector_persistence()
    embeddings = get_embedding_model()

    if ip_name not in st.session_state.ip_raw_docs:
        st.session_state.ip_raw_docs[ip_name] = []
    
    st.session_state.ip_raw_docs[ip_name].extend(new_docs)

    if ip_name in st.session_state.ip_databases:
        # Incrementally add vectors to existing FAISS store
        st.session_state.ip_databases[ip_name].add_documents(new_docs)
    else:
        # Create fresh if it doesn't exist yet
        rebuild_and_retain_vector_store(ip_name)

def query_faiss_vector_store(ip_name: str, query_text: str, k: int = 3):
    """
    Performs a semantic similarity search against the FAISS CPU vector store.
    """
    if "ip_databases" not in st.session_state or ip_name not in st.session_state.ip_databases:
        return []
    
    vector_store = st.session_state.ip_databases[ip_name]
    results = vector_store.similarity_search(query_text, k=k)
    return results
