# ============================================================
# VISIONINSPECT AI
# QUALITY ASSESSMENT SERVICE
#
# MILESTONE 3
# Step 1 - Defect Categorization
# Step 2 - Severity & Quality Risk Assessment
# ============================================================

from typing import Any, Dict, Optional


# ============================================================
# SEVERITY WEIGHTS
#
# Project requirement:
#
# Defect Size       = 30%
# Defect Location   = 25%
# Defect Type       = 25%
# Confidence        = 20%
# ============================================================

SIZE_WEIGHT = 0.30
LOCATION_WEIGHT = 0.25
DEFECT_TYPE_WEIGHT = 0.25
CONFIDENCE_WEIGHT = 0.20


# ============================================================
# SEVERITY LEVELS
# ============================================================

def get_severity_level(score: float) -> str:

    score = float(score)

    if score >= 80:
        return "Critical"

    if score >= 60:
        return "High"

    if score >= 40:
        return "Medium"

    return "Low"


# ============================================================
# QUALITY RISK
# ============================================================

def get_quality_risk(
    severity_level: str,
    is_defect: bool
) -> str:

    if not is_defect:
        return "Low"

    if severity_level == "Critical":
        return "Critical"

    if severity_level == "High":
        return "High"

    if severity_level == "Medium":
        return "Medium"

    return "Low"


# ============================================================
# RECOMMENDED ACTION
# ============================================================

def get_recommended_action(
    severity_level: str,
    is_defect: bool
) -> str:

    if not is_defect:

        return (
            "Product meets the current quality inspection criteria."
        )

    if severity_level == "Critical":

        return (
            "Reject product and perform immediate "
            "quality-control investigation."
        )

    if severity_level == "High":

        return (
            "Hold product for detailed manual inspection "
            "before release."
        )

    if severity_level == "Medium":

        return (
            "Perform additional quality inspection and "
            "verify the detected anomaly."
        )

    return (
        "Review the product manually before final "
        "quality approval."
    )


# ============================================================
# DEFECT TYPE SCORE
# ============================================================
#
# These values represent the seriousness of the defect
# category.
#
# Higher score = more serious defect type.
# ============================================================

DEFECT_TYPE_SCORES = {

    # High severity structural defects
    "Crack": 95.0,
    "Missing Component": 95.0,
    "Broken Component": 95.0,
    "Hole": 90.0,

    # Medium/high defects
    "Contamination": 80.0,
    "Structural Defect": 85.0,
    "Deformation": 80.0,

    # Surface defects
    "Scratch": 45.0,
    "Surface Scratch": 45.0,
    "Discoloration": 40.0,
    "Stain": 40.0,
    "Surface Defect": 50.0,

    # Generic anomaly
    "Visual Anomaly": 50.0,
    "Surface Anomaly": 50.0,
    "Unknown Anomaly": 50.0,

    # Normal
    "No defect detected": 0.0,
}


# ============================================================
# NORMALIZE VALUE
# ============================================================

def _safe_float(
    value: Any,
    default: float = 0.0
) -> float:

    try:

        number = float(value)

        if number != number:
            return default

        if number == float("inf"):
            return default

        if number == float("-inf"):
            return default

        return number

    except Exception:

        return default


# ============================================================
# CLAMP SCORE
# ============================================================

def _clamp_score(
    value: Any
) -> float:

    value = _safe_float(value)

    return max(
        0.0,
        min(
            100.0,
            value
        )
    )


# ============================================================
# CATEGORY-SPECIFIC DEFECT CATEGORIES
# ============================================================
#
# MVTec AD contains different defect classes for different
# product categories.
#
# We use these mappings when defect information is available.
# ============================================================

