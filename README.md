# Crime Analysis API

A data-driven API for crime analysis and prediction powered by Google's Gemini model.

## Features

- **Crime Analysis**: Query crime data and get AI-powered analysis using Gemini model
- **Crime Hotspots**: Identify crime hotspots using DBSCAN clustering
- **Temporal Pattern Analysis**: Analyze crime patterns by month, day of week, or time of day

## Setup

### Prerequisites

- Python 3.8+
- Google Gemini API key

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/crime-gpt.git
   cd crime-gpt
   ```

2. Create a virtual environment and install dependencies:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Create a `.env` file with your Google Gemini API key:
   ```
   GEMINI_API_KEY=your_api_key_here
   DATA_PATH=data.csv  # Path to your crime data CSV file
   ```

### Running the API

```
uvicorn app:app --reload
```

The API will be available at [http://localhost:8000](http://localhost:8000)

## API Endpoints

### Crime Analysis

```
POST /analyze
```

Analyze crime based on a user query.

**Request Body:**
```json
{
  "query": "What's the likelihood of theft in Blue Area at night?",
  "context_type": "full_context",
  "n_results": 5
}
```

**Response:**
```json
{
  "query": "What's the likelihood of theft in Blue Area at night?",
  "crime_probability": "75%",
  "most_likely_crime": "Theft(60%), Assault(25%), Burglary(10%), Kidnapping(5%)",
  "key_factors": "Night time, Poor lighting, High population density",
  "risk_level": "High",
  "relevant_records": [
    {
      "crime_type": "Theft",
      "neighborhood": "Blue Area",
      "latitude": 33.7077,
      "longitude": 73.0498,
      "date": "2023-01-15",
      "time_of_day": "Night",
      "weather": "Cloudy",
      "temperature": 10.5,
      "lighting": "Poorly-lit",
      "population_density": 12000.0,
      "average_income": 150000.0,
      "unemployment_rate": 8.5
    }
    // More records...
  ],
  "raw_response": "..."
}
```

### Crime Hotspots

```
GET /hotspots?eps=0.005&min_samples=3
```

Identify crime hotspots using DBSCAN clustering.

**Response:**
```json
{
  "hotspots": [
    {
      "cluster_id": 0,
      "center_lat": 33.7081,
      "center_lng": 73.0501,
      "total_crimes": 45,
      "crime_counts": {
        "Theft": 25,
        "Assault": 15,
        "Burglary": 5
      },
      "most_common_crime": "Theft",
      "avg_temperature": 22.5,
      "lighting": {
        "Poorly-lit": 30,
        "Well-lit": 15
      },
      "neighborhoods": ["Blue Area", "G-6"]
    }
    // More hotspots...
  ],
  "total_clusters": 12,
  "crime_counts_by_cluster": {
    "0": 45,
    "1": 37,
    "2": 29
    // More clusters...
  }
}
```

### Temporal Patterns

```
GET /temporal-patterns?dimension=month
```

Find temporal patterns in crime data.

**Response:**
```json
{
  "patterns": {
    "January": {
      "Theft": 45,
      "Assault": 38,
      "Kidnapping": 12,
      "Burglary": 25
    },
    "February": {
      "Theft": 39,
      "Assault": 42,
      "Kidnapping": 8,
      "Burglary": 18
    }
    // More months...
  },
  "summary": "Analyzed crime patterns by month"
}
```

## Additional Documentation

Swagger UI documentation is available at [http://localhost:8000/docs](http://localhost:8000/docs) when the API is running.
