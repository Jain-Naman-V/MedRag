from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from pathlib import Path
import os
from dotenv import load_dotenv
import httpx

# Load environment variables
load_dotenv()

# Create necessary directories
os.makedirs(os.getenv("UPLOAD_FOLDER", "./data/uploads"), exist_ok=True)
os.makedirs(os.getenv("VECTOR_STORE_PATH", "./data/vector_store"), exist_ok=True)

# Import database initialization function
from app.db.database import init_db

# Initialize FastAPI app
app = FastAPI(
    title=os.getenv("APP_NAME", "MedRAG"),
    description="Document Analysis and Summarization System",
    version="1.0.0"
)

@app.on_event("startup")
def on_startup():
    # Create database tables
    # This will ensure tables are created if they don't exist
    # based on the models defined in app.db.models
    init_db()
    print(f"Database tables should be created/verified at {os.getenv('DB_PATH', './data/MedRAG.db')}")


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define base directory for paths
BASE_DIR = Path(__file__).resolve().parent.parent

# Mount static files with absolute path
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# Set up templates with absolute path
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Import and include routers
from app.api import documents, summaries

app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(summaries.router, prefix="/api/summaries", tags=["summaries"])

# API Key validation model
class APIKeyRequest(BaseModel):
    api_key: str

@app.post("/api/test-openai-key")
async def test_openai_key(request: APIKeyRequest):
    """Test if the provided OpenAI API key is valid."""
    try:
        # Test the API key by making a simple request to OpenAI
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.openai.com/v1/models",
                headers={
                    "Authorization": f"Bearer {request.api_key}",
                    "Content-Type": "application/json"
                },
                timeout=10.0
            )
            
            if response.status_code == 200:
                return JSONResponse(
                    status_code=200,
                    content={"message": "API key is valid", "status": "success"}
                )
            else:
                error_detail = "Invalid API key"
                try:
                    error_data = response.json()
                    if "error" in error_data:
                        error_detail = error_data["error"].get("message", "Invalid API key")
                except:
                    pass
                
                raise HTTPException(
                    status_code=400,
                    detail=error_detail
                )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=408,
            detail="Request timeout. Please check your internet connection."
        )
    except httpx.RequestError:
        raise HTTPException(
            status_code=500,
            detail="Network error. Please check your internet connection."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/documents")
async def documents_page(request: Request):
    return templates.TemplateResponse("documents.html", {"request": request})

@app.get("/query")
async def query_page(request: Request):
    return templates.TemplateResponse("query.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=os.getenv("HOST", "0.0.0.0"), port=int(os.getenv("PORT", 8000)), reload=True)