CATEGORY_DEFECT_TYPES = {

    "bottle": [
        "Broken Component",
        "Contamination",
        "Crack",
        "Deformation",
        "Surface Anomaly",
    ],

    "cable": [
        "Crack",
        "Cut",
        "Missing Component",
        "Deformation",
        "Surface Anomaly",
    ],

    "capsule": [
        "Crack",
        "Contamination",
        "Pill Defect",
        "Deformation",
        "Surface Anomaly",
    ],

    "carpet": [
        "Cut",
        "Hole",
        "Color Defect",
        "Thread Defect",
        "Surface Anomaly",
    ],

    "grid": [
        "Broken Grid",
        "Bent",
        "Glue Defect",
        "Thread Defect",
        "Surface Anomaly",
    ],

    "hazelnut": [
        "Crack",
        "Cut",
        "Hole",
        "Contamination",
        "Surface Anomaly",
    ],

    "leather": [
        "Cut",
        "Fold",
        "Glue Defect",
        "Color Defect",
        "Surface Anomaly",
    ],

    "metal_nut": [
        "Bend",
        "Color Defect",
        "Flip",
        "Scratch",
        "Surface Anomaly",
    ],

    "pill": [
        "Crack",
        "Contamination",
        "Color Defect",
        "Scratch",
        "Surface Anomaly",
    ],

    "screw": [
        "Bent",
        "Head Defect",
        "Thread Defect",
        "Scratch",
        "Surface Anomaly",
    ],

    "tile": [
        "Crack",
        "Gray Stroke",
        "Oil",
        "Rough Surface",
        "Surface Anomaly",
    ],

    "toothbrush": [
        "Defective Bristles",
        "Broken Bristle",
        "Contamination",
        "Missing Component",
        "Surface Anomaly",
    ],

    "transistor": [
        "Bent Lead",
        "Cut Lead",
        "Damaged Component",
        "Missing Component",
        "Surface Anomaly",
    ],

    "wood": [
        "Color Defect",
        "Hole",
        "Liquid",
        "Scratch",
        "Surface Anomaly",
    ],

    "zipper": [
        "Broken Teeth",
        "Fabric Defect",
        "Rough Edge",
        "Stitch Defect",
        "Surface Anomaly",
    ],
}


# ============================================================
# DEFECT CATEGORIZATION
# ============================================================

def categorize_defect(
    category: str,
    is_defect: bool,
    supplied_defect_type: Optional[str] = None,
    anomaly_score: float = 0.0,
    threshold: float = 0.0,
    location: str = "Center"
) -> str:

    # --------------------------------------------------------
    # Normal product
    # --------------------------------------------------------

    if not is_defect:

        return "No defect detected"

    # --------------------------------------------------------
    # If another part of the system already knows the defect
    # type, preserve it.
    # --------------------------------------------------------

    if supplied_defect_type:

        supplied = str(
            supplied_defect_type
        ).strip()

        if supplied:

            if supplied.lower() not in {
                "visual anomaly",
                "unknown anomaly",
                "anomaly",
                "defect"
            }:

                return supplied

    # --------------------------------------------------------
    # Generic categorization based on available PatchCore
    # information.
    #
    # PatchCore itself detects anomalous visual patterns.
    # It does NOT provide a true semantic defect classifier.
    #
    # Therefore we should not pretend that PatchCore knows
    # "crack", "scratch", etc. without an actual classifier.
    # --------------------------------------------------------

    category = str(
        category or ""
    ).lower().strip()

    score = _safe_float(
        anomaly_score
    )

    threshold = _safe_float(
        threshold
    )

    # --------------------------------------------------------
    # Strong anomaly
    # --------------------------------------------------------

    if threshold > 0:

        ratio = score / threshold

        if ratio >= 2.0:

            return "Structural / Severe Visual Anomaly"

    # --------------------------------------------------------
    # Location information
    # --------------------------------------------------------

    location = str(
        location or ""
    ).lower()

    if (
        "center" in location
        and threshold > 0
        and score >= threshold * 1.20
    ):

        return "Surface Anomaly"

    # --------------------------------------------------------
    # Category-specific generic classification
    # --------------------------------------------------------

    if category in CATEGORY_DEFECT_TYPES:

        return "Surface Anomaly"

    return "Visual Anomaly"


# ============================================================
# DEFECT TYPE SCORE
# ============================================================

