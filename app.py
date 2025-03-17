from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv
import logging

from apps.auth.routes import router as auth_router
from apps.users.routes import router as users_router
from apps.incidents.routes import router as incidents_router
from apps.reports.routes import router as reports_router
from apps.alerts.routes import router as alerts_router
from apps.analytics.routes import router as analytics_router
from apps.resources.routes import router as resources_router
from apps.settings.routes import router as settings_router

from core.rag.llm import llm
from core.rag.vectore_store import get_vector_store
from core.rag.incidents_vectorstore import incident_to_document, get_incident_vector_store
from middlewares.rate_limiter import RateLimiter
from core.config import settings
from core.database import create_db_and_tables
from pydantic import BaseModel
from typing import List, Dict, Any
from sqlmodel import Session, select
from apps.incidents.models import Incident

# Initialize logger
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Crime Analysis API",
    description="API for analyzing crime data using Gemini model",
    version="1.0.0",
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    swagger_ui_oauth2_redirect_url="/api/docs/oauth2-redirect",
    swagger_ui_init_oauth={
        "usePkceWithAuthorizationCodeGrant": True,
        "clientId": "crime-analysis-api"
    },
)

# Configure security for Swagger UI
app.swagger_ui_default_parameters = {
    "persistAuthorization": True,
}

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiter middleware
app.add_middleware(RateLimiter)

# Register API routers with prefix
app.include_router(auth_router, prefix=f"{settings.API_PREFIX}/auth", tags=["Authentication"])
app.include_router(users_router, prefix=f"{settings.API_PREFIX}/users", tags=["Users"])
app.include_router(incidents_router, prefix=f"{settings.API_PREFIX}/incidents", tags=["Incidents"])
app.include_router(reports_router, prefix=f"{settings.API_PREFIX}/reports", tags=["Reports"])
app.include_router(alerts_router, prefix=f"{settings.API_PREFIX}/alerts", tags=["Alerts"])
app.include_router(analytics_router, prefix=f"{settings.API_PREFIX}/analytics", tags=["Analytics"])
app.include_router(resources_router, prefix=f"{settings.API_PREFIX}/resources", tags=["Resource Planning"])
app.include_router(settings_router, prefix=f"{settings.API_PREFIX}/settings", tags=["Settings"])


class SearchRequest(BaseModel):
    query: str
    k: int = 5

class SearchResult(BaseModel):
    content: str
    metadata: Dict[str, Any]

class SearchResponse(BaseModel):
    results: List[SearchResult]

@app.post("/api/search-vectors", response_model=SearchResponse)
async def search_vectors(request: SearchRequest = Body(...)):
    # Get the default vector store
    vs = get_vector_store()

    # Search for similar documents
    documents = vs.similarity_search(request.query, k=request.k)
    
    # Format results for response
    results = [
        SearchResult(content=doc.page_content, metadata=doc.metadata)
        for doc in documents
    ]
    
    return SearchResponse(results=results)

@app.post("/api/insert-vector")
async def insert_vector(request: SearchRequest = Body(...)):
    # Get the default vector store
    vs = get_vector_store()

    from langchain_core.documents import Document

    documents = [
        Document(page_content="Theft incidents in downtown area", metadata={"type": "theft", "location": "downtown"}),
        Document(page_content="Burglary prevention strategies", metadata={"type": "prevention", "crime": "burglary"})
    ]

    vs.add_documents(documents)
    
    return {"message": "Vectors inserted successfully"}

class RagResponse(BaseModel):
    result: str
    error: str = None

@app.post("/api/rag", response_model=RagResponse)
async def rag(request: SearchRequest = Body(...)):
    """Run RAG (Retrieval Augmented Generation) using the user's query"""
    try:
        # Get vector store and create retriever
        vs = get_vector_store()
        retriever = vs.as_retriever(search_kwargs={"k": request.k})
        
        # Format documents into context with source metadata
        def format_docs(docs):
            formatted_docs = []
            for i, doc in enumerate(docs, start=1):
                source_info = f"Source {i}: " + (doc.metadata.get('source', 'Unknown source'))
                content = doc.page_content.strip()
                formatted_docs.append(f"{source_info}\n{content}")
            return "\n\n" + "\n\n".join(formatted_docs)
        
        # Create prompt template
        from langchain_core.prompts import PromptTemplate
        
        prompt_template = PromptTemplate.from_template("""
        You are CrimeGPT, an AI assistant specialized in crime analysis and law enforcement support.
        
        Based on the following retrieved information:
        {context}
        
        Please provide a comprehensive and accurate answer to this question:
        {question}
        
        If the retrieved information doesn't contain relevant details to answer the question,
        please indicate that and provide general information about the topic if possible.
        """)
        
        # Manually implement the RAG flow
        # 1. Retrieve documents
        documents = retriever.invoke(request.query)
        
        # 2. Format the documents
        context = format_docs(documents)
        
        # 3. Create the prompt
        prompt = prompt_template.format(context=context, question=request.query)
        
        # 4. Send to LLM
        response = llm.invoke(prompt)
        
        # 5. Extract the result
        if hasattr(response, 'content'):
            # For newer versions of LangChain that return a structured response
            result = response.content
        else:
            # For older versions that return text directly
            result = str(response)
        
        return {"result": result}
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"RAG processing failed: {error_details}")
        return {"result": "", "error": f"RAG processing failed: {str(e)}"}

async def populate_incident_vector_store():
    """Populate the incident vector store with existing incidents."""
    try:
        logger.info("Starting to populate incident vector store...")
        from core.database import engine
        
        # Create a new session directly with the engine
        with Session(engine) as session:
            # Query all incidents
            incidents = session.exec(select(Incident)).all()
            
            if not incidents:
                logger.info("No incidents found to populate vector store.")
                return
                
            # Get the vector store
            vector_store = get_incident_vector_store()
            
            # Convert incidents to documents
            documents = [incident_to_document(incident) for incident in incidents]
            
            # Add documents to vector store
            if documents:
                vector_store.add_documents(documents)
                logger.info(f"Added {len(documents)} incidents to vector store.")
            else:
                logger.info("No documents created for vector store.")
                
    except Exception as e:
        logger.error(f"Error populating incident vector store: {e}")
        import traceback
        logger.error(traceback.format_exc())


@app.on_event("startup")
async def startup_event():
    """Create database and tables on startup"""
    create_db_and_tables()
    
    # Initialize vector stores
    try:
        # First, make sure our vector store module is set up properly
        from core.rag.vectore_store import VectorStoreConfig, VectorStore
        
        # Create a default vector store config
        default_config = VectorStoreConfig(collection_name="default")
        default_vs = VectorStore(default_config)
        
        # Initialize incident vector store
        incidents_vs = get_incident_vector_store()
        
        # Populate incident vector store with existing data
        await populate_incident_vector_store()
        
        logger.info("Vector stores initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing vector stores: {e}")
        import traceback
        logger.error(traceback.format_exc())

# Run the application
if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
