from pathlib import Path

import cv2
import numpy as np
import torch
import torch.nn.functional as F
from torchvision import models


# ============================================================
# VISIONINSPECT AI
# PATCHCORE MODEL
# STABLE CATEGORY-SPECIFIC PATCHCORE IMPLEMENTATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

MODEL_DIR = PROJECT_ROOT / "models"
FEATURE_BANK_DIR = MODEL_DIR / "feature_banks"

IMAGE_SIZE = 224


# ============================================================
# DEVICE
# ============================================================

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)


# ============================================================
# RESNET18 FEATURE EXTRACTOR
# ============================================================

class ResNet18FeatureExtractor:

    def __init__(self):

        print(
            f"Loading ResNet18 PatchCore feature extractor "
            f"on {DEVICE}..."
        )

        weights = models.ResNet18_Weights.DEFAULT

        backbone = models.resnet18(
            weights=weights
        )

        backbone = backbone.to(DEVICE)

        backbone.eval()

        self.conv1 = backbone.conv1
        self.bn1 = backbone.bn1
        self.relu = backbone.relu
        self.maxpool = backbone.maxpool

        self.layer1 = backbone.layer1
        self.layer2 = backbone.layer2
        self.layer3 = backbone.layer3

        self.device = DEVICE

        for module in [
            self.conv1,
            self.bn1,
            self.layer1,
            self.layer2,
            self.layer3
        ]:

            for parameter in module.parameters():

                parameter.requires_grad = False

        print(
            "ResNet18 PatchCore feature extractor "
            "loaded successfully."
        )


    # ========================================================
    # FEATURE EXTRACTION
    # ========================================================

    @torch.no_grad()
    def extract_features(
        self,
        image_tensor
    ):

        x = self.conv1(
            image_tensor
        )

        x = self.bn1(
            x
        )

        x = self.relu(
            x
        )

        x = self.maxpool(
            x
        )

        x = self.layer1(
            x
        )

        layer2_features = self.layer2(
            x
        )

        layer3_features = self.layer3(
            layer2_features
        )

        layer2_resized = F.interpolate(
            layer2_features,
            size=layer3_features.shape[-2:],
            mode="bilinear",
            align_corners=False
        )

        combined_features = torch.cat(
            [
                layer2_resized,
                layer3_features
            ],
            dim=1
        )

        return combined_features


# ============================================================
# GLOBAL FEATURE EXTRACTOR
# ============================================================

FEATURE_EXTRACTOR = ResNet18FeatureExtractor()


# ============================================================
# IMAGE PREPROCESSING
# ============================================================

def preprocess_image(
    image_path: str
):

    image = cv2.imread(
        str(image_path)
    )

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
        (
            IMAGE_SIZE,
            IMAGE_SIZE
        ),
        interpolation=cv2.INTER_AREA
    )

    image = (
        image.astype(
            np.float32
        )
        / 255.0
    )

    mean = np.array(
        [
            0.485,
            0.456,
            0.406
        ],
        dtype=np.float32
    )

    std = np.array(
        [
            0.229,
            0.224,
            0.225
        ],
        dtype=np.float32
    )

    image = (
        image - mean
    ) / std

    image = np.transpose(
        image,
        (
            2,
            0,
            1
        )
    )

    tensor = torch.from_numpy(
        image
    ).unsqueeze(0)

    tensor = tensor.to(
        DEVICE
    )

    return tensor


# ============================================================
# EXTRACT IMAGE FEATURES
# ============================================================

def extract_image_features(
    image_path: str
):

    image_tensor = preprocess_image(
        image_path
    )

    with torch.no_grad():

        feature_map = (
            FEATURE_EXTRACTOR.extract_features(
                image_tensor
            )
        )

    return feature_map


# ============================================================
# FEATURE MAP -> PATCHES
# ============================================================

def feature_map_to_patches(
    feature_map
):

    if feature_map.dim() != 4:

        raise ValueError(
            "Expected feature map with "
            "shape [B, C, H, W]"
        )

    feature_map = (
        feature_map.squeeze(0)
    )

    feature_map = (
        feature_map.permute(
            1,
            2,
            0
        )
    )

    patches = (
        feature_map.reshape(
            -1,
            feature_map.shape[-1]
        )
    )

    return patches


