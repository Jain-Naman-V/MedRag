# NOTE: This is legacy/optional code for vector store support (FAISS, embeddings, etc.).
# Not used in the current OCR-only MedRAG backend flow.
import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import required libraries
try:
    import faiss
    from langchain.embeddings import OpenAIEmbeddings, HuggingFaceEmbeddings
    from langchain.vectorstores import FAISS
    from langchain.docstore.document import Document
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    import numpy as np
    IMPORT_SUCCESS = True
except ImportError:
    IMPORT_SUCCESS = False
    logger.warning("Optional dependencies not installed. Some functionality may be limited.")

class VectorStoreManager:
    """
    Manages vector storage and retrieval of document embeddings.
    """
    
    def __init__(self, vector_store_path: str, embedding_model: str = "openai"):
        """
        Initialize the vector store manager.
        
        Args:
            vector_store_path: Path to store the vector database
            embedding_model: Which embedding model to use ('openai' or 'huggingface')
        """
        if not IMPORT_SUCCESS:
            raise ImportError("Required dependencies not installed. Please install langchain, faiss, and other required packages.")
        
        self.vector_store_path = Path(vector_store_path)
        self.vector_store_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize embedding model
        self.embedding_model = embedding_model.lower()
        self.embeddings = self._initialize_embeddings()
        
        # Initialize vector store
        self.vector_store = None
        self.docstore = {}
        self.index_to_docstore_id = {}
    
    def _initialize_embeddings(self):
        """Initialize the embedding model."""
        if self.embedding_model == "openai":
            return OpenAIEmbeddings()
        elif self.embedding_model == "huggingface":
            return HuggingFaceEmbeddings()
        else:
            raise ValueError(f"Unsupported embedding model: {self.embedding_model}")
    
    def create_documents(self, texts: List[str], metadatas: Optional[List[Dict[str, Any]]] = None) -> List[Document]:
        """
        Create document objects from texts and metadata.
        
        Args:
            texts: List of text strings
            metadatas: Optional list of metadata dictionaries
            
        Returns:
            List of Document objects
        """
        if metadatas is None:
            metadatas = [{}] * len(texts)
            
        return [
            Document(page_content=text, metadata=metadata)
            for text, metadata in zip(texts, metadatas)
        ]
    
    def add_documents(self, documents: List[Document], **kwargs) -> List[str]:
        """
        Add documents to the vector store.
        
        Args:
            documents: List of Document objects to add
            **kwargs: Additional arguments to pass to the embedding model
            
        Returns:
            List of document IDs
        """
        if not documents:
            return []
        
        # Create or load the vector store
        if self.vector_store is None:
            self.vector_store = FAISS.from_documents(
                documents=documents,
                embedding=self.embeddings,
                **kwargs
            )
        else:
            self.vector_store.add_documents(documents, **kwargs)
        
        # Update document store
        for i, doc in enumerate(documents):
            doc_id = str(len(self.docstore))
            self.docstore[doc_id] = doc
            self.index_to_docstore_id[i] = doc_id
        
        return list(self.docstore.keys())[-len(documents):]
    
    def similarity_search(self, query: str, k: int = 4, **kwargs) -> List[Document]:
        """
        Search for similar documents to the query.
        
        Args:
            query: The query string
            k: Number of results to return
            **kwargs: Additional arguments to pass to the similarity search
            
        Returns:
            List of similar documents
        """
        if self.vector_store is None:
            return []
            
        return self.vector_store.similarity_search(query, k=k, **kwargs)
    
    def save_local(self, path: Optional[str] = None) -> None:
        """
        Save the vector store to disk.
        
        Args:
            path: Optional path to save the vector store. Uses the instance path if not provided.
        """
        if self.vector_store is None:
            return
            
        save_path = Path(path) if path else self.vector_store_path
        self.vector_store.save_local(save_path)
    
    @classmethod
    def load_local(cls, path: str, embedding_model: str = "openai") -> 'VectorStoreManager':
        """
        Load a vector store from disk.
        
        Args:
            path: Path to the vector store directory
            embedding_model: Which embedding model to use ('openai' or 'huggingface')
            
        Returns:
            VectorStoreManager instance
        """
        instance = cls(path, embedding_model)
        instance.vector_store = FAISS.load_local(path, instance.embeddings)
        return instance
    
    def get_document(self, doc_id: str) -> Optional[Document]:
        """
        Get a document by ID.
        
        Args:
            doc_id: Document ID
            
        Returns:
            Document if found, None otherwise
        """
        return self.docstore.get(doc_id)
    
    def get_documents(self, doc_ids: List[str]) -> List[Document]:
        """
        Get multiple documents by their IDs.
        
        Args:
            doc_ids: List of document IDs
            
        Returns:
            List of Documents
        """
        return [self.get_document(doc_id) for doc_id in doc_ids if doc_id in self.docstore]
    
    def delete_documents(self, doc_ids: List[str]) -> None:
        """
        Delete documents from the vector store.
        
        Args:
            doc_ids: List of document IDs to delete
        """
        if self.vector_store is None:
            return
            
        # This is a simplified implementation
        # In a production system, you'd need to handle the FAISS index properly
        for doc_id in doc_ids:
            if doc_id in self.docstore:
                del self.docstore[doc_id]
        
        # Rebuild the index if needed
        if self.docstore:
            documents = list(self.docstore.values())
            self.vector_store = FAISS.from_documents(
                documents=documents,
                embedding=self.embeddings
            )
        else:
            self.vector_store = None
