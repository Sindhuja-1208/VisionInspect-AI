from pathlib import Path
import json
import numpy as np

from app.ai.patchcore_model import predict_with_feature_bank


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATASET_DIR = PROJECT_ROOT / "dataset" / "mvtec_ad"
MODEL_DIR = PROJECT_ROOT / "models"
FEATURE_BANK_DIR = MODEL_DIR / "feature_banks"

OUTPUT_FILE = MODEL_DIR / "patchcore_thresholds.json"


# ============================================================
# MVTec AD CATEGORIES
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
    "zipper",
]


# ============================================================
# CONFIGURATION
# ============================================================

# Percentage of GOOD images that are allowed to be
# incorrectly classified as defective.
#
# 95th percentile means approximately 95% of good images
# should remain NORMAL.
GOOD_PERCENTILE = 95.0

# Small safety margin added above the selected threshold.
THRESHOLD_MARGIN = 0.005


# ============================================================
# LOAD FEATURE BANK
# ============================================================

def check_feature_bank(category: str):
    """
    Check whether the feature bank exists for a category.
    """

    bank_path = FEATURE_BANK_DIR / category / "features.npy"

    if not bank_path.exists():
        print(
            f"[WARNING] Feature bank not found for "
            f"'{category}': {bank_path}"
        )
        return False

    return True


# ============================================================
# GET TEST DIRECTORIES
# ============================================================

def get_good_test_directory(category: str):
    """
    Return MVTec GOOD test directory.
    """

    path = DATASET_DIR / category / "test" / "good"

    if not path.exists():
        return None

    return path


def get_defect_test_directories(category: str):
    """
    Return all defect directories inside the test directory.
    """

    test_dir = DATASET_DIR / category / "test"

    if not test_dir.exists():
        return []

    defect_dirs = []

    for item in sorted(test_dir.iterdir()):

        if not item.is_dir():
            continue

        if item.name.lower() == "good":
            continue

        defect_dirs.append(item)

    return defect_dirs


# ============================================================
# CALCULATE THRESHOLD
# ============================================================

def calculate_threshold(good_scores):
    """
    Calculate a category-specific threshold from GOOD images.

    The threshold is based on the GOOD score distribution.
    """

    if not good_scores:
        return None

    scores = np.array(
        good_scores,
        dtype=np.float32
    )

    percentile_value = float(
        np.percentile(
            scores,
            GOOD_PERCENTILE
        )
    )

    threshold = percentile_value + THRESHOLD_MARGIN

    return float(threshold)


# ============================================================
# EVALUATE ONE CATEGORY
# ============================================================

