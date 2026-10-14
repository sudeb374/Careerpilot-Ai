from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers.admin_ingestion import router as admin_ingestion_router
from app.routers.admin_opportunity import router as admin_opportunity_router
from app.routers.application import router as application_router
from app.routers.copilot import router as copilot_router
from app.routers.opportunity import router as opportunity_router
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
app.include_router(opportunity_router)
app.include_router(admin_opportunity_router)
app.include_router(admin_ingestion_router)
app.include_router(copilot_router)
app.include_router(application_router)


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
