import streamlit as st
import requests

# Define the base URL for the FastAPI server
BASE_URL = "http://127.0.0.1:8000"  # Adjust if FastAPI is hosted elsewhere

st.title("Document Research Assistant")

# Document Selection
st.header("Document Selection")
if st.button("Fetch Available Documents"):
    response = requests.get(f"{BASE_URL}/document_selection")
    if response.status_code == 200:
        documents = response.json().get("documents", [])
        if documents:
            st.write("Available Documents:")
            for i, doc in enumerate(documents):
                st.write(f"{i + 1}. {doc}")
            selected_index = st.number_input("Select Document Index", min_value=0, max_value=len(documents) - 1)
            if st.button("Select Document"):
                select_response = requests.post(f"{BASE_URL}/document_selection", json={"selected_document_index": selected_index})
                st.write("Selected Document:", select_response.json())
        else:
            st.write("No documents available.")
    else:
        st.write("Failed to fetch documents.")

# Arxiv Research
st.header("Arxiv Research")
arxiv_content = st.text_area("Enter document content for Arxiv research")
if st.button("Search Arxiv"):
    response = requests.post(f"{BASE_URL}/arxiv_research", json={"document_content": arxiv_content})
    if response.status_code == 200:
        st.write("Arxiv Research Result:", response.json().get("research_result", "No result"))
    else:
        st.write("Failed to perform Arxiv research.")

# Web Search
st.header("Web Search")
web_query = st.text_input("Enter search query")
if st.button("Search Web"):
    response = requests.post(f"{BASE_URL}/web_search", json={"query": web_query})
    if response.status_code == 200:
        st.write("Web Search Result:", response.json().get("web_search_result", "No result found"))
    else:
        st.write("Failed to perform web search.")

# RAG Query
st.header("RAG Query")
rag_question = st.text_input("Enter a question for RAG query")
if st.button("Get Answer"):
    response = requests.post(f"{BASE_URL}/rag_query", json={"question": rag_question})
    if response.status_code == 200:
        st.write("RAG Answer:", response.json().get("answer", "No answer found"))
    else:
        st.write("Failed to get answer.")
