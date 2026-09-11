from pathlib import Path

import cv2
import numpy as np
import torch

from app.ai.autoencoder import ConvAutoencoder


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

MODEL_DIR = PROJECT_ROOT / "models"
THRESHOLD_DIR = MODEL_DIR / "thresholds"

IMAGE_SIZE = 224


# ============================================================
# SUPPORTED CATEGORIES
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
# DEVICE
# ============================================================

device = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)


# ============================================================
# MODEL CACHE
# ============================================================

_model_cache = {}


# ============================================================
# IMAGE PREPROCESSING
# ============================================================

def preprocess_image(image_path: str):
    """
    Read image, convert to RGB, resize to 224x224,
    normalize to [0, 1], and convert to PyTorch tensor.
    """

    image = cv2.imread(image_path)

    if image is None:
        raise ValueError(
            f"Unable to read image: {image_path}"
        )

    image = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2RGB
    )

    image = cv2.resize(
        image,
        (IMAGE_SIZE, IMAGE_SIZE),
        interpolation=cv2.INTER_AREA
    )

    image = image.astype(
        np.float32
    ) / 255.0

    image = np.transpose(
        image,
        (2, 0, 1)
    )

    tensor = torch.from_numpy(
        image
    ).float()

    return tensor.unsqueeze(0)


# ============================================================
# LOAD CATEGORY MODEL
# ============================================================

def load_model(category: str):

    if category not in CATEGORIES:
        raise ValueError(
            f"Unsupported category: {category}"
        )

    if category in _model_cache:
        return _model_cache[category]

    model_path = (
        MODEL_DIR /
        f"{category}_autoencoder.pth"
    )

    if not model_path.exists():
        raise FileNotFoundError(
            f"Model not found for category "
            f"'{category}': {model_path}"
        )

    model = ConvAutoencoder().to(device)

    checkpoint = torch.load(
        model_path,
        map_location=device
    )

    model.load_state_dict(checkpoint)

    model.eval()

    _model_cache[category] = model

    return model


# ============================================================
# LOAD CATEGORY THRESHOLD
# ============================================================

def load_threshold(category: str):

    threshold_path = (
        THRESHOLD_DIR /
        f"{category}_threshold.txt"
    )

    if threshold_path.exists():

        try:

            return float(
                threshold_path.read_text().strip()
            )

        except ValueError:
            pass

    # Fallback only.
    # Proper category-specific thresholds
    # should be generated using calibration.
    return 0.076


# ============================================================
# CALCULATE ROBUST ANOMALY SCORE
# ============================================================

def calculate_anomaly_score(
    image_path: str,
    category: str
):

    model = load_model(category)

    image_tensor = preprocess_image(
        image_path
    ).to(device)

    with torch.no_grad():

        reconstructed = model(
            image_tensor
        )

        # ----------------------------------------------------
        # Pixel-level reconstruction error
        # ----------------------------------------------------

        error_map = torch.abs(
            image_tensor - reconstructed
        )

        # Convert RGB error into one spatial error map
        spatial_error = torch.mean(
            error_map,
            dim=1
        )

        flat_error = spatial_error.flatten()

        total_pixels = flat_error.numel()

        # ----------------------------------------------------
        # Global average error
        # ----------------------------------------------------

        mean_error = torch.mean(
            spatial_error
        ).item()

        # ----------------------------------------------------
        # Top 5% error
        # ----------------------------------------------------

        top_5_count = max(
            1,
            int(total_pixels * 0.05)
        )

        top_5_errors = torch.topk(
            flat_error,
            top_5_count
        ).values

        top_5_error = torch.mean(
            top_5_errors
        ).item()

        # ----------------------------------------------------
        # Top 1% error
        # ----------------------------------------------------

        top_1_count = max(
            1,
            int(total_pixels * 0.01)
        )

        top_1_errors = torch.topk(
            flat_error,
            top_1_count
        ).values

        top_1_error = torch.mean(
            top_1_errors
        ).item()

        # ----------------------------------------------------
        # Top 0.5% error
        #
        # This focuses more strongly on localized defects.
        # ----------------------------------------------------

        top_05_count = max(
            1,
            int(total_pixels * 0.005)
        )

        top_05_errors = torch.topk(
            flat_error,
            top_05_count
        ).values

        top_05_error = torch.mean(
            top_05_errors
        ).item()

        # ----------------------------------------------------
        # High-error pixel ratio
        #
        # Measures how much of the image contains
        # unusually high reconstruction error.
        # ----------------------------------------------------

        error_mean = torch.mean(
            flat_error
        )

        error_std = torch.std(
            flat_error
        )

        high_error_threshold = (
            error_mean +
            2.0 * error_std
        )

        high_error_pixels = (
            flat_error >
            high_error_threshold
        ).float()

        high_error_ratio = torch.mean(
            high_error_pixels
        ).item()

        # ----------------------------------------------------
        # Maximum error
        # ----------------------------------------------------

        max_error = torch.max(
            flat_error
        ).item()


    # ========================================================
    # ROBUST ANOMALY SCORE
    # ========================================================
    #
    # Stronger focus on localized high-error regions.
    #
    # Mean error       -> overall reconstruction quality
    # Top 5%           -> larger abnormal regions
    # Top 1%           -> concentrated defects
    # Top 0.5%         -> very localized defects
    # High-error ratio -> amount of suspicious area
    #
    # ========================================================

    anomaly_score = (
        0.10 * mean_error
        + 0.20 * top_5_error
        + 0.25 * top_1_error
        + 0.30 * top_05_error
        + 0.10 * high_error_ratio
        + 0.05 * max_error
    )


    return {
        "anomaly_score": float(
            anomaly_score
        ),

        "mean_error": float(
            mean_error
        ),

        "top_5_error": float(
            top_5_error
        ),

        "top_1_error": float(
            top_1_error
        ),

        "top_05_error": float(
            top_05_error
        ),

        "high_error_ratio": float(
            high_error_ratio
        ),

        "max_error": float(
            max_error
        )
    }


# ============================================================
# FINAL PREDICTION
# ============================================================

def predict_image(
    image_path: str,
    category: str
):

    if category not in CATEGORIES:
        raise ValueError(
            f"Unsupported product category: {category}"
        )

    scores = calculate_anomaly_score(
        image_path,
        category
    )

    anomaly_score = scores[
        "anomaly_score"
    ]

    threshold = load_threshold(
        category
    )

    prediction = (
        "DEFECTIVE"
        if anomaly_score > threshold
        else "NORMAL"
    )


    return {

        "prediction": prediction,

        "reconstruction_error": round(
            anomaly_score,
            6
        ),

        "anomaly_score": round(
            anomaly_score,
            6
        ),

        "mean_error": round(
            scores["mean_error"],
            6
        ),

        "top_region_error": round(
            scores["top_5_error"],
            6
        ),

        "top_5_error": round(
            scores["top_5_error"],
            6
        ),

        "top_1_error": round(
            scores["top_1_error"],
            6
        ),

        "top_05_error": round(
            scores["top_05_error"],
            6
        ),

        "high_error_ratio": round(
            scores["high_error_ratio"],
            6
        ),

        "max_error": round(
            scores["max_error"],
            6
        ),

        "threshold": round(
            threshold,
            6
        ),

        "category": category,

        "device": str(device),

        "model": (
            f"{category}_autoencoder"
        )
    }