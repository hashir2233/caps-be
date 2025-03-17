from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from sqlmodel import Session, select

from apps.reports.models import Report, ReportCreate, ReportUpdate
from core.utils.common import paginate_response, format_datetime

class ReportService:
    @staticmethod
    def list_reports(
        session: Session,
        page: int = 1,
        limit: int = 20,
        type: Optional[str] = None,
        district: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """List reports with optional filtering"""
        query = select(Report)
        
        # Apply filters if provided
        if type:
            query = query.where(Report.type == type)
        if district:
            query = query.where(Report.district == district)
        if start_date or end_date:
            # Filter by date range (check if report date range overlaps with requested range)
            if start_date:
                start = datetime.fromisoformat(start_date)
                # Reports with end date >= requested start date
                query = query.where(Report.date_range["end"].as_string() >= start_date)
            if end_date:
                end = datetime.fromisoformat(end_date)
                # Reports with start date <= requested end date
                query = query.where(Report.date_range["start"].as_string() <= end_date)
        
        # Count total items
        total = len(session.exec(query).all())
        
        # Apply pagination
        query = query.offset((page - 1) * limit).limit(limit)
        
        # Execute query
        reports = session.exec(query).all()
        
        # Format reports for response
        reports_data = []
        for report in reports:
            report_dict = {
                "id": report.id,
                "title": report.title,
                "type": report.type,
                "district": report.district,
                "dateRange": {
                    "start": report.date_range.get("start"),
                    "end": report.date_range.get("end")
                },
                "status": report.status,
                "createdBy": report.created_by,
                "createdAt": format_datetime(report.created_at)
            }
            reports_data.append(report_dict)
        
        return paginate_response(
            items=reports_data,
            page=page,
            limit=limit,
            total=total
        )
    
    @staticmethod
    def get_report(session: Session, report_id: UUID) -> Dict[str, Any]:
        """Get report by ID"""
        report = session.get(Report, report_id)
        if not report:
            return None
        
        return {
            "id": report.id,
            "title": report.title,
            "description": report.description,
            "type": report.type,
            "district": report.district,
            "dateRange": report.date_range,
            "content": report.content,
            "parameters": report.parameters,
            "status": report.status,
            "createdBy": report.created_by,
            "estimatedCompletion": format_datetime(report.estimated_completion) if report.estimated_completion else None,
            "createdAt": format_datetime(report.created_at),
            "updatedAt": format_datetime(report.updated_at)
        }
    
    @staticmethod
    def create_report(
        session: Session,
        report_data: ReportCreate,
        user_id: UUID
    ) -> Dict[str, Any]:
        """Create a new report"""
        # Generate ID
        report_id = uuid4()
        
        # Calculate estimated completion time (5 minutes per report as an example)
        estimated_completion = datetime.utcnow() + timedelta(minutes=5)
        
        # Create report
        report = Report(
            id=report_id,
            title=report_data.title,
            description=report_data.description,
            type=report_data.type,
            district=report_data.district,
            date_range={
                "start": report_data.date_range.start,
                "end": report_data.date_range.end
            },
            parameters=report_data.parameters.dict() if report_data.parameters else None,
            content={},  # Empty content initially
            status="pending",
            created_by=user_id,
            estimated_completion=estimated_completion,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Save to database
        session.add(report)
        session.commit()
        session.refresh(report)
        
        return ReportService.get_report(session, report_id)
    
    @staticmethod
    def update_report(
        session: Session,
        report_id: UUID,
        report_data: ReportUpdate,
        user_id: UUID
    ) -> Dict[str, Any]:
        """Update a report"""
        report = session.get(Report, report_id)
        
        # Check if report is in a state that allows updates
        if report.status not in ["pending", "draft"]:
            raise ValueError("Cannot update a report that is already being processed or completed")
        
        # Update fields if provided
        if report_data.title:
            report.title = report_data.title
        if report_data.description is not None:
            report.description = report_data.description
        if report_data.parameters:
            # Merge parameters rather than replace
            if report.parameters:
                report.parameters.update(report_data.parameters)
            else:
                report.parameters = report_data.parameters
        
        # Update timestamp
        report.updated_at = datetime.utcnow()
        
        # Save to database
        session.add(report)
        session.commit()
        session.refresh(report)
        
        return ReportService.get_report(session, report_id)
    
    @staticmethod
    def delete_report(session: Session, report_id: UUID) -> bool:
        """Delete a report"""
        report = session.get(Report, report_id)
        if not report:
            return False
        
        # Check if report can be deleted
        if report.status in ["processing"]:
            raise ValueError("Cannot delete a report that is currently being processed")
        
        session.delete(report)
        session.commit()
        
        return True
    
    @staticmethod
    def generate_report_content(session: Session, report_id: UUID) -> Dict[str, Any]:
        """Generate content for a report - this would typically be triggered by a background task"""
        report = session.get(Report, report_id)
        if not report:
            return None
        
        # Update status
        report.status = "processing"
        session.add(report)
        session.commit()
        
        try:
            # In a real application, this would involve querying data, generating charts, etc.
            # For this example, we'll generate mock content
            
            # Example content structure
            content = {
                "summary": f"Crime report for {report.district} district from {report.date_range['start']} to {report.date_range['end']}",
                "totalIncidents": 425,
                "keyStats": {
                    "mostCommonCrime": "Theft",
                    "highRiskAreas": ["Downtown", "Central Park", "West Avenue"],
                    "peakTime": "Friday 22:00-02:00"
                },
                "charts": [
                    {
                        "type": "bar",
                        "title": "Incidents by Crime Type",
                        "dataUrl": f"/api/reports/{report.id}/charts/by-type"
                    },
                    {
                        "type": "heatmap",
                        "title": "Geographic Distribution",
                        "dataUrl": f"/api/reports/{report.id}/charts/heatmap"
                    },
                    {
                        "type": "line",
                        "title": "Incidents Over Time",
                        "dataUrl": f"/api/reports/{report.id}/charts/time-series"
                    }
                ],
                "breakdown": {
                    "byType": {
                        "theft": 142,
                        "assault": 87,
                        "burglary": 63,
                        "robbery": 45,
                        "vandalism": 38,
                        "other": 50
                    },
                    "byTimeOfDay": {
                        "morning": 85,
                        "afternoon": 102,
                        "evening": 143,
                        "night": 95
                    }
                },
                "recommendations": [
                    "Increase patrol presence in downtown area on Friday and Saturday nights",
                    "Implement targeted theft prevention program in high-risk areas",
                    "Enhance lighting in Central Park to reduce nighttime incidents"
                ]
            }
            
            # Update report with content
            report.content = content
            report.status = "completed"
            
        except Exception as e:
            # If generation fails, mark as failed
            report.status = "failed"
            report.content = {"error": str(e)}
            
        # Update report
        report.updated_at = datetime.utcnow()
        session.add(report)
        session.commit()
        session.refresh(report)
        
        return ReportService.get_report(session, report_id)
