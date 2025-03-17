import csv
import os
import sys
from datetime import datetime
from pathlib import Path

# Add the project root to the sys path to import app modules
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from sqlmodel import Session, SQLModel, create_engine
from uuid import UUID, uuid4
from apps.incidents.models import Incident
from core.utils.common import ensure_uuid
from dotenv import load_dotenv
load_dotenv()

# Database setup
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./crime_analysis.db")
engine = create_engine(DATABASE_URL)
SQLModel.metadata.create_all(engine)

def read_csv_data(file_path):
    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        return list(reader)

def transform_row_to_incident(row):
    # Generate a unique ID
    incident_id = uuid4()  # Use as UUID object, not string
    
    # Parse date and time
    date_str = row['Date']
    time_of_day = row['Time_of_Day']
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    
    # Create location object
    location = {
        "address": f"{row['Neighborhood']} area",
        "city": "Islamabad",
        "district": row['Neighborhood'],
        "coordinates": [float(row['Latitude']), float(row['Longitude'])],
        "neighborhood": row['Neighborhood'],
        "lighting": row['Lighting']
    }
    
    # Create environmental factors
    environmental_factors = {
        "weather": row['Weather'],
        "time_of_day": time_of_day,
        "day_of_week": row['Day_of_Week'],
        "is_weekend": row['Day_of_Week'] in ['Saturday', 'Sunday']
    }
    
    # Create socioeconomic factors if available in data
    socioeconomic_factors = {}
    if 'Average_Income' in row:
        socioeconomic_factors["income_level"] = float(row['Average_Income'])
    if 'Population_Density' in row:
        socioeconomic_factors["population_density"] = float(row['Population_Density'])
    
    # Map crime types to severity
    severity_map = {
        'Theft': 'moderate',
        'Burglary': 'high',
        'Assault': 'high',
        'Vandalism': 'low',
        'Robbery': 'high',
        'Homicide': 'critical'
    }
    
    crime_type = row['Crime_Type']
    severity = severity_map.get(crime_type, 'moderate')
    
    # Create incident object
    incident = {
        "id": incident_id,  # Use UUID object, not string
        "title": f"{crime_type} in {row['Neighborhood']}",
        "description": f"{crime_type} incident reported in {row['Neighborhood']} area during {time_of_day.lower()}",
        "type": crime_type,
        "date": date_obj,
        "location": location,
        "severity": severity,
        "status": "reported",
        "environmental_factors": environmental_factors,
        "socioeconomic_factors": socioeconomic_factors,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    
    return incident

def import_csv_to_db(file_path):
    """Import CSV data into the database"""
    # Read CSV data
    rows = read_csv_data(file_path)
    
    # Transform data into incidents
    incidents = []
    for row in rows:
        try:
            incident_data = transform_row_to_incident(row)
            # Create Incident object
            incident = Incident(
                id=incident_data["id"],  # Already a UUID object
                title=incident_data["title"],
                description=incident_data["description"],
                type=incident_data["type"],
                date=incident_data["date"],
                location=incident_data["location"],
                severity=incident_data["severity"],
                status=incident_data["status"],
                environmental_factors=incident_data["environmental_factors"],
                socioeconomic_factors=incident_data["socioeconomic_factors"],
                created_at=incident_data["created_at"],
                updated_at=incident_data["updated_at"]
            )
            incidents.append(incident)
        except Exception as e:
            print(f"Error processing row: {e}")
            continue
    
    # Save to database
    with Session(engine) as session:
        for incident in incidents:
            session.add(incident)
        
        # Commit to DB
        try:
            session.commit()
            print(f"Successfully imported {len(incidents)} incidents")
        except Exception as e:
            session.rollback()
            print(f"Error committing to database: {e}")
            
    print(f"Import complete: {len(incidents)} records processed")
    
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python import_csv.py <csv_file_path>")
        sys.exit(1)
    
    csv_file_path = sys.argv[1]
    if not os.path.exists(csv_file_path):
        print(f"Error: File {csv_file_path} not found")
        sys.exit(1)
    
    import_csv_to_db(csv_file_path)