# ============================================================
# FEATURE NORMALIZATION
# ============================================================

def normalize_features(
    features
):

    features = np.asarray(
        features,
        dtype=np.float32
    )

    norms = np.linalg.norm(
        features,
        axis=1,
        keepdims=True
    )

    norms = np.maximum(
        norms,
        1e-12
    )

    return (
        features / norms
    )


# ============================================================
# LOAD FEATURE BANK
# ============================================================

def load_feature_bank(
    category: str
):

    feature_file = (
        FEATURE_BANK_DIR
        / category
        / "features.npy"
    )

    if not feature_file.exists():

        raise FileNotFoundError(
            f"Feature bank not found for "
            f"category '{category}': "
            f"{feature_file}"
        )

    features = np.load(
        feature_file
    )

    if features.ndim != 2:

        raise ValueError(
            f"Invalid feature bank shape: "
            f"{features.shape}"
        )

    if features.shape[1] != 384:

        raise ValueError(
            f"Invalid feature dimension for "
            f"{category}. "
            f"Expected 384, got "
            f"{features.shape[1]}. "
            f"Rebuild the feature bank."
        )

    return features.astype(
        np.float32
    )


# ============================================================
# PATCHCORE SCORE
# ============================================================

def calculate_patchcore_score(
    query_features: np.ndarray,
    memory_bank: np.ndarray
):

    if query_features.ndim != 2:

        raise ValueError(
            "query_features must have "
            "shape [N, C]"
        )

    if memory_bank.ndim != 2:

        raise ValueError(
            "memory_bank must have "
            "shape [N, C]"
        )

    if (
        query_features.shape[1]
        !=
        memory_bank.shape[1]
    ):

        raise ValueError(
            "Feature dimension mismatch. "
            f"Query={query_features.shape[1]}, "
            f"Memory={memory_bank.shape[1]}"
        )

    # --------------------------------------------------------
    # Normalize both query and memory features
    # --------------------------------------------------------

    query_features = normalize_features(
        query_features
    )

    memory_bank = normalize_features(
        memory_bank
    )

    # --------------------------------------------------------
    # Cosine similarity
    # --------------------------------------------------------

    similarities = (
        query_features
        @
        memory_bank.T
    )

    similarities = np.clip(
        similarities,
        -1.0,
        1.0
    )

    # --------------------------------------------------------
    # Nearest normal patch
    # --------------------------------------------------------

    max_similarity = np.max(
        similarities,
        axis=1
    )

    distances = (
        1.0
        -
        max_similarity
    )

    distances = np.maximum(
        distances,
        0.0
    )

    total_patch_count = len(
        distances
    )

    grid_size = int(
        np.sqrt(
            total_patch_count
        )
    )

    if (
        grid_size * grid_size
        !=
        total_patch_count
    ):

        raise ValueError(
            "Patch count does not form "
            "a square map. "
            f"Patch count={total_patch_count}"
        )

    # --------------------------------------------------------
    # Anomaly map
    # --------------------------------------------------------

    raw_anomaly_map = (
        distances.reshape(
            grid_size,
            grid_size
        )
    )

    # --------------------------------------------------------
    # Sort anomaly distances
    # --------------------------------------------------------

    sorted_distances = np.sort(
        distances
    )[::-1]

    # --------------------------------------------------------
    # Top 1%
    # --------------------------------------------------------

    top_1_count = max(
        1,
        int(
            np.ceil(
                total_patch_count * 0.01
            )
        )
    )

    top_1_distance = float(
        np.mean(
            sorted_distances[
                :top_1_count
            ]
        )
    )

    # --------------------------------------------------------
    # Top 5%
    # --------------------------------------------------------

    top_5_count = max(
        1,
        int(
            np.ceil(
                total_patch_count * 0.05
            )
        )
    )

    top_5_distance = float(
        np.mean(
            sorted_distances[
                :top_5_count
            ]
        )
    )

    # --------------------------------------------------------
    # Top 10%
    # --------------------------------------------------------

    top_10_count = max(
        1,
        int(
            np.ceil(
                total_patch_count * 0.10
            )
        )
    )

    top_10_distance = float(
        np.mean(
            sorted_distances[
                :top_10_count
            ]
        )
    )

    # --------------------------------------------------------
    # Mean
    # --------------------------------------------------------

    mean_distance = float(
        np.mean(
            distances
        )
    )

    max_distance = float(
        np.max(
            distances
        )
    )

    median_distance = float(
        np.median(
            distances
        )
    )

    # --------------------------------------------------------
    # FINAL PATCHCORE SCORE
    # --------------------------------------------------------

    anomaly_score = float(
        (
            0.50 * top_1_distance
            +
            0.30 * top_5_distance
            +
            0.15 * top_10_distance
            +
            0.05 * mean_distance
        )
    )

    # --------------------------------------------------------
    # Highest anomaly patch
    # --------------------------------------------------------

    max_patch_index = int(
        np.argmax(
            distances
        )
    )

    max_patch_row = (
        max_patch_index
        //
        grid_size
    )

    max_patch_col = (
        max_patch_index
        %
        grid_size
    )

    # --------------------------------------------------------
    # Normalized anomaly map
    # --------------------------------------------------------

    map_min = float(
        np.min(
            raw_anomaly_map
        )
    )

    map_max = float(
        np.max(
            raw_anomaly_map
        )
    )

    map_range = (
        map_max
        -
        map_min
    )

    if map_range > 1e-12:

        normalized_map = (
            raw_anomaly_map
            -
            map_min
        ) / map_range

    else:

        normalized_map = np.zeros_like(
            raw_anomaly_map
        )

    # --------------------------------------------------------
    # Localization
    # --------------------------------------------------------

    localization_threshold = float(
        np.percentile(
            distances,
            90
        )
    )

    anomaly_mask = (
        raw_anomaly_map
        >=
        localization_threshold
    )

    anomalous_patch_count = int(
        np.sum(
            anomaly_mask
        )
    )

    defect_area_percentage = float(
        (
            anomalous_patch_count
            /
            total_patch_count
        )
        *
        100.0
    )

    # --------------------------------------------------------
    # Patch size
    # --------------------------------------------------------

    patch_size = (
        IMAGE_SIZE
        /
        grid_size
    )

    center_x = (
        max_patch_col
        + 0.5
    ) * patch_size

    center_y = (
        max_patch_row
        + 0.5
    ) * patch_size

    # --------------------------------------------------------
    # Location
    # --------------------------------------------------------

    if center_x < IMAGE_SIZE / 3:

        horizontal_location = "Left"

    elif center_x > IMAGE_SIZE * 2 / 3:

        horizontal_location = "Right"

    else:

        horizontal_location = "Center"

    if center_y < IMAGE_SIZE / 3:

        vertical_location = "Top"

    elif center_y > IMAGE_SIZE * 2 / 3:

        vertical_location = "Bottom"

    else:

        vertical_location = "Middle"

    location = (
        f"{vertical_location}-"
        f"{horizontal_location}"
    )

    # --------------------------------------------------------
    # Bounding box
    # --------------------------------------------------------

    anomalous_indices = np.argwhere(
        anomaly_mask
    )

    if len(anomalous_indices) > 0:

        min_row = int(
            np.min(
                anomalous_indices[:, 0]
            )
        )

        max_row = int(
            np.max(
                anomalous_indices[:, 0]
            )
        )

        min_col = int(
            np.min(
                anomalous_indices[:, 1]
            )
        )

        max_col = int(
            np.max(
                anomalous_indices[:, 1]
            )
        )

        x1 = int(
            min_col * patch_size
        )

        y1 = int(
            min_row * patch_size
        )

        x2 = int(
            (max_col + 1)
            * patch_size
        )

        y2 = int(
            (max_row + 1)
            * patch_size
        )

        bounding_box = {
            "x1": max(
                0,
                min(
                    IMAGE_SIZE,
                    x1
                )
            ),
            "y1": max(
                0,
                min(
                    IMAGE_SIZE,
                    y1
                )
            ),
            "x2": max(
                0,
                min(
                    IMAGE_SIZE,
                    x2
                )
            ),
            "y2": max(
                0,
                min(
                    IMAGE_SIZE,
                    y2
                )
            )
        }

    else:

        bounding_box = {
            "x1": 0,
            "y1": 0,
            "x2": 0,
            "y2": 0
        }

    # --------------------------------------------------------
    # Return
    # --------------------------------------------------------

    return {

        "anomaly_score":
            round(
                anomaly_score,
                6
            ),

        "max_distance":
            round(
                max_distance,
                6
            ),

        "mean_distance":
            round(
                mean_distance,
                6
            ),

        "median_distance":
            round(
                median_distance,
                6
            ),

        "top_1_distance":
            round(
                top_1_distance,
                6
            ),

        "top_5_distance":
            round(
                top_5_distance,
                6
            ),

        "top_10_distance":
            round(
                top_10_distance,
                6
            ),

        "top_patch_count":
            top_1_count,

        "top_5_patch_count":
            top_5_count,

        "top_10_patch_count":
            top_10_count,

        "total_patch_count":
            total_patch_count,

        "anomaly_map":
            normalized_map.tolist(),

        "raw_anomaly_map":
            raw_anomaly_map.tolist(),

        "anomaly_map_size": [
            grid_size,
            grid_size
        ],

        "max_anomaly_patch": {

            "row":
                max_patch_row,

            "column":
                max_patch_col,

            "score":
                round(
                    max_distance,
                    6
                )
        },

        "anomalous_patch_count":
            anomalous_patch_count,

        "defect_area_percentage":
            round(
                defect_area_percentage,
                2
            ),

        "defect_center": {

            "x":
                round(
                    float(center_x),
                    2
                ),

            "y":
                round(
                    float(center_y),
                    2
                )
        },

        "location":
            location,

        "bounding_box":
            bounding_box
    }