def get_defect_type_score(
    defect_type: str
) -> float:

    if not defect_type:

        return 50.0

    defect_type = str(
        defect_type
    ).strip()

    # Exact match
    if defect_type in DEFECT_TYPE_SCORES:

        return DEFECT_TYPE_SCORES[
            defect_type
        ]

    # Case-insensitive match
    for name, score in DEFECT_TYPE_SCORES.items():

        if name.lower() == defect_type.lower():

            return score

    # Keyword-based classification
    text = defect_type.lower()

    if (
        "crack" in text
        or "broken" in text
        or "missing" in text
        or "hole" in text
    ):

        return 90.0

    if (
        "structural" in text
        or "damage" in text
        or "deformation" in text
        or "bend" in text
    ):

        return 80.0

    if (
        "contamination" in text
        or "cut" in text
    ):

        return 75.0

    if (
        "scratch" in text
        or "surface" in text
        or "color" in text
        or "stain" in text
    ):

        return 45.0

    return 50.0


# ============================================================
# SIZE SCORE
# ============================================================
#
# Defect area is calculated by PatchCore from anomalous
# patches.
#
# 0% area  -> 0
# 1-5%     -> low
# 5-15%    -> medium
# 15-30%   -> high
# >30%     -> critical size impact
# ============================================================

def calculate_size_score(
    defect_area_percentage: float,
    is_defect: bool
) -> float:

    if not is_defect:

        return 0.0

    area = max(
        0.0,
        _safe_float(
            defect_area_percentage
        )
    )

    if area <= 1.0:

        score = area * 20.0

    elif area <= 5.0:

        score = 20.0 + (
            (area - 1.0)
            / 4.0
        ) * 20.0

    elif area <= 15.0:

        score = 40.0 + (
            (area - 5.0)
            / 10.0
        ) * 20.0

    elif area <= 30.0:

        score = 60.0 + (
            (area - 15.0)
            / 15.0
        ) * 20.0

    else:

        score = 80.0 + min(
            20.0,
            (
                (area - 30.0)
                / 30.0
            ) * 20.0
        )

    return _clamp_score(
        score
    )


# ============================================================
# LOCATION SCORE
# ============================================================
#
# The project specification states that functional areas
# should have higher impact than cosmetic areas.
#
# PatchCore currently provides a coarse image location:
#
# Top-Left
# Top-Center
# Top-Right
# Middle-Left
# Middle-Center
# Middle-Right
# Bottom-Left
# Bottom-Center
# Bottom-Right
#
# Without a product-specific critical-region model, we use
# a conservative spatial score rather than pretending that
# every center/edge region is a true functional component.
# ============================================================

def calculate_location_score(
    location: str,
    is_defect: bool
) -> float:

    if not is_defect:

        return 0.0

    if not location:

        return 50.0

    text = str(
        location
    ).lower().strip()

    # Explicit critical/functional information
    if (
        "critical" in text
        or "functional" in text
    ):

        return 90.0

    # Central region generally receives moderate impact.
    if (
        "center" in text
        or "middle" in text
    ):

        return 60.0

    # Edges/corners receive lower default impact because
    # we do not have a product-specific functional map.
    if (
        "top" in text
        or "bottom" in text
        or "left" in text
        or "right" in text
    ):

        return 45.0

    return 50.0


# ============================================================
# CONFIDENCE SCORE
# ============================================================
#
# PatchCore gives an anomaly score, not a calibrated
# probability.
#
# Therefore this is a DETECTION CONFIDENCE SCORE derived
# from the separation between anomaly score and threshold.
#
# It must not be interpreted as a statistical probability.
# ============================================================

def calculate_confidence_score(
    anomaly_score: float,
    threshold: float,
    is_defect: bool
) -> float:

    if not is_defect:

        # A normal result below threshold receives confidence
        # according to its distance from the threshold.
        if threshold <= 0:

            return 100.0

        score = _safe_float(
            anomaly_score
        )

        separation = (
            (threshold - score)
            / max(
                threshold,
                1e-12
            )
        )

        confidence = 70.0 + (
            max(
                0.0,
                min(
                    1.0,
                    separation
                )
            )
            * 30.0
        )

        return round(
            _clamp_score(
                confidence
            ),
            2
        )

    # --------------------------------------------------------
    # Defect
    # --------------------------------------------------------

    if threshold <= 0:

        return 50.0

    score = _safe_float(
        anomaly_score
    )

    ratio = (
        score / max(
            threshold,
            1e-12
        )
    )

    # At threshold = 50
    # 1.25x threshold = 62.5
    # 1.50x threshold = 75
    # 2.00x threshold = 100

    confidence = 50.0 + (
        min(
            2.0,
            max(
                0.0,
                ratio - 1.0
            )
        )
        * 25.0
    )

    return round(
        _clamp_score(
            confidence
        ),
        2
    )


