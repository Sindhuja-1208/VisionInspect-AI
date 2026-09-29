from fastapi import APIRouter, Depends, HTTPException
from app.database import get_database
from app.dependencies import get_current_user

from datetime import datetime, date


router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"]
)


# ============================================================
# HELPER: GET AUTHENTICATED USER ID
# ============================================================

def get_authenticated_user_id(current_user):

    if isinstance(current_user, dict):

        user_id = (
            current_user.get("id")
            or current_user.get("_id")
            or current_user.get("user_id")
        )

    else:

        user_id = (
            getattr(current_user, "id", None)
            or getattr(current_user, "_id", None)
            or getattr(current_user, "user_id", None)
        )

    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="Unable to identify authenticated user"
        )

    return str(user_id)


# ============================================================
# HELPER: NORMALIZE DATE
# ============================================================

def get_date_key(value):

    if value is None:
        return None

    try:

        # MongoDB datetime
        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%d")

        # Python date
        if isinstance(value, date):
            return value.strftime("%Y-%m-%d")

        # Unix timestamp
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(
                float(value)
            ).strftime("%Y-%m-%d")

        # String value
        value = str(value).strip()

        if not value:
            return None

        # ISO datetime
        try:
            parsed = datetime.fromisoformat(
                value.replace("Z", "+00:00")
            )

            return parsed.strftime("%Y-%m-%d")

        except Exception:
            pass

        # Try common date formats
        formats = [
            "%Y-%m-%d",
            "%d-%m-%Y",
            "%d/%m/%Y",
            "%Y/%m/%d",
            "%d %b %Y",
            "%d %B %Y"
        ]

        for fmt in formats:

            try:

                parsed = datetime.strptime(
                    value,
                    fmt
                )

                return parsed.strftime("%Y-%m-%d")

            except Exception:
                continue

    except Exception:
        pass

    return None


# ============================================================
# ANALYTICS SUMMARY
# ============================================================

