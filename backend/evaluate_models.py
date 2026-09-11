from pathlib import Path

import cv2
import numpy as np
import torch

from app.ai.autoencoder import ConvAutoencoder


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

IMAGE_SIZE = 224

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

device = torch.device(
    "cuda"
    if torch.cuda.is_available()
    else "cpu"
)


def preprocess(path):

    image = cv2.imread(
        str(path)
    )

    if image is None:
        return None

    image = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2RGB
    )

    image = cv2.resize(
        image,
        (IMAGE_SIZE, IMAGE_SIZE)
    )

    image = image.astype(
        np.float32
    ) / 255.0

    image = np.transpose(
        image,
        (2, 0, 1)
    )

    return torch.tensor(
        image,
        dtype=torch.float32
    ).unsqueeze(0)


def score(model, path):

    tensor = preprocess(path)

    if tensor is None:
        return None

    tensor = tensor.to(device)

    with torch.no_grad():

        reconstructed = model(
            tensor
        )

        error = torch.abs(
            tensor - reconstructed
        )

        spatial_error = torch.mean(
            error,
            dim=1
        )

        mean_error = torch.mean(
            spatial_error
        ).item()

        flat = spatial_error.flatten()

        top_k = max(
            1,
            int(flat.numel() * 0.05)
        )

        top_error = torch.topk(
            flat,
            top_k
        ).values.mean().item()

    return (
        0.30 * mean_error
        +
        0.70 * top_error
    )


def load_threshold(category):

    path = (
        THRESHOLD_DIR
        / f"{category}_threshold.txt"
    )

    if path.exists():

        return float(
            path.read_text().strip()
        )

    return 0.076


def evaluate_category(category):

    model_path = (
        MODEL_DIR
        / f"{category}_autoencoder.pth"
    )

    if not model_path.exists():
        return None

    model = ConvAutoencoder().to(
        device
    )

    model.load_state_dict(
        torch.load(
            model_path,
            map_location=device
        )
    )

    model.eval()

    threshold = load_threshold(
        category
    )

    good_dir = (
        DATASET_DIR
        / category
        / "test"
        / "good"
    )

    test_root = (
        DATASET_DIR
        / category
        / "test"
    )

    normal_scores = []
    defect_scores = []

    if good_dir.exists():

        for path in good_dir.glob("*.png"):

            value = score(
                model,
                path
            )

            if value is not None:
                normal_scores.append(
                    value
                )

    for defect_dir in test_root.iterdir():

        if not defect_dir.is_dir():
            continue

        if defect_dir.name == "good":
            continue

        for path in defect_dir.glob("*.png"):

            value = score(
                model,
                path
            )

            if value is not None:
                defect_scores.append(
                    value
                )

    normal_correct = sum(
        value <= threshold
        for value in normal_scores
    )

    defect_correct = sum(
        value > threshold
        for value in defect_scores
    )

    total = (
        len(normal_scores)
        +
        len(defect_scores)
    )

    correct = (
        normal_correct
        +
        defect_correct
    )

    accuracy = (
        correct / total
        if total > 0
        else 0
    )

    return {
        "category": category,
        "threshold": threshold,
        "normal_samples": len(
            normal_scores
        ),
        "defect_samples": len(
            defect_scores
        ),
        "normal_accuracy":
            (
                normal_correct
                / len(normal_scores)
                if normal_scores
                else 0
            ),
        "defect_accuracy":
            (
                defect_correct
                / len(defect_scores)
                if defect_scores
                else 0
            ),
        "overall_accuracy": accuracy
    }


def main():

    print("=" * 70)
    print(
        "VISIONINSPECT AI - MODEL EVALUATION"
    )
    print("=" * 70)

    results = []

    for category in CATEGORIES:

        print(
            f"\nEvaluating {category}..."
        )

        try:

            result = evaluate_category(
                category
            )

            if result:

                results.append(
                    result
                )

                print(
                    f"Threshold: "
                    f"{result['threshold']:.6f}"
                )

                print(
                    f"Normal Accuracy: "
                    f"{result['normal_accuracy'] * 100:.2f}%"
                )

                print(
                    f"Defect Accuracy: "
                    f"{result['defect_accuracy'] * 100:.2f}%"
                )

                print(
                    f"Overall Accuracy: "
                    f"{result['overall_accuracy'] * 100:.2f}%"
                )

            else:

                print(
                    "Model not found."
                )

        except Exception as error:

            print(
                f"Evaluation error: {error}"
            )

    print("\n" + "=" * 70)
    print("FINAL EVALUATION SUMMARY")
    print("=" * 70)

    for result in results:

        print(
            f"{result['category']:12} | "
            f"Overall: "
            f"{result['overall_accuracy'] * 100:6.2f}% | "
            f"Normal: "
            f"{result['normal_accuracy'] * 100:6.2f}% | "
            f"Defect: "
            f"{result['defect_accuracy'] * 100:6.2f}%"
        )

    print("=" * 70)


if __name__ == "__main__":
    main()