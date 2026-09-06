import streamlit as st
from langchain_groq import ChatGroq

def render():
    st.image("PragyanAI_Transperent.png")
    st.title("Cross-Spec & Version Comparison Engine")
    st.markdown("Compare generational specification differences side-by-side (e.g., PCIe Gen 1 vs. Gen 2, or AXI3 vs. AXI4) to analyze architectural evolution, register map changes, signaling updates, and protocol deltas.")

    # Check if IP databases exist
    if "ip_databases" not in st.session_state or len(st.session_state.ip_databases) < 1:
        st.warning("⚠️ At least one IP model or specification container is required. Please ingest data on **Page 1: Ingestion & IP Management** first.")
        return

    available_ips = list(st.session_state.ip_databases.keys())
    ip_groups = st.session_state.get("ip_groups", {})

    # Helper to display friendly labels with group prefixes
    def get_ip_label(ip_name):
        group = ip_groups.get(ip_name, "General")
        return f"[{group}] {ip_name}"

    # Selection controls for comparison
    col_sel1, col_sel2 = st.columns(2)
    with col_sel1:
        spec_a = st.selectbox(
            "Select Baseline Spec / Version A", 
            available_ips, 
            format_func=get_ip_label,
            index=0
        )
    with col_sel2:
        default_idx = 1 if len(available_ips) > 1 else 0
        spec_b = st.selectbox(
            "Select Target Spec / Version B", 
            available_ips, 
            format_func=get_ip_label,
            index=default_idx
        )

    # Safely load Groq credentials and model name from st.secrets
    try:
        groq_api_key = st.secrets["GROQ_API_KEY"]
        model_name = st.secrets.get("MODEL_NAME", "llama-3.3-70b-versatile")
    except Exception:
        st.error("⚠️ `GROQ_API_KEY` or `MODEL_NAME` not found in `st.secrets`. Please configure your `.streamlit/secrets.toml` file.")
        return

    comparison_topic = st.text_input(
        "Specify Comparison Topic / Parameter", 
        placeholder="e.g., Signaling Rate, Max Payload Size, Link Training State Machine, or Register Offsets"
    )

    # Unique key assigned to prevent duplicate element ID collision
    if st.button("Generate Side-by-Side Comparison", type="primary", key="btn_generate_comparison"):
        if not comparison_topic.strip():
            st.warning("💡 Please specify a comparison topic (e.g., 'Signaling Rate' or 'Register Offsets') above.")
            return

        if spec_a == spec_b:
            st.warning("⚠️ Please select two different IP models or specification versions for comparison.")
            return

        llm = ChatGroq(model=model_name, temperature=0.1, groq_api_key=groq_api_key)

        with st.spinner(f"Retrieving context from [{spec_a}] and [{spec_b}] for comparative analysis..."):
            # Retrieve chunks from Spec A
            db_a = st.session_state.ip_databases[spec_a]
            chunks_a = db_a.similarity_search(comparison_topic, k=3)

            # Retrieve chunks from Spec B
            db_b = st.session_state.ip_databases[spec_b]
            chunks_b = db_b.similarity_search(comparison_topic, k=3)

            # Format contexts for comparison
            context_a = "\n".join([f"[{c.metadata.get('source')} - Page/Slide {c.metadata.get('page', 1)}]: {c.page_content[:1000]}" for c in chunks_a])
            context_b = "\n".join([f"[{c.metadata.get('source')} - Page/Slide {c.metadata.get('page', 1)}]: {c.page_content[:1000]}" for c in chunks_b])

            # Expert Comparative Prompt
            comparison_prompt = f"""You are a Principal Silicon Architect specializing in protocol evolution, ASIC design standards, and backwards compatibility. 
Perform a rigorous, side-by-side comparative analysis between **{spec_a}** and **{spec_b}** regarding the following topic: **{comparison_topic}**.

### Guidelines for Response:
1. **Structured Comparison Table:** Provide a clear Markdown table contrasting parameters, performance metrics, bit-widths, signaling rates, or protocol behaviors between {spec_a} and {spec_b}.
2. **Generational Deltas:** Explicitly highlight what features, registers, or states were added, modified, or deprecated in the newer version.
3. **Architectural Implications:** Explain how these protocol or register differences impact hardware design, verification testbenches, and backward compatibility.

=== CONTEXT FROM {spec_a} ===
{context_a}

=== CONTEXT FROM {spec_b} ===
{context_b}
=============================
"""

            response = llm.invoke(comparison_prompt)
            
            st.markdown("---")
            st.subheader(f" Comparative Analysis: {spec_a} vs. {spec_b}")
            st.markdown(response.content)

            # Store references for audit on Page 3
            st.session_state.last_references = chunks_a + chunks_b
