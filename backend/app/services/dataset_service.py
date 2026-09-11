from pathlib import Path
import cv2


# ============================================================
# MVTec AD DATASET PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

DATASET_DIR = (
    PROJECT_ROOT
    / "dataset"
    / "mvtec_ad"
)


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
# CHECK DATASET
# ============================================================

def check_dataset():
    """
    Check whether the MVTec AD dataset exists.
    """

    if not DATASET_DIR.exists():
        return {
            "available": False,
            "message": f"Dataset not found at {DATASET_DIR}"
        }

    available_categories = []

    for category in CATEGORIES:

        category_path = DATASET_DIR / category

        if category_path.exists():
            available_categories.append(category)

    return {
        "available": True,
        "dataset_path": str(DATASET_DIR),
        "category_count": len(available_categories),
        "categories": available_categories
    }


# ============================================================
# GET SAMPLE IMAGE
# ============================================================

def get_sample_image(category: str):
    """
    Find one sample training image from a category.
    """

    category_path = DATASET_DIR / category

    if not category_path.exists():
        return None

    train_path = category_path / "train"

    if not train_path.exists():
        return None


    # MVTec training images are generally
    # inside a 'good' folder.

    good_path = train_path / "good"

    if not good_path.exists():
        return None


    image_files = list(good_path.glob("*.png"))

    if not image_files:
        return None


    return image_files[0]


# ============================================================
# LOAD IMAGE
# ============================================================

def load_image(image_path):
    """
    Load an image using OpenCV.
    """

    image = cv2.imread(
        str(image_path)
    )

    if image is None:
        raise ValueError(
            f"Unable to read image: {image_path}"
        )

    return image


# ============================================================
# BASIC PREPROCESSING
# ============================================================

def preprocess_image(image):
    """
    Basic image preprocessing for the AI pipeline.

    Steps:
    1. Resize
    2. Convert BGR → RGB
    3. Normalize pixel values
    """

    resized = cv2.resize(
        image,
        (224, 224)
    )

    rgb_image = cv2.cvtColor(
        resized,
        cv2.COLOR_BGR2RGB
    )

    normalized = rgb_image / 255.0

    return normalized