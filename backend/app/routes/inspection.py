from fastapi import (
    APIRouter,
    Depends,
    UploadFile,
    File,
    Form,
    HTTPException
)

from pathlib import Path
import shutil
import uuid
import time
import json

from app.database import get_database
from app.models.user import User
from app.dependencies import get_current_user

from app.services.image_service import (
    load_image,
    get_image_quality,
    preprocess_image
)

from app.ai.patchcore_model import (
    predict_with_feature_bank
)


router = APIRouter(
    prefix="/inspections",
    tags=["Inspections"]
)


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

UPLOAD_DIR = PROJECT_ROOT / "backend" / "uploads"

UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True
)

THRESHOLD_FILE = (
    PROJECT_ROOT
    / "models"
    / "patchcore_thresholds.json"
)


# ============================================================
# SUPPORTED PRODUCT CATEGORIES
# ============================================================

CATEGORIES = [
    "bottle",
    "cable",
    "capsule",
    "carpet",
    "grid",
    "hazelnut",
    "leather",
    "metal_nut",
    "pill",
    "screw",
    "tile",
    "toothbrush",
    "transistor",
    "wood",
    "zipper"
]


# ============================================================
# LOAD CALIBRATED PATCHCORE THRESHOLDS
# ============================================================

def load_patchcore_thresholds():

    if not THRESHOLD_FILE.exists():

        raise FileNotFoundError(
            "PatchCore threshold file not found: "
            f"{THRESHOLD_FILE}"
        )

    with open(
        THRESHOLD_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        thresholds = json.load(file)

    return thresholds


# ============================================================
# GET CATEGORY-SPECIFIC THRESHOLD
# ============================================================

def get_category_threshold(category: str):

    thresholds = load_patchcore_thresholds()

    categories_data = thresholds.get("categories")

    if not isinstance(categories_data, dict):

        raise ValueError(
            "Invalid PatchCore threshold file format. "
            "'categories' section is missing."
        )

    if category not in categories_data:

        raise ValueError(
            f"No calibrated threshold found "
            f"for category: {category}"
        )

    category_data = categories_data[category]

    if isinstance(category_data, dict):

        threshold = category_data.get("threshold")

        if threshold is None:

            raise ValueError(
                f"Threshold missing for "
                f"category: {category}"
            )

        return float(threshold)

    return float(category_data)


# ============================================================
# GET ALL USER INSPECTIONS
# ============================================================

@router.get("/")
def get_inspections(
    current_user: User = Depends(get_current_user)
):

    try:

        db = get_database()

        inspections_collection = db["inspections"]

        # MongoDB-compatible user access
        user_id = str(current_user["id"])

        inspections = list(
            inspections_collection.find(
                {
                    "user_id": user_id
                }
            ).sort(
                "created_at",
                -1
            )
        )

        # Convert MongoDB ObjectId to string
        for inspection in inspections:

            inspection["_id"] = str(
                inspection["_id"]
            )

        return inspections

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to fetch inspections: "
                f"{error}"
            )
        )


# ============================================================
# UPLOAD + PATCHCORE AI INSPECTION
# ============================================================

