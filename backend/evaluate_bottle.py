from pathlib import Path
import statistics

from app.ai.predictor import calculate_anomaly_score, load_threshold


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATASET_DIR = PROJECT_ROOT / "dataset" / "mvtec_ad"
BOTTLE_DIR = DATASET_DIR / "bottle"
TEST_DIR = BOTTLE_DIR / "test"


# ============================================================
# SETTINGS
# ============================================================

CATEGORY = "bottle"

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp"}

threshold = load_threshold(CATEGORY)


# ============================================================
# HELPER
# ============================================================

def get_images(folder):
    if not folder.exists():
        return []

    return sorted(
        [
            path
            for path in folder.iterdir()
            if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
        ]
    )


def calculate_scores(image_paths):
    scores = []

    for index, image_path in enumerate(image_paths, start=1):
        try:
            result = calculate_anomaly_score(
                str(image_path),
                CATEGORY
            )

            score = result["anomaly_score"]
            scores.append(score)

            print(
                f"  [{index}/{len(image_paths)}] "
                f"{image_path.name} -> {score:.6f}"
            )

        except Exception as e:
            print(
                f"  ERROR: {image_path.name} -> {e}"
            )

    return scores


def print_statistics(name, scores):
    if not scores:
        print(f"\n{name}: No scores found.")
        return

    sorted_scores = sorted(scores)

    minimum = min(sorted_scores)
    maximum = max(sorted_scores)
    average = statistics.mean(sorted_scores)
    median = statistics.median(sorted_scores)

    p95_index = min(
        len(sorted_scores) - 1,
        max(0, int(len(sorted_scores) * 0.95))
    )

    p99_index = min(
        len(sorted_scores) - 1,
        max(0, int(len(sorted_scores) * 0.99))
    )

    p95 = sorted_scores[p95_index]
    p99 = sorted_scores[p99_index]

    print(f"\n{name}")
    print("-" * 60)
    print(f"Count       : {len(scores)}")
    print(f"Minimum     : {minimum:.6f}")
    print(f"Maximum     : {maximum:.6f}")
    print(f"Average     : {average:.6f}")
    print(f"Median      : {median:.6f}")
    print(f"95th %ile   : {p95:.6f}")
    print(f"99th %ile   : {p99:.6f}")


# ============================================================
# MAIN
# ============================================================

print("=" * 70)
print("VISIONINSPECT AI - BOTTLE MODEL EVALUATION")
print("=" * 70)

print(f"Dataset      : {BOTTLE_DIR}")
print(f"Category     : {CATEGORY}")
print(f"AI Threshold : {threshold:.6f}")

if not TEST_DIR.exists():
    print("\nERROR: Bottle test directory not found.")
    print(TEST_DIR)
    raise SystemExit(1)


# ============================================================
# LOAD TEST DATA
# ============================================================

good_dir = TEST_DIR / "good"

good_images = get_images(good_dir)

defect_images = []

for defect_dir in sorted(TEST_DIR.iterdir()):
    if not defect_dir.is_dir():
        continue

    if defect_dir.name.lower() == "good":
        continue

    images = get_images(defect_dir)

    if images:
        print(
            f"\nFound defect type: {defect_dir.name} "
            f"({len(images)} images)"
        )

        defect_images.extend(images)


print("\n")
print("=" * 70)
print("DATASET SUMMARY")
print("=" * 70)

print(f"Normal test images   : {len(good_images)}")
print(f"Defective test images: {len(defect_images)}")


# ============================================================
# NORMAL IMAGES
# ============================================================

print("\n")
print("=" * 70)
print("EVALUATING NORMAL IMAGES")
print("=" * 70)

good_scores = calculate_scores(good_images)


# ============================================================
# DEFECTIVE IMAGES
# ============================================================

print("\n")
print("=" * 70)
print("EVALUATING DEFECTIVE IMAGES")
print("=" * 70)

