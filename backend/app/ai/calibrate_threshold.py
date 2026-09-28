from pathlib import Path
import numpy as np

from app.ai.predictor import predict_with_feature_bank


# ============================================================
# VISIONINSPECT AI
# PATCHCORE THRESHOLD CALIBRATION
# IMPROVED CATEGORY-WISE THRESHOLD CALIBRATION
# ============================================================


# ============================================================
# PATHS
# ============================================================

# calibrate_threshold.py
# is inside:
# VisionInspect-AI/backend/app/ai/
#
# parents[3] -> VisionInspect-AI

PROJECT_ROOT = Path(__file__).resolve().parents[3]

DATASET_DIR = PROJECT_ROOT / "dataset" / "mvtec_ad"

MODEL_DIR = PROJECT_ROOT / "models"

THRESHOLD_DIR = MODEL_DIR / "thresholds"


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
# CALIBRATION SETTINGS
# ============================================================

PERCENTILE = 99.0

SAFETY_FACTOR = 1.10

# Prevents a category from receiving an unusably
# small threshold such as 0.000001.
MIN_THRESHOLD = 0.05


# ============================================================
# FIND NORMAL TRAINING IMAGES
# ============================================================

def find_normal_images(category):

    folder = (
        DATASET_DIR
        / category
        / "train"
        / "good"
    )

    if not folder.exists():

        raise FileNotFoundError(
            f"Normal image folder not found:\n{folder}"
        )

    extensions = {
        ".png",
        ".jpg",
        ".jpeg",
        ".bmp"
    }

    images = sorted(
        [
            p
            for p in folder.iterdir()
            if p.is_file()
            and p.suffix.lower() in extensions
        ]
    )

    if len(images) == 0:

        raise ValueError(
            f"No normal images found for category "
            f"'{category}' in:\n{folder}"
        )

    return images


# ============================================================
# CALIBRATE ONE CATEGORY
# ============================================================

