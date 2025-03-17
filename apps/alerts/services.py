from typing import Dict, Any, Optional
from datetime import datetime
from uuid import UUID, uuid4
from sqlmodel import Session, select

from apps.alerts.models import Alert, AlertCreate, AlertUpdate
from apps.incidents.services import IncidentService
from core.utils.common import paginate_response, format_datetime

class AlertService:
    @staticmethod
    def list_alerts(
        session: Session,
        page: int = 1,
        limit: int = 20,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        district: Optional[str] = None
    ) -> Dict[str, Any]:
        """List alerts with optional filtering"""
        query = select(Alert)
        
        # Apply filters if provided
        if severity:
            query = query.where(Alert.severity == severity)
        if status:
            if status == "reviewed":
                query = query.where(Alert.reviewed.is_(True))
            elif status == "unreviewed":
                query = query.where(Alert.reviewed.is_(False))
        if district:
            query = query.where(Alert.location["district"].as_string() == district)
        
        # Count total items
        total = len(session.exec(query).all())
        
        # Apply pagination
        query = query.offset((page - 1) * limit).limit(limit)
        
        # Execute query
        alerts = session.exec(query).all()
        
        # Format alerts for response
        alerts_data = []
        for alert in alerts:
            alert_dict = {
                "id": alert.id,
                "title": alert.title,
                "severity": alert.severity,
                "location": alert.location["address"] if isinstance(alert.location, dict) and "address" in alert.location else "Unknown",
                "timestamp": format_datetime(alert.timestamp),
                "reviewed": alert.reviewed
            }
            alerts_data.append(alert_dict)
        
        return {
            "alerts": alerts_data,
            "pagination": {
                "total": total,
                "page": page,
                "limit": limit,
                "pages": (total + limit - 1) // limit
            }
        }
    
    @staticmethod
    def get_alert(session: Session, alert_id: UUID) -> Dict[str, Any]:
        """Get alert by ID"""
        alert = session.get(Alert, alert_id)
        if not alert:
            return None
        
        return {
            "id": alert.id,
            "title": alert.title,
            "description": alert.description,
            "severity": alert.severity,
            "location": alert.location,
            "timestamp": format_datetime(alert.timestamp),
            "source": alert.source,
            "relatedIncidents": alert.related_incidents,
            "recommendations": alert.recommendations,
            "reviewed": alert.reviewed,
            "createdAt": format_datetime(alert.created_at),
            "updatedAt": format_datetime(alert.updated_at)
        }
    
    @staticmethod
    def create_alert(
        session: Session,
        alert_data: AlertCreate,
        user_id: UUID
    ) -> Dict[str, Any]:
        """Create a new alert"""
        # Generate ID
        alert_id = uuid4()
        
        # Process related incidents
        related_incidents = []
        if alert_data.related_incidents:
            for incident_id in alert_data.related_incidents:
                incident = IncidentService.get_incident(session, incident_id)
                if incident:
                    related_incidents.append({
                        "id": incident["id"],
                        "title": incident["title"],
                        "type": incident["type"],
                        "date": incident["date"]
                    })
        
        # Create alert
        alert = Alert(
            id=alert_id,
            title=alert_data.title,
            description=alert_data.description,
            severity=alert_data.severity,
            location=alert_data.location.dict(),
            timestamp=datetime.utcnow(),
            source="predictive_algorithm",
            related_incidents=related_incidents,
            recommendations=alert_data.recommendations,
            reviewed=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Save to database
        session.add(alert)
        session.commit()
        session.refresh(alert)
        
        return AlertService.get_alert(session, alert_id)
    
    @staticmethod
    def update_alert(
        session: Session,
        alert_id: UUID,
        alert_data: AlertUpdate
    ) -> Dict[str, Any]:
        """Update an alert"""
        alert = session.get(Alert, alert_id)
        
        # Update fields if provided
        if alert_data.title:
            alert.title = alert_data.title
        if alert_data.description is not None:
            alert.description = alert_data.description
        if alert_data.severity:
            alert.severity = alert_data.severity
        if alert_data.reviewed is not None:
            alert.reviewed = alert_data.reviewed
        if alert_data.recommendations:
            alert.recommendations = alert_data.recommendations
        
        # Update timestamp
        alert.updated_at = datetime.utcnow()
        
        # Save to database
        session.add(alert)
        session.commit()
        session.refresh(alert)
        
        return AlertService.get_alert(session, alert_id)
    
    @staticmethod
    def delete_alert(session: Session, alert_id: UUID) -> bool:
        """Delete an alert"""
        alert = session.get(Alert, alert_id)
        if not alert:
            return False
        
        session.delete(alert)
        session.commit()
        
        return True
