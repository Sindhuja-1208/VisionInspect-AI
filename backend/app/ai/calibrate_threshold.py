from pathlib import Path
import numpy as np

from app.ai.predictor import calculate_anomaly_score


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATASET_DIR = (
    PROJECT_ROOT
    / "dataset"
    / "mvtec_ad"
)

MODEL_DIR = (
    PROJECT_ROOT
    / "models"
)

THRESHOLD_DIR = (
    MODEL_DIR
    / "thresholds"
)

THRESHOLD_DIR.mkdir(
    parents=True,
    exist_ok=True
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
    "zipper",
]


# ============================================================
# CONFIGURATION
# ============================================================

# We use a high percentile of GOOD-image scores.
#
# This means:
# Almost all normal training images should remain NORMAL.
#
# A small safety margin is then added so that normal images
# are not unnecessarily classified as defective.
#
GOOD_PERCENTILE = 99.0
SAFETY_MARGIN = 1.10


# ============================================================
# CALIBRATE ONE CATEGORY
# ============================================================

def calibrate_category(category: str):

    good_dir = (
        DATASET_DIR
        / category
        / "train"
        / "good"
    )

    if not good_dir.exists():

        print(
            f"\n[{category}] GOOD directory not found:"
        )

        print(good_dir)

        return False

    image_files = sorted(
        list(good_dir.glob("*.png"))
        + list(good_dir.glob("*.jpg"))
        + list(good_dir.glob("*.jpeg"))
    )

    if not image_files:

        print(
            f"\n[{category}] No GOOD images found."
        )

        return False

    print("\n" + "=" * 70)
    print(f"CALIBRATING: {category.upper()}")
    print("=" * 70)

    print(
        f"GOOD images found: {len(image_files)}"
    )

    scores = []

    for index, image_path in enumerate(
        image_files,
        start=1
    ):

        try:

            result = calculate_anomaly_score(
                str(image_path),
                category
            )

            score = float(
                result["anomaly_score"]
            )

            scores.append(score)

            if index % 20 == 0 or index == len(image_files):

                print(
                    f"Processed: "
                    f"{index}/{len(image_files)}"
                )

        except Exception as error:

            print(
                f"Error processing "
                f"{image_path.name}: {error}"
            )

    if not scores:

        print(
            f"[{category}] "
            f"No valid scores generated."
        )

        return False

    scores = np.array(
        scores,
        dtype=np.float64
    )

    # ========================================================
    # SCORE STATISTICS
    # ========================================================

    minimum = float(
        np.min(scores)
    )

    maximum = float(
        np.max(scores)
    )

    mean = float(
        np.mean(scores)
    )

    median = float(
        np.median(scores)
    )

    percentile = float(
        np.percentile(
            scores,
            GOOD_PERCENTILE
        )
    )

    # ========================================================
    # FINAL THRESHOLD
    # ========================================================
    #
    # Example:
    #
    # 99th percentile = 0.110
    #
    # safety margin = 10%
    #
    # threshold = 0.121
    #
    # This prevents GOOD images close to the boundary from
    # being immediately classified as defective.
    #
    # ========================================================

    threshold = (
        percentile
        * SAFETY_MARGIN
    )

    # Never allow a threshold of zero.
    threshold = max(
        threshold,
        0.000001
    )

    # ========================================================
    # SAVE THRESHOLD
    # ========================================================

    threshold_file = (
        THRESHOLD_DIR
        / f"{category}_threshold.txt"
    )

    threshold_file.write_text(
        f"{threshold:.6f}",
        encoding="utf-8"
    )

    # ========================================================
    # DISPLAY RESULTS
    # ========================================================

    print("\nScore Statistics")
    print("-" * 50)

    print(
        f"Minimum           : {minimum:.6f}"
    )

    print(
        f"Maximum           : {maximum:.6f}"
    )

    print(
        f"Mean              : {mean:.6f}"
    )

    print(
        f"Median            : {median:.6f}"
    )

    print(
        f"{GOOD_PERCENTILE:.0f}th Percentile   : "
        f"{percentile:.6f}"
    )

    print(
        f"Safety Margin     : "
        f"{SAFETY_MARGIN:.2f}x"
    )

    print(
        f"FINAL THRESHOLD   : "
        f"{threshold:.6f}"
    )

    print(
        f"\nSaved to:"
    )

    print(threshold_file)

    return True


# ============================================================
# MAIN
# ============================================================

def main():

    print("\n")
    print("=" * 70)
    print("VISIONINSPECT AI")
    print("CATEGORY-SPECIFIC THRESHOLD CALIBRATION")
    print("=" * 70)

    print(
        "\nScoring method:"
    )

    print(
        "15% Mean Error"
    )

    print(
        "35% Top 5% Error"
    )

    print(
        "40% Top 1% Error"
    )

    print(
        "10% Maximum Error"
    )

    print(
        f"\nGOOD percentile: "
        f"{GOOD_PERCENTILE}%"
    )

    print(
        f"Safety margin: "
        f"{SAFETY_MARGIN}x"
    )

    successful = []
    failed = []

    for category in CATEGORIES:

        try:

            success = calibrate_category(
                category
            )

            if success:

                successful.append(
                    category
                )

            else:

                failed.append(
                    category
                )

        except Exception as error:

            print(
                f"\n[{category}] "
                f"Calibration failed:"
            )

            print(error)

            failed.append(
                category
            )

    # ========================================================
    # FINAL SUMMARY
    # ========================================================

    print("\n")
    print("=" * 70)
    print("CALIBRATION COMPLETE")
    print("=" * 70)

    print(
        f"Successful: "
        f"{len(successful)}"
    )

    print(
        f"Failed: "
        f"{len(failed)}"
    )

    if successful:

        print(
            "\nSuccessfully calibrated:"
        )

        for category in successful:

            threshold_file = (
                THRESHOLD_DIR
                / f"{category}_threshold.txt"
            )

            if threshold_file.exists():

                value = (
                    threshold_file
                    .read_text()
                    .strip()
                )

                print(
                    f"  {category:12s} "
                    f"-> {value}"
                )

    if failed:

        print(
            "\nFailed categories:"
        )

        for category in failed:

            print(
                f"  {category}"
            )

    print(
        "\nThreshold files are stored in:"
    )

    print(THRESHOLD_DIR)

    print(
        "\nNo model retraining was performed."
    )


if __name__ == "__main__":
    main()