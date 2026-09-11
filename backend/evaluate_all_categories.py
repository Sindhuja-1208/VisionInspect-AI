from pathlib import Path
import sys
import statistics

# Make sure backend is available
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.ai.predictor import calculate_anomaly_score, load_threshold


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

DATASET_DIR = PROJECT_ROOT.parent / "dataset" / "mvtec_ad"


def evaluate_category(category):
    test_dir = DATASET_DIR / category / "test"

    if not test_dir.exists():
        print(f"\n[{category}] TEST FOLDER NOT FOUND")
        return None

    good_dir = test_dir / "good"

    if not good_dir.exists():
        print(f"\n[{category}] GOOD FOLDER NOT FOUND")
        return None

    try:
        threshold = load_threshold(category)
    except Exception as e:
        print(f"\n[{category}] THRESHOLD ERROR: {e}")
        return None

    good_scores = []
    defect_scores = []

    # -------------------------
    # GOOD IMAGES
    # -------------------------
    good_files = sorted(good_dir.glob("*.png"))

    for image_path in good_files:
        try:
            result = calculate_anomaly_score(
                str(image_path),
                category
            )

            score = float(result["anomaly_score"])
            good_scores.append(score)

        except Exception as e:
            print(f"  Error GOOD {image_path.name}: {e}")

    # -------------------------
    # DEFECT IMAGES
    # -------------------------
    defect_counts = {}

    for defect_dir in sorted(test_dir.iterdir()):

        if not defect_dir.is_dir():
            continue

        if defect_dir.name.lower() == "good":
            continue

        defect_files = sorted(defect_dir.glob("*.png"))

        detected = 0
        missed = 0
        scores = []

        for image_path in defect_files:

            try:
                result = calculate_anomaly_score(
                    str(image_path),
                    category
                )

                score = float(result["anomaly_score"])
                scores.append(score)
                defect_scores.append(score)

                if score >= threshold:
                    detected += 1
                else:
                    missed += 1

            except Exception as e:
                print(
                    f"  Error {defect_dir.name}/{image_path.name}: {e}"
                )

        defect_counts[defect_dir.name] = {
            "total": len(defect_files),
            "detected": detected,
            "missed": missed,
            "scores": scores,
        }

    # -------------------------
    # GOOD ACCURACY
    # -------------------------
    good_correct = sum(
        1 for score in good_scores
        if score < threshold
    )

    good_wrong = len(good_scores) - good_correct

    # -------------------------
    # DEFECT ACCURACY
    # -------------------------
    defect_correct = sum(
        1 for score in defect_scores
        if score >= threshold
    )

    defect_wrong = len(defect_scores) - defect_correct

    total = len(good_scores) + len(defect_scores)
    overall_correct = good_correct + defect_correct

    good_accuracy = (
        good_correct / len(good_scores) * 100
        if good_scores else 0
    )

    defect_accuracy = (
        defect_correct / len(defect_scores) * 100
        if defect_scores else 0
    )

    overall_accuracy = (
        overall_correct / total * 100
        if total else 0
    )

    # -------------------------
    # SCORE OVERLAP
    # -------------------------
    highest_good = max(good_scores) if good_scores else 0
    lowest_defect = min(defect_scores) if defect_scores else 0

    overlap = sum(
        1 for score in defect_scores
        if score <= highest_good
    )

    # -------------------------
    # PRINT CATEGORY RESULT
    # -------------------------
    print("\n" + "=" * 70)
    print(f"CATEGORY: {category.upper()}")
    print("=" * 70)

    print(f"Threshold              : {threshold:.6f}")

    print("\nGOOD:")
    print(f"  Images               : {len(good_scores)}")
    print(f"  Correct NORMAL       : {good_correct}")
    print(f"  Wrong DEFECT         : {good_wrong}")
    print(f"  Good Accuracy        : {good_accuracy:.2f}%")

    if good_scores:
        print(f"  Min Score            : {min(good_scores):.6f}")
        print(f"  Max Score            : {max(good_scores):.6f}")
        print(f"  Average Score        : {statistics.mean(good_scores):.6f}")

    print("\nDEFECT:")
    print(f"  Images               : {len(defect_scores)}")
    print(f"  Correct DEFECT       : {defect_correct}")
    print(f"  Wrong NORMAL         : {defect_wrong}")
    print(f"  Defect Detection     : {defect_accuracy:.2f}%")

    if defect_scores:
        print(f"  Min Score            : {min(defect_scores):.6f}")
        print(f"  Max Score            : {max(defect_scores):.6f}")
        print(f"  Average Score        : {statistics.mean(defect_scores):.6f}")

    print("\nOVERALL:")
    print(f"  Total Images         : {total}")
    print(f"  Correct              : {overall_correct}")
    print(f"  Overall Accuracy     : {overall_accuracy:.2f}%")

    print("\nSCORE OVERLAP:")
    print(f"  Highest GOOD Score   : {highest_good:.6f}")
    print(f"  Lowest DEFECT Score  : {lowest_defect:.6f}")
    print(f"  Defects inside GOOD range : {overlap}/{len(defect_scores)}")

    print("\nDEFECT TYPE PERFORMANCE:")

    for defect_name, data in defect_counts.items():

        if data["total"] == 0:
            continue

        accuracy = (
            data["detected"] /
            data["total"] *
            100
        )

        print(
            f"  {defect_name:20s} "
            f"{data['detected']:3d}/{data['total']:3d} "
            f"= {accuracy:6.2f}%"
        )

    return {
        "category": category,
        "good_accuracy": good_accuracy,
        "defect_accuracy": defect_accuracy,
        "overall_accuracy": overall_accuracy,
        "threshold": threshold,
    }


def main():

    print("\n")
    print("=" * 70)
    print("VISIONINSPECT AI - ALL CATEGORY EVALUATION")
    print("=" * 70)
    print("Testing current models WITHOUT changing anything.")
    print("=" * 70)

    results = []

    for category in CATEGORIES:

        result = evaluate_category(category)

        if result:
            results.append(result)

    # -------------------------
    # FINAL SUMMARY
    # -------------------------
    print("\n\n")
    print("=" * 90)
    print("FINAL SUMMARY - ALL 15 CATEGORIES")
    print("=" * 90)

    print(
        f"{'Category':15s}"
        f"{'Good %':>12s}"
        f"{'Defect %':>12s}"
        f"{'Overall %':>12s}"
        f"{'Threshold':>14s}"
    )

    print("-" * 90)

    for r in results:

        print(
            f"{r['category']:15s}"
            f"{r['good_accuracy']:>11.2f}%"
            f"{r['defect_accuracy']:>11.2f}%"
            f"{r['overall_accuracy']:>11.2f}%"
            f"{r['threshold']:>14.6f}"
        )

    print("-" * 90)

    if results:

        avg_good = statistics.mean(
            r["good_accuracy"] for r in results
        )

        avg_defect = statistics.mean(
            r["defect_accuracy"] for r in results
        )

        avg_overall = statistics.mean(
            r["overall_accuracy"] for r in results
        )

        print(
            f"{'AVERAGE':15s}"
            f"{avg_good:>11.2f}%"
            f"{avg_defect:>11.2f}%"
            f"{avg_overall:>11.2f}%"
        )

    print("\nEvaluation completed.")
    print("No models or thresholds were modified.")


if __name__ == "__main__":
    main()