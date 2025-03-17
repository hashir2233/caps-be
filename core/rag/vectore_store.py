from dotenv import load_dotenv
import os
from typing import List, Optional, Dict, Any
import logging
from functools import lru_cache

from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_postgres.vectorstores import PGVector
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VectorStoreConfig:
    """Configuration class for VectorStore settings"""
    
    def __init__(
        self,
        collection_name: str = "caps_docs",
        embedding_model: str = "models/text-embedding-004",
        embedding_dimensions: int = 768,
        use_jsonb: bool = True,
        task_type_query: str = "retrieval_query",
        task_type_document: str = "retrieval_document",
    ):
        """
        Initialize the vector store configuration.
        
        Args:
            collection_name: Name of the collection in the vector database
            embedding_model: Model name for embedding generation
            embedding_dimensions: Dimensions of the embedding vectors
            use_jsonb: Whether to use JSONB for metadata storage
            task_type_query: Task type for query embedding
            task_type_document: Task type for document embedding
        """
        load_dotenv()
        self.collection_name = collection_name
        self.embedding_model = embedding_model
        self.embedding_dimensions = embedding_dimensions
        self.use_jsonb = use_jsonb
        self.task_type_query = task_type_query
        self.task_type_document = task_type_document
        self.connection_string = os.getenv("DATABASE_URL")
        
        if not self.connection_string:
            raise ValueError("Database connection string not found. Set DATABASE_URL environment variable.")


