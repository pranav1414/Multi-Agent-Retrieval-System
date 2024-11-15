import openai
import pinecone
from typing import List, Dict

# Configuration - Replace with your actual API keys and index information
PINECONE_API_KEY = ''
OPENAI_API_KEY = ''
INDEX_NAME = 'team9-project4-vector'
EMBEDDING_MODEL_NAME = "text-embedding-ada-002"  # Model for embeddings

# Initialize APIs
def initialize_apis() -> pinecone.Index:
    """
    Initialize OpenAI and Pinecone with provided API keys and return Pinecone index.
    """
    openai.api_key = OPENAI_API_KEY
    pinecone.init(api_key=PINECONE_API_KEY, environment="us-west1-gcp")  # Update environment if needed
    return pinecone.Index(INDEX_NAME)

# Function to create embeddings
def get_query_embedding(query: str) -> List[float]:
    """
    Generate embedding for a query using OpenAI's API.

    Args:
        query (str): The query string to embed.

    Returns:
        List[float]: The embedding vector for the query.
    """
    response = openai.Embedding.create(input=query, model=EMBEDDING_MODEL_NAME)
    return response['data'][0]['embedding']

# Function to retrieve context from Pinecone
def retrieve_context(index, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, str]]:
    """
    Retrieve relevant documents from Pinecone based on query embedding.

    Args:
        index: Pinecone index instance.
        query_embedding (List[float]): Embedding vector for the query.
        top_k (int): Number of top results to retrieve.

    Returns:
        List[Dict[str, str]]: List of relevant documents with metadata.
    """
    results = index.query(vector=query_embedding, top_k=top_k, include_metadata=True)
    return [
        {
            "document": match['metadata'].get("document", "Unknown Document"),
            "page_num": match['metadata'].get("page_num", "Unknown Page"),
            "content": match['metadata'].get("content", "")
        }
        for match in results['matches']
    ]

# Function to generate an answer based on context and query
def generate_answer(query: str, context: List[Dict[str, str]]) -> str:
    """
    Generate an answer to the query using OpenAI's ChatCompletion API.

    Args:
        query (str): The question or query.
        context (List[Dict[str, str]]): Retrieved context from Pinecone.

    Returns:
        str: The generated answer.
    """
    # Format retrieved context for the language model
    context_text = "\n\n".join(
        [f"Document: {item['document']}, Page: {item['page_num']}\nContent: {item['content']}" for item in context]
    )
    prompt = f"Using the following context, answer the question:\n\nContext:\n{context_text}\n\nQuestion: {query}\nAnswer:"

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=200,
        temperature=0.7
    )
    return response['choices'][0]['message']['content'].strip()

# Main function to handle RAG query answering
def rag_query_answer(query: str, index, top_k: int = 5, return_metadata: bool = False) -> str:
    """
    Retrieve relevant context from Pinecone and generate an answer to the query.

    Args:
        query (str): The input query.
        index: Pinecone index instance.
        top_k (int): Number of top results to retrieve from Pinecone.
        return_metadata (bool): Whether to return metadata along with the answer.

    Returns:
        str or tuple: The generated answer, optionally with metadata.
    """
    try:
        # Generate query embedding
        query_embedding = get_query_embedding(query)
        
        # Retrieve relevant context from Pinecone
        context = retrieve_context(index, query_embedding, top_k)
        
        # Generate an answer based on the retrieved context
        answer = generate_answer(query, context)
        metadata = {"query_context": context}
        return (answer, metadata) if return_metadata else answer
    except Exception as e:
        return f"An error occurred: {e}"

# Example Usage
if __name__ == "__main__":
    index = initialize_apis()
    query = "What are the challenges in African capital markets? Provide five core points from the document."
    answer = rag_query_answer(query=query, index=index, top_k=5, return_metadata=True)
    print("Answer:", answer)

