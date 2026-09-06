import streamlit as st
from views import page1_ingest, page2_chat, page3_citations, page4_compare

# Page Configuration
st.set_page_config(
    page_title="PragyanAI Semiconductor IP RAG Assistant",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Global Session State Initializations
if "ip_databases" not in st.session_state:
    st.session_state.ip_databases = {}  # Format: {ip_name: FAISS_vector_store}

if "ip_groups" not in st.session_state:
    st.session_state.ip_groups = {}     # Format: {ip_name: group_name}

if "ip_raw_docs" not in st.session_state:
    st.session_state.ip_raw_docs = {}   # Format: {ip_name: [Document, ...]}

if "ip_file_registry" not in st.session_state:
    st.session_state.ip_file_registry = {}  # Format: {ip_name: {source_name: {type, pages, brief}}}

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

# Navigation Radio Menu (Including Page 4: Spec & Version Comparison)
page_selection = st.sidebar.radio(
    "Navigation Menu",
    [
        "Ingestion & IP Management",
        "Interactive IP RAG Chat",
        "References & Citation Dashboard",
        "Spec & Version Comparison"
    ]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### Registered IP Families")

# Render active IP status grouped by Family in the sidebar
if st.session_state.ip_databases:
    grouped_ips = {}
    for ip_name in st.session_state.ip_databases.keys():
        g_name = st.session_state.ip_groups.get(ip_name, "General")
        if g_name not in grouped_ips:
            grouped_ips[g_name] = []
        grouped_ips[g_name].append(ip_name)

    for group, ips in grouped_ips.items():
        st.sidebar.markdown(f"** {group}**")
        for ip in ips:
            doc_count = len(st.session_state.ip_file_registry.get(ip, {}))
            st.sidebar.write(f"&nbsp;&nbsp;&nbsp;&nbsp;• {ip} (`{doc_count} docs`)")
else:
    st.sidebar.caption("No IP models registered yet. Go to Page 1 to start.")

# Route to the selected page view
if page_selection == "Ingestion & IP Management":
    page1_ingest.render()
elif page_selection == "Interactive IP RAG Chat":
    page2_chat.render()
elif page_selection == "References & Citation Dashboard":
    page3_citations.render()
elif page_selection == "Spec & Version Comparison":
    page4_compare.render()
