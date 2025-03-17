import os
from main import load_and_preprocess_data, engineer_features, generate_embeddings, setup_chroma_db, crime_rag_interface
from advanced_query import advanced_query_interface
from gemini_integration import setup_gemini

def main():
    print("=" * 70)
    print("CRIME DATA ANALYSIS AND RAG SYSTEM")
    print("=" * 70)
    
    # Check for Gemini API key
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key is None:
        api_key = input("Please enter your Gemini API key: ")
        os.environ["GEMINI_API_KEY"] = api_key
    
    # Load and preprocess data
    print("\nLoading and preprocessing data...")
    df = load_and_preprocess_data()
    print(f"Loaded {len(df)} crime records")
    
    # Engineer features
    print("\nEngineering contextual features...")
    df = engineer_features(df)
    
    # Generate embeddings
    print("\nGenerating embeddings (this may take a moment)...")
    embeddings = generate_embeddings(df)
    
    # Set up ChromaDB
    print("\nSetting up vector database...")
    chroma_client, collections = setup_chroma_db(df, embeddings)
    
    # Initialize Gemini
    print("\nInitializing Gemini model...")
    gemini_model = setup_gemini(api_key=api_key)
    
    # Main menu loop
    while True:
        print("\n" + "=" * 40)
        print("MAIN MENU")
        print("=" * 40)
        print("1. Simple Query Interface")
        print("2. Advanced Analysis Interface")
        print("3. Exit")
        
        choice = input("\nEnter your choice (1-3): ")
        
        if choice == '1':
            crime_rag_interface()
        elif choice == '2':
            advanced_query_interface(df, collections, gemini_model)
        elif choice == '3':
            print("\nExiting system. Goodbye!")
            break
        else:
            print("\nInvalid choice. Please try again.")

if __name__ == "__main__":
    main()