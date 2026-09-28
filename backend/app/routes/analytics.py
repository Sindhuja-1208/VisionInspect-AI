from fastapi import APIRouter, Depends, HTTPException
from app.database import get_database
from app.dependencies import get_current_user


router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"]
)


@router.get("/summary")
def get_analytics_summary(
    current_user=Depends(get_current_user)
):
    try:
        db = get_database()
        inspections_collection = db["inspections"]

        # ----------------------------------------------------
        # GET USER ID SAFELY
        # ----------------------------------------------------

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

        user_id = str(user_id)

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
                item.get("result", "")
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
                    category_severity[category] = []

                category_severity[category].append(
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

                category_average_severity[category] = round(
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

            "total_inspections": total,

            "normal_products": normal,

            "defects_detected": defects,

            "normal_rate": normal_rate,

            "defect_rate": defect_rate,

            "overall_quality_status":
                overall_quality_status,

            "severity": severity,

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