class VectorStore:
    """Class for managing vector database operations"""
    
    def __init__(self, config: Optional[VectorStoreConfig] = None):
        """
        Initialize the VectorStore.
        
        Args:
            config: Configuration for the vector store (optional)
        """
        self.config = config or VectorStoreConfig()
        self._query_embeddings = None
        self._doc_embeddings = None
        self._vector_store = None
        logger.info(f"Initialized VectorStore with collection: {self.config.collection_name}")
    
    @property
    def query_embeddings(self) -> GoogleGenerativeAIEmbeddings:
        """Lazy-loaded query embeddings model optimized for retrieval queries"""
        if self._query_embeddings is None:
            self._query_embeddings = GoogleGenerativeAIEmbeddings(
                model=self.config.embedding_model,
                task_type=self.config.task_type_query
            )
            logger.debug("Query embeddings model initialized")
        return self._query_embeddings
    
    @property
    def doc_embeddings(self) -> GoogleGenerativeAIEmbeddings:
        """Lazy-loaded document embeddings model optimized for document embedding"""
        if self._doc_embeddings is None:
            self._doc_embeddings = GoogleGenerativeAIEmbeddings(
                model=self.config.embedding_model,
                task_type=self.config.task_type_document
            )
            logger.debug("Document embeddings model initialized")
        return self._doc_embeddings
    
    @property
    def vector_store(self) -> PGVector:
        """Lazy-loaded vector store instance"""
        if self._vector_store is None:
            try:
                self._vector_store = PGVector(
                    embeddings=self.doc_embeddings,
                    collection_name=self.config.collection_name,
                    connection=self.config.connection_string,  # Changed from use_jsonb
                    use_jsonb=self.config.use_jsonb
                )
                logger.info(f"Vector store connected to collection: {self.config.collection_name}")
            except Exception as e:
                logger.error(f"Failed to initialize vector store: {str(e)}")
                raise
        return self._vector_store
    
    def as_retriever(self, search_type: str = "similarity", search_kwargs: Optional[Dict[str, Any]] = None) -> VectorStoreRetriever:
        """
        Create a retriever from the vector store for use in RAG pipelines.
        
        Args:
            search_type: Type of search to perform ("similarity", "mmr", etc.)
            search_kwargs: Additional search parameters (k, fetch_k, lambda_mult, etc.)
            
        Returns:
            A VectorStoreRetriever instance for use in LangChain pipelines
        """
        search_kwargs = search_kwargs or {}
        
        try:
            return self.vector_store.as_retriever(
                search_type=search_type,
                search_kwargs=search_kwargs
            )
        except Exception as e:
            logger.error(f"Error creating retriever: {e}")
            raise
    
    @lru_cache(maxsize=128)
    def embed_query(self, query: str) -> List[float]:
        """
        Embed a single query with caching for better performance.
        
        Args:
            query: Text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        try:
            return self.query_embeddings.embed_query(query)
        except Exception as e:
            logger.error(f"Error embedding query: {e}")
            raise
    
    def embed_queries(self, queries: List[str]) -> List[List[float]]:
        """
        Embed multiple queries in batch for better performance.
        
        Args:
            queries: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        if not queries:
            return []
            
        try:
            return self.query_embeddings.embed_documents(queries)
        except Exception as e:
            logger.error(f"Error batch embedding queries: {e}")
            raise
    
    def embed_documents(self, documents: List[str]) -> List[List[float]]:
        """
        Embed multiple documents in batch for better performance.
        
        Args:
            documents: List of document texts to embed
            
        Returns:
            List of embedding vectors
        """
        if not documents:
            return []
            
        try:
            return self.doc_embeddings.embed_documents(documents)
        except Exception as e:
            logger.error(f"Error batch embedding documents: {e}")
            raise
    
    def similarity_search(
        self, 
        query: str, 
        k: int = 4, 
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        Perform a similarity search.
        
        Args:
            query: Query text
            k: Number of results to return
            filter: Metadata filter to apply
            
        Returns:
            List of document objects with similarity scores
        """
        try:
            return self.vector_store.similarity_search(query, k=k, filter=filter)
        except Exception as e:
            logger.error(f"Error in similarity search: {e}")
            raise
    
    def similarity_search_with_score(
        self, 
        query: str, 
        k: int = 4, 
        filter: Optional[Dict[str, Any]] = None
    ) -> List[tuple]:
        """
        Perform a similarity search with scores.
        
        Args:
            query: Query text
            k: Number of results to return
            filter: Metadata filter to apply
            
        Returns:
            List of tuples (document, score)
        """
        try:
            return self.vector_store.similarity_search_with_score(query, k=k, filter=filter)
        except Exception as e:
            logger.error(f"Error in similarity search with score: {e}")
            raise
    
    def add_documents(self, documents: List[Document]) -> List[str]:
        """
        Add documents to the vector store.
        
        Args:
            documents: List of Document objects
            
        Returns:
            List of document IDs
        """
        if not documents:
            logger.warning("No documents to add")
            return []
            
        try:
            logger.info(f"Adding {len(documents)} documents to vector store")
            return self.vector_store.add_documents(documents)
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            raise
    
    def add_texts(
        self, 
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """
        Add texts to the vector store.
        
        Args:
            texts: List of text strings
            metadatas: Optional list of metadata dicts
            ids: Optional list of IDs
            
        Returns:
            List of document IDs
        """
        try:
            return self.vector_store.add_texts(texts, metadatas=metadatas, ids=ids)
        except Exception as e:
            logger.error(f"Error adding texts: {e}")
            raise
    
    def delete(self, ids: Optional[List[str]] = None, **kwargs) -> None:
        """
        Delete documents from the vector store.
        
        Args:
            ids: List of document IDs to delete
            **kwargs: Additional arguments for delete operation
        """
        try:
            self.vector_store.delete(ids, **kwargs)
            logger.info(f"Deleted {len(ids) if ids else 'all'} documents from vector store")
        except Exception as e:
            logger.error(f"Error deleting documents: {e}")
            raise
    
    def invoke(
        self, 
        query: str,
        k: int = 4,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        Get relevant documents for a query.
        
        Args:
            query: Query text
            k: Number of results to return
            filter: Metadata filter to apply
            
        Returns:
            List of relevant documents
        """
        return self.similarity_search(query, k=k, filter=filter)


# Create a default vector store instance for easy import
default_vector_store = None

def get_vector_store(config: Optional[VectorStoreConfig] = None) -> VectorStore:
    """
    Factory function to create or get a vector store instance.
    
    Args:
        config: Optional custom configuration
        
    Returns:
        VectorStore instance
    """
    global default_vector_store
    
    if default_vector_store is None:
        default_vector_store = VectorStore(config)
    elif config:
        return VectorStore(config)
        
    return default_vector_store