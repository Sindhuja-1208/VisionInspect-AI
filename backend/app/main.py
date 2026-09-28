from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.routes import auth
from app.routes import inspection
from app.routes import analytics


# ============================================================
# VISIONINSPECT AI
# MAIN FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="VisionInspect AI",
    description=(
        "AI-powered Manufacturing Defect Detection "
        "& Quality Inspection System"
    ),
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
# PROJECT PATHS
# ============================================================

# main.py location:
#
# VisionInspect-AI/
# └── backend/
#     └── app/
#         └── main.py
#
# parents[0] = app
# parents[1] = backend
# parents[2] = VisionInspect-AI

PROJECT_ROOT = Path(__file__).resolve().parents[2]

UPLOAD_DIR = PROJECT_ROOT / "backend" / "uploads"

UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# STATIC FILES
# SERVE UPLOADED INSPECTION IMAGES
# ============================================================

app.mount(
    "/uploads",
    StaticFiles(
        directory=str(UPLOAD_DIR)
    ),
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

app.include_router(
    analytics.router
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