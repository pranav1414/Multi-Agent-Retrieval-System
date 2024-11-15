# Document Selection
"""The user will first select a document by its title from the list of available documents. 
This ensures the system knows the exact document the user wants to work with."""

import pinecone
from typing import List

# Pinecone Configuration
PINECONE_API_KEY = ""
INDEX_NAME = "team9-project4-vector"

# Initialize Pinecone
pc = pinecone.Pinecone(api_key=PINECONE_API_KEY)

# Access the existing index
index = pc.Index(INDEX_NAME)


class DocumentSelectionAgent:
    def __init__(self, pinecone_index):
        self.index = pinecone_index

    def fetch_documents(self) -> List[str]:
        """
        Fetch all available document titles from Pinecone.
        
        Returns:
            List[str]: A list of unique document titles.
        """
        try:
            stats = self.index.describe_index_stats()
            titles = set()

            for namespace, namespace_stats in stats.get("namespaces", {}).items():
                vector_count = namespace_stats.get("vector_count", 0)
                if vector_count > 0:
                    matches = self.index.query(
                        vector=[0] * 1536,  # Use a dummy query vector
                        top_k=vector_count,
                        include_metadata=True,
                        namespace=namespace
                    )["matches"]
                    for match in matches:
                        title = match["metadata"].get("document", "Unknown Title")
                        titles.add(title)

            return sorted(titles)

        except Exception as e:
            print(f"Error fetching documents: {e}")
            return []

    def offer_document_selection(self, titles: List[str]) -> str:
        """
        Allow the user to select a document from the available options.

        Args:
            titles (List[str]): List of available document titles.

        Returns:
            str: Selected document title.
        """
        if not titles:
            print("No documents available for selection.")
            return None

        while True:
            print("\nAvailable Documents:")
            for idx, title in enumerate(titles, start=1):
                print(f"{idx}. {title}")

            try:
                selection = int(input("Enter the number corresponding to the document: "))
                if 1 <= selection <= len(titles):
                    selected_title = titles[selection - 1]
                    print(f"\nSelected Document: {selected_title}")
                    return selected_title
                else:
                    print("Invalid selection. Please try again.")
            except ValueError:
                print("Invalid input. Please enter a number.")

    def select_document(self) -> str:
        """
        Fetch documents and allow the user to select one in a single flow.

        Returns:
            str: Selected document title or None if no document was selected.
        """
        print("\nFetching available documents...")
        available_titles = self.fetch_documents()

        if not available_titles:
            print("No documents found.")
            return None

        print("Offering document selection...")
        return self.offer_document_selection(available_titles)


# # Example Usage
# if __name__ == "__main__":
#     # Initialize the agent
#     agent = DocumentSelectionAgent(index)

#     # Single parent function to select document
#     selected_document = agent.select_document()
#     if selected_document:
#         print(f"\nDocument '{selected_document}' has been selected for research.")
#     else:
#         print("\nNo document selected.")





