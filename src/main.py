from fastapi import FastAPI
from src.modules.auth.router import router as auth_router

app = FastAPI(
    title="Amrutam Telemedicine API",
    description="Production-grade Backend for Telemedicine",
    version="1.0.0"
)

# 1. Include the Auth Router
app.include_router(auth_router)

@app.get("/health")
def health_check():
    return {"status": "active", "service": "Amrutam API"}
  
@app.get("/")
def root():
    return {"message": "Welcome to Amrutam API. Go to /docs for Swagger UI"}