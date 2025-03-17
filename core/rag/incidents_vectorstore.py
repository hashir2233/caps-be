from typing import List, Dict, Any
import logging
from uuid import UUID
from datetime import datetime
import json

from langchain_core.documents import Document
from core.rag.vectore_store import VectorStore, VectorStoreConfig
from core.rag.llm import llm
from apps.incidents.models import Incident

logger = logging.getLogger(__name__)

# Store vector store instance
_incident_vector_store = None

def get_incident_vector_store():
    """Get a dedicated vector store instance for incidents"""
    global _incident_vector_store
    
    if _incident_vector_store is None:
        # Create a specific config for incidents
        config = VectorStoreConfig(
            collection_name="incidents",
            embedding_model="models/text-embedding-004",
            embedding_dimensions=768,
        )
        _incident_vector_store = VectorStore(config)
        logger.info("Created incident vector store")
    
    return _incident_vector_store

def incident_to_document(incident: Incident) -> Document:
    """Convert an incident to a document that can be embedded."""
    # Serialize incident data to a string, including all relevant fields for RAG
    
    # Format date for consistent serialization
    date_str = incident.date.isoformat() if isinstance(incident.date, datetime) else str(incident.date)
    
    # Generate a concise text representation of the incident
    content = f"""
    Incident ID: {incident.id}
    Title: {incident.title}
    Type: {incident.type}
    Date: {date_str}
    Description: {incident.description or ""}
    Location: {json.dumps(incident.location)}
    Severity: {incident.severity}
    Status: {incident.status}
    Notes: {incident.notes or ""}
    """
    
    # Add environmental factors if present
    if hasattr(incident, "environmental_factors") and incident.environmental_factors:
        content += f"Environmental Factors: {json.dumps(incident.environmental_factors)}\n"
    
    # Add socioeconomic factors if present
    if hasattr(incident, "socioeconomic_factors") and incident.socioeconomic_factors:
        content += f"Socioeconomic Factors: {json.dumps(incident.socioeconomic_factors)}\n"

    # Create document with metadata for filtering
    return Document(
        page_content=content,
        metadata={
            "id": str(incident.id),
            "type": incident.type,
            "date": date_str,
            "severity": incident.severity,
            "status": incident.status,
            "district": incident.location.get("district", "unknown"),
            "neighborhood": incident.location.get("neighborhood", "unknown"),
            "created_at": incident.created_at.isoformat() if isinstance(incident.created_at, datetime) else str(incident.created_at),
            "updated_at": incident.updated_at.isoformat() if isinstance(incident.updated_at, datetime) else str(incident.updated_at),
        }
    )

def add_incident_to_vector_store(incident: Incident) -> None:
    """Add incident to vector store."""
    try:
        vector_store = get_incident_vector_store()
        document = incident_to_document(incident)
        vector_store.add_documents([document])
        logger.info(f"Added incident {incident.id} to vector store")
    except Exception as e:
        logger.error(f"Error adding incident {incident.id} to vector store: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise

def update_incident_in_vector_store(incident: Incident) -> None:
    """Update incident in vector store by deleting and re-adding."""
    try:
        vector_store = get_incident_vector_store()
        
        # Delete the existing document
        vector_store.delete(filter={"id": str(incident.id)})
        
        # Add the updated document
        document = incident_to_document(incident)
        vector_store.add_documents([document])
        
        logger.info(f"Updated incident {incident.id} in vector store")
    except Exception as e:
        logger.error(f"Error updating incident {incident.id} in vector store: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise

def delete_incident_from_vector_store(incident_id: UUID) -> None:
    """Remove incident from vector store."""
    try:
        vector_store = get_incident_vector_store()
        vector_store.delete(filter={"id": str(incident_id)})
        logger.info(f"Deleted incident {incident_id} from vector store")
    except Exception as e:
        logger.error(f"Error deleting incident {incident_id} from vector store: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise

def get_similar_incidents(query: str, filters: Dict[str, Any] = None, k: int = 5) -> List[Dict]:
    """Get similar incidents based on a query and optional filters."""
    try:
        vector_store = get_incident_vector_store()
        
        # Convert filters to the format expected by the vector store
        search_filter = {}
        if filters:
            search_filter = filters
            
        # Perform similarity search
        documents = vector_store.similarity_search(query, k=k, filter=search_filter)
        
        # Extract and return incident IDs and metadata
        return [
            {
                "id": doc.metadata["id"],
                "score": doc.metadata.get("score", 1.0),  # Some vector stores provide score
                "type": doc.metadata["type"],
                "date": doc.metadata["date"],
                "severity": doc.metadata["severity"],
                "district": doc.metadata["district"]
            }
            for doc in documents
        ]
    except Exception as e:
        logger.error(f"Error searching for similar incidents: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return []
