import pandas as pd
import numpy as np
import chromadb
import os
from gemini_integration import setup_gemini, generate_gemini_embeddings, generate_gemini_response

from dotenv import load_dotenv
load_dotenv()

# Create directories if they don't exist
os.makedirs('embeddings', exist_ok=True)
os.makedirs('models', exist_ok=True)
os.makedirs('output', exist_ok=True)
os.makedirs('chroma_db', exist_ok=True)

# Global dataframe to store all crime data
global_df = None

# Load and preprocess data
def load_and_preprocess_data(file_path='data.csv'):
    df = pd.read_csv(file_path)
    
    # Convert date to datetime
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Extract additional temporal features
    df['Year'] = df['Date'].dt.year
    df['Month_Num'] = df['Date'].dt.month
    df['Day'] = df['Date'].dt.day
    df['Day_of_Week_Num'] = df['Date'].dt.dayofweek
    df['Is_Weekend'] = df['Day_of_Week_Num'].apply(lambda x: 1 if x >= 5 else 0)
    
    # Create time period categories
    time_mapping = {
        'Morning': 1,
        'Afternoon': 2,
        'Evening': 3,
        'Night': 4
    }
    df['Time_of_Day_Num'] = df['Time_of_Day'].map(time_mapping)
    
    # Weather encoding
    weather_mapping = {
        'Sunny': 1,
        'Cloudy': 2,
        'Rainy': 3,
        'Snowy': 4
    }
    df['Weather_Num'] = df['Weather'].map(weather_mapping)
    
    # Lighting encoding
    df['Lighting_Num'] = df['Lighting'].apply(lambda x: 1 if x == 'Well-lit' else 0)
    
    # Add crime count field for aggregation
    df['Crime_Count'] = 1
    
    return df

# Feature engineering for better context representation
def engineer_features(df):
    """
    Add contextual descriptions to the dataframe
    """
    # Create a copy of the dataframe to avoid modifying the original
    df_engineered = df.copy()
    
    # Create rich textual descriptions for each crime entry
    df_engineered['contextual_description'] = df.apply(
        lambda row: (
            f"Crime: {row['Crime_Type']} in {row['Neighborhood']} on {row['Date'].strftime('%A, %B %d, %Y')} "
            f"during the {row['Time_of_Day']} hours. The weather was {row['Weather']} with a temperature of "
            f"{row['Temperature']:.1f}°C. The area was {row['Lighting']} with a population density of "
            f"{row['Population_Density']:.1f} people per sq km. The neighborhood has an average income of "
            f"{row['Average_Income']:.1f} and an unemployment rate of {row['Unemployment_Rate']:.1f}%."
        ), axis=1
    )
    
    # Create geographical context
    df_engineered['geo_context'] = df.apply(
        lambda row: f"Location at coordinates ({row['Latitude']}, {row['Longitude']}) in {row['Neighborhood']}",
        axis=1
    )
    
    # Create temporal context
    df_engineered['temporal_context'] = df.apply(
        lambda row: (
            f"Occurred on {row['Date'].strftime('%A, %B %d, %Y')} during {row['Time_of_Day']} hours"
        ), axis=1
    )
    
    # Create environmental context
    df_engineered['environmental_context'] = df.apply(
        lambda row: (
            f"Weather was {row['Weather']} with {row['Temperature']:.1f}°C and {row['Lighting']} conditions"
        ), axis=1
    )
    
    # Create socioeconomic context
    df_engineered['socioeconomic_context'] = df.apply(
        lambda row: (
            f"Area with population density of {row['Population_Density']:.1f}, average income of "
            f"{row['Average_Income']:.1f}, and unemployment rate of {row['Unemployment_Rate']:.1f}%"
        ), axis=1
    )
    
    return df_engineered

