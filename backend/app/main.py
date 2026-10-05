from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers.profile import router as profile_router
from app.routers.skills import router as skills_router

app = FastAPI(
    title="CareerPilot AI API",
    description="AI-powered career discovery and internship matching platform",
    version="0.1.0",
)

# CORS — allow the frontend to communicate with the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(profile_router)
app.include_router(skills_router)


@app.get("/")
def root():
    return {
        "message": "Welcome to CareerPilot AI API",
        "status": "running",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "careerpilot-ai-backend",
    }