@router.get("/summary")
def get_analytics_summary(
    current_user=Depends(get_current_user)
):

    try:

        db = get_database()
        inspections_collection = db["inspections"]

        # ----------------------------------------------------
        # USER ID
        # ----------------------------------------------------

        user_id = get_authenticated_user_id(
            current_user
        )

        # ----------------------------------------------------
        # GET USER INSPECTIONS
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # BASIC COUNTS
        # ----------------------------------------------------

        total = len(inspections)

        normal = 0
        defects = 0

        for item in inspections:

            result = str(
                item.get(
                    "result",
                    ""
                )
            ).upper()

            if result == "NORMAL":

                normal += 1

            elif result in [
                "DEFECT",
                "DEFECTIVE"
            ]:

                defects += 1

        # ----------------------------------------------------
        # RATES
        # ----------------------------------------------------

        normal_rate = (
            round(
                normal / total * 100,
                2
            )
            if total
            else 0
        )

        defect_rate = (
            round(
                defects / total * 100,
                2
            )
            if total
            else 0
        )

        # ----------------------------------------------------
        # SEVERITY
        # ----------------------------------------------------

        severity = {

            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "pending": 0

        }

        severity_scores = []

        # ----------------------------------------------------
        # CATEGORY DATA
        # ----------------------------------------------------

        category_counts = {}
        category_defects = {}
        category_severity = {}

        # ----------------------------------------------------
        # PROCESS INSPECTIONS
        # ----------------------------------------------------

        for item in inspections:

            category = str(
                item.get(
                    "category",
                    "Unknown"
                )
            )

            category_counts[category] = (
                category_counts.get(
                    category,
                    0
                ) + 1
            )

            result = str(
                item.get(
                    "result",
                    ""
                )
            ).upper()

            if result in [
                "DEFECT",
                "DEFECTIVE"
            ]:

                category_defects[category] = (
                    category_defects.get(
                        category,
                        0
                    ) + 1
                )

            # ------------------------------------------------
            # QUALITY ASSESSMENT
            # ------------------------------------------------

            assessment = item.get(
                "quality_assessment"
            )

            if not isinstance(
                assessment,
                dict
            ):

                severity["pending"] += 1

                continue

            # ------------------------------------------------
            # SEVERITY LEVEL
            # ------------------------------------------------

            level = str(
                assessment.get(
                    "severity_level",
                    ""
                )
            ).lower()

            if level == "critical":

                severity["critical"] += 1

            elif level == "high":

                severity["high"] += 1

            elif level == "medium":

                severity["medium"] += 1

            elif level == "low":

                severity["low"] += 1

            else:

                severity["pending"] += 1

            # ------------------------------------------------
            # SEVERITY SCORE
            # ------------------------------------------------

            score = assessment.get(
                "severity_score"
            )

            if isinstance(
                score,
                (int, float)
            ):

                score = float(score)

                severity_scores.append(
                    score
                )

                if category not in category_severity:

                    category_severity[
                        category
                    ] = []

                category_severity[
                    category
                ].append(
                    score
                )

        # ----------------------------------------------------
        # AVERAGE SEVERITY
        # ----------------------------------------------------

        average_severity = (

            round(
                sum(severity_scores)
                / len(severity_scores),
                2
            )

            if severity_scores
            else 0

        )

        # ----------------------------------------------------
        # CATEGORY DEFECT RATES
        # ----------------------------------------------------

        category_defect_rates = {}

        for category, count in category_counts.items():

            category_defect_rates[category] = round(
                (
                    category_defects.get(
                        category,
                        0
                    )
                    / count
                ) * 100,
                2
            )

        # ----------------------------------------------------
        # CATEGORY AVERAGE SEVERITY
        # ----------------------------------------------------

        category_average_severity = {}

        for category, scores in category_severity.items():

            if scores:

                category_average_severity[
                    category
                ] = round(
                    sum(scores)
                    / len(scores),
                    2
                )

        # ----------------------------------------------------
        # RECENT INSPECTIONS
        # ----------------------------------------------------

        recent_inspections = []

        for item in inspections[:10]:

            assessment = item.get(
                "quality_assessment"
            )

            if not isinstance(
                assessment,
                dict
            ):

                assessment = {}

            recent_inspections.append({

                "id": str(
                    item.get(
                        "_id",
                        ""
                    )
                ),

                "category": item.get(
                    "category",
                    "Unknown"
                ),

                "result": item.get(
                    "result",
                    "PENDING"
                ),

                "anomaly_score": float(
                    item.get(
                        "anomaly_score",
                        0
                    ) or 0
                ),

                "threshold": float(
                    item.get(
                        "threshold",
                        0
                    ) or 0
                ),

                "severity_level": assessment.get(
                    "severity_level",
                    "Pending"
                ),

                "severity_score": float(
                    assessment.get(
                        "severity_score",
                        0
                    ) or 0
                ),

                "created_at": item.get(
                    "created_at"
                )

            })

        # ----------------------------------------------------
        # OVERALL QUALITY STATUS
        # ----------------------------------------------------

        if total == 0:

            overall_quality_status = (
                "No Inspections"
            )

        elif defects == 0:

            overall_quality_status = (
                "All Products Normal"
            )

        elif defect_rate < 20:

            overall_quality_status = (
                "Quality Stable"
            )

        elif defect_rate < 50:

            overall_quality_status = (
                "Quality Attention Required"
            )

        else:

            overall_quality_status = (
                "High Defect Activity"
            )

        # ----------------------------------------------------
        # RESPONSE
        # ----------------------------------------------------

        return {

            "total_inspections":
                total,

            "normal_products":
                normal,

            "defects_detected":
                defects,

            "normal_rate":
                normal_rate,

            "defect_rate":
                defect_rate,

            "overall_quality_status":
                overall_quality_status,

            "severity":
                severity,

            "severity_distribution":
                severity,

            "average_severity_score":
                average_severity,

            "average_severity":
                average_severity,

            "category_counts":
                category_counts,

            "category_defects":
                category_defects,

            "category_defect_rates":
                category_defect_rates,

            "category_average_severity":
                category_average_severity,

            "recent_inspections":
                recent_inspections

        }

    except HTTPException:

        raise

    except Exception as error:

        print(
            "ANALYTICS ERROR:",
            repr(error)
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to generate analytics: "
                f"{error}"
            )
        )


# ============================================================
# TREND MONITORING
# ============================================================

