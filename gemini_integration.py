import os
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
from typing import Dict, Any

# Set up Gemini API
def setup_gemini(api_key=None):
    """
    Configure Gemini API with the provided key or from environment variable
    """
    if api_key is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if api_key is None:
            raise ValueError("No Gemini API key provided. Set GEMINI_API_KEY environment variable or pass api_key parameter.")
    
    # Configure the Gemini API
    genai.configure(api_key=api_key)
    
    try:
        # Use Gemini Pro for better reasoning capabilities
        model = genai.GenerativeModel('gemini-1.5-pro')
        print(f"Gemini model initialized: gemini-1.5-pro")
    except Exception as e:
        # Fallback to gemini-pro if 1.5 is not available
        print(f"Could not initialize gemini-1.5-pro: {e}")
        print("Falling back to gemini-pro model")
        model = genai.GenerativeModel('gemini-pro')
        print(f"Gemini model initialized: gemini-pro")
    
    return model

# Function to generate embeddings using Sentence Transformers
def generate_gemini_embeddings(texts, model_name='all-MiniLM-L6-v2'):
    """
    Generate embeddings using Sentence Transformers
    """
    model = SentenceTransformer(model_name)
    embeddings = model.encode(texts)
    return embeddings

# Function to generate responses using Gemini
def generate_gemini_response(query: str, context_records: Any, model: Any) -> str:
    """
    Generate responses using Gemini based on the query and retrieved context
    
    Args:
        query: User query string
        context_records: Pandas DataFrame containing relevant crime records
        model: Initialized Gemini model
        
    Returns:
        str: Formatted response from Gemini
    """
    # Format context records into text
    context_text = "\n\n".join([
        f"Record {i+1}:\n" +
        f"Crime Type: {row['Crime_Type']}\n" +
        f"Location: {row['Neighborhood']} at coordinates ({row['Latitude']}, {row['Longitude']})\n" +
        f"Date and Time: {row['Date'].strftime('%A, %B %d, %Y') if hasattr(row['Date'], 'strftime') else row['Date']}, {row['Time_of_Day']}\n" +
        f"Weather: {row['Weather']}, Temperature: {row['Temperature']:.1f}°C, {row['Lighting']}\n" +
        f"Population Density: {row['Population_Density']:.1f}, Average Income: {row['Average_Income']:.1f}, " +
        f"Unemployment Rate: {row['Unemployment_Rate']:.1f}%"
        for i, (_, row) in enumerate(context_records.iterrows())
    ])
    
    # Create prompt for the model
    prompt = f"""
    You are CrimeAnalyst-GPT, an AI crime prediction expert. Analyze the likelihood of crime based on the provided data.
    
    CONTEXT DATA:
    {context_text}
    
    QUERY DETAILS:
    {query}
    
    Provide a CONCISE crime probability analysis with this exact format:

    1. CRIME PROBABILITY: [Give a percentage probability estimate for crime occurring]
    2. MOST LIKELY CRIME TYPE: [Name the most likely crime, with percentage: e.g., Theft(60%), Assault(20%), Vandalism(10%), Kidnapping(5%)]
    3. KEY FACTORS: [List 2-3 main risk factors affecting probability]
    4. RISK LEVEL: [Categorize as Low/Moderate/High/Very High]
    
    Base your analysis strictly on the patterns in the provided crime data. Your response must be data-driven and reference specific factors from the context.
    Keep your complete response under 10 lines. Focus only on data-driven insights with specific numbers and probabilities.
    """
    
    try:
        # Generate response with Gemini
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error generating response with Gemini: {e}")
        return f"Error generating response: {str(e)}"

# Function to parse Gemini's response into structured data
def parse_gemini_response(response: str) -> Dict[str, Any]:
    """
    Parse the formatted response from Gemini into structured data
    
    Args:
        response: Formatted response string from Gemini
        
    Returns:
        dict: Structured data with crime analysis
    """
    try:
        lines = [line.strip() for line in response.split('\n') if line.strip()]
        result = {}
        
        for line in lines:
            if line.startswith("1. CRIME PROBABILITY:"):
                result["crime_probability"] = line.replace("1. CRIME PROBABILITY:", "").strip()
            elif line.startswith("2. MOST LIKELY CRIME TYPE:"):
                result["most_likely_crime"] = line.replace("2. MOST LIKELY CRIME TYPE:", "").strip()
            elif line.startswith("3. KEY FACTORS:"):
                result["key_factors"] = line.replace("3. KEY FACTORS:", "").strip()
            elif line.startswith("4. RISK LEVEL:"):
                result["risk_level"] = line.replace("4. RISK LEVEL:", "").strip()
        
        return result
    except Exception as e:
        print(f"Error parsing Gemini response: {e}")
        return {"error": str(e), "raw_response": response}