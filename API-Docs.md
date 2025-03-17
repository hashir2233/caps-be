### Crime Analysis Platform API Documentation

This document provides comprehensive details about the Crime Analysis Platform API endpoints, including request/response formats and error handling.

## Table of Contents

1. [Authentication](#authentication)
2. [Incidents](#incidents)
3. [Users](#users)
4. [Reports](#reports)
5. [Alerts](#alerts)
6. [Analytics](#analytics)
7. [Resource Planning](#resource-planning)
8. [Settings](#settings)


## Authentication

### Login

Authenticates a user and returns a JWT token.

- **URL**: `/api/auth/login`
- **Method**: `POST`
- **Description**: Authenticates a user with email and password credentials.


**Request Body**:

```json
{
  "email": "john.doe@example.com",
  "password": "securePassword123"
}
```

**Success Response (200 OK)**:

```json
{
  "success": true,
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": "usr_123456789",
      "email": "john.doe@example.com",
      "name": "John Doe",
      "role": "analyst"
    }
  }
}
```

**Error Response (401 Unauthorized)**:

```json
{
  "success": false,
  "error": {
    "code": "auth_failed",
    "message": "Invalid email or password"
  }
}
```

### Register

Creates a new user account.

- **URL**: `/api/auth/register`
- **Method**: `POST`
- **Description**: Registers a new user with the provided information.


**Request Body**:

```json
{
  "email": "new.user@example.com",
  "password": "securePassword123",
  "name": "New User",
  "role": "officer"
}
```

**Success Response (201 Created)**:

```json
{
  "success": true,
  "data": {
    "user": {
      "id": "usr_987654321",
      "email": "new.user@example.com",
      "name": "New User",
      "role": "officer",
      "createdAt": "2025-03-14T21:30:45Z"
    }
  }
}
```

**Error Response (400 Bad Request)**:

```json
{
  "success": false,
  "error": {
    "code": "validation_error",
    "message": "Email already in use",
    "fields": {
      "email": "This email is already registered"
    }
  }
}
```

### Refresh Token

Refreshes an expired JWT token.

- **URL**: `/api/auth/refresh`
- **Method**: `POST`
- **Description**: Generates a new access token using a valid refresh token.


**Request Body**:

```json
{
  "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Success Response (200 OK)**:

```json
{
  "success": true,
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

**Error Response (401 Unauthorized)**:

```json
{
  "success": false,
  "error": {
    "code": "invalid_token",
    "message": "Refresh token is invalid or expired"
  }
}
```

### Reset Password Request

Initiates a password reset process.

- **URL**: `/api/auth/reset-password`
- **Method**: `POST`
- **Description**: Sends a password reset link to the user's email.


**Request Body**:

```json
{
  "email": "john.doe@example.com"
}
```

**Success Response (200 OK)**:

```json
{
  "success": true,
  "message": "Password reset instructions sent to your email"
}
```

**Error Response (404 Not Found)**:

```json
{
  "success": false,
  "error": {
    "code": "user_not_found",
    "message": "No user found with this email address"
  }
}
```

## Incidents

### List Incidents

Retrieves a paginated list of crime incidents.

- **URL**: `/api/incidents`
- **Method**: `GET`
- **Description**: Returns a list of crime incidents with optional filtering.
- **Query Parameters**:

- `page`: Page number (default: 1)
- `limit`: Items per page (default: 20)
- `type`: Filter by crime type
- `district`: Filter by district
- `startDate`: Filter by date range start
- `endDate`: Filter by date range end
- `severity`: Filter by severity level





**Success Response (200 OK)**:

```json
{
  "success": true,
  "data": {
    "incidents": [
      {
        "id": "inc_123456",
        "title": "Theft at Main Street",
        "type": "theft",
        "date": "2025-03-10T14:30:00Z",
        "location": {
          "address": "123 Main St",
          "district": "downtown",
          "coordinates": [-74.006, 40.7128],
          "neighborhood": "Central Business District"
        },
        "severity": "medium",
        "status": "open",
        "environmental_factors": {
          "time_of_day": "Afternoon",
          "weather": "Clear"
        },
        "risk_score": 32.5
      },
      {
        "id": "inc_123457",
        "title": "Vandalism at City Park",
        "type": "vandalism",
        "date": "2025-03-09T18:45:00Z",
        "location": {
          "address": "City Park, West Entrance",
          "district": "westside",
          "coordinates": [-74.012, 40.7135],
          "neighborhood": "Parkside"
        },
        "severity": "low",
        "status": "investigating",
        "environmental_factors": {
          "time_of_day": "Evening",
          "weather": "Cloudy"
        },
        "risk_score": 21.8
      }
    ],
    "pagination": {
      "total": 1284,
      "page": 1,
      "limit": 20,
      "pages": 65
    }
  }
}
```

**Error Response (400 Bad Request)**:

```json
{
  "success": false,
  "error": {
    "code": "invalid_parameters",
    "message": "Invalid date range specified",
    "details": "End date must be after start date"
  }
}
```

### Get Incident

Retrieves detailed information about a specific incident.

- **URL**: `/api/incidents/:id`
- **Method**: `GET`
- **Description**: Returns comprehensive details about a specific crime incident.
- **URL Parameters**:

- `id`: Incident ID





**Success Response (200 OK)**:

```json
{
  "success": true,
  "data": {
    "incident": {
      "id": "inc_123456",
      "title": "Theft at Main Street",
      "description": "Shoplifting incident at retail store. Suspect took merchandise valued at approximately $250.",
      "type": "theft",
      "date": "2025-03-10T14:30:00Z",
      "location": {
        "address": "123 Main St",
        "city": "New York",
        "zipCode": "10001",
        "district": "downtown",
        "locationType": "commercial",
        "coordinates": [-74.006, 40.7128],
        "neighborhood": "Central Business District",
        "lighting": "Well-lit",
        "population_density": 12000.0,
        "average_income": 75000.0,
        "unemployment_rate": 5.2
      },
      "severity": "medium",
      "status": "open",
      "reportingOfficer": {
        "id": "off_789012",
        "name": "Officer Johnson"
      },
      "evidence": [
        {
          "id": "ev_123",
          "type": "image",
          "url": "https://evidence.crimeanalysis.com/inc_123456/image1.jpg",
          "description": "Security camera footage",
          "uploadedAt": "2025-03-10T15:45:00Z"
        }
      ],
      "notes": "Suspect was wearing a blue jacket and baseball cap. Store has provided security footage.",
      "flags": {
        "repeatOffender": true,
        "relatedCases": false,
        "requiresFollowup": true,
        "involvesMinor": false,
        "gangRelated": false,
        "domesticViolence": false
      },
      "environmental_factors": {
        "weather": "Clear",
        "temperature": 18.5,
        "visibility": "Good",
        "time_of_day": "Afternoon",
        "day_of_week": "Tuesday",
        "is_holiday": false,
        "is_weekend": false,
        "precipitation": 0.0
      },
      "socioeconomic_factors": {
        "poverty_rate": 12.5,
        "education_level": "High",
        "housing_density": 8500,
        "public_transport_access": "Good",
        "police_presence": "Medium",
        "nearby_facilities": ["Shopping Mall", "Bus Station", "Office Building"],
        "crime_history": 42.3
      },
      "weapon_used": null,
      "victim_count": 1,
      "suspect_count": 1,
      "estimated_loss_value": 250.0,
      "response_time_minutes": 8,
      "related_incidents": ["inc_122345", "inc_122346"],
      "risk_score": 32.5,
      "createdAt": "2025-03-10T15:30:00Z",
      "updatedAt": "2025-03-11T09:15:00Z"
    }
  }
}
```

**Error Response (404 Not Found)**:

```json
{
  "success": false,
  "error": {
    "code": "not_found",
    "message": "Incident with ID inc_123456 not found"
  }
}
```

### Create Incident

Creates a new crime incident.

- **URL**: `/api/incidents`
- **Method**: `POST`
- **Description**: Records a new crime incident with the provided details.


**Request Body**:

```json
{
  "title": "Burglary on Oak Street",
  "description": "Residential burglary with forced entry through rear window.",
  "type": "burglary",
  "date": "2025-03-14T02:30:00Z",
  "location": {
    "address": "456 Oak St",
    "city": "New York",
    "zipCode": "10002",
    "district": "eastside",
    "locationType": "residential",
    "coordinates": [-73.986, 40.7282],
    "neighborhood": "Oak Heights",
    "lighting": "Poorly-lit",
    "population_density": 8500.0,
    "average_income": 65000.0,
    "unemployment_rate": 7.3
  },
  "severity": "high",
  "status": "open",
  "reportingOfficer": "off_789012",
  "notes": "Homeowner was away on vacation. Neighbors reported suspicious activity around midnight.",
  "flags": {
    "repeatOffender": false,
    "relatedCases": true,
    "requiresFollowup": true,
    "involvesMinor": false,
    "gangRelated": false,
    "domesticViolence": false
  },
  "environmental_factors": {
    "weather": "Cloudy",
    "temperature": 12.5,
    "visibility": "Poor",
    "time_of_day": "Night",
    "day_of_week": "Friday",
    "is_holiday": false,
    "is_weekend": false,
    "precipitation": 0.0
  },
  "socioeconomic_factors": {
    "poverty_rate": 15.8,
    "education_level": "Medium",
    "housing_density": 5200,
    "public_transport_access": "Limited",
    "police_presence": "Low",
    "nearby_facilities": ["Park", "Elementary School"],
    "crime_history": 38.7
  },
  "weapon_used": null,
  "victim_count": 1,
  "suspect_count": 2,
  "estimated_loss_value": 3500.0
}
```

**Success Response (201 Created)**:

```json
{
  "success": true,
  "data": {
    "incident": {
      "id": "inc_789012",
      "title": "Burglary on Oak Street",
      "type": "burglary",
      "date": "2025-03-14T02:30:00Z",
      "location": {
        "address": "456 Oak St",
        "district": "eastside",
        "coordinates": [-73.986, 40.7282]
      },
      "severity": "high",
      "status": "open",
      "createdAt": "2025-03-14T10:15:00Z"
    }
  }
}
```

**Error Response (400 Bad Request)**:

```json
{
  "success": false,
  "error": {
    "code": "validation_error",
    "message": "Invalid incident data",
    "fields": {
      "type": "Crime type is required",
      "date": "Date must be a valid ISO date string"
    }
  }
}
```

### Update Incident

Updates an existing crime incident.

- **URL**: `/api/incidents/:id`
- **Method**: `PUT`
- **Description**: Updates the details of an existing crime incident.
- **URL Parameters**:

- `id`: Incident ID





**Request Body**:

```json
{
  "status": "investigating",
  "severity": "critical",
  "notes": "Updated: Homeowner was away on vacation. Neighbors reported suspicious activity around midnight. Similar break-in pattern to recent cases in the area.",
  "flags": {
    "repeatOffender": true,
    "relatedCases": true,
    "requiresFollowup": true,
    "involvesMinor": false,
    "gangRelated": true,
    "domesticViolence": false
  },
  "environmental_factors": {
    "weather": "Rainy",
    "temperature": 11.0,
    "visibility": "Poor" 
  },
  "socioeconomic_factors": {
    "police_presence": "Medium",
    "crime_history": 45.2
  },
  "risk_score": 78.5
}
```

**Success Response (200 OK)**:

```json
{
  "success": true,
  "data": {
    "incident": {
      "id": "inc_789012",
      "title": "Burglary on Oak Street",
      "type": "burglary",
      "date": "2025-03-14T02:30:00Z",
      "location": {
        "address": "456 Oak St",
        "district": "eastside",
        "coordinates": [-73.986, 40.7282]
      },
      "severity": "critical",
      "status": "investigating",
      "updatedAt": "2025-03-15T08:45:00Z"
    }
  }
}
```

**Error Response (404 Not Found)**:

```json
{
  "success": false,
  "error": {
    "code": "not_found",
    "message": "Incident with ID inc_789012 not found"
  }
}
```

### Delete Incident

Deletes a crime incident.

- **URL**: `/api/incidents/:id`
- **Method**: `DELETE`
- **Description**: Removes a crime incident from the system.
- **URL Parameters**:

- `id`: Incident ID





**Success Response (200 OK)**:

```json
{
  "success": true,
  "message": "Incident successfully deleted"
}
```

**Error Response (403 Forbidden)**:

```json
{
  "success": false,
  "error": {
    "code": "permission_denied",
    "message": "You do not have permission to delete this incident"
  }
}
```

### Add Evidence

Adds evidence to an incident.

- **URL**: `/api/incidents/:id/evidence`
- **Method**: `POST`
- **Description**: Uploads and attaches evidence to a crime incident.
- **URL Parameters**:

- `id`: Incident ID





**Request Body**:

```json
{
  "type": "image",
  "description": "Security camera footage from neighboring building",
  "file": "[Base64 encoded file or file upload]"
}
```

**Success Response (201 Created)**:

```json
{
  "success": true,
  "data": {
    "evidence": {
      "id": "ev_456",
      "type": "image",
      "url": "https://evidence.crimeanalysis.com/inc_789012/image2.jpg",
      "description": "Security camera footage from neighboring building",
      "uploadedAt": "2025-03-15T14:30:00Z"
    }
  }
}
```

**Error Response (413 Payload Too Large)**:

```json
{
  "success": false,
  "error": {
    "code": "file_too_large",
    "message": "The uploaded file exceeds the maximum allowed size of 10MB"
  }
}
```

## Users

### List Users

Retrieves a list of users.

- **URL**: `/api/users`
- **Method**: `GET`
- **Description**: Returns a paginated list of users with optional filtering.
- **Query Parameters**:

- `page`: Page number (default: 1)
- `limit`: Items per page (default: 20)
- `role`: Filter by user role
- `district`: Filter by assigned district





**Success Response (200 OK)**:

```json
{
  "success": true,
  "data": {
    "users": [
      {
        "id": "usr_123456",
        "name": "John Doe",
        "email": "john.doe@example.com",
        "role": "analyst",
        "district": "downtown",
        "lastActive": "2025-03-14T20:15:00Z"
      },
      {
        "id": "usr_123457",
        "name": "Jane Smith",
        "email": "jane.smith@example.com",
        "role": "officer",
        "district": "westside",
        "lastActive": "2025-03-14T18:30:00Z"
      }
    ],
    "pagination": {
      "total": 42,
      "page": 1,
      "limit": 20,
      "pages": 3
    }
  }
}
```

**Error Response (403 Forbidden)**:

```json
{
  "success": false,
  "error": {
    "code": "permission_denied",
    "message": "You do not have permission to view user list"
  }
}
```

### Get User

Retrieves details about a specific user.

- **URL**: `/api/users/:id`
- **Method**: `GET`
- **Description**: Returns comprehensive details about a specific user.
- **URL Parameters**:

- `id`: User ID





**Success Response (200 OK)**:

```json
{
  "success": true,
  "data": {
    "user": {
      "id": "usr_123456",
      "name": "John Doe",
      "email": "john.doe@example.com",
      "role": "analyst",
      "district": "downtown",
      "phone": "+1-555-123-4567",
      "badgeNumber": "A12345",
      "department": "Crime Analysis Unit",
      "joinDate": "2023-06-15T00:00:00Z",
      "permissions": ["view_incidents", "edit_incidents", "view_reports", "create_reports"],
      "lastActive": "2025-03-14T20:15:00Z",
      "profileComplete": 75
    }
  }
}
```

**Error Response (404 Not Found)**:

```json
{
  "success": false,
  "error": {
    "code": "not_found",
    "message": "User with ID usr_123456 not found"
  }
}
```

### Create User

Creates a new user.

- **URL**: `/api/users`
- **Method**: `POST`
- **Description**: Creates a new user with the provided information.


**Request Body**:

```json
{
  "name": "Robert Johnson",
  "email": "robert.johnson@example.com",
  "password": "securePassword123",
  "role": "officer",
  "district": "northside",
  "phone": "+1-555-987-6543",
  "badgeNumber": "B54321",
  "department": "Patrol Division"
}
```

**Success Response (201 Created)**:

```json
{
  "success": true,
  "data": {
    "user": {
      "id": "usr_789012",
      "name": "Robert Johnson",
      "email": "robert.johnson@example.com",
      "role": "officer",
      "district": "northside",
      "createdAt": "2025-03-14T21:30:00Z"
    }
  }
}
```

**Error Response (400 Bad Request)**:

```json
{
  "success": false,
  "error": {
    "code": "validation_error",
    "message": "Invalid user data",
    "fields": {
      "email": "Email already in use",
      "badgeNumber": "Badge number must be unique"
    }
  }
}
```

### Update User

Updates an existing user.

- **URL**: `/api/users/:id`
- **Method**: `PUT`
- **Description**: Updates the details of an existing user.
- **URL Parameters**:

- `id`: User ID





**Request Body**:

```json
{
  "name": "Robert M. Johnson",
  "phone": "+1-555-987-6543",
  "district": "eastside",
  "department": "Special Investigations Unit"
}
```

**Success Response (200 OK)**:

```json
{
  "success": true,
  "data": {
    "user": {
      "id": "usr_789012",
      "name": "Robert M. Johnson",
      "email": "robert.johnson@example.com",
      "role": "officer",
      "district": "eastside",
      "department": "Special Investigations Unit",
      "updatedAt": "2025-03-15T09:45:00Z"
    }
  }
}
```

**Error Response (403 Forbidden)**:

```json
{
  "success": false,
  "error": {
    "code": "permission_denied",
    "message": "You do not have permission to update this user"
  }
}
```

### Delete User

Deletes a user.

- **URL**: `/api/users/:id`
- **Method**: `DELETE`
- **Description**: Removes a user from the system.
- **URL Parameters**:

- `id`: User ID





**Success Response (200 OK)**:

```json
{
  "success": true,
  "message": "User successfully deleted"
}
```

**Error Response (403 Forbidden)**:

```json
{
  "success": false,
  "error": {
    "code": "permission_denied",
    "message": "You do not have permission to delete users"
  }
}
```

## Reports

### List Reports

Retrieves a list of reports.

- **URL**: `/api/reports`
- **Method**: `GET`
- **Description**: Returns a paginated list of reports with optional filtering.
- **Query Parameters**:

- `page`: Page number (default: 1)
- `limit`: Items per page (default: 20)
- `type`: Filter by report type
- `district`: Filter by district
- `startDate`: Filter by date range start
- `endDate`: Filter by date range end





**Success Response (200 OK)**:

```json
{
  "success": true,
  "data": {
    "reports": [
      {
        "id": "rep_123456",
        "title": "Downtown Crime Analysis",
        "type": "crime_analysis",
        "district": "downtown",
        "createdBy": {
          "id": "usr_123456",
          "name": "John Doe"
        },
        "createdAt": "2025-03-10T15:30:00Z",
        "updatedAt": "2025-03-10T15:30:00Z"
      },
      {
        "id": "rep_123457",
        "title": "Westside Monthly Report",
        "type": "monthly",
        "district": "westside",
        "createdBy": {
          "id": "usr_123457",
          "name": "Jane Smith"
        },
        "createdAt": "2025-03-05T10:15:00Z",
        "updatedAt": "2025-03-05T10:15:00Z"
      }
    ],
    "pagination": {
      "total": 156,
      "page": 1,
      "limit": 20,
      "pages": 8
    }
  }
}
```

**Error Response (400 Bad Request)**:

```json
{
  "success": false,
  "error": {
    "code": "invalid_parameters",
    "message": "Invalid date range specified",
    "details": "End date must be after start date"
  }
}
```

### Get Report

Retrieves details about a specific report.

- **URL**: `/api/reports/:id`
- **Method**: `GET`
- **Description**: Returns comprehensive details about a specific report.
- **URL Parameters**:

- `id`: Report ID





**Success Response (200 OK)**:

```json
{
  "success": true,
  "data": {
    "report": {
      "id": "rep_123456",
      "title": "Downtown Crime Analysis",
      "description": "Comprehensive analysis of crime patterns in downtown area",
      "type": "crime_analysis",
      "district": "downtown",
      "dateRange": {
        "start": "2025-02-01T00:00:00Z",
        "end": "2025-02-28T23:59:59Z"
      },
      "content": {
        "summary": "Crime rates in the downtown area have decreased by 7% compared to the previous month. Theft remains the most common crime type, accounting for 35% of all incidents.",
        "keyFindings": [
          "Overall 7% decrease in crime rates",
          "Theft accounts for 35% of all incidents",
          "Assault incidents decreased by 12%",
          "Weekend incidents are 23% higher than weekday incidents"
        ],
        "charts": [
          {
            "type": "bar",
            "title": "Crime by Type",
            "dataUrl": "https://api.crimeanalysis.com/reports/rep_123456/charts/crime-by-type"
          },
          {
            "type": "line",
            "title": "Crime Trends (Feb 2025)",
            "dataUrl": "https://api.crimeanalysis.com/reports/rep_123456/charts/crime-trends"
          }
        ],
        "recommendations": [
          "Increase patrol presence during weekend evenings",
          "Focus on theft prevention in commercial areas",
          "Continue community outreach programs in high-risk zones"
        ]
      },
      "createdBy": {
        "id": "usr_123456",
        "name": "John Doe"
      },
      "createdAt": "2025-03-10T15:30:00Z",
      "updatedAt": "2025-03-10T15:30:00Z"
    }
  }
}
```

**Error Response (404 Not Found)**:

```json
{
  "success": false,
  "error": {
    "code": "not_found",
    "message": "Report with ID rep_123456 not found"
  }
}
```

### Create Report

Creates a new report.

- **URL**: `/api/reports`
- **Method**: `POST`
- **Description**: Generates a new report with the provided parameters.


**Request Body**:

```json
{
  "title": "Robbery Trend Analysis",
  "description": "Analysis of robbery trends across all districts",
  "type": "trend_analysis",
  "district": "all",
  "dateRange": {
    "start": "2025-01-01T00:00:00Z",
    "end": "2025-03-01T23:59:59Z"
  },
  "parameters": {
    "crimeTypes": ["robbery"],
    "includeCharts": true,
    "includeRecommendations": true,
    "compareWithPrevious": true
  }
}
```

**Success Response (201 Created)**:

```json
{
  "success": true,
  "data": {
    "report": {
      "id": "rep_789012",
      "title": "Robbery Trend Analysis",
      "type": "trend_analysis",
      "district": "all",
      "status": "generating",
      "estimatedCompletion": "2025-03-14T22:00:00Z",
      "createdAt": "2025-03-14T21:45:00Z"
    }
  }
}
```

**Error Response (400 Bad Request)**:

```json
{
  "success": false,
  "error": {
    "code": "validation_error",
    "message": "Invalid report parameters",
    "fields": {
      "dateRange": "Date range must not exceed 3 months for trend analysis"
    }
  }
}
```

### Update Report

Updates an existing report.

- **URL**: `/api/reports/:id`
- **Method**: `PUT`
- **Description**: Updates the details of an existing report.
- **URL Parameters**:

- `id`: Report ID





**Request Body**:

```json
{
  "title": "Robbery Trend Analysis - Q1 2025",
  "description": "Comprehensive analysis of robbery trends across all districts in Q1 2025",
  "parameters": {
    "includeRecommendations": true,
    "includeHeatmaps": true
  }
}
```

**Success Response (200 OK)**:

```json
{
  "success": true,
  "data": {
    "report": {
      "id": "rep_789012",
      "title": "Robbery Trend Analysis - Q1 2025",
      "description": "Comprehensive analysis of robbery trends across all districts in Q1 2025",
      "type": "trend_analysis",
      "district": "all",
      "status": "regenerating",
      "estimatedCompletion": "2025-03-14T22:15:00Z",
      "updatedAt": "2025-03-14T21:55:00Z"
    }
  }
}
```

**Error Response (404 Not Found)**:

```json
{
  "success": false,
  "error": {
    "code": "not_found",
    "message": "Report with ID rep_789012 not found"
  }
}
```

### Delete Report

Deletes a report.

- **URL**: `/api/reports/:id`
- **Method**: `DELETE`
- **Description**: Removes a report from the system.
- **URL Parameters**:

- `id`: Report ID





**Success Response (200 OK)**:

```json
{
  "success": true,
  "message": "Report successfully deleted"
}
```

**Error Response (403 Forbidden)**:

```json
{
  "success": false,
  "error": {
    "code": "permission_denied",
    "message": "You do not have permission to delete this report"
  }
}
```

### Export Report

Exports a report in the specified format.

- **URL**: `/api/reports/:id/export`
- **Method**: `GET`
- **Description**: Generates and returns a report in the requested format.
- **URL Parameters**:

- `id`: Report ID



- **Query Parameters**:

- `format`: Export format (pdf, csv, json)





**Success Response (200 OK)**:

```plaintext
Binary file content with appropriate Content-Type header
```

**Error Response (400 Bad Request)**:

```json
{
  "success": false,
  "error": {
    "code": "invalid_format",
    "message": "Unsupported export format. Supported formats: pdf, csv, json"
  }
}
```

## Alerts

### List Alerts

Retrieves a list of alerts.

- **URL**: `/api/alerts`
- **Method**: `GET`
- **Description**: Returns a paginated list of alerts with optional filtering.
- **Query Parameters**:

- `page`: Page number (default: 1)
- `limit`: Items per page (default: 20)
- `severity`: Filter by severity level
- `status`: Filter by status (reviewed, unreviewed)
- `district`: Filter by district





**Success Response (200 OK)**:

```json
{
  "success": true,
  "data": {
    "alerts": [
      {
        "id": "alt_123456",
        "title": "High Risk Area Detected",
        "severity": "high",
        "location": "Downtown, Main St & 5th Ave",
        "timestamp": "2025-03-14T14:30:00Z",
        "reviewed": false
      },
      {
        "id": "alt_123457",
        "title": "Unusual Activity Pattern",
        "severity": "medium",
        "location": "Westside, Park Boulevard",
        "timestamp": "2025-03-14T12:15:00Z",
        "reviewed": false
      }
    ],
    "pagination": {
      "total": 24,
      "page": 1,
      "limit": 20,
      "pages": 2
    }
  }
}
```

**Error Response (401 Unauthorized)**:

```json
{
  "success": false,
  "error": {
    "code": "unauthorized",
    "message": "Authentication required to access alerts"
  }
}
```

### Get Alert

Retrieves details about a specific alert.

- **URL**: `/api/alerts/:id`
- **Method**: `GET`
- **Description**: Returns comprehensive details about a specific alert.
- **URL Parameters**:

- `id`: Alert ID





**Success Response (200 OK)**:

```json
{
  "success": true,
  "data": {
    "alert": {
      "id": "alt_123456",
      "title": "High Risk Area Detected",
      "description": "Significant increase in theft incidents detected in this area over the past 24 hours.",
      "severity": "high",
      "location": {
        "address": "Downtown, Main St & 5th Ave",
        "district": "downtown",
        "coordinates": [-74.006, 40.7128]
      },
      "timestamp": "2025-03-14T14:30:00Z",
      "source": "predictive_algorithm",
      "relatedIncidents": [
        {
          "id": "inc_345678",
          "title": "Theft at Main Street Store",
          "type": "theft",
          "date": "2025-03-14T10:15:00Z"
        },
        {
          "id": "inc_345679",
          "title": "Robbery on 5th Avenue",
          "type": "robbery",
          "date": "2025-03-14T12:30:00Z"
        }
      ],
      "recommendations": [
        "Increase patrol presence in the area",
        "Alert local businesses to enhance security measures",
        "Review security camera footage from the area"
      ],
      "reviewed": false,
      "createdAt": "2025-03-14T14:30:00Z",
      "updatedAt": "2025-03-14T14:30:00Z"
    }
  }
}
```

**Error Response (404 Not Found)**:

```json
{
  "success": false,
  "error": {
    "code": "not_found",
    "message": "Alert with ID alt_123456 not found"
  }
}
```

### Create Alert

Creates a new alert.

- **URL**: `/api/alerts`
- **Method**: `POST`
- **Description**: Generates a new alert with the provided information.


**Request Body**:

```json
{
  "title": "Potential Hotspot Forming",
  "description": "Early indicators of a potential crime hotspot forming based on recent incidents.",
  "severity": "medium",
  "location": {
    "address": "Northside, Industrial District",
    "district": "northside",
    "coordinates": [-74.015, 40.7350]
  },
  "relatedIncidents": ["inc_567890", "inc_567891"],
  "recommendations": [
    "Monitor area for increased activity",
    "Conduct preventive patrols during evening hours"
  ]
}
```

**Success Response (201 Created)**:

```json
{
  "success": true,
  "data": {
    "alert": {
      "id": "alt_789012",
      "title": "Potential Hotspot Forming",
      "severity": "medium",
      "location": "Northside, Industrial District",
      "timestamp": "2025-03-14T22:00:00Z",
      "reviewed": false,
      "createdAt": "2025-03-14T22:00:00Z"
    }
  }
}
```

**Error Response (400 Bad Request)**:

```json
{
  "success": false,
  "error": {
    "code": "validation_error",
    "message": "Invalid alert data",
    "fields": {
      "severity": "Severity must be one of: low, medium, high"
    }
  }
}
```

### Update Alert

Updates an existing alert.

- **URL**: `/api/alerts/:id`
- **Method**: `PUT`
- **Description**: Updates the details of an existing alert.
- **URL Parameters**:

- `id`: Alert ID





**Request Body**:

```json
{
  "severity": "high",
  "reviewed": true,
  "recommendations": [
    "Immediate increase in patrol presence",
    "Notify local businesses of potential threat",
    "Deploy mobile surveillance unit to the area"
  ]
}
```

**Success Response (200 OK)**:

```json
{
  "success": true,
  "data": {
    "alert": {
      "id": "alt_789012",
      "title": "Potential Hotspot Forming",
      "severity": "high",
      "location": "Northside, Industrial District",
      "timestamp": "2025-03-14T22:00:00Z",
      "reviewed": true,
      "updatedAt": "2025-03-14T22:15:00Z"
    }
  }
}
```

**Error Response (404 Not Found)**:

```json
{
  "success": false,
  "error": {
    "code": "not_found",
    "message": "Alert with ID alt_789012 not found"
  }
}
```

### Delete Alert

Deletes an alert.

- **URL**: `/api/alerts/:id`
- **Method**: `DELETE`
- **Description**: Removes an alert from the system.
- **URL Parameters**:

- `id`: Alert ID





**Success Response (200 OK)**:

```json
{
  "success": true,
  "message": "Alert successfully deleted"
}
```

**Error Response (403 Forbidden)**:

```json
{
  "success": false,
  "error": {
    "code": "permission_denied",
    "message": "You do not have permission to delete alerts"
  }
}
```

## Analytics

### Crime Statistics

Retrieves crime statistics for analysis.

- **URL**: `/api/analytics/crime-statistics`
- **Method**: `GET`
- **Description**: Returns aggregated crime statistics based on specified parameters.
- **Query Parameters**:

- `startDate`: Start date for analysis period
- `endDate`: End date for analysis period
- `district`: Filter by district (optional)
- `crimeType`: Filter by crime type (optional)
- `groupBy`: Group results by (day, week, month, type, district)





**Success Response (200 OK)**:

```json
{
  "success": true,
  "data": {
    "timeframe": {
      "start": "2025-01-01T00:00:00Z",
      "end": "2025-03-01T23:59:59Z"
    },
    "totalIncidents": 1284,
    "groupedBy": "month",
    "statistics": [
      {
        "period": "2025-01",
        "count": 425,
        "breakdown": {
          "theft": 148,
          "assault": 85,
          "burglary": 64,
          "robbery": 42,
          "vandalism": 38,
          "other": 48
        }
      },
      {
        "period": "2025-02",
        "count": 398,
        "breakdown": {
          "theft": 139,
          "assault": 80,
          "burglary": 60,
          "robbery": 39,
          "vandalism": 36,
          "other": 44
        }
      },
      {
        "period": "2025-03",
        "count": 461,
        "breakdown": {
          "theft": 161,
          "assault": 92,
          "burglary": 69,
          "robbery": 46,
          "vandalism": 41,
          "other": 52
        }
      }
    ],
    "trends": {
      "overall": "+8.5%",
      "byType": {
        "theft": "+8.8%",
        "assault": "+8.2%",
        "burglary": "+7.8%",
        "robbery": "+9.5%",
        "vandalism": "+7.9%",
        "other": "+8.3%"
      }
    }
  }
}
```

**Error Response (400 Bad Request)**:

```json
{
  "success": false,
  "error": {
    "code": "invalid_parameters",
    "message": "Invalid date range specified",
    "details": "Date range must not exceed 12 months"
  }
}
```

### Heatmap Data

Retrieves data for generating crime heatmaps.

- **URL**: `/api/analytics/heatmap`
- **Method**: `GET`
- **Description**: Returns geospatial crime data for generating heatmaps.
- **Query Parameters**:

- `startDate`: Start date for analysis period
- `endDate`: End date for analysis period
- `crimeType`: Filter by crime type (optional)
- `district`: Filter by district (optional)
- `resolution`: Data resolution (high, medium, low)





**Success Response (200 OK)**:

```json
{
  "success": true,
  "data": {
    "timeframe": {
      "start": "2025-02-01T00:00:00Z",
      "end": "2025-03-01T23:59:59Z"
    },
    "totalPoints": 398,
    "boundingBox": {
      "southwest": [-74.0300, 40.7000],
      "northeast": [-73.9700, 40.7500]
    },
    "points": [
      {
        "coordinates": [-74.006, 40.7128],
        "weight": 0.8,
        "type": "theft",
        "count": 5
      },
      {
        "coordinates": [-74.012, 40.7135],
        "weight": 0.6,
        "type": "assault",
        "count": 3
      },
      // Additional points...
    ]
  }
}
```

**Error Response (400 Bad Request)**:

```json
{
  "success": false,
  "error": {
    "code": "invalid_parameters",
    "message": "Invalid resolution specified",
    "details": "Resolution must be one of: high, medium, low"
  }
}
```

### Predictive Analysis

Retrieves predictive crime analysis data.

- **URL**: `/api/analytics/predictive`
- **Method**: `GET`
- **Description**: Returns AI-generated predictive analysis of potential crime hotspots.
- **Query Parameters**:

- `daysAhead`: Number of days to predict (1-30)
- `crimeType`: Filter by crime type (optional)
- `district`: Filter by district (optional)
- `confidence`: Minimum confidence threshold (0-100)





**Success Response (200 OK)**:

```json
{
  "success": true,
  "data": {
    "predictionDate": "2025-03-14T22:00:00Z",
    "daysAhead": 7,
    "modelVersion": "v2.3.1",
    "modelAccuracy": 87,
    "predictions": [
      {
        "coordinates": [-74.006, 40.7128],
        "probability": 0.85,
        "crimeType": "theft",
        "timeframe": {
          "start": "2025-03-15T18:00:00Z",
          "end": "2025-03-15T23:59:59Z"
        },
        "factors": [
          "Recent similar incidents in area",
          "Weekend evening pattern",
          "Proximity to commercial district"
        ]
      },
      {
        "coordinates": [-74.015, 40.7350],
        "probability": 0.72,
        "crimeType": "burglary",
        "timeframe": {
          "start": "2025-03-16T00:00:00Z",
          "end": "2025-03-16T06:00:00Z"
        },
        "factors": [
          "Similar break-in pattern emerging",
          "Low visibility area",
          "Limited patrol coverage"
        ]
      },
      // Additional predictions...
    ],
    "recommendations": [
      {
        "district": "downtown",
        "action": "Increase patrol presence during evening hours (6PM-10PM)",
        "priority": "high"
      },
      {
        "district": "northside",
        "action": "Focus on residential areas during early morning hours (12AM-6AM)",
        "priority": "medium"
      }
    ]
  }
}
```

**Error Response (400 Bad Request)**:

```json
{
  "success": false,
  "error": {
    "code": "invalid_parameters",
    "message": "Invalid prediction timeframe",
    "details": "Days ahead must be between 1 and 30"
  }
}
```

### Trend Analysis

Retrieves trend analysis data for crime patterns.

- **URL**: `/api/analytics/trends`
- **Method**: `GET`
- **Description**: Returns analysis of crime trends over time.
- **Query Parameters**:

- `startDate`: Start date for analysis period
- `endDate`: End date for analysis period
- `crimeType`: Filter by crime type (optional)
- `district`: Filter by district (optional)
- `interval`: Analysis interval (daily, weekly, monthly)





**Success Response (200 OK)**:

```json
{
  "success": true,
  "data": {
    "timeframe": {
      "start": "2024-03-01T00:00:00Z",
      "end": "2025-03-01T23:59:59Z"
    },
    "interval": "monthly",
    "trends": [
      {
        "period": "2024-03",
        "total": 410,
        "breakdown": {
          "theft": 143,
          "assault": 82,
          "burglary": 62,
          "robbery": 41,
          "vandalism": 37,
          "other": 45
        }
      },
      // Additional periods...
      {
        "period": "2025-02",
        "total": 398,
        "breakdown": {
          "theft": 139,
          "assault": 80,
          "burglary": 60,
          "robbery": 39,
          "vandalism": 36,
          "other": 44
        }
      }
    ],
    "analysis": {
      "overallTrend": "-2.9%",
      "seasonalPatterns": [
        {
          "pattern": "Summer increase",
          "description": "Crime rates typically increase by 15-20% during summer months (June-August)",
          "confidence": 92
        },
        {
          "pattern": "Weekend spike",
          "description": "Weekend incidents are 23% higher than weekday incidents",
          "confidence": 95
        }
      ],
      "emergingPatterns": [
        {
          "pattern": "Eastside burglary increase",
          "description": "Burglary incidents in Eastside district have increased by 18% in the last 3 months",
          "confidence": 87
        }
      ]
    }
  }
}
```

**Error Response (400 Bad Request)**:

```json
{
  "success": false,
  "error": {
    "code": "invalid_parameters",
    "message": "Invalid interval specified",
    "details": "Interval must be one of: daily, weekly, monthly"
  }
}
```

## Resource Planning

### Resource Allocation

Retrieves current resource allocation data.

- **URL**: `/api/resources/allocation`
- **Method**: `GET`
- **Description**: Returns information about how resources are currently allocated.
- **Query Parameters**:

- `district`: Filter by district (optional)
- `resourceType`: Filter by resource type (officers, vehicles)





**Success Response (200 OK)**:

```json
{
  "success": true,
  "data": {
    "totalResources": {
      "officers": 124,
      "vehicles": 42
    },
    "allocation": [
      {
        "district": "downtown",
        "risk": "high",
        "resources": {
          "officers": 45,
          "vehicles": 18
        },
        "coverage": 85,
        "responseTime": 7.2
      },
      {
        "district": "westside",
        "risk": "medium",
        "resources": {
          "officers": 25,
          "vehicles": 10
        },
        "coverage": 72,
        "responseTime": 8.5
      },
      {
        "district": "eastside",
        "risk": "medium",
        "resources": {
          "officers": 20,
          "vehicles": 8
        },
        "coverage": 68,
        "responseTime": 9.1
      },
      {
        "district": "northside",
        "risk": "low",
        "resources": {
          "officers": 18,
          "vehicles": 7
        },
        "coverage": 65,
        "responseTime": 9.8
      },
      {
        "district": "southside",
        "risk": "low",
        "resources": {
          "officers": 16,
          "vehicles": 6
        },
        "coverage": 60,
        "responseTime": 10.5
      }
    ]
  }
}
```

**Error Response (403 Forbidden)**:

```json
{
  "success": false,
  "error": {
    "code": "permission_denied",
    "message": "You do not have permission to view resource allocation data"
  }
}
```

### Patrol Schedule

Retrieves patrol schedule information.

- **URL**: `/api/resources/schedule`
- **Method**: `GET`
- **Description**: Returns patrol schedule information by district and shift.
- **Query Parameters**:

- `district`: Filter by district (optional)
- `date`: Schedule for specific date (default: current date)





**Success Response (200 OK)**:

```json
{
  "success": true,
  "data": {
    "date": "2025-03-15",
    "schedules": [
      {
        "district": "downtown",
        "shifts": [
          {
            "name": "Morning",
            "timeRange": "06:00-14:00",
            "officers": 12,
            "vehicles": 5,
            "priorityAreas": ["Transit Hubs", "Commercial District"],
            "supervisor": "Officer Johnson"
          },
          {
            "name": "Afternoon",
            "timeRange": "14:00-22:00",
            "officers": 18,
            "vehicles": 8,
            "priorityAreas": ["Commercial District", "Entertainment Zone"],
            "supervisor": "Officer Williams"
          },
          {
            "name": "Night",
            "timeRange": "22:00-06:00",
            "officers": 15,
            "vehicles": 7,
            "priorityAreas": ["Entertainment Zone", "Transit Hubs"],
            "supervisor": "Officer Davis"
          }
        ]
      },
      // Additional districts...
    ]
  }
}
```

**Error Response (400 Bad Request)**:

```json
{
  "success": false,
  "error": {
    "code": "invalid_parameters",
    "message": "Invalid date format",
    "details": "Date must be in YYYY-MM-DD format"
  }
}
```

### Optimize Resources

Generates optimized resource allocation recommendations.

- **URL**: `/api/resources/optimize`
- **Method**: `POST`
- **Description**: Calculates optimal resource allocation based on crime data and constraints.


**Request Body**:

```json
{
  "constraints": {
    "totalOfficers": 124,
    "totalVehicles": 42,
    "maxResponseTime": 10,
    "minCoverage": 60
  },
  "priorities": {
    "downtown": "high",
    "westside": "medium",
    "eastside": "medium",
    "northside": "low",
    "southside": "low"
  },
  "crimeData": {
    "useLatest": true,
    "includePredictive": true
  }
}
```

**Success Response (200 OK)**:

```json
{
  "success": true,
  "data": {
    "optimizationId": "opt_123456",
    "status": "completed",
    "currentAllocation": {
      "downtown": {
        "officers": 45,
        "vehicles": 18
      },
      "westside": {
        "officers": 25,
        "vehicles": 10
      },
      "eastside": {
        "officers": 20,
        "vehicles": 8
      },
      "northside": {
        "officers": 18,
        "vehicles": 7
      },
      "southside": {
        "officers": 16,
        "vehicles": 6
      }
    },
    "recommendedAllocation": {
      "downtown": {
        "officers": 42,
        "vehicles": 16
      },
      "westside": {
        "officers": 28,
        "vehicles": 11
      },
      "eastside": {
        "officers": 24,
        "vehicles": 9
      },
      "northside": {
        "officers": 16,
        "vehicles": 6
      },
      "southside": {
        "officers": 14,
        "vehicles": 5
      }
    },
    "impact": {
      "responseTime": {
        "downtown": "-0.2 min",
        "westside": "-0.8 min",
        "eastside": "-0.7 min",
        "northside": "+0.3 min",
        "southside": "+0.5 min"
      },
      "coverage": {
        "downtown": "-2%",
        "westside": "+5%",
        "eastside": "+4%",
        "northside": "-1%",
        "southside": "-2%"
      },
      "overall": {
        "averageResponseTime": "-0.2 min",
        "averageCoverage": "+1.5%",
        "predictedCrimeReduction": "+3.2%"
      }
    }
  }
}
```

**Error Response (400 Bad Request)**:

```json
{
  "success": false,
  "error": {
    "code": "invalid_constraints",
    "message": "Resource constraints cannot be satisfied",
    "details": "Minimum coverage requirements cannot be met with the specified number of officers"
  }
}
```

## Settings

### Get System Settings

Retrieves system settings.

- **URL**: `/api/settings/system`
- **Method**: `GET`
- **Description**: Returns current system settings.


**Success Response (200 OK)**:

```json
{
  "success": true,
  "data": {
    "settings": {
      "general": {
        "systemName": "Crime Analysis Platform",
        "defaultLanguage": "en",
        "defaultTimezone": "America/New_York",
        "dateFormat": "MM/DD/YYYY"
      },
      "security": {
        "sessionTimeout": 30,
        "passwordPolicy": {
          "minLength": 8,
          "requireUppercase": true,
          "requireLowercase": true,
          "requireNumbers": true,
          "requireSpecialChars": true,
          "expiryDays": 90
        },
        "twoFactorAuthEnabled": true
      },
      "notifications": {
        "emailEnabled": true,
        "pushEnabled": true,
        "alertThreshold": "medium"
      },
      "analytics": {
        "dataRetentionDays": 365,
        "predictiveModelVersion": "v2.3.1",
        "autoRefreshInterval": 5
      }
    }
  }
}
```

**Error Response (403 Forbidden)**:

```json
{
  "success": false,
  "error": {
    "code": "permission_denied",
    "message": "You do not have permission to view system settings"
  }
}
```

### Update System Settings

Updates system settings.

- **URL**: `/api/settings/system`
- **Method**: `PUT`
- **Description**: Updates system settings with the provided values.


**Request Body**:

```json
{
  "general": {
    "defaultLanguage": "es",
    "defaultTimezone": "America/Los_Angeles",
    "dateFormat": "DD/MM/YYYY"
  },
  "security": {
    "sessionTimeout": 60,
    "passwordPolicy": {
      "minLength": 10,
      "expiryDays": 60
    }
  }
}
```

**Success Response (200 OK)**:

```json
{
  "success": true,
  "data": {
    "settings": {
      "general": {
        "systemName": "Crime Analysis Platform",
        "defaultLanguage": "es",
        "defaultTimezone": "America/Los_Angeles",
        "dateFormat": "DD/MM/YYYY"
      },
      "security": {
        "sessionTimeout": 60,
        "passwordPolicy": {
          "minLength": 10,
          "requireUppercase": true,
          "requireLowercase": true,
          "requireNumbers": true,
          "requireSpecialChars": true,
          "expiryDays": 60
        },
        "twoFactorAuthEnabled": true
      },
      "notifications": {
        "emailEnabled": true,
        "pushEnabled": true,
        "alertThreshold": "medium"
      },
      "analytics": {
        "dataRetentionDays": 365,
        "predictiveModelVersion": "v2.3.1",
        "autoRefreshInterval": 5
      }
    }
  }
}
```

**Error Response (400 Bad Request)**:

```json
{
  "success": false,
  "error": {
    "code": "validation_error",
    "message": "Invalid settings data",
    "fields": {
      "security.sessionTimeout": "Session timeout must be between 15 and 120 minutes"
    }
  }
}
```

### Get User Settings

Retrieves settings for the current user.

- **URL**: `/api/settings/user`
- **Method**: `GET`
- **Description**: Returns settings for the authenticated user.


**Success Response (200 OK)**:

```json
{
  "success": true,
  "data": {
    "settings": {
      "preferences": {
        "language": "en",
        "timezone": "America/New_York",
        "dateFormat": "MM/DD/YYYY",
        "theme": "light",
        "density": "comfortable"
      },
      "notifications": {
        "email": true,
        "push": true,
        "highRiskAlerts": true,
        "predictiveAlerts": true,
        "reportGeneration": true
      },
      "dashboard": {
        "defaultView": "overview",
        "autoRefresh": true,
        "refreshInterval": 5,
        "widgets": [
          "crime-heatmap",
          "recent-alerts",
          "crime-type-chart",
          "predictive-analysis"
        ]
      }
    }
  }
}
```

**Error Response (401 Unauthorized)**:

```json
{
  "success": false,
  "error": {
    "code": "unauthorized",
    "message": "Authentication required to access user settings"
  }
}
```

### Update User Settings

Updates settings for the current user.

- **URL**: `/api/settings/user`
- **Method**: `PUT`
- **Description**: Updates settings for the authenticated user.


**Request Body**:

```json
{
  "preferences": {
    "theme": "dark",
    "density": "compact"
  },
  "notifications": {
    "push": false,
    "reportGeneration": false
  },
  "dashboard": {
    "defaultView": "heatmap",
    "widgets": [
      "crime-heatmap",
      "predictive-analysis",
      "crime-type-chart",
      "resource-allocation"
    ]
  }
}
```

**Success Response (200 OK)**:

```json
{
  "success": true,
  "data": {
    "settings": {
      "preferences": {
        "language": "en",
        "timezone": "America/New_York",
        "dateFormat": "MM/DD/YYYY",
        "theme": "dark",
        "density": "compact"
      },
      "notifications": {
        "email": true,
        "push": false,
        "highRiskAlerts": true,
        "predictiveAlerts": true,
        "reportGeneration": false
      },
      "dashboard": {
        "defaultView": "heatmap",
        "autoRefresh": true,
        "refreshInterval": 5,
        "widgets": [
          "crime-heatmap",
          "predictive-analysis",
          "crime-type-chart",
          "resource-allocation"
        ]
      }
    }
  }
}
```

**Error Response (400 Bad Request)**:

```json
{
  "success": false,
  "error": {
    "code": "validation_error",
    "message": "Invalid settings data",
    "fields": {
      "dashboard.widgets": "Maximum of 4 widgets allowed"
    }
  }
}
```

---

## Error Codes

| Code | Description
|-----|-----
| `auth_failed` | Authentication failed due to invalid credentials
| `invalid_token` | The provided token is invalid or expired
| `permission_denied` | User does not have permission for the requested action
| `not_found` | The requested resource was not found
| `validation_error` | The request data failed validation
| `invalid_parameters` | The request parameters are invalid
| `file_too_large` | The uploaded file exceeds the maximum allowed size
| `unauthorized` | Authentication is required for this endpoint
| `invalid_format` | The requested format is not supported
| `invalid_constraints` | The provided constraints cannot be satisfied
| `server_error` | An unexpected server error occurred


## Rate Limiting

The API implements rate limiting to prevent abuse. The current limits are:

- 100 requests per minute for authenticated users
- 20 requests per minute for unauthenticated users


When a rate limit is exceeded, the API will respond with a 429 Too Many Requests status code:

```json
{
  "success": false,
  "error": {
    "code": "rate_limit_exceeded",
    "message": "Rate limit exceeded. Please try again later.",
    "retryAfter": 30
  }
}
```

The `retryAfter` field indicates the number of seconds to wait before making another request.

## Authentication

All API requests (except for login and register) require authentication using a JWT token. The token should be included in the Authorization header:

```plaintext
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```
Tokens expire after 24 hours, after which a new token must be obtained using the refresh token endpoint.