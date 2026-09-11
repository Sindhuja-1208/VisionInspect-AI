from pathlib import Path
import cv2
import numpy as np


def load_image(image_path: str):
    """
    Load an image from the given path.
    """

    path = Path(image_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Image not found: {image_path}"
        )

    image = cv2.imread(str(path))

    if image is None:
        raise ValueError(
            f"Unable to read image: {image_path}"
        )

    return image


def get_image_quality(image):
    """
    Calculate basic image quality information.
    """

    height, width = image.shape[:2]

    # Convert to grayscale
    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    # Calculate brightness
    brightness = float(np.mean(gray))

    # Calculate sharpness using Laplacian variance
    sharpness = float(
        cv2.Laplacian(
            gray,
            cv2.CV_64F
        ).var()
    )

    return {
        "width": width,
        "height": height,
        "brightness": round(brightness, 2),
        "sharpness": round(sharpness, 2)
    }


def preprocess_image(image):
    """
    Preprocess an image before AI inspection.

    Steps:
    1. Resize to 224 x 224
    2. Convert BGR to RGB
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

    normalized = rgb_image.astype(
        np.float32
    ) / 255.0

    return normalized


def preprocess_image_from_path(image_path: str):
    """
    Complete preprocessing pipeline for an image file.
    """

    image = load_image(image_path)

    quality = get_image_quality(image)

    processed_image = preprocess_image(image)

    return {
        "quality": quality,
        "processed_shape": list(
            processed_image.shape
        ),
        "processed_image": processed_image
    }