from pathlib import Path
import sys
import numpy as np

# ------------------------------------------------------------
# PROJECT PATH
# ------------------------------------------------------------

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


# ------------------------------------------------------------
# IMPORT PREDICTOR
# ------------------------------------------------------------

from app.ai.predictor import (
    calculate_anomaly_score,
    load_threshold
)


# ------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------

CATEGORY = "bottle"

DATASET_DIR = (
    PROJECT_ROOT
    / "dataset"
    / "mvtec_ad"
    / CATEGORY
)

TEST_DIR = DATASET_DIR / "test"

THRESHOLD = load_threshold(CATEGORY)


# ------------------------------------------------------------
# EVALUATE ONE FOLDER
# ------------------------------------------------------------

def evaluate_folder(folder_path, threshold):

    scores = []

    image_files = sorted(
        folder_path.glob("*.png")
    )

    for index, image_path in enumerate(
        image_files,
        start=1
    ):

        result = calculate_anomaly_score(
            str(image_path),
            CATEGORY
        )

        score = result["anomaly_score"]

        scores.append(score)

        prediction = (
            "DEFECTIVE"
            if score >= threshold
            else "NORMAL"
        )

        print(
            f"  [{index}/{len(image_files)}] "
            f"{image_path.name} -> "
            f"{score:.6f} -> "
            f"{prediction}"
        )

    return scores


# ------------------------------------------------------------
# STATISTICS
# ------------------------------------------------------------

def print_statistics(scores):

    if not scores:
        return

    values = np.array(scores)

    print()
    print("-" * 60)

    print(
        f"Count       : {len(values)}"
    )

    print(
        f"Minimum     : {values.min():.6f}"
    )

    print(
        f"Maximum     : {values.max():.6f}"
    )

    print(
        f"Average     : {values.mean():.6f}"
    )

    print(
        f"Median      : {np.median(values):.6f}"
    )

    print(
        f"95th %ile   : "
        f"{np.percentile(values, 95):.6f}"
    )

    print(
        f"99th %ile   : "
        f"{np.percentile(values, 99):.6f}"
    )


# ============================================================
# MAIN
# ============================================================

print("=" * 70)
print(
    "VISIONINSPECT AI - BOTTLE DEFECT TYPE EVALUATION"
)
print("=" * 70)

print(
    f"Dataset   : {DATASET_DIR}"
)

print(
    f"Category  : {CATEGORY}"
)

print(
    f"Threshold : {THRESHOLD:.6f}"
)

print()


# ============================================================
# CHECK TEST DIRECTORY
# ============================================================

if not TEST_DIR.exists():

    print(
        f"ERROR: Test directory not found:"
    )

    print(TEST_DIR)

    sys.exit(1)


# ============================================================
# GOOD
# ============================================================

good_dir = TEST_DIR / "good"

print("=" * 70)
print("NORMAL / GOOD")
print("=" * 70)

good_scores = evaluate_folder(
    good_dir,
    THRESHOLD
)

print_statistics(
    good_scores
)

good_correct = sum(
    score < THRESHOLD
    for score in good_scores
)

good_total = len(good_scores)

print()

if good_total > 0:

    print(
        f"Correctly NORMAL : "
        f"{good_correct}/{good_total}"
    )

    print(
        f"Normal accuracy  : "
        f"{good_correct / good_total * 100:.2f}%"
    )


# ============================================================
# DEFECT TYPES
# ============================================================

defect_folders = sorted(
    [
        folder
        for folder in TEST_DIR.iterdir()
        if folder.is_dir()
        and folder.name != "good"
    ]
)


total_defect_images = 0
total_defect_correct = 0


for defect_dir in defect_folders:

    defect_name = defect_dir.name

    print()
    print("=" * 70)

    print(
        f"DEFECT TYPE: "
        f"{defect_name.upper()}"
    )

    print("=" * 70)

    scores = evaluate_folder(
        defect_dir,
        THRESHOLD
    )

    print_statistics(
        scores
    )

    correctly_detected = sum(
        score >= THRESHOLD
        for score in scores
    )

    incorrectly_normal = (
        len(scores)
        - correctly_detected
    )

    total_defect_images += len(scores)

    total_defect_correct += (
        correctly_detected
    )

    print()

    print(
        f"Correctly DEFECTIVE : "
        f"{correctly_detected}/{len(scores)}"
    )

    print(
        f"Incorrectly NORMAL  : "
        f"{incorrectly_normal}/{len(scores)}"
    )

    if scores:

        detection_rate = (
            correctly_detected
            / len(scores)
            * 100
        )

        print(
            f"Detection rate      : "
            f"{detection_rate:.2f}%"
        )


# ============================================================
# FINAL SUMMARY
# ============================================================

print()
print("=" * 70)
print("FINAL SUMMARY")
print("=" * 70)

print()

if good_total > 0:

    print(
        f"GOOD images      : "
        f"{good_correct}/{good_total} "
        f"({good_correct / good_total * 100:.2f}%)"
    )

if total_defect_images > 0:

    print(
        f"DEFECTIVE images : "
        f"{total_defect_correct}/"
        f"{total_defect_images} "
        f"({total_defect_correct / total_defect_images * 100:.2f}%)"
    )

total_images = (
    good_total
    + total_defect_images
)

total_correct = (
    good_correct
    + total_defect_correct
)

print()

if total_images > 0:

    print(
        f"Overall accuracy : "
        f"{total_correct}/{total_images} "
        f"({total_correct / total_images * 100:.2f}%)"
    )

print()
print("=" * 70)
print("EVALUATION COMPLETE")
print("=" * 70)