def calibrate_category(category):

    print()
    print("=" * 70)
    print(
        f"CALIBRATING CATEGORY: "
        f"{category.upper()}"
    )
    print("=" * 70)

    images = find_normal_images(category)

    print(
        f"Normal images found: "
        f"{len(images)}"
    )

    print(
        f"Dataset directory: "
        f"{DATASET_DIR}"
    )

    scores = []

    # ========================================================
    # RUN PATCHCORE ON NORMAL IMAGES
    # ========================================================

    for i, image_path in enumerate(
        images,
        start=1
    ):

        result = predict_with_feature_bank(
            str(image_path),
            category
        )

        score = float(
            result["anomaly_score"]
        )

        # Safety against invalid values
        if not np.isfinite(score):

            print(
                f"[{i:3d}/{len(images)}] "
                f"{image_path.name:<20} "
                f"INVALID SCORE -> skipped"
            )

            continue

        score = max(
            score,
            0.0
        )

        scores.append(score)

        print(
            f"[{i:3d}/{len(images)}] "
            f"{image_path.name:<20} "
            f"score={score:.6f}"
        )

    # ========================================================
    # VALIDATE SCORES
    # ========================================================

    if len(scores) == 0:

        raise ValueError(
            f"No valid anomaly scores generated "
            f"for category '{category}'."
        )

    scores = np.asarray(
        scores,
        dtype=np.float32
    )

    # ========================================================
    # SCORE STATISTICS
    # ========================================================

    minimum_score = float(
        np.min(scores)
    )

    maximum_score = float(
        np.max(scores)
    )

    mean_score = float(
        np.mean(scores)
    )

    median_score = float(
        np.median(scores)
    )

    zero_count = int(
        np.sum(scores <= 1e-8)
    )

    non_zero_scores = scores[
        scores > 1e-8
    ]

    non_zero_count = len(
        non_zero_scores
    )

    # ========================================================
    # PRINT SCORE DISTRIBUTION
    # ========================================================

    print()
    print(
        f"Valid scores      : "
        f"{len(scores)}"
    )

    print(
        f"Zero scores       : "
        f"{zero_count}"
    )

    print(
        f"Non-zero scores   : "
        f"{non_zero_count}"
    )

    print(
        f"Minimum score     : "
        f"{minimum_score:.6f}"
    )

    print(
        f"Maximum score     : "
        f"{maximum_score:.6f}"
    )

    print(
        f"Mean score        : "
        f"{mean_score:.6f}"
    )

    print(
        f"Median score      : "
        f"{median_score:.6f}"
    )

    # ========================================================
    # IMPORTANT:
    # HANDLE CATEGORIES WITH MANY ZERO SCORES
    # ========================================================

    if non_zero_count >= 5:

        # If enough meaningful scores exist,
        # calculate percentile using non-zero values.
        calibration_scores = non_zero_scores

        print()
        print(
            "Calibration mode  : "
            "NON-ZERO SCORES"
        )

    else:

        # If almost everything is zero,
        # use all valid scores.
        calibration_scores = scores

        print()
        print(
            "Calibration mode  : "
            "ALL VALID SCORES"
        )

    # ========================================================
    # PERCENTILE
    # ========================================================

    percentile_score = float(
        np.percentile(
            calibration_scores,
            PERCENTILE
        )
    )

    # ========================================================
    # APPLY SAFETY FACTOR
    # ========================================================

    calculated_threshold = (
        percentile_score
        * SAFETY_FACTOR
    )

    # ========================================================
    # MINIMUM THRESHOLD PROTECTION
    # ========================================================

    threshold = max(
        calculated_threshold,
        MIN_THRESHOLD
    )

    # ========================================================
    # CREATE OUTPUT DIRECTORY
    # ========================================================

    output_dir = (
        THRESHOLD_DIR
        / category
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    # ========================================================
    # SAVE THRESHOLD
    # ========================================================

    output_file = (
        output_dir
        / "threshold.txt"
    )

    output_file.write_text(
        f"{threshold:.6f}",
        encoding="utf-8"
    )

    # ========================================================
    # PRINT RESULTS
    # ========================================================

    print()
    print(
        f"Minimum score     : "
        f"{minimum_score:.6f}"
    )

    print(
        f"Maximum score     : "
        f"{maximum_score:.6f}"
    )

    print(
        f"Mean score        : "
        f"{mean_score:.6f}"
    )

    print(
        f"Median score      : "
        f"{median_score:.6f}"
    )

    print(
        f"{PERCENTILE:.0f}th percentile "
        f": {percentile_score:.6f}"
    )

    print(
        f"Safety factor     : "
        f"{SAFETY_FACTOR:.2f}"
    )

    print(
        f"Calculated thresh : "
        f"{calculated_threshold:.6f}"
    )

    print(
        f"Minimum allowed   : "
        f"{MIN_THRESHOLD:.6f}"
    )

    print(
        f"FINAL THRESHOLD   : "
        f"{threshold:.6f}"
    )

    print(
        f"Saved to          : "
        f"{output_file}"
    )

    return threshold


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 70)
    print("VISIONINSPECT AI")
    print("PATCHCORE THRESHOLD CALIBRATION")
    print("=" * 70)

    print()
    print(
        f"Dataset directory: "
        f"{DATASET_DIR}"
    )

    print(
        f"Threshold directory: "
        f"{THRESHOLD_DIR}"
    )

    print()

    THRESHOLD_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    results = {}

    # ========================================================
    # CALIBRATE ALL CATEGORIES
    # ========================================================

    for category in CATEGORIES:

        try:

            threshold = calibrate_category(
                category
            )

            results[category] = threshold

        except Exception as error:

            print()
            print("=" * 70)

            print(
                f"FAILED CATEGORY: "
                f"{category}"
            )

            print(
                f"ERROR: "
                f"{error}"
            )

            print("=" * 70)

            results[category] = None

    # ========================================================
    # FINAL SUMMARY
    # ========================================================

    print()
    print("=" * 70)
    print("FINAL THRESHOLD SUMMARY")
    print("=" * 70)

    successful = 0

    for category in CATEGORIES:

        threshold = results.get(
            category
        )

        if threshold is None:

            print(
                f"{category:<15} "
                f"FAILED"
            )

        else:

            print(
                f"{category:<15} "
                f"{threshold:.6f}"
            )

            successful += 1

    print()
    print(
        f"Successful: "
        f"{successful}/{len(CATEGORIES)}"
    )

    print("=" * 70)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()