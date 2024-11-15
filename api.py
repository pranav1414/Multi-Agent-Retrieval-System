from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from agents.document_selection_agent import DocumentSelectionAgent
from agents.arxiv_agent import ArxivAgent
from agents.web_search_agent import WebSearchAgent
from agents.rag_agent import rag_query_answer
from pinecone import Pinecone
import pandas as pd

# Temporary DataFrame to hold interactions
temp_df = pd.DataFrame(columns=["document_selected", "question", "response"])


# Initialize FastAPI app
app = FastAPI()

# Initialize Pinecone and index
pc = Pinecone(api_key="")
index = pc.Index("team9-project4-vector")

# SerpAPI Key
serp_api_key = ""

# Input models
class DocumentSelectionInput(BaseModel):
    selected_document_index: int


class ArxivInput(BaseModel):
    document_content: str


class WebSearchInput(BaseModel):
    query: str


class RAGInput(BaseModel):
    question: str


# API endpoints
@app.get("/document_selection")
def get_documents():
    """
    Endpoint to fetch available documents for selection.
    """
    agent = DocumentSelectionAgent(index)
    documents = agent.fetch_documents()
    if not documents:
        raise HTTPException(status_code=404, detail="No documents found.")
    return {"documents": documents}


@app.post("/document_selection")
def select_document(input: DocumentSelectionInput):
    """
    Endpoint to select a document based on the user's choice.
    """
    agent = DocumentSelectionAgent(index)
    documents = agent.fetch_documents()

    # Ensure the provided index is valid
    if input.selected_document_index < 0 or input.selected_document_index >= len(documents):
        raise HTTPException(status_code=400, detail="Invalid document index.")

    selected_document = documents[input.selected_document_index]
    return {"selected_document": selected_document}


@app.post("/arxiv_research")
def arxiv_research(input: ArxivInput):
    """
    Endpoint to perform Arxiv research based on a document's content.
    """
    agent = ArxivAgent()
    if not input.document_content:
        raise HTTPException(status_code=400, detail="Document content is required for Arxiv research.")

    result = agent.search_arxiv(input.document_content)
    return {"research_result": result}


@app.post("/web_search")
def web_search(input: WebSearchInput):
    """
    Endpoint to perform a web search using the provided query.
    """
    if not input.query:
        raise HTTPException(status_code=400, detail="Query is required for web search.")

    agent = WebSearchAgent(query=input.query, serp_api_key=serp_api_key)
    search_result = agent.search_web()
    if search_result:
        return {"web_search_result": search_result}
    else:
        return {"message": "No results found for the query."}


@app.post("/rag_query")
def rag_query(input: RAGInput):
    """
    Endpoint to answer a question using RAG (retrieval-augmented generation).
    """
    if not input.question:
        raise HTTPException(status_code=400, detail="Question is required for RAG query.")

    answer = rag_query_answer(query=input.question, top_k=5, index=index)
    return {"answer": answer}


# Run the FastAPI app with Uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
