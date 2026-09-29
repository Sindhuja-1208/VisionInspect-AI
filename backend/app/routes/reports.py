from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from datetime import datetime

from app.database import get_database
from app.dependencies import get_current_user


router = APIRouter(
    prefix="/reports",
    tags=["Production Reports"]
)


# ============================================================
# HELPERS
# ============================================================

def get_user_id(current_user):
    """
    Supports both dictionary-style and object-style
    current_user values.
    """

    if isinstance(current_user, dict):
        return str(current_user.get("id"))

    return str(current_user.id)


def format_category(category):
    if not category:
        return "Unknown"

    return str(category).replace("_", " ").title()


def format_created_at(value):
    """
    Convert MongoDB stored Unix timestamp into
    a readable date/time.
    """

    if value is None:
        return "Not available"

    try:
        return datetime.fromtimestamp(
            float(value)
        ).strftime(
            "%d %b %Y, %I:%M %p"
        )

    except Exception:
        return str(value)


def build_quality_summary(inspection):
    """
    Uses the existing quality_assessment information
    when available.

    Older inspection records may not contain this field,
    so a safe fallback is provided.
    """

    quality_assessment = inspection.get(
        "quality_assessment"
    )

    if isinstance(
        quality_assessment,
        dict
    ):
        return quality_assessment

    result = str(
        inspection.get(
            "result",
            "UNKNOWN"
        )
    ).upper()

    if result == "NORMAL":

        return {
            "severity_score": 0,
            "severity_level": "Low",
            "quality_risk": "Low",
            "defect_type": "No defect detected",
            "recommended_action": (
                "Product can proceed to the next "
                "quality-control stage."
            )
        }

    if result in [
        "DEFECT",
        "DEFECTIVE"
    ]:

        return {
            "severity_score": None,
            "severity_level": "Assessment Required",
            "quality_risk": "Review Required",
            "defect_type": "Visual Anomaly",
            "recommended_action": (
                "Perform additional quality inspection "
                "and verify the detected anomaly."
            )
        }

    return {
        "severity_score": None,
        "severity_level": "Not Available",
        "quality_risk": "Not Available",
        "defect_type": "Not Available",
        "recommended_action": (
            "Review the inspection result."
        )
    }


def build_report(inspection):
    """
    Converts an inspection document into a
    production-quality report structure.
    """

    quality = inspection.get(
        "image_quality",
        {}
    )

    preprocessing = inspection.get(
        "preprocessing",
        {}
    )

    quality_assessment = build_quality_summary(
        inspection
    )

    result = str(
        inspection.get(
            "result",
            "UNKNOWN"
        )
    ).upper()

    anomaly_score = inspection.get(
        "anomaly_score"
    )

    threshold = inspection.get(
        "threshold"
    )

    processing_time = inspection.get(
        "processing_time_seconds"
    )

    report = {

        "report_title":
            "VisionInspect-AI Production Quality Report",

        "report_version":
            "1.0",

        "inspection": {

            "inspection_id":
                str(
                    inspection.get(
                        "_id",
                        ""
                    )
                ),

            "filename":
                inspection.get(
                    "filename",
                    "Unknown"
                ),

            "product_category":
                format_category(
                    inspection.get(
                        "category"
                    )
                ),

            "status":
                inspection.get(
                    "status",
                    "Unknown"
                ),

            "result":
                result,

            "inspected_by":
                inspection.get(
                    "uploaded_by",
                    "Unknown"
                ),

            "created_at":
                format_created_at(
                    inspection.get(
                        "created_at"
                    )
                )
        },

        "ai_analysis": {

            "model":
                inspection.get(
                    "model",
                    "PatchCore-Style Multi-Scale ResNet18"
                ),

            "detection_method":
                "Feature Memory Bank",

            "anomaly_score":
                round(
                    float(anomaly_score),
                    6
                )
                if anomaly_score is not None
                else None,

            "category_threshold":
                round(
                    float(threshold),
                    6
                )
                if threshold is not None
                else None,

            "classification":
                result,

            "device":
                inspection.get(
                    "device",
                    "cpu"
                )
        },

        "quality_assessment": {

            "severity_score":
                quality_assessment.get(
                    "severity_score"
                ),

            "severity_level":
                quality_assessment.get(
                    "severity_level",
                    "Not Available"
                ),

            "quality_risk":
                quality_assessment.get(
                    "quality_risk",
                    "Not Available"
                ),

            "defect_type":
                quality_assessment.get(
                    "defect_type",
                    "Not Available"
                ),

            "recommended_action":
                quality_assessment.get(
                    "recommended_action",
                    "Review inspection result."
                )
        },

        "image_quality": {

            "width":
                quality.get(
                    "width"
                ),

            "height":
                quality.get(
                    "height"
                ),

            "brightness":
                quality.get(
                    "brightness"
                ),

            "sharpness":
                quality.get(
                    "sharpness"
                )
        },

        "preprocessing": {

            "output_size":
                preprocessing.get(
                    "output_size"
                ),

            "normalization":
                preprocessing.get(
                    "normalization",
                    "0-1"
                )
        },

        "processing": {

            "processing_time_seconds":
                processing_time
        }
    }

    return report


# ============================================================
# GET ALL PRODUCTION REPORTS
# ============================================================

@router.get("/")
def get_reports(
    current_user=Depends(
        get_current_user
    )
):

    try:

        db = get_database()

        inspections_collection = db[
            "inspections"
        ]

        user_id = get_user_id(
            current_user
        )

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

        reports = []

        for inspection in inspections:

            inspection["_id"] = str(
                inspection["_id"]
            )

            reports.append(
                build_report(
                    inspection
                )
            )

        return {
            "total_reports":
                len(reports),

            "reports":
                reports
        }

    except Exception as error:

        raise HTTPException(

            status_code=500,

            detail=(
                "Failed to generate "
                f"production reports: {error}"
            )
        )


# ============================================================
# GET SINGLE PRODUCTION REPORT
# ============================================================

@router.get("/{inspection_id}")
def get_single_report(
    inspection_id: str,
    current_user=Depends(
        get_current_user
    )
):

    try:

        if not ObjectId.is_valid(
            inspection_id
        ):

            raise HTTPException(

                status_code=400,

                detail="Invalid inspection ID."
            )

        db = get_database()

        inspections_collection = db[
            "inspections"
        ]

        user_id = get_user_id(
            current_user
        )

        inspection = (
            inspections_collection.find_one(
                {
                    "_id":
                        ObjectId(
                            inspection_id
                        ),

                    "user_id":
                        user_id
                }
            )
        )

        if not inspection:

            raise HTTPException(

                status_code=404,

                detail=(
                    "Inspection report "
                    "not found."
                )
            )

        inspection["_id"] = str(
            inspection["_id"]
        )

        return build_report(
            inspection
        )

    except HTTPException:
        raise

    except Exception as error:

        raise HTTPException(

            status_code=500,

            detail=(
                "Failed to generate "
                f"production report: {error}"
            )
        )