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

from app.services.quality_service import (
    calculate_severity
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/inspections",
    tags=["Inspections"]
)


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[3]
)


# ============================================================
# UPLOAD DIRECTORY
# ============================================================

UPLOAD_DIR = (
    PROJECT_ROOT
    / "backend"
    / "uploads"
)

UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# THRESHOLD DIRECTORY
# ============================================================

THRESHOLD_DIR = (
    PROJECT_ROOT
    / "models"
    / "thresholds"
)


# ============================================================
# CATEGORIES
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
# LOAD CATEGORY THRESHOLD
# ============================================================

def get_category_threshold(
    category: str
):

    category = (
        category
        .strip()
        .lower()
    )

    if category not in CATEGORIES:

        raise ValueError(
            f"Unsupported product category: "
            f"{category}"
        )

    threshold_file = (
        THRESHOLD_DIR
        / category
        / "threshold.txt"
    )

    if not threshold_file.exists():

        raise FileNotFoundError(
            f"Threshold file not found for "
            f"category '{category}'. "
            f"Expected: {threshold_file}"
        )

    try:

        threshold_text = (
            threshold_file
            .read_text(
                encoding="utf-8"
            )
            .strip()
        )

        threshold = float(
            threshold_text
        )

    except Exception as error:

        raise ValueError(
            f"Invalid threshold for "
            f"{category}: {error}"
        )

    if threshold <= 0:

        raise ValueError(
            f"Threshold must be greater than zero "
            f"for {category}. "
            f"Current value: {threshold}"
        )

    print(
        "=" * 70
    )

    print(
        "CALIBRATED THRESHOLD"
    )

    print(
        f"Category : {category}"
    )

    print(
        f"Threshold: {threshold:.12f}"
    )

    print(
        f"File     : {threshold_file}"
    )

    print(
        "=" * 70
    )

    return threshold


# ============================================================
# GET INSPECTIONS
# ============================================================

