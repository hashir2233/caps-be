from typing import Dict, Any, Optional
from datetime import datetime
import logging
from uuid import UUID, uuid4
from sqlmodel import Session, select
from sqlalchemy.exc import SQLAlchemyError, OperationalError

from apps.incidents.models import Incident, IncidentCreate, IncidentUpdate
from core.utils.common import paginate_response, format_datetime
from core.rag.incidents_vectorstore import (
    add_incident_to_vector_store,
    update_incident_in_vector_store,
    delete_incident_from_vector_store
)

logger = logging.getLogger(__name__)

# Define a custom exception for schema mismatch
class SchemaMismatchError(Exception):
    """Raised when database schema doesn't match the models"""
    pass

class IncidentService:
    @staticmethod
    def list_incidents(
        session: Session,
        page: int = 1,
        limit: int = 20,
        type: Optional[str] = None,
        district: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        severity: Optional[str] = None
    ) -> Dict[str, Any]:
        """List incidents with optional filtering"""
        try:
            query = select(Incident)
            
            # Apply filters if provided
            if type:
                query = query.where(Incident.type == type)
            if district:
                query = query.where(Incident.location["district"].as_string() == district)
            if start_date:
                start_datetime = datetime.fromisoformat(start_date)
                query = query.where(Incident.date >= start_datetime)
            if end_date:
                end_datetime = datetime.fromisoformat(end_date)
                query = query.where(Incident.date <= end_datetime)
            if severity:
                query = query.where(Incident.severity == severity)
            
            # Count total items - use a try/except to handle potential column mapping issues
            try:
                total = len(session.exec(query).all())
                
                # Apply pagination
                query = query.offset((page - 1) * limit).limit(limit)
                
                # Execute query
                incidents = session.exec(query).all()
                
                # Convert to dict and format datetime fields
                incidents_data = [IncidentService._format_incident(incident) for incident in incidents]
                
                return paginate_response(
                    items=incidents_data,
                    page=page,
                    limit=limit,
                    total=total
                )
            except OperationalError as e:
                # If there's a database schema mismatch, log it and handle it gracefully
                error_message = f"Database schema mismatch error: {str(e)}"
                logger.error(error_message)
                # Raise a custom exception instead of returning a tuple
                raise SchemaMismatchError("Database schema needs to be updated. Some columns might be missing.")
        except SQLAlchemyError as e:
            # Log the exception for debugging
            logger.error(f"Database error in list_incidents: {str(e)}")
            # Return a structured error response
            raise ValueError(f"Database error: {str(e)}")
    
    @staticmethod
    def get_incident(session: Session, incident_id: UUID) -> Dict[str, Any]:
        """Get incident by ID"""
        try:
            incident = session.get(Incident, incident_id)
            if not incident:
                return None
            
            return IncidentService._format_incident(incident)
        except SQLAlchemyError as e:
            logger.error(f"Database error in get_incident: {str(e)}")
            raise ValueError(f"Database error: {str(e)}")
    
    @staticmethod
    def create_incident(
        session: Session,
        incident_data: IncidentCreate,
        user_id: UUID
    ) -> Dict[str, Any]:
        """Create a new incident"""
        try:
            # Generate ID
            incident_id = uuid4()
            
            # Parse date
            date = datetime.fromisoformat(incident_data.date)
            
            # Create incident
            incident = Incident(
                id=incident_id,
                title=incident_data.title,
                description=incident_data.description,
                type=incident_data.type,
                date=date,
                location=incident_data.location.dict(),
                severity=incident_data.severity,
                status=incident_data.status,
                reporting_officer=user_id,
                notes=incident_data.notes,
                flags=incident_data.flags.dict() if incident_data.flags else None,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Add additional fields if they exist in the database schema
            try:
                if incident_data.environmental_factors:
                    incident.environmental_factors = incident_data.environmental_factors.dict()
                if incident_data.socioeconomic_factors:
                    incident.socioeconomic_factors = incident_data.socioeconomic_factors.dict()
                if incident_data.weapon_used:
                    incident.weapon_used = incident_data.weapon_used
                if incident_data.victim_count is not None:
                    incident.victim_count = incident_data.victim_count
                if incident_data.suspect_count is not None:
                    incident.suspect_count = incident_data.suspect_count
                if incident_data.estimated_loss_value is not None:
                    incident.estimated_loss_value = incident_data.estimated_loss_value
            except AttributeError:
                # Log but continue if some attributes aren't found
                logger.warning("Some attributes couldn't be set - schema may be outdated")
            
            # Save to database
            session.add(incident)
            session.commit()
            session.refresh(incident)
            
            # Add to vector store for RAG
            try:
                add_incident_to_vector_store(incident)
            except Exception as e:
                logger.error(f"Vector store update failed, but incident was created: {e}")
            
            return IncidentService._format_incident(incident)
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error in create_incident: {str(e)}")
            raise ValueError(f"Database error: {str(e)}")
    
    @staticmethod
    def update_incident(
        session: Session,
        incident_id: UUID,
        incident_data: IncidentUpdate,
        user_id: UUID
    ) -> Dict[str, Any]:
        """Update an incident"""
        try:
            incident = session.get(Incident, incident_id)
            if not incident:
                return None
            
            # Update fields if provided
            if incident_data.title:
                incident.title = incident_data.title
            if incident_data.description is not None:
                incident.description = incident_data.description
            if incident_data.type:
                incident.type = incident_data.type
            if incident_data.date:
                incident.date = datetime.fromisoformat(incident_data.date)
            if incident_data.location:
                incident.location = incident_data.location.dict()
            if incident_data.severity:
                incident.severity = incident_data.severity
            if incident_data.status:
                incident.status = incident_data.status
            if incident_data.reporting_officer:
                incident.reporting_officer = incident_data.reporting_officer
            if incident_data.notes is not None:
                incident.notes = incident_data.notes
            if incident_data.flags:
                incident.flags = incident_data.flags.dict()
            
            # Try to update additional fields if they exist in the schema
            try:
                if incident_data.environmental_factors:
                    incident.environmental_factors = incident_data.environmental_factors.dict()
                if incident_data.socioeconomic_factors:
                    incident.socioeconomic_factors = incident_data.socioeconomic_factors.dict()
                if incident_data.weapon_used is not None:
                    incident.weapon_used = incident_data.weapon_used
                if incident_data.victim_count is not None:
                    incident.victim_count = incident_data.victim_count
                if incident_data.suspect_count is not None:
                    incident.suspect_count = incident_data.suspect_count
                if incident_data.estimated_loss_value is not None:
                    incident.estimated_loss_value = incident_data.estimated_loss_value
                if incident_data.response_time_minutes is not None:
                    incident.response_time_minutes = incident_data.response_time_minutes
                if incident_data.risk_score is not None:
                    incident.risk_score = incident_data.risk_score
            except AttributeError:
                # Log but continue if some attributes aren't found
                logger.warning("Some attributes couldn't be updated - schema may be outdated")
            
            # Update timestamp
            incident.updated_at = datetime.utcnow()
            
            # Save to database
            session.add(incident)
            session.commit()
            session.refresh(incident)
            
            # Update in vector store
            try:
                update_incident_in_vector_store(incident)
            except Exception as e:
                logger.error(f"Vector store update failed, but incident was updated: {e}")
            
            return IncidentService._format_incident(incident)
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error in update_incident: {str(e)}")
            raise ValueError(f"Database error: {str(e)}")
    
    @staticmethod
    def delete_incident(session: Session, incident_id: UUID) -> bool:
        """Delete an incident"""
        try:
            incident = session.get(Incident, incident_id)
            if not incident:
                return False
            
            session.delete(incident)
            session.commit()
            
            # Delete from vector store
            try:
                delete_incident_from_vector_store(incident_id)
            except Exception as e:
                logger.error(f"Vector store deletion failed, but incident was deleted: {e}")
            
            return True
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error in delete_incident: {str(e)}")
            raise ValueError(f"Database error: {str(e)}")
    
    @staticmethod
    def _format_incident(incident: Incident) -> Dict[str, Any]:
        """Format incident data for response"""
        incident_data = {
            "id": incident.id,
            "title": incident.title,
            "description": incident.description,
            "type": incident.type,
            "date": format_datetime(incident.date),
            "location": incident.location,
            "severity": incident.severity,
            "status": incident.status,
            "reporting_officer": incident.reporting_officer,
            "notes": incident.notes,
            "flags": incident.flags,
            "created_at": format_datetime(incident.created_at),
            "updated_at": format_datetime(incident.updated_at)
        }
        
        # Include additional fields safely if they exist
        try:
            if hasattr(incident, "environmental_factors") and incident.environmental_factors:
                incident_data["environmental_factors"] = incident.environmental_factors
            if hasattr(incident, "socioeconomic_factors") and incident.socioeconomic_factors:
                incident_data["socioeconomic_factors"] = incident.socioeconomic_factors
            if hasattr(incident, "weapon_used") and incident.weapon_used:
                incident_data["weapon_used"] = incident.weapon_used
            if hasattr(incident, "victim_count") and incident.victim_count is not None:
                incident_data["victim_count"] = incident.victim_count
            if hasattr(incident, "suspect_count") and incident.suspect_count is not None:
                incident_data["suspect_count"] = incident.suspect_count
            if hasattr(incident, "estimated_loss_value") and incident.estimated_loss_value is not None:
                incident_data["estimated_loss_value"] = incident.estimated_loss_value
            if hasattr(incident, "response_time_minutes") and incident.response_time_minutes is not None:
                incident_data["response_time_minutes"] = incident.response_time_minutes
            if hasattr(incident, "related_incidents") and incident.related_incidents:
                incident_data["related_incidents"] = incident.related_incidents
            if hasattr(incident, "risk_score") and incident.risk_score is not None:
                incident_data["risk_score"] = incident.risk_score
        except (AttributeError, TypeError) as e:
            # Just log and continue if fields aren't accessible
            logger.warning(f"Error accessing attribute in _format_incident: {str(e)}")
        
        return incident_data
