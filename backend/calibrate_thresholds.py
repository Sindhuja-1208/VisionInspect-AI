from pathlib import Path
import numpy as np

from app.ai.predictor import predict_with_feature_bank


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATASET_DIR = PROJECT_ROOT / "dataset" / "mvtec_ad"

MODEL_DIR = PROJECT_ROOT / "models"
THRESHOLD_DIR = MODEL_DIR / "thresholds"


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


PERCENTILE = 99.0
SAFETY_FACTOR = 1.10


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

    return sorted(
        [
            p
            for p in folder.iterdir()
            if p.is_file()
            and p.suffix.lower() in extensions
        ]
    )


def calibrate_category(category):

    print()
    print("=" * 70)
    print(f"CALIBRATING: {category.upper()}")
    print("=" * 70)

    images = find_normal_images(category)

    print(
        f"Normal images found: {len(images)}"
    )

    scores = []

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

        scores.append(score)

        print(
            f"[{i:3d}/{len(images)}] "
            f"{image_path.name:<20} "
            f"score={score:.6f}"
        )

    scores = np.asarray(
        scores,
        dtype=np.float32
    )

    percentile_score = float(
        np.percentile(
            scores,
            PERCENTILE
        )
    )

    threshold = (
        percentile_score
        * SAFETY_FACTOR
    )

    output_dir = (
        THRESHOLD_DIR
        / category
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    output_file = (
        output_dir
        / "threshold.txt"
    )

    output_file.write_text(
        f"{threshold:.6f}",
        encoding="utf-8"
    )

    print()
    print(
        f"Minimum score : {np.min(scores):.6f}"
    )

    print(
        f"Maximum score : {np.max(scores):.6f}"
    )

    print(
        f"Mean score    : {np.mean(scores):.6f}"
    )

    print(
        f"99th percentile: {percentile_score:.6f}"
    )

    print(
        f"FINAL THRESHOLD: {threshold:.6f}"
    )

    print(
        f"Saved to: {output_file}"
    )

    return threshold


def main():

    print()
    print("=" * 70)
    print("VISIONINSPECT AI")
    print("PATCHCORE THRESHOLD CALIBRATION")
    print("=" * 70)

    THRESHOLD_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    results = {}

    for category in CATEGORIES:

        try:

            threshold = calibrate_category(
                category
            )

            results[category] = threshold

        except Exception as error:

            print()
            print(
                f"FAILED: {category}"
            )

            print(
                f"ERROR: {error}"
            )

    print()
    print("=" * 70)
    print("FINAL THRESHOLD SUMMARY")
    print("=" * 70)

    for category, threshold in results.items():

        print(
            f"{category:<15} "
            f"{threshold:.6f}"
        )

    print()
    print(
        f"Successful: "
        f"{len(results)}/{len(CATEGORIES)}"
    )

    print("=" * 70)


if __name__ == "__main__":
    main()