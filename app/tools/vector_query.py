from typing import Any, Dict, List

from app.tools.base import ToolSpec
from app.vectorstore import get_retriever


class VectorQueryTool(ToolSpec):

    def __init__(self):
        super().__init__()
        self.name = "vector_query"
        self.description = "Query the vector database for relevant documents"
        self.retriever = None

    def _run(self, query: str, k: int = 4) -> str:
        """Query the vector database for relevant documents"""
        try:
            if not self.retriever:
                self.retriever = get_retriever(k=k)

            # Retrieve relevant documents
            docs = self.retriever.invoke(query)

            if not docs:
                return f"No relevant documents found for: {query}"

            # Format the results
            result = f"Found {len(docs)} relevant documents:\n\n"
            for i, doc in enumerate(docs[:k], 1):
                content = (
                    doc.page_content[:200] + "..."
                    if len(doc.page_content) > 200
                    else doc.page_content
                )
                result += f"{i}. {content}\n"
                if hasattr(doc, "metadata") and doc.metadata:
                    result += f"   Source: {doc.metadata.get('source', 'Unknown')}\n"
                result += "\n"

            return result

        except Exception as e:
            return f"Error querying vector database: {str(e)}"