# ============================================================
# MAIN SEVERITY CALCULATION
# ============================================================

def calculate_quality_assessment(
    anomaly_score: float,
    threshold: float,
    category: str,
    defect_area_percentage: float = 0.0,
    location: str = "Center",
    defect_type: Optional[str] = None,
    is_defect: Optional[bool] = None
) -> Dict[str, Any]:

    anomaly_score = _safe_float(
        anomaly_score
    )

    threshold = _safe_float(
        threshold
    )

    # --------------------------------------------------------
    # Determine pass/fail
    # --------------------------------------------------------

    if is_defect is None:

        if threshold <= 0:

            is_defect = anomaly_score > 0.0

        else:

            is_defect = (
                anomaly_score
                > threshold
            )

    is_defect = bool(
        is_defect
    )

    # --------------------------------------------------------
    # Defect categorization
    # --------------------------------------------------------

    final_defect_type = categorize_defect(

        category=category,

        is_defect=is_defect,

        supplied_defect_type=defect_type,

        anomaly_score=anomaly_score,

        threshold=threshold,

        location=location
    )

    # --------------------------------------------------------
    # Size
    # --------------------------------------------------------

    size_score = calculate_size_score(

        defect_area_percentage=
            defect_area_percentage,

        is_defect=is_defect
    )

    # --------------------------------------------------------
    # Location
    # --------------------------------------------------------

    location_score = calculate_location_score(

        location=location,

        is_defect=is_defect
    )

    # --------------------------------------------------------
    # Defect type
    # --------------------------------------------------------

    defect_type_score = get_defect_type_score(

        final_defect_type
    )

    # --------------------------------------------------------
    # Confidence
    # --------------------------------------------------------

    confidence_score = calculate_confidence_score(

        anomaly_score=anomaly_score,

        threshold=threshold,

        is_defect=is_defect
    )

    # --------------------------------------------------------
    # NORMAL PRODUCT
    # --------------------------------------------------------

    if not is_defect:

        severity_score = 0.0

        severity_level = "Low"

        quality_risk = "Low"

        quality_status = "PASS"

        assessment_reason = (

            "The PatchCore anomaly score is below "
            "the calibrated category threshold."
        )

        recommended_action = (

            "Product meets the current quality "
            "inspection criteria."
        )

    # --------------------------------------------------------
    # DEFECTIVE PRODUCT
    # --------------------------------------------------------

    else:

        severity_score = (

            (
                size_score
                * SIZE_WEIGHT
            )

            +

            (
                location_score
                * LOCATION_WEIGHT
            )

            +

            (
                defect_type_score
                * DEFECT_TYPE_WEIGHT
            )

            +

            (
                confidence_score
                * CONFIDENCE_WEIGHT
            )
        )

        severity_score = _clamp_score(
            severity_score
        )

        severity_level = get_severity_level(
            severity_score
        )

        quality_risk = get_quality_risk(

            severity_level=

                severity_level,

            is_defect=True
        )

        quality_status = "FAIL"

        assessment_reason = (

            "The PatchCore anomaly score is above "
            "the calibrated category threshold."
        )

        recommended_action = get_recommended_action(

            severity_level=

                severity_level,

            is_defect=True
        )

    # ========================================================
    # RETURN COMPLETE ASSESSMENT
    # ========================================================

    return {

        "is_defect":
            is_defect,

        "defect_type":
            final_defect_type,

        "defect_category":
            final_defect_type,

        "severity_score":
            round(
                severity_score,
                2
            ),

        "severity_level":
            severity_level,

        "quality_risk":
            quality_risk,

        "quality_status":
            quality_status,

        "size_score":
            round(
                size_score,
                2
            ),

        "location_score":
            round(
                location_score,
                2
            ),

        "defect_type_score":
            round(
                defect_type_score,
                2
            ),

        "confidence_score":
            round(
                confidence_score,
                2
            ),

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

        "defect_area_percentage":
            round(
                _safe_float(
                    defect_area_percentage
                ),
                2
            ),

        "location":
            location,

        "assessment_reason":
            assessment_reason,

        "recommended_action":
            recommended_action,

        "scoring_weights": {

            "size":
                SIZE_WEIGHT,

            "location":
                LOCATION_WEIGHT,

            "defect_type":
                DEFECT_TYPE_WEIGHT,

            "confidence":
                CONFIDENCE_WEIGHT
        }
    }