defect_scores = calculate_scores(defect_images)


# ============================================================
# STATISTICS
# ============================================================

print("\n")
print("=" * 70)
print("SCORE STATISTICS")
print("=" * 70)

print_statistics("NORMAL / GOOD", good_scores)
print_statistics("DEFECTIVE", defect_scores)


# ============================================================
# CLASSIFICATION RESULTS
# ============================================================

good_normal = sum(score <= threshold for score in good_scores)
good_defective = sum(score > threshold for score in good_scores)

defect_normal = sum(score <= threshold for score in defect_scores)
defect_defective = sum(score > threshold for score in defect_scores)


print("\n")
print("=" * 70)
print("CLASSIFICATION RESULTS")
print("=" * 70)

print(f"\nThreshold: {threshold:.6f}")

print("\nNORMAL IMAGES")
print(f"Correctly NORMAL     : {good_normal}/{len(good_scores)}")
print(f"Incorrectly DEFECTIVE: {good_defective}/{len(good_scores)}")

if good_scores:
    normal_accuracy = good_normal / len(good_scores) * 100
    print(f"Normal accuracy      : {normal_accuracy:.2f}%")


print("\nDEFECTIVE IMAGES")
print(f"Correctly DEFECTIVE  : {defect_defective}/{len(defect_scores)}")
print(f"Incorrectly NORMAL   : {defect_normal}/{len(defect_scores)}")

if defect_scores:
    defect_accuracy = defect_defective / len(defect_scores) * 100
    print(f"Defect detection rate: {defect_accuracy:.2f}%")


# ============================================================
# OVERALL
# ============================================================

total = len(good_scores) + len(defect_scores)
correct = good_normal + defect_defective

print("\n")
print("=" * 70)
print("OVERALL RESULT")
print("=" * 70)

if total > 0:
    overall_accuracy = correct / total * 100
    print(f"Total images     : {total}")
    print(f"Correct          : {correct}")
    print(f"Incorrect        : {total - correct}")
    print(f"Overall accuracy : {overall_accuracy:.2f}%")


# ============================================================
# SCORE OVERLAP
# ============================================================

print("\n")
print("=" * 70)
print("NORMAL vs DEFECT SCORE OVERLAP")
print("=" * 70)

if good_scores and defect_scores:

    highest_normal = max(good_scores)
    lowest_defect = min(defect_scores)

    print(f"Highest NORMAL score : {highest_normal:.6f}")
    print(f"Lowest DEFECT score  : {lowest_defect:.6f}")

    if lowest_defect > highest_normal:
        print("\nGOOD NEWS:")
        print("There is no score overlap in this test set.")
        print("A threshold can separate normal and defective images.")
    else:
        print("\nIMPORTANT:")
        print("Normal and defective scores overlap.")
        print("Changing the threshold alone may not solve the problem.")

        overlap_count = sum(
            score <= highest_normal
            for score in defect_scores
        )

        print(
            f"Defective images inside normal-score range: "
            f"{overlap_count}/{len(defect_scores)}"
        )


# ============================================================
# LOW-SCORING DEFECTS
# ============================================================

print("\n")
print("=" * 70)
print("LOWEST DEFECTIVE SCORES")
print("=" * 70)

if defect_images:

    defect_results = []

    for image_path in defect_images:
        try:
            result = calculate_anomaly_score(
                str(image_path),
                CATEGORY
            )

            defect_results.append(
                (
                    result["anomaly_score"],
                    image_path
                )
            )

        except Exception:
            pass

    defect_results.sort(key=lambda x: x[0])

    for score, image_path in defect_results[:10]:
        status = "NORMAL" if score <= threshold else "DEFECTIVE"

        print(
            f"{image_path.parent.name:20s} "
            f"{image_path.name:30s} "
            f"score={score:.6f} "
            f"-> {status}"
        )


print("\n")
print("=" * 70)
print("EVALUATION COMPLETE")
print("=" * 70)