@router.get("/trends")
def get_analytics_trends(
    current_user=Depends(get_current_user)
):

    try:

        db = get_database()
        inspections_collection = db["inspections"]

        # ----------------------------------------------------
        # USER ID
        # ----------------------------------------------------

        user_id = get_authenticated_user_id(
            current_user
        )

        # ----------------------------------------------------
        # GET USER INSPECTIONS
        # ----------------------------------------------------

        inspections = list(
            inspections_collection.find(
                {
                    "user_id": user_id
                }
            ).sort(
                "created_at",
                1
            )
        )

        # ====================================================
        # DAILY TREND
        # ====================================================

        daily_data = {}

        for item in inspections:

            date_key = get_date_key(
                item.get("created_at")
            )

            if not date_key:
                continue

            if date_key not in daily_data:

                daily_data[date_key] = {

                    "date": date_key,

                    "total": 0,

                    "normal": 0,

                    "defect": 0

                }

            daily_data[date_key]["total"] += 1

            result = str(
                item.get(
                    "result",
                    ""
                )
            ).upper()

            if result == "NORMAL":

                daily_data[
                    date_key
                ]["normal"] += 1

            elif result in [
                "DEFECT",
                "DEFECTIVE"
            ]:

                daily_data[
                    date_key
                ]["defect"] += 1

        # Convert dictionary to sorted list

        daily_trend = sorted(
            daily_data.values(),
            key=lambda item: item["date"]
        )

        # ====================================================
        # ADD DEFECT RATE TO DAILY TREND
        # ====================================================

        for item in daily_trend:

            total = item["total"]

            if total:

                item["defect_rate"] = round(
                    (
                        item["defect"]
                        / total
                    ) * 100,
                    2
                )

                item["normal_rate"] = round(
                    (
                        item["normal"]
                        / total
                    ) * 100,
                    2
                )

            else:

                item["defect_rate"] = 0
                item["normal_rate"] = 0

        # ====================================================
        # CATEGORY TREND
        # ====================================================

        category_data = {}

        for item in inspections:

            category = str(
                item.get(
                    "category",
                    "Unknown"
                )
            )

            if category not in category_data:

                category_data[category] = {

                    "category": category,

                    "total": 0,

                    "normal": 0,

                    "defect": 0

                }

            category_data[
                category
            ]["total"] += 1

            result = str(
                item.get(
                    "result",
                    ""
                )
            ).upper()

            if result == "NORMAL":

                category_data[
                    category
                ]["normal"] += 1

            elif result in [
                "DEFECT",
                "DEFECTIVE"
            ]:

                category_data[
                    category
                ]["defect"] += 1

        # ----------------------------------------------------
        # CATEGORY RATES
        # ----------------------------------------------------

        category_trend = []

        for category, data in category_data.items():

            total = data["total"]

            defect_rate = (

                round(
                    (
                        data["defect"]
                        / total
                    ) * 100,
                    2
                )

                if total
                else 0

            )

            normal_rate = (

                round(
                    (
                        data["normal"]
                        / total
                    ) * 100,
                    2
                )

                if total
                else 0

            )

            category_trend.append({

                "category":
                    category,

                "total":
                    total,

                "normal":
                    data["normal"],

                "defect":
                    data["defect"],

                "normal_rate":
                    normal_rate,

                "defect_rate":
                    defect_rate

            })

        # Sort by total inspections

        category_trend.sort(
            key=lambda item: item["total"],
            reverse=True
        )

        # ====================================================
        # OVERALL SUMMARY
        # ====================================================

        total_inspections = len(
            inspections
        )

        normal_inspections = 0
        defective_inspections = 0

        for item in inspections:

            result = str(
                item.get(
                    "result",
                    ""
                )
            ).upper()

            if result == "NORMAL":

                normal_inspections += 1

            elif result in [
                "DEFECT",
                "DEFECTIVE"
            ]:

                defective_inspections += 1

        defect_rate = (

            round(
                (
                    defective_inspections
                    / total_inspections
                ) * 100,
                2
            )

            if total_inspections
            else 0

        )

        normal_rate = (

            round(
                (
                    normal_inspections
                    / total_inspections
                ) * 100,
                2
            )

            if total_inspections
            else 0

        )

        # ====================================================
        # RESPONSE
        # ====================================================

        return {

            "summary": {

                "total_inspections":
                    total_inspections,

                "normal_inspections":
                    normal_inspections,

                "defective_inspections":
                    defective_inspections,

                "normal_rate":
                    normal_rate,

                "defect_rate":
                    defect_rate

            },

            "daily_trend":
                daily_trend,

            "category_trend":
                category_trend

        }

    except HTTPException:

        raise

    except Exception as error:

        print(
            "TREND ANALYTICS ERROR:",
            repr(error)
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to generate trend analytics: "
                f"{error}"
            )
        )