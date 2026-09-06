import streamlit as st
from views import page1_ingest, page2_chat, page3_citations, page4_compare, page5_doc_viewer
from utils.database import init_db, db_get_all_groups_and_ips, db_get_file_registry
from utils.vector_store import initialize_vector_persistence

# Page Configuration
st.set_page_config(
    page_title="PragyanAI Semiconductor IP RAG Assistant",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize SQLite Database & Vector Persistence Structures
init_db()
initialize_vector_persistence()

# Global Session State Initializations & Sync with SQLite
if "ip_databases" not in st.session_state:
    st.session_state.ip_databases = {}  # Format: {ip_name: FAISS_vector_store}

if "ip_groups" not in st.session_state:
    st.session_state.ip_groups = db_get_all_groups_and_ips()  # Format: {ip_name: group_name}
else:
    # Sync with database if session dictionary is empty
    if not st.session_state.ip_groups:
        st.session_state.ip_groups = db_get_all_groups_and_ips()

if "ip_raw_docs" not in st.session_state:
    st.session_state.ip_raw_docs = {}   # Format: {ip_name: [Document, ...]}

if "ip_file_registry" not in st.session_state:
    st.session_state.ip_file_registry = {}  # Format: {ip_name: {source_name: {type, pages, brief}}}

# Sync SQLite registry files into session state on load
for ip_name in st.session_state.ip_groups.keys():
    if ip_name not in st.session_state.ip_file_registry or not st.session_state.ip_file_registry[ip_name]:
        st.session_state.ip_file_registry[ip_name] = db_get_file_registry(ip_name)

if "ip_metadata" not in st.session_state:
    st.session_state.ip_metadata = {}   # Legacy support metadata container

if "last_references" not in st.session_state:
    st.session_state.last_references = []

if "multi_chat_histories" not in st.session_state:
    st.session_state.multi_chat_histories = {}

# Sidebar Navigation Header
st.sidebar.image("PragyanAI_Transperent.png")
st.sidebar.title("PragyanAI Silicon RAG")
st.sidebar.caption("Hardware IP & Datasheet Engineering Suite")

# Navigation Radio Menu (Including Page 5: Document Viewer & Summarizer)
page_selection = st.sidebar.radio(
    "Navigation Menu",
    [
        "Ingestion & IP Management",
        "Interactive IP RAG Chat",
        "References & Citation Dashboard",
        "Spec & Version Comparison",
        "Document Viewer & Page Summarizer"
    ]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Registered IP Families")

# Render active IP status grouped by Family in the sidebar pulled from SQLite backend
all_db_groups = db_get_all_groups_and_ips()

if all_db_groups:
    grouped_ips = {}
    for ip_name, group_name in all_db_groups.items():
        if group_name not in grouped_ips:
            grouped_ips[group_name] = []
        grouped_ips[group_name].append(ip_name)

    for group, ips in grouped_ips.items():
        st.sidebar.markdown(f"**📂 {group}**")
        for ip in ips:
            reg_files = db_get_file_registry(ip)
            doc_count = len(reg_files)
            st.sidebar.write(f"&nbsp;&nbsp;&nbsp;&nbsp;• {ip} (`{doc_count} docs`)")
else:
    st.sidebar.caption("No IP models registered yet. Go to Ingestion to start.")

# Route to the selected page view
if page_selection == "Ingestion & IP Management":
    page1_ingest.render()
elif page_selection == "Interactive IP RAG Chat":
    page2_chat.render()
elif page_selection == "References & Citation Dashboard":
    page3_citations.render()
elif page_selection == "Spec & Version Comparison":
    page4_compare.render()
elif page_selection == "Document Viewer & Page Summarizer":
    page5_doc_viewer.render()
