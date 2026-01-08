from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.common.config import settings

app = FastAPI(
    title="Amrutam Telemedicine API",
    version="1.0.0",
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
)

# CORS (Security Checklist Item)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Change this to frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    """AWS/Docker Healthcheck endpoint"""
    return {
        "status": "healthy",
        "app_name": "Amrutam Backend",
        "env": settings.ENVIRONMENT
    }

@app.get("/")
def root():
    return {"message": "Amrutam API is running"}