# Generate embeddings for the contextual descriptions using Gemini
def generate_embeddings(df):
    """
    Generate embeddings for the various context fields
    """
    # Verify the required columns exist
    required_columns = ['contextual_description', 'geo_context', 'temporal_context', 
                      'environmental_context', 'socioeconomic_context']
    
    for col in required_columns:
        if col not in df.columns:
            raise KeyError(f"Required column '{col}' not found in dataframe. Columns available: {df.columns.tolist()}")
    
    print("Generating embeddings for the following contexts:")
    print(f"- Full context: {len(df['contextual_description'])} records")
    print(f"- Geographical context: {len(df['geo_context'])} records")
    print(f"- Temporal context: {len(df['temporal_context'])} records")
    print(f"- Environmental context: {len(df['environmental_context'])} records")
    print(f"- Socioeconomic context: {len(df['socioeconomic_context'])} records")
    
    # Generate embeddings for different contexts
    embeddings = {
        'full_context': generate_gemini_embeddings(df['contextual_description'].tolist()),
        'geo_context': generate_gemini_embeddings(df['geo_context'].tolist()),
        'temporal_context': generate_gemini_embeddings(df['temporal_context'].tolist()),
        'environmental_context': generate_gemini_embeddings(df['environmental_context'].tolist()),
        'socioeconomic_context': generate_gemini_embeddings(df['socioeconomic_context'].tolist())
    }
    
    # Save embeddings
    for name, emb in embeddings.items():
        np.save(f'embeddings/{name}_embeddings.npy', emb)
    
    return embeddings

# Set up ChromaDB for vector storage and retrieval
def setup_chroma_db(df, embeddings):
    """
    Set up ChromaDB for vector storage and retrieval using the updated API
    """
    # Initialize ChromaDB client with the updated API
    client = chromadb.PersistentClient(path="chroma_db")
    
    # Create collections for different contexts
    collections = {}
    for context_type in ['full_context', 'geo_context', 'temporal_context', 
                         'environmental_context', 'socioeconomic_context']:
        try:
            # Delete collection if it exists
            client.delete_collection(name=context_type)
        except Exception as e:
            print(f"Error deleting collection '{context_type}': {e}")
            # Collection doesn't exist or other error
            pass
            
        # Create new collection
        collection = client.create_collection(name=context_type)
        
        # Add documents with their embeddings
        collection.add(
            embeddings=embeddings[context_type].tolist(),
            documents=df[context_type.replace('full_context', 'contextual_description')].tolist(),
            metadatas=[{
                'id': str(i),
                'crime_type': crime_type,
                'neighborhood': neighborhood,
                'date': date.strftime("%Y-%m-%d"),
                'time_of_day': time_of_day
            } for i, (crime_type, neighborhood, date, time_of_day) in 
                enumerate(zip(df['Crime_Type'], df['Neighborhood'], df['Date'], df['Time_of_Day']))],
            ids=[str(i) for i in range(len(df))]
        )
        
        collections[context_type] = collection
    
    return client, collections

# Define query functions for the RAG system
def query_crime_data(query_text, df, collections, context_type='full_context', n_results=5):
    """
    Query the crime data based on text input
    """
    # Generate embedding for the query
    query_embedding = generate_gemini_embeddings([query_text])[0]
    
    # Query the appropriate collection
    collection = collections[context_type]
    results = collection.query(
        query_embeddings=[query_embedding.tolist()],
        n_results=n_results
    )
    
    # Get the matching document IDs
    doc_ids = [int(id) for id in results['ids'][0]]
    
    # Return the matching records from the dataframe
    return df.iloc[doc_ids].copy()

def multi_context_query(query_text, df, collections, weights=None, n_results=5):
    """
    Query across multiple context types with optional weighting
    """
    if weights is None:
        # Default equal weighting
        weights = {
            'full_context': 0.3,
            'geo_context': 0.2, 
            'temporal_context': 0.2,
            'environmental_context': 0.15,
            'socioeconomic_context': 0.15
        }
    
    # Dictionary to track document scores
    doc_scores = {}
    
    # Query each context type
    for context_type, weight in weights.items():
        query_embedding = generate_gemini_embeddings([query_text])[0]
        
        collection = collections[context_type]
        results = collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=len(df)  # Get all results to combine scores
        )
        
        # Process distances into scores (smaller distance = higher score)
        distances = results['distances'][0]
        max_dist = max(distances) if distances else 1.0
        
        # Convert distances to scores and apply weight
        for i, doc_id in enumerate(results['ids'][0]):
            score = (1 - (distances[i] / max_dist)) * weight
            doc_scores[doc_id] = doc_scores.get(doc_id, 0) + score
    
    # Sort by score and get top n_results
    top_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)[:n_results]
    
    # Return top documents
    top_ids = [int(doc_id) for doc_id, score in top_docs]
    return df.iloc[top_ids].copy()

