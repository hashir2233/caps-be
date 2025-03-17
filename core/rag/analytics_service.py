from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
from uuid import UUID
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import json
import pandas as pd
from collections import Counter
from sklearn.cluster import DBSCAN
import numpy as np

from core.rag.llm import llm
from core.rag.incidents_vectorstore import get_similar_incidents
from apps.incidents.services import IncidentService
from sqlmodel import Session, select
from apps.incidents.models import Incident

logger = logging.getLogger(__name__)

# Custom JSON encoder to handle UUID serialization
class UUIDEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            # Convert UUID to string
            return str(obj)
        if isinstance(obj, datetime):
            # Convert datetime to ISO format string
            return obj.isoformat()
        # Let the base class default method handle other types
        return super().default(obj)

class AnalyticsService:
    
    @staticmethod
    def generate_predictive_analysis(
        session: Session,
        days_ahead: int,
        crime_type: Optional[str] = None,
        district: Optional[str] = None,
        confidence_threshold: int = 70
    ) -> Dict[str, Any]:
        """Generate predictive crime analysis using LLM and RAG"""
        
        try:
            # 1. Fetch recent incidents data
            query = select(Incident).order_by(Incident.date.desc()).limit(100)
            
            # Apply filters if provided
            if crime_type:
                query = query.where(Incident.type == crime_type)
            if district:
                query = query.where(Incident.location["district"].as_string() == district)
                
            incidents = session.exec(query).all()
            
            if not incidents:
                return {
                    "predictionDate": datetime.now().isoformat(),
                    "daysAhead": days_ahead,
                    "message": "Insufficient data for prediction",
                    "predictions": []
                }
            
            # 2. Prepare input data for LLM
            incidents_data = []
            for incident in incidents:
                incident_dict = IncidentService._format_incident(incident)
                incidents_data.append(incident_dict)
            
            # 3. Create a prompt template for the prediction task
            prediction_prompt = PromptTemplate(
                input_variables=["incidents_data", "days_ahead", "crime_type", "district", "confidence_threshold"],
                template="""
                You are an advanced crime prediction AI. Based on the historical crime incident data provided, 
                generate predictions for potential future crime incidents in the next {days_ahead} days.
                
                Historical incident data:
                {incidents_data}
                
                Instructions:
                1. Analyze patterns in the historical data
                2. Consider time-based patterns, location-based patterns, crime types, and severity
                3. Generate predictions for the next {days_ahead} days
                4. Only include predictions with confidence level at or above {confidence_threshold}%
                5. If a specific crime type "{crime_type}" or district "{district}" is specified, focus on that
                6. For each prediction, provide realistic coordinates matching the districts in the historical data
                7. Ensure the probability values are between 0.0 and 1.0
                8. Use specific time ranges in the timeframe that reflect typical crime patterns
                9. List 2-4 specific factors that led to each prediction
                10. Include 3-5 specific recommendations for law enforcement action
                
                Return your analysis as a valid JSON object with the following structure:
                ```
                {{
                    "predictions": [
                        {{
                            "coordinates": [longitude, latitude],
                            "probability": 0.XX (a value between 0-1),
                            "crimeType": "type of crime predicted",
                            "timeframe": {{
                                "start": "ISO datetime",
                                "end": "ISO datetime"
                            }},
                            "factors": ["factor1", "factor2", "factor3"]
                        }},
                        ... more predictions ...
                    ],
                    "recommendations": [
                        {{
                            "district": "district name",
                            "action": "recommended action"
                        }},
                        ... more recommendations ...
                    ]
                }}
                ```
                
                Ensure the output is properly formatted JSON, so it can be parsed programmatically.
                """
            )
            
            # 4. Use LLMChain
            chain = LLMChain(llm=llm, prompt=prediction_prompt)
            
            # Filter parameters for prompt
            crime_type_param = crime_type if crime_type else "any"
            district_param = district if district else "all districts"
            
            # Serialize with custom encoder to handle UUID and datetime objects
            incidents_json = json.dumps(
                incidents_data[:20],  # Limit to avoid token limits
                cls=UUIDEncoder
            )
            
            # Execute the chain
            response = chain.run(
                incidents_data=incidents_json,
                days_ahead=days_ahead,
                crime_type=crime_type_param,
                district=district_param,
                confidence_threshold=confidence_threshold
            )
            
            # 5. Parse and format the response
            try:
                # Extract the JSON part from the response
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = response[json_start:json_end]
                    predictions_data = json.loads(json_str)
                else:
                    # If no JSON found, attempt to parse the entire response
                    predictions_data = json.loads(response)

                # 6. Structure the final response
                result = {
                    "predictionDate": datetime.now().isoformat(),
                    "daysAhead": days_ahead,
                    "modelVersion": "v2.3.1",  # Placeholder version info
                    "modelAccuracy": 87,       # Placeholder accuracy
                }
                
                # Add predictions if present
                if "predictions" in predictions_data:
                    result["predictions"] = predictions_data["predictions"]
                else:
                    result["predictions"] = []
                
                # Add recommendations if present
                if "recommendations" in predictions_data:
                    result["recommendations"] = predictions_data["recommendations"]
                else:
                    result["recommendations"] = []
                    
                return result
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM response as JSON: {e}")
                logger.debug(f"Response was: {response}")
                
                # Return a fallback response
                return {
                    "predictionDate": datetime.now().isoformat(),
                    "daysAhead": days_ahead,
                    "error": "Failed to generate structured predictions",
                    "rawResponse": response[:500]  # Include part of raw response for debugging
                }
                
        except Exception as e:
            logger.error(f"Error in predictive analysis: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise ValueError(f"Prediction generation failed: {str(e)}")
    
    @staticmethod
    def generate_crime_statistics(
        incidents: List[Incident],
        start_date: datetime,
        end_date: datetime,
        group_by: str,
        district: Optional[str] = None,
        crime_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate crime statistics with AI-enhanced insights"""
        try:
            # Group incidents by the specified dimension
            grouped_stats = {}
            
            # Extract basic statistics first
            if group_by == "month":
                # Group by month
                for incident in incidents:
                    month_key = incident.date.strftime('%Y-%m')
                    if month_key not in grouped_stats:
                        grouped_stats[month_key] = {"count": 0, "breakdown": {}}
                    
                    grouped_stats[month_key]["count"] += 1
                    
                    # Track breakdown by type
                    incident_type = incident.type
                    if incident_type not in grouped_stats[month_key]["breakdown"]:
                        grouped_stats[month_key]["breakdown"][incident_type] = 0
                    
                    grouped_stats[month_key]["breakdown"][incident_type] += 1
            
            elif group_by == "day":
                # Group by day
                for incident in incidents:
                    day_key = incident.date.strftime('%Y-%m-%d')
                    if day_key not in grouped_stats:
                        grouped_stats[day_key] = {"count": 0, "breakdown": {}}
                    
                    grouped_stats[day_key]["count"] += 1
                    
                    # Track breakdown by type
                    incident_type = incident.type
                    if incident_type not in grouped_stats[day_key]["breakdown"]:
                        grouped_stats[day_key]["breakdown"][incident_type] = 0
                    
                    grouped_stats[day_key]["breakdown"][incident_type] += 1
            
            elif group_by == "week":
                # Group by week
                for incident in incidents:
                    week_key = f"{incident.date.strftime('%Y')}-W{incident.date.isocalendar()[1]}"
                    if week_key not in grouped_stats:
                        grouped_stats[week_key] = {"count": 0, "breakdown": {}}
                    
                    grouped_stats[week_key]["count"] += 1
                    
                    # Track breakdown by type
                    incident_type = incident.type
                    if incident_type not in grouped_stats[week_key]["breakdown"]:
                        grouped_stats[week_key]["breakdown"][incident_type] = 0
                    
                    grouped_stats[week_key]["breakdown"][incident_type] += 1
            
            elif group_by == "type":
                # Group by crime type
                for incident in incidents:
                    type_key = incident.type
                    if type_key not in grouped_stats:
                        grouped_stats[type_key] = {"count": 0, "districts": {}}
                    
                    grouped_stats[type_key]["count"] += 1
                    
                    # Track breakdown by district
                    district_val = incident.location.get("district", "unknown")
                    if district_val not in grouped_stats[type_key]["districts"]:
                        grouped_stats[type_key]["districts"][district_val] = 0
                    
                    grouped_stats[type_key]["districts"][district_val] += 1
            
            elif group_by == "district":
                # Group by district
                for incident in incidents:
                    district_key = incident.location.get("district", "unknown")
                    if district_key not in grouped_stats:
                        grouped_stats[district_key] = {"count": 0, "breakdown": {}}
                    
                    grouped_stats[district_key]["count"] += 1
                    
                    # Track breakdown by type
                    incident_type = incident.type
                    if incident_type not in grouped_stats[district_key]["breakdown"]:
                        grouped_stats[district_key]["breakdown"][incident_type] = 0
                    
                    grouped_stats[district_key]["breakdown"][incident_type] += 1
            
            # Format statistics for output
            statistics = []
            for key, stats in grouped_stats.items():
                if group_by == "type":
                    stat_item = {
                        "type": key,
                        "count": stats["count"],
                        "districts": stats["districts"]
                    }
                elif group_by == "district":
                    stat_item = {
                        "district": key,
                        "count": stats["count"],
                        "breakdown": stats["breakdown"]
                    }
                else:
                    stat_item = {
                        "period": key,
                        "count": stats["count"],
                        "breakdown": stats["breakdown"]
                    }
                statistics.append(stat_item)
            
            # Sort statistics by period or count
            if group_by in ["month", "day", "week"]:
                statistics.sort(key=lambda x: x["period"])
            else:
                statistics.sort(key=lambda x: x["count"], reverse=True)
            
            # Calculate trends if we have time-based data
            trends = {"overall": "0%", "byType": {}}
            if len(statistics) >= 2 and group_by in ["month", "day", "week"]:
                try:
                    # Calculate overall trend
                    first_count = statistics[0]["count"] if statistics[0]["count"] > 0 else 1
                    last_count = statistics[-1]["count"]
                    percent_change = ((last_count - first_count) / first_count) * 100
                    trends["overall"] = f"{'+' if percent_change >= 0 else ''}{percent_change:.1f}%"
                    
                    # Calculate trends by type
                    crime_types = set()
                    for stat in statistics:
                        crime_types.update(stat["breakdown"].keys())
                    
                    for crime_type in crime_types:
                        first_type_count = statistics[0]["breakdown"].get(crime_type, 0)
                        last_type_count = statistics[-1]["breakdown"].get(crime_type, 0)
                        
                        if first_type_count > 0:
                            type_change = ((last_type_count - first_type_count) / first_type_count) * 100
                            trends["byType"][crime_type] = f"{'+' if type_change >= 0 else ''}{type_change:.1f}%"
                        else:
                            trends["byType"][crime_type] = "N/A"
                except Exception as e:
                    logger.error(f"Error calculating trends: {e}")
            
            # Prepare data for LLM insights
            incidents_data = []
            for incident in incidents[:50]:  # Limit to 50 incidents for the LLM
                incident_dict = IncidentService._format_incident(incident)
                incidents_data.append(incident_dict)
            
            # Use LLM to generate insights
            insights = AnalyticsService._generate_statistics_insights(
                incidents_data=incidents_data,
                statistics=statistics,
                trends=trends,
                group_by=group_by,
                district=district,
                crime_type=crime_type
            )
            
            # Build the complete response
            result = {
                "timeframe": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "totalIncidents": len(incidents),
                "groupedBy": group_by,
                "statistics": statistics,
                "trends": trends,
                "insights": insights
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating crime statistics: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise ValueError(f"Statistics generation failed: {str(e)}")
    
    @staticmethod
    def _generate_statistics_insights(
        incidents_data: List[Dict[str, Any]],
        statistics: List[Dict[str, Any]],
        trends: Dict[str, Any],
        group_by: str,
        district: Optional[str] = None,
        crime_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate insights for crime statistics using LLM"""
        try:
            # Serialize data for LLM
            incidents_json = json.dumps(
                incidents_data[:20],  # Limit to avoid token limits
                cls=UUIDEncoder
            )
            
            statistics_json = json.dumps(statistics, cls=UUIDEncoder)
            trends_json = json.dumps(trends, cls=UUIDEncoder)
            
            # Create prompt for insights
            insights_prompt = PromptTemplate(
                input_variables=["incidents_data", "statistics", "trends", "group_by", "district", "crime_type"],
                template="""
                You are an expert crime analyst. Based on the crime statistics provided, generate insightful observations and recommendations.
                
                Crime incident sample:
                {incidents_data}
                
                Statistics (grouped by {group_by}):
                {statistics}
                
                Trends:
                {trends}
                
                Filters:
                - District: {district}
                - Crime Type: {crime_type}
                
                Provide a comprehensive analysis with the following components in JSON format:
                1. Key findings (3-5 bullet points)
                2. Patterns (2-3 emerging or declining patterns)
                3. Hotspots (1-3 areas with highest crime concentration, if district data is available)
                4. Recommendations (3-5 actionable items for law enforcement)
                
                Return your analysis as a valid JSON object with this structure:
                ```
                {{
                    "keyFindings": [
                        "Finding 1",
                        "Finding 2",
                        ...more findings...
                    ],
                    "patterns": [
                        "Pattern 1",
                        "Pattern 2",
                        ...more patterns...
                    ],
                    "hotspots": [
                        {{
                            "district": "District name",
                            "count": 0
                        }},
                        ...more hotspots...
                    ],
                    "recommendations": [
                        "Recommendation 1",
                        "Recommendation 2",
                        ...more recommendations...
                    ]
                }}
                ```
                
                Ensure your analysis is data-driven and provides actionable insights.
                """
            )
            
            # Execute LLM chain
            chain = LLMChain(llm=llm, prompt=insights_prompt)
            
            district_param = district if district else "all districts"
            crime_type_param = crime_type if crime_type else "all crime types"
            
            response = chain.run(
                incidents_data=incidents_json,
                statistics=statistics_json,
                trends=trends_json,
                group_by=group_by,
                district=district_param,
                crime_type=crime_type_param
            )
            
            # Parse LLM response
            try:
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = response[json_start:json_end]
                    insights_data = json.loads(json_str)
                else:
                    insights_data = json.loads(response)
                
                return insights_data
            except json.JSONDecodeError:
                logger.error("Failed to parse insights as JSON")
                return {
                    "keyFindings": ["Analysis error"],
                    "patterns": ["Could not analyze patterns"],
                    "hotspots": [],
                    "recommendations": ["Review raw data manually"]
                }
                
        except Exception as e:
            logger.error(f"Error generating insights: {str(e)}")
            return {
                "keyFindings": [f"Error: {str(e)}"],
                "patterns": ["Analysis failed"],
                "hotspots": [],
                "recommendations": ["Error in analysis"]
            }
    
    @staticmethod
    def analyze_time_patterns(
        incidents: List[Incident],
        time_factor: str,
        crime_type: Optional[str] = None,
        district: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze crime patterns across different time periods"""
        try:
            # Count incidents by the specified time factor
            time_counts = {}
            
            if time_factor == "hour_of_day":
                # Group by hour of day (0-23)
                for incident in incidents:
                    hour = incident.date.hour
                    if hour not in time_counts:
                        time_counts[hour] = {"count": 0, "types": {}}
                    
                    time_counts[hour]["count"] += 1
                    
                    # Track breakdown by type
                    incident_type = incident.type
                    if incident_type not in time_counts[hour]["types"]:
                        time_counts[hour]["types"][incident_type] = 0
                    
                    time_counts[hour]["types"][incident_type] += 1
                
                # Format for output
                patterns = []
                for hour in range(24):  # Ensure all 24 hours are represented
                    patterns.append({
                        "timeValue": hour,
                        "displayValue": f"{hour:02d}:00",
                        "count": time_counts.get(hour, {"count": 0, "types": {}})["count"],
                        "breakdown": time_counts.get(hour, {"count": 0, "types": {}})["types"]
                    })
                
            elif time_factor == "day_of_week":
                # Map of day indices to names
                days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                
                # Group by day of week (0-6 where 0 is Monday)
                for incident in incidents:
                    # Convert to 0-6 (Monday-Sunday)
                    weekday = incident.date.weekday()
                    day_name = days[weekday]
                    
                    if day_name not in time_counts:
                        time_counts[day_name] = {"count": 0, "types": {}}
                    
                    time_counts[day_name]["count"] += 1
                    
                    # Track breakdown by type
                    incident_type = incident.type
                    if incident_type not in time_counts[day_name]["types"]:
                        time_counts[day_name]["types"][incident_type] = 0
                    
                    time_counts[day_name]["types"][incident_type] += 1
                
                # Format for output
                patterns = []
                for day in days:  # Ensure all days are represented
                    patterns.append({
                        "timeValue": day,
                        "displayValue": day,
                        "count": time_counts.get(day, {"count": 0, "types": {}})["count"],
                        "breakdown": time_counts.get(day, {"count": 0, "types": {}})["types"]
                    })
                
            else:  # month_of_year
                # Map of month indices to names
                months = ["January", "February", "March", "April", "May", "June", 
                         "July", "August", "September", "October", "November", "December"]
                
                # Group by month (1-12)
                for incident in incidents:
                    month = incident.date.month
                    month_name = months[month - 1]
                    
                    if month_name not in time_counts:
                        time_counts[month_name] = {"count": 0, "types": {}}
                    
                    time_counts[month_name]["count"] += 1
                    
                    # Track breakdown by type
                    incident_type = incident.type
                    if incident_type not in time_counts[month_name]["types"]:
                        time_counts[month_name]["types"][incident_type] = 0
                    
                    time_counts[month_name]["types"][incident_type] += 1
                
                # Format for output
                patterns = []
                for month in months:  # Ensure all months are represented
                    patterns.append({
                        "timeValue": month,
                        "displayValue": month,
                        "count": time_counts.get(month, {"count": 0, "types": {}})["count"],
                        "breakdown": time_counts.get(month, {"count": 0, "types": {}})["types"]
                    })
            
            # Find peak times and patterns
            peak_time = max(patterns, key=lambda x: x["count"]) if patterns else None
            
            # Calculate the standard deviation to identify unusual patterns
            counts = [p["count"] for p in patterns]
            mean_count = sum(counts) / len(counts) if counts else 0
            variance = sum((c - mean_count) ** 2 for c in counts) / len(counts) if counts else 0
            std_dev = variance ** 0.5
            
            # Find anomalies (values more than 1.5 standard deviations from the mean)
            anomalies = []
            for pattern in patterns:
                if abs(pattern["count"] - mean_count) > 1.5 * std_dev:
                    anomalies.append({
                        "timeValue": pattern["displayValue"],
                        "count": pattern["count"],
                        "deviation": (pattern["count"] - mean_count) / std_dev if std_dev else 0,
                        "isHigh": pattern["count"] > mean_count
                    })
            
            # Prepare data for LLM analysis
            incidents_data = []
            for incident in incidents[:30]:  # Limit to 30 incidents for the LLM
                incident_dict = IncidentService._format_incident(incident)
                incidents_data.append(incident_dict)
            
            # Get LLM insights
            insights = AnalyticsService._analyze_time_pattern_insights(
                patterns=patterns,
                anomalies=anomalies,
                peak_time=peak_time,
                time_factor=time_factor,
                incidents_sample=incidents_data,
                district=district,
                crime_type=crime_type
            )
            
            # Return final result
            return {
                "timeFactor": time_factor,
                "crimeType": crime_type or "all",
                "district": district or "all",
                "patterns": patterns,
                "peakTime": peak_time,
                "anomalies": anomalies,
                "insights": insights,
                "totalIncidents": len(incidents)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing time patterns: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise ValueError(f"Time pattern analysis failed: {str(e)}")
    
    @staticmethod
    def _analyze_time_pattern_insights(
        patterns: List[Dict[str, Any]],
        anomalies: List[Dict[str, Any]],
        peak_time: Dict[str, Any],
        time_factor: str,
        incidents_sample: List[Dict[str, Any]],
        district: Optional[str] = None,
        crime_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate insights on time patterns using LLM"""
        try:
            # Prepare data for prompt
            patterns_json = json.dumps(patterns, cls=UUIDEncoder)
            anomalies_json = json.dumps(anomalies, cls=UUIDEncoder)
            peak_time_json = json.dumps(peak_time, cls=UUIDEncoder) if peak_time else "null"
            incidents_json = json.dumps(incidents_sample[:15], cls=UUIDEncoder)  # Limit sample size for prompt
            
            # Create prompt for time pattern insights
            time_prompt = PromptTemplate(
                input_variables=["patterns", "anomalies", "peak_time", "time_factor", "incidents", "district", "crime_type"],
                template="""
                You are a crime time pattern analyst. Based on the provided crime data grouped by {time_factor}, analyze temporal patterns and provide insights.
                
                Time patterns:
                {patterns}
                
                Peak time period:
                {peak_time}
                
                Anomalies detected:
                {anomalies}
                
                Sample incidents:
                {incidents}
                
                Filters:
                - District: {district}
                - Crime Type: {crime_type}
                
                Analyze these patterns and provide a comprehensive analysis including:
                1. Key patterns in crime distribution across {time_factor}
                2. Possible explanations for peak times
                3. Explanations for anomalies
                4. Actionable recommendations for scheduling police resources
                5. Potential causative factors for observed patterns
                
                Return your analysis as a valid JSON object with this structure:
                ```
                {{
                    "keyPatterns": [
                        {{
                            "pattern": "Pattern description",
                            "significance": "High/Medium/Low",
                            "explanation": "Why this pattern occurs"
                        }},
                        ...more patterns...
                    ],
                    "peakTimeAnalysis": "Detailed explanation of peak time findings",
                    "anomalyExplanations": [
                        {{
                            "timeValue": "Specific time value",
                            "explanation": "Why this anomaly might occur"
                        }},
                        ...more explanations...
                    ],
                    "resourceRecommendations": [
                        {{
                            "timeFrame": "Specific time period",
                            "recommendation": "Resource allocation recommendation",
                            "priority": "High/Medium/Low"
                        }},
                        ...more recommendations...
                    ],
                    "causativeFactors": [
                        "Factor 1",
                        "Factor 2",
                        ...more factors...
                    ]
                }}
                ```
                
                Ensure your analysis is data-driven and provides actionable insights.
                """
            )
            
            # Execute LLM chain
            chain = LLMChain(llm=llm, prompt=time_prompt)
            
            district_param = district if district else "all districts"
            crime_type_param = crime_type if crime_type else "all crime types"
            
            response = chain.run(
                patterns=patterns_json,
                anomalies=anomalies_json,
                peak_time=peak_time_json,
                time_factor=time_factor,
                incidents=incidents_json,
                district=district_param,
                crime_type=crime_type_param
            )
            
            # Parse LLM response
            try:
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = response[json_start:json_end]
                    insights_data = json.loads(json_str)
                else:
                    insights_data = json.loads(response)
                
                return insights_data
            except json.JSONDecodeError:
                logger.error("Failed to parse time pattern insights as JSON")
                return {
                    "keyPatterns": [{"pattern": "Analysis error", "significance": "Low", "explanation": "Could not analyze patterns"}],
                    "peakTimeAnalysis": "Could not analyze peak times",
                    "anomalyExplanations": [],
                    "resourceRecommendations": [{
                        "timeFrame": "General",
                        "recommendation": "Review raw data manually",
                        "priority": "Medium"
                    }],
                    "causativeFactors": ["Analysis failed"]
                }
                
        except Exception as e:
            logger.error(f"Error generating time pattern insights: {str(e)}")
            return {
                "keyPatterns": [{"pattern": "Analysis error", "significance": "Low", "explanation": f"Error: {str(e)}"}],
                "peakTimeAnalysis": "Analysis failed",
                "anomalyExplanations": [],
                "resourceRecommendations": [],
                "causativeFactors": ["Error in analysis"]
            }

    @staticmethod
    def generate_heatmap_data(
        incidents: List[Incident],
        resolution: str,
        district: Optional[str] = None,
        crime_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate heatmap data with clustering for hotspot detection"""
        try:
            # Extract coordinates from incidents
            coordinates = []
            types = []
            weights = []
            
            for incident in incidents:
                try:
                    coords = incident.location.get("coordinates")
                    if coords and len(coords) == 2:
                        coordinates.append(coords)
                        types.append(incident.type)
                        
                        # Apply weight based on severity
                        severity_weights = {
                            "low": 0.3,
                            "moderate": 0.6,
                            "high": 0.8,
                            "critical": 1.0
                        }
                        weight = severity_weights.get(incident.severity.lower(), 0.5)
                        weights.append(weight)
                except Exception as e:
                    logger.warning(f"Skipping incident due to invalid coordinates: {e}")
            
            if not coordinates:
                return {
                    "resolution": resolution,
                    "district": district or "all",
                    "crimeType": crime_type or "all",
                    "points": [],
                    "clusters": [],
                    "totalIncidents": len(incidents)
                }
            
            # Format points for heatmap
            points = []
            for i, coord in enumerate(coordinates):
                points.append({
                    "coordinates": coord,
                    "weight": weights[i],
                    "type": types[i],
                    "count": 1
                })
            
            # Apply clustering for hotspot detection
            eps_values = {"high": 0.001, "medium": 0.005, "low": 0.01}
            eps = eps_values.get(resolution, 0.005)
            
            try:
                # Convert to numpy array for DBSCAN
                coords_array = np.array(coordinates)
                
                # Apply DBSCAN clustering
                clustering = DBSCAN(eps=eps, min_samples=3).fit(coords_array)
                labels = clustering.labels_
                
                # Process clusters
                clusters = []
                cluster_ids = set(labels)
                
                for cluster_id in cluster_ids:
                    if cluster_id == -1:
                        continue  # Skip noise points
                    
                    # Get points in this cluster
                    cluster_points = coords_array[labels == cluster_id]
                    cluster_types = [types[i] for i, label in enumerate(labels) if label == cluster_id]
                    
                    # Calculate cluster center
                    center_lat = sum(point[1] for point in cluster_points) / len(cluster_points)
                    center_lng = sum(point[0] for point in cluster_points) / len(cluster_points)
                    
                    # Count crime types in cluster
                    crime_counts = Counter(cluster_types)
                    
                    # Add cluster to results
                    clusters.append({
                        "id": int(cluster_id),
                        "center": [center_lng, center_lat],
                        "pointCount": len(cluster_points),
                        "crimeTypes": dict(crime_counts),
                        "radius": 0.01  # Arbitrary radius for visualization
                    })
                
                # Generate cluster insights using LLM
                hotspot_insights = AnalyticsService._analyze_hotspots(
                    clusters=clusters,
                    incidents=incidents[:50],  # Limit for token count
                    district=district,
                    crime_type=crime_type
                )
                
                # Return the final result
                return {
                    "resolution": resolution,
                    "district": district or "all",
                    "crimeType": crime_type or "all",
                    "points": points,
                    "clusters": clusters,
                    "insights": hotspot_insights,
                    "totalIncidents": len(incidents)
                }
                
            except Exception as e:
                logger.error(f"Clustering error: {e}")
                # Return just the points without clustering
                return {
                    "resolution": resolution,
                    "district": district or "all",
                    "crimeType": crime_type or "all",
                    "points": points,
                    "clusters": [],
                    "totalIncidents": len(incidents)
                }
            
        except Exception as e:
            logger.error(f"Error generating heatmap data: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise ValueError(f"Heatmap generation failed: {str(e)}")
    
    @staticmethod
    def _analyze_hotspots(
        clusters: List[Dict[str, Any]],
        incidents: List[Incident],
        district: Optional[str] = None,
        crime_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Use LLM to analyze hotspots and provide insights"""
        try:
            # Prepare data for LLM
            incidents_data = []
            for incident in incidents[:20]:  # Limit for token count
                incident_dict = IncidentService._format_incident(incident)
                incidents_data.append(incident_dict)
            
            clusters_json = json.dumps(clusters, cls=UUIDEncoder)
            incidents_json = json.dumps(incidents_data, cls=UUIDEncoder)
            
            # Create prompt for hotspot analysis
            hotspot_prompt = PromptTemplate(
                input_variables=["clusters", "incidents", "district", "crime_type"],
                template="""
                You are a crime hotspot analysis specialist. Based on the crime clusters and incident data provided,
                analyze the hotspots and generate insights.
                
                Clusters (crime hotspots):
                {clusters}
                
                Sample incidents:
                {incidents}
                
                Filters:
                - District: {district}
                - Crime Type: {crime_type}
                
                Analyze these hotspots and provide the following in JSON format:
                1. Hotspot patterns (2-4 patterns observed in these hotspots)
                2. Contributing factors for these hotspots
                3. Recommendations for targeted intervention
                
                Return your analysis as a valid JSON object with this structure:
                ```
                {{
                    "hotspotPatterns": [
                        {{
                            "name": "Pattern name",
                            "description": "Pattern description",
                            "affectedAreas": ["area1", "area2"]
                        }},
                        ...
                    ],
                    "contributingFactors": [
                        {{
                            "factor": "Factor name",
                            "description": "Why this contributes to hotspots"
                        }},
                        ...
                    ],
                    "recommendations": [
                        {{
                            "action": "Recommended action",
                            "targetedAt": "Specific hotspot or general",
                            "priority": "High/Medium/Low"
                        }},
                        ...
                    ]
                }}
                ```
                
                Ensure your analysis is specific, data-driven, and actionable.
                """
            )
            
            # Execute LLM chain
            chain = LLMChain(llm=llm, prompt=hotspot_prompt)
            district_param = district if district else "all districts"
            crime_type_param = crime_type if crime_type else "all crime types"
            
            response = chain.run(
                clusters=clusters_json,
                incidents=incidents_json,
                district=district_param,
                crime_type=crime_type_param
            )
            
            # Parse LLM response
            try:
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = response[json_start:json_end]
                    hotspot_data = json.loads(json_str)
                else:
                    hotspot_data = json.loads(response)
                
                return hotspot_data
            except json.JSONDecodeError:
                logger.error("Failed to parse hotspot analysis as JSON")
                return {
                    "hotspotPatterns": [],
                    "contributingFactors": [],
                    "recommendations": []
                }
                
        except Exception as e:
            logger.error(f"Error analyzing hotspots: {str(e)}")
            return {
                "hotspotPatterns": [],
                "contributingFactors": [],
                "recommendations": []
            }

    @staticmethod
    def generate_trend_analysis(
        incidents: List[Incident],
        start_date: datetime,
        end_date: datetime,
        interval: str,
        district: Optional[str] = None,
        crime_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate trend analysis with AI-enhanced pattern detection"""
        try:
            # Group incidents by interval
            grouped_trends = {}
            
            if interval == "daily":
                # Group by day
                for incident in incidents:
                    day_key = incident.date.strftime('%Y-%m-%d')
                    if day_key not in grouped_trends:
                        grouped_trends[day_key] = {"total": 0, "breakdown": {}}
                    
                    grouped_trends[day_key]["total"] += 1
                    
                    # Track breakdown by type
                    incident_type = incident.type
                    if incident_type not in grouped_trends[day_key]["breakdown"]:
                        grouped_trends[day_key]["breakdown"][incident_type] = 0
                    
                    grouped_trends[day_key]["breakdown"][incident_type] += 1
            
            elif interval == "weekly":
                # Group by week
                for incident in incidents:
                    week_key = f"{incident.date.strftime('%Y')}-W{incident.date.isocalendar()[1]}"
                    if week_key not in grouped_trends:
                        grouped_trends[week_key] = {"total": 0, "breakdown": {}}
                    
                    grouped_trends[week_key]["total"] += 1
                    
                    # Track breakdown by type
                    incident_type = incident.type
                    if incident_type not in grouped_trends[week_key]["breakdown"]:
                        grouped_trends[week_key]["breakdown"][incident_type] = 0
                    
                    grouped_trends[week_key]["breakdown"][incident_type] += 1
            
            else:  # monthly
                # Group by month
                for incident in incidents:
                    month_key = incident.date.strftime('%Y-%m')
                    if month_key not in grouped_trends:
                        grouped_trends[month_key] = {"total": 0, "breakdown": {}}
                    
                    grouped_trends[month_key]["total"] += 1
                    
                    # Track breakdown by type
                    incident_type = incident.type
                    if incident_type not in grouped_trends[month_key]["breakdown"]:
                        grouped_trends[month_key]["breakdown"][incident_type] = 0
                    
                    grouped_trends[month_key]["breakdown"][incident_type] += 1
            
            # Format trends for output
            trends = []
            for key in sorted(grouped_trends.keys()):
                trend_item = {
                    "period": key,
                    "total": grouped_trends[key]["total"],
                    "breakdown": grouped_trends[key]["breakdown"]
                }
                trends.append(trend_item)
            
            # Prepare data for LLM analysis
            incidents_data = []
            for incident in incidents[:50]:  # Limit for token count
                incident_dict = IncidentService._format_incident(incident)
                incidents_data.append(incident_dict)
            
            # Get LLM analysis on emerging patterns
            emerging_patterns = AnalyticsService._analyze_emerging_patterns(
                trends=trends,
                incidents=incidents_data,
                start_date=start_date,
                end_date=end_date,
                interval=interval,
                district=district,
                crime_type=crime_type
            )
            
            # Return final result
            return {
                "timeframe": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "interval": interval,
                "trends": trends,
                "emergingPatterns": emerging_patterns
            }
            
        except Exception as e:
            logger.error(f"Error in trend analysis: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise ValueError(f"Trend analysis failed: {str(e)}")
    
    @staticmethod
    def _analyze_emerging_patterns(
        trends: List[Dict[str, Any]],
        incidents: List[Dict[str, Any]],
        start_date: datetime,
        end_date: datetime,
        interval: str,
        district: Optional[str] = None,
        crime_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Use LLM to identify emerging patterns in crime data"""
        try:
            # Prepare data for the LLM
            trends_json = json.dumps(trends, cls=UUIDEncoder)
            incidents_json = json.dumps(incidents[:20], cls=UUIDEncoder)  # Limit for token count
            
            # Create LLM prompt
            pattern_prompt = PromptTemplate(
                input_variables=["trends", "incidents", "start_date", "end_date", "interval", "district", "crime_type"],
                template="""
                You are an expert crime analyst specializing in trend identification. Based on the crime data provided,
                identify emerging patterns and trends.
                
                Crime trends data (grouped by {interval}):
                {trends}
                
                Sample incidents:
                {incidents}
                
                Analysis period: {start_date} to {end_date}
                Filters:
                - District: {district}
                - Crime Type: {crime_type}
                
                Identify 3-5 notable patterns in this data, including emerging trends, periodic patterns, or concerning developments.
                For each pattern, provide:
                1. A short descriptive name
                2. A detailed explanation of the pattern
                3. Supporting evidence from the data
                4. The confidence level (as a percentage)
                5. Potential causes
                
                Return your analysis as a valid JSON array with this structure:
                ```
                [
                    {{
                        "name": "Pattern name",
                        "description": "Detailed explanation of the pattern",
                        "evidence": "Supporting evidence from the data",
                        "confidence": 0-100,
                        "causes": ["Cause 1", "Cause 2"]
                    }},
                    ...more patterns...
                ]
                ```
                
                Ensure your analysis is data-driven and provides actionable insights.
                """
            )
            
            # Execute LLM chain
            chain = LLMChain(llm=llm, prompt=pattern_prompt)
            
            district_param = district if district else "all districts"
            crime_type_param = crime_type if crime_type else "all crime types"
            
            response = chain.run(
                trends=trends_json,
                incidents=incidents_json,
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
                interval=interval,
                district=district_param,
                crime_type=crime_type_param
            )
            
            # Parse LLM response
            try:
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = response[json_start:json_end]
                    patterns_data = json.loads(json_str)
                else:
                    patterns_data = json.loads(response)
                
                return patterns_data
            except json.JSONDecodeError:
                logger.error("Failed to parse emerging patterns as JSON")
                return []
                
        except Exception as e:
            logger.error(f"Error generating emerging patterns: {str(e)}")
            return []