@router.get("/")
def get_inspections(
    current_user: User = Depends(
        get_current_user
    )
):

    try:

        db = get_database()

        collection = (
            db["inspections"]
        )

        user_id = str(
            current_user["id"]
        )

        inspections = list(
            collection.find(
                {
                    "user_id":
                        user_id
                }
            )
            .sort(
                "created_at",
                -1
            )
        )

        for inspection in inspections:

            inspection["_id"] = str(
                inspection["_id"]
            )

            inspection["id"] = (
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
# UPLOAD INSPECTION
# ============================================================

@router.post("/upload")
async def upload_inspection(

    file: UploadFile = File(...),

    category: str = Form(...),

    current_user: User = Depends(
        get_current_user
    )
):

    start_time = time.time()

    # ========================================================
    # CATEGORY
    # ========================================================

    category = (
        category
        .strip()
        .lower()
    )

    if category not in CATEGORIES:

        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported product category: "
                f"{category}"
            )
        )

    # ========================================================
    # FILE TYPE
    # ========================================================

    allowed_types = {

        "image/jpeg",
        "image/png",
        "image/bmp"
    }

    if file.content_type not in allowed_types:

        raise HTTPException(
            status_code=400,
            detail=(
                "Only JPG, PNG and BMP "
                "images are allowed."
            )
        )

    # ========================================================
    # FILE NAME
    # ========================================================

    original_filename = (
        file.filename
        or
        "product_image.png"
    )

    extension = (
        Path(
            original_filename
        )
        .suffix
        .lower()
    )

    if extension not in [
        ".jpg",
        ".jpeg",
        ".png",
        ".bmp"
    ]:

        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported image extension."
            )
        )

    unique_filename = (
        "inspection_"
        +
        uuid.uuid4().hex
        +
        extension
    )

    file_path = (
        UPLOAD_DIR
        /
        unique_filename
    )

    # ========================================================
    # SAVE FILE
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
    # IMAGE QUALITY
    # ========================================================

    try:

        quality = get_image_quality(
            image
        )

    except Exception as error:

        raise HTTPException(
            status_code=400,
            detail=(
                "Image quality analysis failed: "
                f"{error}"
            )
        )

    # ========================================================
    # PREPROCESSING
    # ========================================================

    try:

        processed_image = preprocess_image(
            image
        )

    except Exception as error:

        raise HTTPException(
            status_code=400,
            detail=(
                "Image preprocessing failed: "
                f"{error}"
            )
        )

    # ========================================================
    # THRESHOLD
    # ========================================================

    try:

        threshold = get_category_threshold(
            category
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to load calibrated "
                f"threshold: {error}"
            )
        )

    # ========================================================
    # PATCHCORE
    # ========================================================

    try:

        prediction = (
            predict_with_feature_bank(
                str(file_path),
                category
            )
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "PatchCore prediction failed: "
                f"{error}"
            )
        )

    # ========================================================
    # VALIDATE RESPONSE
    # ========================================================

    if not isinstance(
        prediction,
        dict
    ):

        raise HTTPException(
            status_code=500,
            detail=(
                "PatchCore returned an invalid response."
            )
        )

    # ========================================================
    # SCORE
    # ========================================================

    anomaly_score = prediction.get(
        "anomaly_score"
    )

    if anomaly_score is None:

        raise HTTPException(
            status_code=500,
            detail=(
                "PatchCore did not return "
                "anomaly_score."
            )
        )

    try:

        anomaly_score = float(
            anomaly_score
        )

    except Exception:

        raise HTTPException(
            status_code=500,
            detail=(
                "Invalid anomaly score."
            )
        )

    # ========================================================
    # FINAL CLASSIFICATION
    # ========================================================

    if anomaly_score >= threshold:

        result = "DEFECT"

    else:

        result = "NORMAL"

    # ========================================================
    # QUALITY ASSESSMENT
    # ========================================================

    try:

        quality_assessment = (
            calculate_severity(
                anomaly_score=
                    anomaly_score,

                threshold=
                    threshold,

                result=
                    result,

                category=
                    category
            )
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "Quality assessment failed: "
                f"{error}"
            )
        )

    # ========================================================
    # MODEL
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
        -
        start_time
    )

    # ========================================================
    # DATABASE DOCUMENT
    # ========================================================

    inspection_document = {

        "image_path":
            str(file_path),

        "filename":
            unique_filename,

        "category":
            category,

        "status":
            "completed",

        "result":
            result,

        "anomaly_score":
            anomaly_score,

        "threshold":
            threshold,

        "quality_assessment":
            quality_assessment,

        "user_id":
            str(
                current_user["id"]
            ),

        "uploaded_by":
            current_user["name"],

        "model":
            model_name,

        "device":
            device,

        # ----------------------------------------------------
        # IMAGE QUALITY
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # PATCHCORE DETAILS
        # ----------------------------------------------------

        "patchcore": {

            "max_distance":
                prediction.get(
                    "max_distance"
                ),

            "mean_distance":
                prediction.get(
                    "mean_distance"
                ),

            "top_1_distance":
                prediction.get(
                    "top_1_distance"
                ),

            "top_5_distance":
                prediction.get(
                    "top_5_distance"
                ),

            "top_10_distance":
                prediction.get(
                    "top_10_distance"
                ),

            "defect_area_percentage":
                prediction.get(
                    "defect_area_percentage"
                ),

            "location":
                prediction.get(
                    "location"
                ),

            "bounding_box":
                prediction.get(
                    "bounding_box"
                )
        },

        # ----------------------------------------------------
        # PREPROCESSING
        # ----------------------------------------------------

        "preprocessing": {

            "output_size":
                list(
                    processed_image.shape
                ),

            "normalization":
                "0-1"
        },

        # ----------------------------------------------------
        # PROCESSING TIME
        # ----------------------------------------------------

        "processing_time_seconds":
            round(
                processing_time,
                4
            ),

        # ----------------------------------------------------
        # CREATED
        # ----------------------------------------------------

        "created_at":
            time.time()
    }

    # ========================================================
    # SAVE DATABASE
    # ========================================================

    try:

        db = get_database()

        collection = (
            db["inspections"]
        )

        insert_result = (
            collection.insert_one(
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
                "Failed to save inspection record: "
                f"{error}"
            )
        )

    # ========================================================
    # RESPONSE
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
            threshold,

        "quality_assessment":
            quality_assessment,

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

        "patchcore": {

            "max_distance":
                prediction.get(
                    "max_distance"
                ),

            "mean_distance":
                prediction.get(
                    "mean_distance"
                ),

            "top_1_distance":
                prediction.get(
                    "top_1_distance"
                ),

            "top_5_distance":
                prediction.get(
                    "top_5_distance"
                ),

            "top_10_distance":
                prediction.get(
                    "top_10_distance"
                ),

            "defect_area_percentage":
                prediction.get(
                    "defect_area_percentage"
                ),

            "location":
                prediction.get(
                    "location"
                ),

            "bounding_box":
                prediction.get(
                    "bounding_box"
                )
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