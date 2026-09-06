import streamlit as st
from views import page1_ingest, page2_chat, page3_citations

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

if "ip_metadata" not in st.session_state:
    st.session_state.ip_metadata = {}   # Format: {ip_name: [list_of_sources]}

if "last_references" not in st.session_state:
    st.session_state.last_references = []

if "multi_chat_histories" not in st.session_state:
    st.session_state.multi_chat_histories = {}

# Sidebar Navigation Header
st.sidebar.image("PragyanAI_Transperent.png")
st.sidebar.title(" PragyanAI Silicon RAG")
st.sidebar.caption("Hardware IP & Datasheet Engineering Suite")

# Navigation Radio Menu
page_selection = st.sidebar.radio(
    "Navigation Menu",
    [
        "Page 1: Ingestion & IP Management",
        "Page 2: Interactive IP RAG Chat",
        "Page 3: References & Citation Dashboard"
    ]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Registered IP Stores")

# Render active IP status in sidebar
if st.session_state.ip_databases:
    for ip_name in st.session_state.ip_databases.keys():
        source_count = len(st.session_state.ip_metadata.get(ip_name, []))
        st.sidebar.write(f"- **{ip_name}**: `{source_count}` source(s)")
else:
    st.sidebar.caption("No IP models registered yet. Go to Page 1 to start.")

# Route to the selected page view
if page_selection == "Page 1: Ingestion & IP Management":
    page1_ingest.render()
elif page_selection == "Page 2: Interactive IP RAG Chat":
    page2_chat.render()
elif page_selection == "Page 3: References & Citation Dashboard":
    page3_citations.render()
