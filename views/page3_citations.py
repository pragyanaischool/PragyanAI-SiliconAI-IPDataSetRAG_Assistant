import streamlit as st

def render():
    st.image("PragyanAI_Transperent.png")
    st.title("Reference Materials & Citation Dashboard")
    st.markdown("Audit the exact knowledge chunks, page indices, register tables, and RTL code snippets surfaced during the latest chat query across your semiconductor IP databases.")

    # Check if reference data exists in session state from Page 2
    if "last_references" not in st.session_state or not st.session_state.last_references:
        st.info(" No query references recorded yet. Head over to **Page 2: Interactive IP RAG Chat**, select an IP model, and ask a question to generate complete citation traces here.")
        return

    references = st.session_state.last_references
    st.success(f"Successfully tracked **{len(references)}** citation chunks used to synthesize the latest engineering response.")

    # High-level Metrics Summary Row
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Context Chunks", len(references))
    with col2:
        unique_sources = len(set([doc.metadata.get("source", "Unknown") for doc in references]))
        st.metric("Unique Source Files", unique_sources)
    with col3:
        unique_ips = len(set([doc.metadata.get("ip", "General") for doc in references]))
        st.metric("Referenced IP Models", unique_ips)

    st.markdown("---")
    st.subheader("🔍 Context Node Inspection & Audit")

    # Detailed inspection expanders for each reference chunk
    for idx, doc in enumerate(references):
        meta = doc.metadata
        source_name = meta.get("source", "Unknown Source")
        doc_type = meta.get("type", "Specification")
        page_num = meta.get("page", 1)
        ip_name = meta.get("ip", "Generic IP")

        with st.expander(f"[{idx + 1}] IP: {ip_name} | {source_name} (Page/Slide: {page_num})"):
            c1, c2 = st.columns(2)
            with c1:
                st.write(f"**Target IP Model Container:** `{ip_name}`")
                st.write(f"**Document Format:** `{doc_type}`")
            with c2:
                st.write(f"**Source Document / URL:** `{source_name}`")
                st.write(f"**Extracted Location:** Page/Slide/Index `{page_num}`")

            st.markdown("**Retrieved Chunk Content:**")
            
            # Render syntax-highlighted code block if it is HDL code, otherwise use a readable text area
            if doc_type in ["HDL Code", "Verilog/Code"]:
                st.code(doc.page_content, language="verilog")
            else:
                st.text_area(
                    label=f"Content Chunk [{idx+1}]",
                    value=doc.page_content,
                    height=200,
                    disabled=True,
                    label_visibility="collapsed"
                )

    st.markdown("---")
    if st.button("Clear Audit Trail"):
        st.session_state.last_references = []
        st.rerun()
