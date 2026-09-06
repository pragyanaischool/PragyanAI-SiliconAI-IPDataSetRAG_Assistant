import streamlit as st
from langchain_groq import ChatGroq
from langchain.chains import ConversationalRetrievalChain

def render():
    st.title("💬 Page 2: Interactive IP & Verilog RAG Assistant")
    st.markdown("Select a target semiconductor IP core model, input your Groq API key, and query specifications, registers, or generated HDL blocks with context-aware retrieval.")

    # Check if any IP dataset containers have been created on Page 1
    if "ip_databases" not in st.session_state or not st.session_state.ip_databases:
        st.warning("⚠️ No IP knowledge bases found. Please go to **Page 1 (Ingestion & IP Management)** first to register an IP model and ingest documentation sources.")
        return

    # Sidebar or top selector for IP model selection
    available_ips = list(st.session_state.ip_databases.keys())
    
    col1, col2 = st.columns([2, 1])
    with col1:
        selected_ip = st.selectbox("Select Active IP Model / Dataset Container", available_ips)
    with col2:
        st.markdown(f"**Loaded Sources:** `{len(st.session_state.ip_metadata.get(selected_ip, []))}` files/links")

    # Groq API Key Configuration
    groq_api_key = st.text_input("Enter Groq API Key", type="password", help="Get a free key from console.groq.com")

    if groq_api_key and selected_ip:
        # Retrieve the vector database for the selected IP model
        vector_store = st.session_state.ip_databases[selected_ip]
        retriever = vector_store.as_retriever(search_kwargs={"k": 4})

        # Initialize Groq LLM & Conversational Retrieval Chain
        llm = ChatGroq(
            model="llama-3.3-70b-versatile", 
            temperature=0.1, 
            groq_api_key=groq_api_key
        )
        
        qa_chain = ConversationalRetrievalChain.from_llm(
            llm=llm, 
            retriever=retriever, 
            return_source_documents=True
        )

        # Initialize session chat history specifically indexed per IP model if needed
        if "chat_histories" not in st.session_state:
            st.session_state.chat_histories = {}
        if selected_ip not in st.session_state.chat_histories:
            st.session_state.chat_histories[selected_ip] = []

        current_history = st.session_state.chat_histories[selected_ip]

        # Display historical messages for the selected IP
        for message in current_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Chat Input Bar
        user_query = st.chat_input(f"Ask questions about specs, register layouts, or Verilog code for {selected_ip}...")

        if user_query:
            # Append user message
            current_history.append({"role": "user", "content": user_query})
            with st.chat_message("user"):
                st.markdown(user_query)

            with st.spinner(f"Synthesizing answer using {selected_ip} context..."):
                # Format past chat history into tuples expected by LangChain (if any)
                langchain_history = []
                for i in range(0, len(current_history) - 1, 2):
                    if i + 1 < len(current_history):
                        langchain_history.append((current_history[i]["content"], current_history[i+1]["content"]))

                # Execute RAG chain invocation
                response = qa_chain({
                    "question": user_query, 
                    "chat_history": langchain_history
                })
                
                answer = response["answer"]
                source_docs = response["source_documents"]

                # Save source documents globally so Page 3 can render precise reference links and citations
                st.session_state.last_references = source_docs

                # Format inline source summary for the chat response
                citations_summary = []
                for doc in source_docs:
                    meta = doc.metadata
                    source_name = meta.get("source", "Unknown Source")
                    doc_type = meta.get("type", "Document")
                    page_num = meta.get("page", 1)
                    citations_summary.append(f"- **{source_name}** ({doc_type}, Page/Slide: {page_num})")

                unique_citations = list(set(citations_summary))
                
                final_output = answer
                if unique_citations:
                    final_output += "\n\n__Quick Sources Referenced:__\n" + "\n".join(unique_citations[:3])
                    final_output += f"\n\n*(Tip: Go to **Page 3: References & Citations** to examine full text snippets and complete metadata trace)*"

                # Append assistant response
                current_history.append({"role": "assistant", "content": final_output})
                with st.chat_message("assistant"):
                    st.markdown(final_output)
    else:
        st.info("💡 Please provide your Groq API key above to initialize the LLM chat engine for the selected IP model.")
