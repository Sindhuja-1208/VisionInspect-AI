from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routes import auth
from app.routes import inspection


app = FastAPI(
    title="VisionInspect AI",
    description="AI-powered Manufacturing Defect Detection & Quality Inspection System",
    version="1.0.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# STATIC FILES - UPLOADED INSPECTION IMAGES
# ============================================================

app.mount(
    "/uploads",
    StaticFiles(directory="uploads"),
    name="uploads"
)


# ============================================================
# ROUTES
# ============================================================

app.include_router(
    auth.router
)

app.include_router(
    inspection.router
)


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    return {
        "message": "VisionInspect AI Backend is running",
        "status": "success"
    }