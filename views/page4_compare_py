import streamlit as st
from langchain_groq import ChatGroq

def render():
    st.image("PragyanAI_Transperent.png")
    st.title("⚖️ Cross-Spec & Version Comparison Engine")
    st.markdown("Select protocol groups and specific specification versions to perform side-by-side comparisons, analyze architecture evolution, and automatically list page-by-page change deltas.")

    # Check if IP databases exist
    if "ip_databases" not in st.session_state or len(st.session_state.ip_databases) < 1:
        st.warning("⚠️ At least one IP model or specification container is required. Please ingest data on **Page 1: Ingestion & IP Management** first.")
        return

    ip_databases = st.session_state.ip_databases
    ip_groups = st.session_state.get("ip_groups", {})
    ip_file_registry = st.session_state.get("ip_file_registry", {})
    ip_raw_docs = st.session_state.get("ip_raw_docs", {})

    available_ips = list(ip_databases.keys())

    # Group Extraction
    unique_groups = sorted(list(set(ip_groups.get(ip, "General") for ip in available_ips)))

    st.markdown("---")
    st.subheader("1. Protocol Group & Spec Version Selection")
    
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        group_a = st.selectbox("Select Baseline Group A", unique_groups, index=0, key="group_a_sel")
        ips_in_group_a = [ip for ip in available_ips if ip_groups.get(ip, "General") == group_a]
        spec_a = st.selectbox("Select Baseline Spec / Version A", ips_in_group_a, index=0, key="spec_a_sel")

    with col_g2:
        default_group_b_idx = min(1, len(unique_groups) - 1)
        group_b = st.selectbox("Select Target Group B", unique_groups, index=default_group_b_idx, key="group_b_sel")
        ips_in_group_b = [ip for ip in available_ips if ip_groups.get(ip, "General") == group_b]
        default_spec_b_idx = min(1, len(ips_in_group_b) - 1)
        spec_b = st.selectbox("Select Target Spec / Version B", ips_in_group_b, index=default_spec_b_idx, key="spec_b_sel")

    # Optional: Specific Document / Page Filter
    st.markdown("---")
    st.subheader("2. Scope & Target Parameters")
    
    col_scope1, col_scope2 = st.columns(2)
    with col_scope1:
        sources_a = list(ip_file_registry.get(spec_a, {}).keys())
        selected_source_a = st.selectbox("Filter Source Document A (Optional)", ["All Documents"] + sources_a, key="src_a_sel")
    with col_scope2:
        sources_b = list(ip_file_registry.get(spec_b, {}).keys())
        selected_source_b = st.selectbox("Filter Source Document B (Optional)", ["All Documents"] + sources_b, key="src_b_sel")

    # Safely load Groq credentials and model name from st.secrets
    try:
        groq_api_key = st.secrets["GROQ_API_KEY"]
        model_name = st.secrets.get("MODEL_NAME", "llama-3.3-70b-versatile")
    except Exception:
        st.error("⚠️ `GROQ_API_KEY` or `MODEL_NAME` not found in `st.secrets`. Please configure your `.streamlit/secrets.toml` file.")
        return

    comparison_topic = st.text_input(
        "Specify Comparison Topic / Parameter / Register", 
        placeholder="e.g., Signaling Rate, Max Payload Size, Link Training State Machine, or Register Offsets"
    )

    # Unique button key
    if st.button("Generate Side-by-Side Comparison & Delta Audit", type="primary", key="btn_generate_comparison"):
        if not comparison_topic.strip():
            st.warning("💡 Please specify a comparison topic (e.g., 'Signaling Rate' or 'Register Offsets') above.")
            return

        if spec_a == spec_b and selected_source_a == selected_source_b:
            st.warning("⚠️ Please select two different specifications or document versions for comparison.")
            return

        llm = ChatGroq(model=model_name, temperature=0.1, groq_api_key=groq_api_key)

        with st.spinner(f"Retrieving and aligning context between [{spec_a}] and [{spec_b}]..."):
            # Retrieve chunks with optional document source filtering
            docs_a = ip_raw_docs.get(spec_a, [])
            docs_b = ip_raw_docs.get(spec_b, [])

            if selected_source_a != "All Documents":
                docs_a = [d for d in docs_a if d.metadata.get("source") == selected_source_a]
            if selected_source_b != "All Documents":
                docs_b = [d for d in docs_b if d.metadata.get("source") == selected_source_b]

            # Fallback to vector search if filtered doc lists are small or empty
            db_a = ip_databases[spec_a]
            db_b = ip_databases[spec_b]
            
            search_chunks_a = db_a.similarity_search(comparison_topic, k=4)
            search_chunks_b = db_b.similarity_search(comparison_topic, k=4)

            # Format context strings with explicit Page/Slide tracking
            context_a = "\n".join([f"[Source: {c.metadata.get('source')} | Page/Slide: {c.metadata.get('page', 1)}]: {c.page_content[:1200]}" for c in search_chunks_a])
            context_b = "\n".join([f"[Source: {c.metadata.get('source')} | Page/Slide: {c.metadata.get('page', 1)}]: {c.page_content[:1200]}" for c in search_chunks_b])

            # Expert Comparative Prompt with Page Change Delta Mapping
            comparison_prompt = f"""You are a Principal Silicon Architect specializing in protocol evolution, ASIC design standards, and backwards compatibility. 
Perform a rigorous, side-by-side comparative analysis between **{spec_a}** (Group: {group_a}) and **{spec_b}** (Group: {group_b}) regarding: **{comparison_topic}**.

### Guidelines for Response:
1. **Structured Comparison Table:** Provide a clear Markdown table contrasting parameters, performance metrics, bit-widths, signaling rates, or protocol behaviors between {spec_a} and {spec_b}.
2. **Page-by-Page Change Delta Index:** Explicitly list the exact document sources and page/slide numbers where functional, register, or protocol changes exist between the two specs. Use a structured list format indicating:
   - `{spec_a}` (Source File & Page X) vs `{spec_b}` (Source File & Page Y): Description of change.
3. **Generational Deltas & Architectural Implications:** Highlight what features, registers, or states were added, modified, or deprecated, and how they impact hardware verification.

=== CONTEXT FROM {spec_a} ===
{context_a}

=== CONTEXT FROM {spec_b} ===
{context_b}
=============================
"""

            response = llm.invoke(comparison_prompt)
            
            st.markdown("---")
            st.subheader(f"📊 Comparative Analysis & Page Delta Audit: {spec_a} vs. {spec_b}")
            st.markdown(response.content)

            # Store references for audit on Page 3
            st.session_state.last_references = search_chunks_a + search_chunks_b
