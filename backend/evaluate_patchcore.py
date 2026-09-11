from pathlib import Path
from collections import defaultdict

from app.ai.patchcore_model import (
    predict_with_feature_bank,
)


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATASET_DIR = (
    PROJECT_ROOT
    / "dataset"
    / "mvtec_ad"
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
# SETTINGS
# ============================================================

MAX_GOOD_IMAGES = 20
MAX_DEFECT_IMAGES_PER_TYPE = 20


# ============================================================
# COLLECT IMAGES
# ============================================================

def collect_test_images(category):

    category_dir = DATASET_DIR / category

    test_dir = category_dir / "test"

    if not test_dir.exists():
        return [], []

    good_dir = test_dir / "good"

    good_images = []

    if good_dir.exists():

        good_images = sorted(
            good_dir.glob("*.png")
        )[:MAX_GOOD_IMAGES]

    defect_images = []

    for defect_dir in sorted(test_dir.iterdir()):

        if not defect_dir.is_dir():
            continue

        if defect_dir.name == "good":
            continue

        images = sorted(
            defect_dir.glob("*.png")
        )[:MAX_DEFECT_IMAGES_PER_TYPE]

        for image in images:

            defect_images.append(
                (
                    defect_dir.name,
                    image
                )
            )

    return good_images, defect_images


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 100)
    print("VISIONINSPECT AI - PATCHCORE-STYLE EVALUATION")
    print("=" * 100)

    print()
    print(
        "This test ONLY measures the new feature-based detector."
    )

    print(
        "No models or feature banks will be modified."
    )

    print()

    all_results = []

    for category in CATEGORIES:

        print()
        print("=" * 100)
        print(f"CATEGORY: {category.upper()}")
        print("=" * 100)

        good_images, defect_images = (
            collect_test_images(category)
        )

        print(
            f"Good test images: {len(good_images)}"
        )

        print(
            f"Defect test images: {len(defect_images)}"
        )

        if not good_images and not defect_images:

            print("No test images found.")
            continue

        good_scores = []

        defect_scores = defaultdict(list)

        # ----------------------------------------------------
        # GOOD
        # ----------------------------------------------------

        print()
        print("Testing GOOD images...")

        for image_path in good_images:

            try:

                result = predict_with_feature_bank(
                    str(image_path),
                    category
                )

                score = result["anomaly_score"]

                good_scores.append(score)

            except Exception as error:

                print(
                    f"ERROR: {image_path.name}: {error}"
                )

        # ----------------------------------------------------
        # DEFECTS
        # ----------------------------------------------------

        print(
            "Testing DEFECT images..."
        )

        for defect_type, image_path in defect_images:

            try:

                result = predict_with_feature_bank(
                    str(image_path),
                    category
                )

                score = result["anomaly_score"]

                defect_scores[
                    defect_type
                ].append(score)

            except Exception as error:

                print(
                    f"ERROR: {image_path.name}: {error}"
                )

        # ----------------------------------------------------
        # GOOD STATISTICS
        # ----------------------------------------------------

        if good_scores:

            good_min = min(
                good_scores
            )

            good_max = max(
                good_scores
            )

            good_avg = sum(
                good_scores
            ) / len(good_scores)

            good_sorted = sorted(
                good_scores
            )

            print()
            print(
                f"GOOD   -> "
                f"min={good_min:.6f}, "
                f"max={good_max:.6f}, "
                f"avg={good_avg:.6f}"
            )

        else:

            good_min = None
            good_max = None
            good_avg = None

        # ----------------------------------------------------
        # DEFECT STATISTICS
        # ----------------------------------------------------

        print()
        print("DEFECT TYPE SCORES")

        for defect_type in sorted(
            defect_scores
        ):

            scores = defect_scores[
                defect_type
            ]

            if not scores:
                continue

            minimum = min(scores)
            maximum = max(scores)
            average = sum(scores) / len(scores)

            print(
                f"{defect_type:<25} "
                f"min={minimum:.6f} "
                f"max={maximum:.6f} "
                f"avg={average:.6f}"
            )

        # ----------------------------------------------------
        # STORE RESULTS
        # ----------------------------------------------------

        all_results.append(
            {
                "category": category,
                "good_scores": good_scores,
                "defect_scores": dict(
                    defect_scores
                ),
            }
        )

    # ========================================================
    # GLOBAL SUMMARY
    # ========================================================

    print()
    print("=" * 100)
    print("PATCHCORE SCORE SUMMARY")
    print("=" * 100)

    for result in all_results:

        category = result["category"]

        good_scores = result[
            "good_scores"
        ]

        defect_scores = result[
            "defect_scores"
        ]

        all_defect_scores = []

        for scores in defect_scores.values():

            all_defect_scores.extend(
                scores
            )

        print()

        print(
            f"{category:<15}",
            end=""
        )

        if good_scores:

            print(
                f"GOOD: "
                f"{min(good_scores):.6f} - "
                f"{max(good_scores):.6f} | "
                f"AVG: "
                f"{sum(good_scores) / len(good_scores):.6f}",
                end=""
            )

        if all_defect_scores:

            print(
                f" | DEFECT: "
                f"{min(all_defect_scores):.6f} - "
                f"{max(all_defect_scores):.6f} | "
                f"AVG: "
                f"{sum(all_defect_scores) / len(all_defect_scores):.6f}"
            )

        else:

            print()

    print()
    print("=" * 100)
    print("EVALUATION COMPLETED")
    print("=" * 100)

    print()
    print(
        "No models or feature banks were modified."
    )


if __name__ == "__main__":

    main()