# ============================================================
# PREDICTION
# ============================================================

def predict_with_feature_bank(
    image_path: str,
    category: str
):

    category = (
        category
        .strip()
        .lower()
    )

    print(
        "=" * 70
    )

    print(
        "PATCHCORE INSPECTION"
    )

    print(
        f"Category : {category}"
    )

    print(
        f"Image    : {image_path}"
    )

    # --------------------------------------------------------
    # Extract query features
    # --------------------------------------------------------

    feature_map = (
        extract_image_features(
            image_path
        )
    )

    query_features = (
        feature_map_to_patches(
            feature_map
        )
    )

    query_features = (
        query_features
        .detach()
        .cpu()
        .numpy()
        .astype(
            np.float32
        )
    )

    # --------------------------------------------------------
    # Load category-specific memory bank
    # --------------------------------------------------------

    memory_bank = (
        load_feature_bank(
            category
        )
    )

    # --------------------------------------------------------
    # Verify dimensions
    # --------------------------------------------------------

    if (
        query_features.shape[1]
        !=
        memory_bank.shape[1]
    ):

        raise ValueError(
            "Feature dimension mismatch. "
            f"Query={query_features.shape[1]}, "
            f"Memory={memory_bank.shape[1]}. "
            "Rebuild feature banks."
        )

    # --------------------------------------------------------
    # Calculate score
    # --------------------------------------------------------

    result = (
        calculate_patchcore_score(
            query_features,
            memory_bank
        )
    )

    # --------------------------------------------------------
    # Metadata
    # --------------------------------------------------------

    result.update({

        "category":
            category,

        "model":
            "PatchCore-Style Multi-Scale ResNet18",

        "device":
            str(
                DEVICE
            ),

        "feature_dimension":
            int(
                query_features.shape[1]
            ),

        "query_patch_count":
            int(
                query_features.shape[0]
            ),

        "memory_bank_patch_count":
            int(
                memory_bank.shape[0]
            ),

        "input_size":
            f"{IMAGE_SIZE} × {IMAGE_SIZE}",

        "detection_method":
            "Category-Specific Feature Memory Bank"
    })

    print(
        f"Anomaly score: "
        f"{result['anomaly_score']:.6f}"
    )

    print(
        f"Max distance : "
        f"{result['max_distance']:.6f}"
    )

    print(
        f"Mean distance: "
        f"{result['mean_distance']:.6f}"
    )

    print(
        f"Memory patches: "
        f"{len(memory_bank)}"
    )

    print(
        "=" * 70
    )

    return result