@router.post("/upload")
async def upload_inspection(

    file: UploadFile = File(...),

    category: str = Form(...),

    current_user: User = Depends(get_current_user)
):

    start_time = time.time()


    # ========================================================
    # CATEGORY VALIDATION
    # ========================================================

    category = category.strip().lower()

    if category not in CATEGORIES:

        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported product category: "
                f"{category}"
            )
        )


    # ========================================================
    # FILE TYPE VALIDATION
    # ========================================================

    allowed_types = [
        "image/jpeg",
        "image/png",
        "image/bmp"
    ]

    if file.content_type not in allowed_types:

        raise HTTPException(
            status_code=400,
            detail=(
                "Only JPG, PNG and BMP "
                "images are allowed."
            )
        )


    # ========================================================
    # ORIGINAL FILE NAME
    # ========================================================

    original_filename = (
        file.filename
        or "product_image.png"
    )


    # ========================================================
    # FILE EXTENSION
    # ========================================================

    file_extension = (
        Path(original_filename)
        .suffix
        .lower()
    )

    if not file_extension:

        file_extension = ".png"


    # ========================================================
    # UNIQUE FILE NAME
    # ========================================================

    unique_filename = (
        "inspection_"
        f"{uuid.uuid4().hex}"
        f"{file_extension}"
    )

    file_path = (
        UPLOAD_DIR
        / unique_filename
    )


    # ========================================================
    # SAVE UPLOADED IMAGE
    # ========================================================

    try:

        with open(
            file_path,
            "wb"
        ) as buffer:

            shutil.copyfileobj(
                file.file,
                buffer
            )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to save uploaded image: "
                f"{error}"
            )
        )


    # ========================================================
    # LOAD IMAGE
    # ========================================================

    try:

        image = load_image(
            str(file_path)
        )

    except Exception as error:

        if file_path.exists():
            file_path.unlink()

        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid image file: "
                f"{error}"
            )
        )


    # ========================================================
    # IMAGE QUALITY ANALYSIS
    # ========================================================

    try:

        quality = get_image_quality(
            image
        )

    except Exception as error:

        raise HTTPException(
            status_code=400,
            detail=(
                "Image quality analysis "
                f"failed: {error}"
            )
        )


    # ========================================================
    # IMAGE PREPROCESSING
    # ========================================================

    try:

        processed_image = preprocess_image(
            image
        )

    except Exception as error:

        raise HTTPException(
            status_code=400,
            detail=(
                "Image preprocessing "
                f"failed: {error}"
            )
        )


    # ========================================================
    # LOAD CATEGORY-SPECIFIC THRESHOLD
    # ========================================================

    try:

        threshold = get_category_threshold(
            category
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to load PatchCore "
                f"threshold: {error}"
            )
        )


    # ========================================================
    # PATCHCORE AI PREDICTION
    # ========================================================

    try:

        prediction = predict_with_feature_bank(
            str(file_path),
            category
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "PatchCore AI prediction failed: "
                f"{error}"
            )
        )


    # ========================================================
    # VALIDATE PATCHCORE RESPONSE
    # ========================================================

    if not isinstance(
        prediction,
        dict
    ):

        raise HTTPException(
            status_code=500,
            detail=(
                "Invalid response returned "
                "by PatchCore model."
            )
        )


    # ========================================================
    # GET ANOMALY SCORE
    # ========================================================

    anomaly_score = prediction.get(
        "anomaly_score"
    )

    if anomaly_score is None:

        anomaly_score = prediction.get(
            "score"
        )

    if anomaly_score is None:

        raise HTTPException(
            status_code=500,
            detail=(
                "PatchCore did not return "
                "anomaly score."
            )
        )


    # ========================================================
    # CONVERT SCORE TO FLOAT
    # ========================================================

    try:

        anomaly_score = float(
            anomaly_score
        )

    except Exception:

        raise HTTPException(
            status_code=500,
            detail=(
                "Invalid anomaly score "
                "returned by PatchCore."
            )
        )


    # ========================================================
    # CLASSIFY NORMAL / DEFECT
    # ========================================================

    if anomaly_score >= threshold:

        result = "DEFECT"

    else:

        result = "NORMAL"


    # ========================================================
    # MODEL INFORMATION
    # ========================================================

    model_name = prediction.get(
        "model",
        "PatchCore-Style Multi-Scale ResNet18"
    )

    device = prediction.get(
        "device",
        "cpu"
    )


    # ========================================================
    # PROCESSING TIME
    # ========================================================

    processing_time = (
        time.time()
        - start_time
    )


    # ========================================================
    # MONGODB RECORD
    # ========================================================

    inspection_document = {

        "image_path": str(
            file_path
        ),

        "filename": unique_filename,

        "category": category,

        "status": "completed",

        "result": result,

        "anomaly_score": anomaly_score,

        "threshold": threshold,

        "user_id": str(
            current_user["id"]
        ),

        "uploaded_by": current_user["name"],

        "model": model_name,

        "device": device,

        "image_quality": {

            "width": quality["width"],

            "height": quality["height"],

            "brightness": quality["brightness"],

            "sharpness": quality["sharpness"]
        },

        "preprocessing": {

            "output_size": list(
                processed_image.shape
            ),

            "normalization": "0-1"
        },

        "processing_time_seconds": round(
            processing_time,
            4
        ),

        "created_at": time.time()
    }


    # ========================================================
    # SAVE TO MONGODB
    # ========================================================

    try:

        db = get_database()

        inspections_collection = db["inspections"]

        insert_result = (
            inspections_collection.insert_one(
                inspection_document
            )
        )

        inspection_id = str(
            insert_result.inserted_id
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to save inspection "
                f"record: {error}"
            )
        )


    # ========================================================
    # FINAL RESPONSE
    # ========================================================

    return {

        "message":
            "Image inspected successfully",

        "inspection_id":
            inspection_id,

        "filename":
            unique_filename,

        "category":
            category,

        "status":
            "completed",

        "result":
            result,

        "anomaly_score":
            round(
                anomaly_score,
                6
            ),

        "threshold":
            round(
                threshold,
                6
            ),

        "uploaded_by":
            current_user["name"],

        "user_id":
            str(
                current_user["id"]
            ),

        "model":
            model_name,

        "device":
            device,

        "image_quality": {

            "width":
                quality["width"],

            "height":
                quality["height"],

            "brightness":
                quality["brightness"],

            "sharpness":
                quality["sharpness"]
        },

        "preprocessing": {

            "output_size":
                list(
                    processed_image.shape
                ),

            "normalization":
                "0-1"
        },

        "processing_time_seconds":
            round(
                processing_time,
                4
            )
    }