# ============================================================
# COMPATIBILITY FUNCTION
#
# Existing inspection.py may already call:
#
# calculate_severity(...)
#
# Keep this function so we don't break the existing backend.
# ============================================================

def calculate_severity(
    *args,
    **kwargs
) -> Dict[str, Any]:

    # --------------------------------------------------------
    # Case 1:
    #
    # calculate_severity(result_dict)
    # --------------------------------------------------------

    if len(args) >= 1 and isinstance(
        args[0],
        dict
    ):

        result = args[0]

        anomaly_score = result.get(
            "anomaly_score",
            kwargs.get(
                "anomaly_score",
                0.0
            )
        )

        threshold = result.get(
            "threshold",
            kwargs.get(
                "threshold",
                0.0
            )
        )

        category = result.get(
            "category",
            kwargs.get(
                "category",
                "unknown"
            )
        )

        defect_area = result.get(
            "defect_area_percentage",
            0.0
        )

        location = result.get(
            "location",
            "Center"
        )

        defect_type = result.get(
            "defect_type",
            None
        )

        is_defect = result.get(
            "is_defect",
            None
        )

        return calculate_quality_assessment(

            anomaly_score=
                anomaly_score,

            threshold=
                threshold,

            category=
                category,

            defect_area_percentage=
                defect_area,

            location=
                location,

            defect_type=
                defect_type,

            is_defect=
                is_defect
        )

    # --------------------------------------------------------
    # Case 2:
    #
    # Keyword arguments
    # --------------------------------------------------------

    anomaly_score = kwargs.get(
        "anomaly_score",
        kwargs.get(
            "score",
            0.0
        )
    )

    threshold = kwargs.get(
        "threshold",
        0.0
    )

    category = kwargs.get(
        "category",
        "unknown"
    )

    defect_area = kwargs.get(
        "defect_area_percentage",
        kwargs.get(
            "defect_area",
            0.0
        )
    )

    location = kwargs.get(
        "location",
        "Center"
    )

    defect_type = kwargs.get(
        "defect_type",
        None
    )

    is_defect = kwargs.get(
        "is_defect",
        None
    )

    # --------------------------------------------------------
    # Case 3:
    #
    # Positional:
    #
    # calculate_severity(
    #     anomaly_score,
    #     threshold,
    #     category,
    #     ...
    # )
    # --------------------------------------------------------

    if len(args) >= 1:

        anomaly_score = args[0]

    if len(args) >= 2:

        threshold = args[1]

    if len(args) >= 3:

        category = args[2]

    if len(args) >= 4:

        defect_area = args[3]

    if len(args) >= 5:

        location = args[4]

    if len(args) >= 6:

        defect_type = args[5]

    if len(args) >= 7:

        is_defect = args[6]

    return calculate_quality_assessment(

        anomaly_score=
            anomaly_score,

        threshold=
            threshold,

        category=
            category,

        defect_area_percentage=
            defect_area,

        location=
            location,

        defect_type=
            defect_type,

        is_defect=
            is_defect
    )


# ============================================================
# SIMPLE ALIAS
# ============================================================

def assess_quality(
    anomaly_score: float,
    threshold: float,
    category: str,
    defect_area_percentage: float = 0.0,
    location: str = "Center",
    defect_type: Optional[str] = None,
    is_defect: Optional[bool] = None
) -> Dict[str, Any]:

    return calculate_quality_assessment(

        anomaly_score=
            anomaly_score,

        threshold=
            threshold,

        category=
            category,

        defect_area_percentage=
            defect_area_percentage,

        location=
            location,

        defect_type=
            defect_type,

        is_defect=
            is_defect
    )


# ============================================================
# END OF FILE
# ============================================================