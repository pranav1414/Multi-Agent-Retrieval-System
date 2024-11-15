import streamlit as st
import requests
import pandas as pd
from io import StringIO, BytesIO
from fpdf import FPDF

# Define the base URL for the FastAPI server
BASE_URL = "http://127.0.0.1:8000"  # Adjust if FastAPI is hosted elsewhere

st.title("Document Research Assistant")

# Initialize session state to hold interaction history if not already present
if "interaction_history" not in st.session_state:
    st.session_state.interaction_history = []

# Document Selection
st.header("Document Selection")

# Fetch Available Documents
if st.button("Fetch Available Documents"):
    response = requests.get(f"{BASE_URL}/document_selection")
    if response.status_code == 200:
        documents = response.json().get("documents", [])
        if documents:
            # Store document names directly in session state
            st.session_state.documents = documents
        else:
            st.write("No documents available.")
    else:
        st.write("Failed to fetch documents.")

# Display a dropdown with available document names if documents are loaded
if "documents" in st.session_state:
    selected_document_name = st.selectbox(
        "Select a Document",
        options=st.session_state.documents,
    )
    if st.button("Select Document"):
        # Find the index of the selected document name
        selected_document_index = st.session_state.documents.index(selected_document_name)
        select_response = requests.post(
            f"{BASE_URL}/document_selection", 
            json={"selected_document_index": selected_document_index}
        )
        st.write("Selected Document:", select_response.json())

# RAG Query
st.header("RAG Query")
rag_question = st.text_input("Enter a question for RAG query")
if st.button("Get Answer"):
    # Ensure a document is selected before querying RAG
    if not selected_document_name:
        st.write("Please select a document first.")
    elif rag_question:
        # Make the RAG query
        response = requests.post(f"{BASE_URL}/rag_query", json={"question": rag_question})
        if response.status_code == 200:
            answer = response.json().get("answer", "No answer found")
            st.write("RAG Answer:", answer)

            # Save the interaction to the session state history
            st.session_state.interaction_history.append({
                "Document Name": selected_document_name,
                "Question": rag_question,
                "Answer": answer
            })
        else:
            st.write("Failed to get answer.")
    else:
        st.write("Please enter a question for RAG.")

# Display Interaction History
st.header("Interaction History")
if st.session_state.interaction_history:
    for interaction in st.session_state.interaction_history:
        st.write(f"**Document**: {interaction['Document Name']}")
        st.write(f"**Question**: {interaction['Question']}")
        st.write(f"**Answer**: {interaction['Answer']}")
        st.write("---")
else:
    st.write("No interactions saved yet.")

# Download Interaction History
st.header("Download Interaction History")
if st.session_state.interaction_history:
    # Convert interaction history to a DataFrame
    df = pd.DataFrame(st.session_state.interaction_history)

    # Option 1: Download as CSV
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_data = csv_buffer.getvalue()

    st.download_button(
        label="Download Interaction History as CSV",
        data=csv_data,
        file_name="interaction_history.csv",
        mime="text/csv"
    )

    # Option 2: Download as PDF
    def generate_pdf(dataframe):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Title
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "Interaction History", ln=True, align="C")
        pdf.ln(10)

        # Add each interaction one below the other
        for idx, row in dataframe.iterrows():
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, f"Interaction {idx + 1}:", ln=True)
            pdf.ln(2)  # Small spacing after the interaction header
            
            pdf.set_font("Arial", size=12)
            # Adjust width for wrapping text
            content_width = 190  # Adjust for page margins
            
            # Wrap and render each field
            pdf.set_font("Arial", "B", 11)
            pdf.multi_cell(content_width, 10, f"Document:", border=0)
            pdf.set_font("Arial", size=12)
            pdf.multi_cell(content_width, 10, row['Document Name'], border=0)
            pdf.ln(1)

            pdf.set_font("Arial", "B", 11)
            pdf.multi_cell(content_width, 10, f"Question:", border=0)
            pdf.set_font("Arial", size=12)
            pdf.multi_cell(content_width, 10, row['Question'], border=0)
            pdf.ln(1)

            pdf.set_font("Arial", "B", 11)
            pdf.multi_cell(content_width, 10, f"Answer:", border=0)
            pdf.set_font("Arial", size=12)
            pdf.multi_cell(content_width, 10, row['Answer'], border=0)
            pdf.ln(5)  # Add spacing between entries

        # Output to a bytes buffer
        pdf_buffer = BytesIO()
        pdf.output(pdf_buffer)
        pdf_buffer.seek(0)
        return pdf_buffer

    # Generate the PDF file
    pdf_data = generate_pdf(df)

    # Download button for PDF
    st.download_button(
        label="Download Interaction History as PDF",
        data=pdf_data,
        file_name="interaction_history.pdf",
        mime="application/pdf"
    )