def evaluate_category(category: str):

    print()
    print("=" * 100)
    print(f"CATEGORY: {category.upper()}")
    print("=" * 100)

    # --------------------------------------------------------
    # CHECK FEATURE BANK
    # --------------------------------------------------------

    if not check_feature_bank(category):
        print("[SKIP] Feature bank missing.")
        return None

    # --------------------------------------------------------
    # DIRECTORIES
    # --------------------------------------------------------

    good_dir = get_good_test_directory(category)

    defect_dirs = get_defect_test_directories(category)

    if good_dir is None:
        print("[SKIP] GOOD test directory not found.")
        return None

    good_images = sorted(
        good_dir.glob("*.png")
    )

    defect_images = []

    for defect_dir in defect_dirs:

        images = sorted(
            defect_dir.glob("*.png")
        )

        for image_path in images:

            defect_images.append(
                (
                    image_path,
                    defect_dir.name
                )
            )

    print(
        f"Good test images:   {len(good_images)}"
    )

    print(
        f"Defect test images: {len(defect_images)}"
    )

    if len(good_images) == 0:
        print("[SKIP] No GOOD images found.")
        return None

    if len(defect_images) == 0:
        print("[WARNING] No defect images found.")

    # --------------------------------------------------------
    # TEST GOOD IMAGES
    # --------------------------------------------------------

    print()
    print("Testing GOOD images...")

    good_scores = []

    for image_path in good_images:

        try:

            # IMPORTANT:
            # predict_with_feature_bank expects:
            #
            # predict_with_feature_bank(image_path, category)
            #
            # NOT the feature-bank array/path.

            result = predict_with_feature_bank(
                str(image_path),
                category
            )

            # ------------------------------------------------
            # EXTRACT SCORE
            # ------------------------------------------------

            if isinstance(result, dict):

                score = result.get(
                    "anomaly_score"
                )

                if score is None:
                    score = result.get(
                        "score"
                    )

            else:

                score = result

            if score is None:
                print(
                    f"[WARNING] No score for "
                    f"{image_path.name}"
                )
                continue

            score = float(score)

            good_scores.append(score)

        except Exception as e:

            print(
                f"[ERROR] {image_path.name}: {e}"
            )

    # --------------------------------------------------------
    # TEST DEFECT IMAGES
    # --------------------------------------------------------

    print()
    print("Testing DEFECT images...")

    defect_scores = []

    defect_details = {}

    for image_path, defect_type in defect_images:

        try:

            # IMPORTANT:
            # Second argument must be category.
            result = predict_with_feature_bank(
                str(image_path),
                category
            )

            # ------------------------------------------------
            # EXTRACT SCORE
            # ------------------------------------------------

            if isinstance(result, dict):

                score = result.get(
                    "anomaly_score"
                )

                if score is None:
                    score = result.get(
                        "score"
                    )

            else:

                score = result

            if score is None:
                print(
                    f"[WARNING] No score for "
                    f"{image_path.name}"
                )
                continue

            score = float(score)

            defect_scores.append(score)

            if defect_type not in defect_details:
                defect_details[defect_type] = []

            defect_details[defect_type].append(
                score
            )

        except Exception as e:

            print(
                f"[ERROR] {image_path.name}: {e}"
            )

    # --------------------------------------------------------
    # VALIDATE GOOD SCORES
    # --------------------------------------------------------

    if not good_scores:

        print()
        print("[SKIP] No valid GOOD scores.")

        return None

    # --------------------------------------------------------
    # CALCULATE THRESHOLD
    # --------------------------------------------------------

    good_array = np.array(
        good_scores,
        dtype=np.float32
    )

    threshold = calculate_threshold(
        good_scores
    )

    if threshold is None:

        print(
            "[SKIP] Unable to calculate threshold."
        )

        return None

    # --------------------------------------------------------
    # GOOD STATISTICS
    # --------------------------------------------------------

    good_min = float(
        np.min(good_array)
    )

    good_max = float(
        np.max(good_array)
    )

    good_avg = float(
        np.mean(good_array)
    )

    good_median = float(
        np.median(good_array)
    )

    good_95 = float(
        np.percentile(
            good_array,
            95
        )
    )

    good_99 = float(
        np.percentile(
            good_array,
            99
        )
    )

    # --------------------------------------------------------
    # DEFECT STATISTICS
    # --------------------------------------------------------

    defect_min = None
    defect_max = None
    defect_avg = None
    defect_median = None

    if defect_scores:

        defect_array = np.array(
            defect_scores,
            dtype=np.float32
        )

        defect_min = float(
            np.min(defect_array)
        )

        defect_max = float(
            np.max(defect_array)
        )

        defect_avg = float(
            np.mean(defect_array)
        )

        defect_median = float(
            np.median(defect_array)
        )

    # --------------------------------------------------------
    # GOOD CLASSIFICATION
    # --------------------------------------------------------

    good_normal_count = sum(
        score < threshold
        for score in good_scores
    )

    good_defect_count = sum(
        score >= threshold
        for score in good_scores
    )

    good_accuracy = (
        good_normal_count / len(good_scores)
    ) * 100.0

    # --------------------------------------------------------
    # DEFECT CLASSIFICATION
    # --------------------------------------------------------

    defect_detected_count = 0
    defect_missed_count = 0

    defect_accuracy = None

    if defect_scores:

        defect_detected_count = sum(
            score >= threshold
            for score in defect_scores
        )

        defect_missed_count = sum(
            score < threshold
            for score in defect_scores
        )

        defect_accuracy = (
            defect_detected_count
            / len(defect_scores)
        ) * 100.0

    # --------------------------------------------------------
    # OVERALL ACCURACY
    # --------------------------------------------------------

    total_images = (
        len(good_scores)
        + len(defect_scores)
    )

    correct_images = (
        good_normal_count
        + defect_detected_count
    )

    overall_accuracy = None

    if total_images > 0:

        overall_accuracy = (
            correct_images
            / total_images
        ) * 100.0

    # --------------------------------------------------------
    # PRINT RESULTS
    # --------------------------------------------------------

    print()
    print("-" * 100)
    print("GOOD SCORE STATISTICS")
    print("-" * 100)

    print(
        f"Min:       {good_min:.6f}"
    )

    print(
        f"Max:       {good_max:.6f}"
    )

    print(
        f"Average:   {good_avg:.6f}"
    )

    print(
        f"Median:    {good_median:.6f}"
    )

    print(
        f"95%:       {good_95:.6f}"
    )

    print(
        f"99%:       {good_99:.6f}"
    )

    print()
    print("-" * 100)
    print("DEFECT SCORE STATISTICS")
    print("-" * 100)

    if defect_scores:

        print(
            f"Min:       {defect_min:.6f}"
        )

        print(
            f"Max:       {defect_max:.6f}"
        )

        print(
            f"Average:   {defect_avg:.6f}"
        )

        print(
            f"Median:    {defect_median:.6f}"
        )

    else:

        print(
            "No valid defect scores."
        )

    print()
    print("-" * 100)
    print("CALIBRATED THRESHOLD")
    print("-" * 100)

    print(
        f"GOOD {GOOD_PERCENTILE:.0f}th percentile: "
        f"{good_95:.6f}"
    )

    print(
        f"Safety margin:       "
        f"{THRESHOLD_MARGIN:.6f}"
    )

    print(
        f"FINAL THRESHOLD:     "
        f"{threshold:.6f}"
    )

    print()
    print("-" * 100)
    print("CLASSIFICATION PERFORMANCE")
    print("-" * 100)

    print(
        f"GOOD correctly NORMAL: "
        f"{good_normal_count}/{len(good_scores)} "
        f"({good_accuracy:.2f}%)"
    )

    print(
        f"GOOD incorrectly DEFECT: "
        f"{good_defect_count}/{len(good_scores)}"
    )

    if defect_scores:

        print(
            f"DEFECT correctly DETECTED: "
            f"{defect_detected_count}/{len(defect_scores)} "
            f"({defect_accuracy:.2f}%)"
        )

        print(
            f"DEFECT missed: "
            f"{defect_missed_count}/{len(defect_scores)}"
        )

        print(
            f"OVERALL ACCURACY: "
            f"{overall_accuracy:.2f}%"
        )

    # --------------------------------------------------------
    # DEFECT TYPE PERFORMANCE
    # --------------------------------------------------------

    if defect_details:

        print()
        print("-" * 100)
        print("DEFECT TYPE PERFORMANCE")
        print("-" * 100)

        for defect_type in sorted(
            defect_details.keys()
        ):

            scores = defect_details[
                defect_type
            ]

            detected = sum(
                score >= threshold
                for score in scores
            )

            accuracy = (
                detected / len(scores)
            ) * 100.0

            average = float(
                np.mean(scores)
            )

            print(
                f"{defect_type:<30}"
                f"count={len(scores):<5}"
                f"avg={average:.6f} "
                f"detected={detected}/{len(scores)} "
                f"({accuracy:.2f}%)"
            )

    # --------------------------------------------------------
    # RETURN RESULTS
    # --------------------------------------------------------

    return {
        "threshold": round(
            threshold,
            6
        ),

        "good": {
            "count": len(good_scores),
            "min": round(
                good_min,
                6
            ),
            "max": round(
                good_max,
                6
            ),
            "average": round(
                good_avg,
                6
            ),
            "median": round(
                good_median,
                6
            ),
            "percentile_95": round(
                good_95,
                6
            ),
            "percentile_99": round(
                good_99,
                6
            ),
            "correct_normal": good_normal_count,
            "incorrect_defect": good_defect_count,
            "accuracy": round(
                good_accuracy,
                2
            ),
        },

        "defect": {
            "count": len(defect_scores),
            "min": (
                round(defect_min, 6)
                if defect_min is not None
                else None
            ),
            "max": (
                round(defect_max, 6)
                if defect_max is not None
                else None
            ),
            "average": (
                round(defect_avg, 6)
                if defect_avg is not None
                else None
            ),
            "median": (
                round(defect_median, 6)
                if defect_median is not None
                else None
            ),
            "correct_detected": defect_detected_count,
            "missed": defect_missed_count,
            "accuracy": (
                round(
                    defect_accuracy,
                    2
                )
                if defect_accuracy is not None
                else None
            ),
        },

        "overall_accuracy": (
            round(
                overall_accuracy,
                2
            )
            if overall_accuracy is not None
            else None
        ),

        "defect_types": {
            defect_type: {
                "count": len(
                    defect_details[
                        defect_type
                    ]
                ),
                "average_score": round(
                    float(
                        np.mean(
                            defect_details[
                                defect_type
                            ]
                        )
                    ),
                    6
                ),
                "detected": sum(
                    score >= threshold
                    for score in
                    defect_details[
                        defect_type
                    ]
                ),
            }
            for defect_type in defect_details
        },
    }


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 100)
    print("PATCHCORE THRESHOLD CALIBRATION")
    print("=" * 100)

    print()
    print(
        f"Dataset directory:"
        f"\n{DATASET_DIR}"
    )

    print()
    print(
        f"Feature bank directory:"
        f"\n{FEATURE_BANK_DIR}"
    )

    print()
    print(
        f"Threshold output:"
        f"\n{OUTPUT_FILE}"
    )

    print()
    print(
        f"GOOD percentile: "
        f"{GOOD_PERCENTILE}"
    )

    print(
        f"Threshold margin: "
        f"{THRESHOLD_MARGIN}"
    )

    # --------------------------------------------------------
    # CHECK DATASET
    # --------------------------------------------------------

    if not DATASET_DIR.exists():

        print()
        print(
            "[ERROR] Dataset directory not found:"
        )

        print(
            DATASET_DIR
        )

        return

    # --------------------------------------------------------
    # RESULTS
    # --------------------------------------------------------

    all_results = {}

    successful = 0
    failed = 0

    # --------------------------------------------------------
    # PROCESS CATEGORIES
    # --------------------------------------------------------

    for category in CATEGORIES:

        try:

            result = evaluate_category(
                category
            )

            if result is None:

                failed += 1

                continue

            all_results[
                category
            ] = result

            successful += 1

        except KeyboardInterrupt:

            print()
            print(
                "[STOPPED] Calibration interrupted by user."
            )

            break

        except Exception as e:

            failed += 1

            print()
            print(
                f"[ERROR] Category '{category}' failed:"
            )

            print(
                str(e)
            )

    # --------------------------------------------------------
    # SAVE JSON
    # --------------------------------------------------------

    print()
    print("=" * 100)
    print("PATCHCORE THRESHOLD CALIBRATION SUMMARY")
    print("=" * 100)

    if all_results:

        for category in CATEGORIES:

            if category not in all_results:
                continue

            result = all_results[
                category
            ]

            threshold = result[
                "threshold"
            ]

            good_accuracy = result[
                "good"
            ][
                "accuracy"
            ]

            defect_accuracy = result[
                "defect"
            ][
                "accuracy"
            ]

            overall_accuracy = result[
                "overall_accuracy"
            ]

            print(
                f"{category:<15} "
                f"threshold={threshold:.6f} "
                f"good={good_accuracy:.2f}% "
                f"defect={defect_accuracy if defect_accuracy is not None else 'N/A'}% "
                f"overall={overall_accuracy if overall_accuracy is not None else 'N/A'}%"
            )

    else:

        print(
            "No categories were successfully calibrated."
        )

    # --------------------------------------------------------
    # OUTPUT JSON STRUCTURE
    # --------------------------------------------------------

    output_data = {
        "method": "PatchCore Multi-Scale ResNet18",

        "description": (
            "Category-specific anomaly thresholds "
            "calibrated from MVTec AD GOOD test images."
        ),

        "configuration": {
            "good_percentile": GOOD_PERCENTILE,
            "threshold_margin": THRESHOLD_MARGIN,
        },

        "categories": all_results,
    }

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            output_data,
            f,
            indent=4
        )

    # --------------------------------------------------------
    # FINAL MESSAGE
    # --------------------------------------------------------

    print()
    print(
        f"Successful categories: "
        f"{successful}"
    )

    print(
        f"Failed categories: "
        f"{failed}"
    )

    print()
    print(
        "CALIBRATION COMPLETED"
    )

    print()
    print(
        "Threshold file saved to:"
    )

    print(
        OUTPUT_FILE
    )

    print()
    print(
        "Feature banks were NOT modified."
    )

    print(
        "Existing PatchCore models were NOT retrained."
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()