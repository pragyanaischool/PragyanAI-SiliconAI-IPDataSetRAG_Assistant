"""
Utility Modules Package for PragyanAI Semiconductor IP RAG Assistant.
Contains SQLite persistence and FAISS CPU vectorization engines.
"""
from .database import (
    init_db,
    db_add_ip,
    db_add_document,
    db_remove_document,
    db_get_all_groups_and_ips,
    db_get_file_registry
)
from .vector_store import (
    get_embedding_model,
    initialize_vector_persistence,
    rebuild_and_retain_vector_store,
    add_documents_to_faiss,
    query_faiss_vector_store
)