# Generate contextual response using Gemini
def generate_contextual_response(query, context_records, model=None):
    """
    Generate responses based on the query and retrieved context using Gemini
    """
    if model is None:
        # Set up Gemini if not provided
        model = setup_gemini()
    
    return generate_gemini_response(query, context_records, model)

# Create a simple interface to interact with the RAG system
def crime_rag_interface(df, collections):
    """
    Interactive interface for querying crime data
    """
    print("=" * 50)
    print("CRIME DATA RAG SYSTEM")
    print("=" * 50)
    print("Enter your query about crime data (or 'exit' to quit):")
    
    # Set up Gemini model
    gemini_model = setup_gemini()
    
    while True:
        query = input("\nQuery: ")
        if query.lower() == 'exit':
            break
        
        # Get context weighting
        print("\nSelect context weighting strategy:")
        print("1. Default - balanced weighting across all contexts")
        print("2. Geographic focus")
        print("3. Temporal focus")
        print("4. Environmental focus")
        print("5. Socioeconomic focus")
        
        strategy = input("Select strategy (1-5): ")
        
        # Set context weights based on strategy
        if strategy == '2':
            weights = {'geo_context': 0.6, 'full_context': 0.2, 'temporal_context': 0.1, 
                       'environmental_context': 0.05, 'socioeconomic_context': 0.05}
        elif strategy == '3':
            weights = {'temporal_context': 0.6, 'full_context': 0.2, 'geo_context': 0.1,
                       'environmental_context': 0.05, 'socioeconomic_context': 0.05}
        elif strategy == '4':
            weights = {'environmental_context': 0.6, 'full_context': 0.2, 'geo_context': 0.1,
                       'temporal_context': 0.05, 'socioeconomic_context': 0.05}
        elif strategy == '5':
            weights = {'socioeconomic_context': 0.6, 'full_context': 0.2, 'geo_context': 0.1,
                       'temporal_context': 0.05, 'environmental_context': 0.05}
        else:
            weights = None  # Default weighting
        
        # Retrieve context
        context_records = multi_context_query(query, df, collections, weights=weights, n_results=5)
        
        print("\nRetrieved context:")
        for i, (_, row) in enumerate(context_records.iterrows()):
            print(f"{i+1}. {row['Crime_Type']} in {row['Neighborhood']} on {row['Date'].strftime('%Y-%m-%d')}")
        
        # Generate response
        print("\nGenerating response...")
        response = generate_contextual_response(query, context_records, model=gemini_model)
        
        print("\n" + "=" * 30 + " RESPONSE " + "=" * 30)
        print(response)
        print("=" * 70)

# Main function to run everything
def main():
    """
    Main function to run the Crime RAG system
    """
    global global_df
    
    # Load and preprocess data
    print("Loading and preprocessing data...")
    df = load_and_preprocess_data()
    print(f"Loaded {len(df)} crime records")
    
    # Engineer features
    print("Engineering contextual features...")
    df = engineer_features(df)
    print("Features engineered successfully")
    
    # Store in global variable for access by other functions
    global_df = df
    
    # Generate embeddings
    print("Generating embeddings (this may take a moment)...")
    embeddings = generate_embeddings(df)
    print("Embeddings generated successfully")
    
    # Set up ChromaDB
    print("Setting up vector database...")
    chroma_client, collections = setup_chroma_db(df, embeddings)
    print("Vector database setup complete")
    
    # Start the interface
    crime_rag_interface(df, collections)

# Example of running the interface
if __name__ == "__main__":
    main()