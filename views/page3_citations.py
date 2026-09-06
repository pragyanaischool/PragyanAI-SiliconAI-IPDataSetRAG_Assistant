import streamlit as st

def render():
    st.title("📚 Page 3: Reference Materials & Citation Dashboard")
    st.markdown("Inspect source materials, exact page numbers, document segments, and file metadata utilized during the latest query interaction with your semiconductor IP knowledge bases.")

    # Check if reference data exists in session state from Page 2 queries
    if "last_references" in st.session_state and st.session_state.last_references:
        references = st.session_state.last_references
        
        st.success(f"Successfully tracked **{len(references)}** distinct citation nodes from your latest query context.")
        
        # Summary metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Context Chunks", len(references))
        with col2:
            unique_sources = len(set([doc.metadata.get('source') for doc in references]))
            st.metric("Unique Source Files", unique_sources)
        with col3:
            active_ip = references[0].metadata.get('ip', 'N/A') if references else 'N/A'
            st.metric("Associated IP Model", active_ip)

        st.markdown("---")
        st.subheader("🔍 Detailed Source Breakdown & Content Trace")

        for idx, doc in enumerate(references):
            meta = doc.metadata
            source_name = meta.get('source', 'Unknown Source')
            doc_type = meta.get('type', 'Document Format')
            page_idx = meta.get('page', 1)
            ip_container = meta.get('ip', 'General Workspace')

            # Render an interactive expander for each citation node
            with st.expander(f"[{idx + 1}] {source_name} — ({doc_type} | Page/Slide: {page_idx})"):
                
                col_a, col_b = st.columns(2)
                with col_a:
                    st.write(f"**Target IP Model Container:** `{ip_container}`")
                    st.write(f"**Document Type:** `{doc_type}`")
                with col_b:
                    st.write(f"**Source Reference / Link:** `{source_name}`")
                    st.write(f"**Page / Segment Number:** `{page_idx}`")

                st.markdown("**Extracted Text Snippet / Verilog Context Window:**")
                
                # Check if it's code/Verilog or text to render properly
                content_text = doc.page_content
                if doc_type in ["Verilog/Code", "Verilog Code"]:
                    st.code(content_text, language="verilog")
                else:
                    st.code(content_text[:1200] + ("..." if len(content_text) > 1200 else ""), language="text")

        # Option to clear or export reference trail
        st.markdown("---")
        if st.button("Clear Reference Audit Trail"):
            st.session_state.last_references = []
            st.rerun()

    else:
        st.info("💡 No active query references found yet. Head over to **Page 2: Interactive IP RAG Chat**, select an IP model, and ask a question to generate complete citation traces here.")
