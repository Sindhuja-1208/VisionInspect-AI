from pathlib import Path

import cv2
import numpy as np
import torch
import torch.nn.functional as F
from torchvision import models


# ============================================================
# PATHS
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
# RESNET MULTI-SCALE FEATURE EXTRACTOR
# ============================================================

class ResNet18FeatureExtractor:

    def __init__(self):

        print(
            f"Loading multi-scale ResNet18 feature extractor "
            f"on {DEVICE}..."
        )

        weights = models.ResNet18_Weights.DEFAULT

        backbone = models.resnet18(weights=weights)

        backbone = backbone.to(DEVICE)
        backbone.eval()

        # We use:
        #
        # layer2 -> 28 x 28 spatial features
        # layer3 -> 14 x 14 spatial features
        #
        # layer2 is resized to 14 x 14 and combined
        # with layer3.
        #
        # Final:
        # 14 x 14 patches = 196 patches
        # feature dimension = 128 + 256 = 384

        self.conv1 = backbone.conv1
        self.bn1 = backbone.bn1
        self.relu = backbone.relu
        self.maxpool = backbone.maxpool

        self.layer1 = backbone.layer1
        self.layer2 = backbone.layer2
        self.layer3 = backbone.layer3

        self.device = DEVICE

        # Freeze model
        for module in [
            self.conv1,
            self.bn1,
            self.layer1,
            self.layer2,
            self.layer3
        ]:
            for parameter in module.parameters():
                parameter.requires_grad = False

        print("Multi-scale ResNet18 feature extractor loaded successfully.")


    # ========================================================
    # FORWARD FEATURE EXTRACTION
    # ========================================================

    @torch.no_grad()
    def extract_features(self, image_tensor):

        x = self.conv1(image_tensor)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.maxpool(x)

        x = self.layer1(x)

        # 128 channels, approximately 28 x 28
        layer2_features = self.layer2(x)

        # 256 channels, approximately 14 x 14
        layer3_features = self.layer3(layer2_features)

        # Resize layer2 to layer3 spatial resolution
        layer2_resized = F.interpolate(
            layer2_features,
            size=layer3_features.shape[-2:],
            mode="bilinear",
            align_corners=False
        )

        # Combine local + deeper semantic information
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

def preprocess_image(image_path: str):

    image = cv2.imread(str(image_path))

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

    image = image.astype(np.float32) / 255.0

    # ImageNet normalization
    mean = np.array(
        [0.485, 0.456, 0.406],
        dtype=np.float32
    )

    std = np.array(
        [0.229, 0.224, 0.225],
        dtype=np.float32
    )

    image = (image - mean) / std

    # HWC -> CHW
    image = np.transpose(
        image,
        (2, 0, 1)
    )

    tensor = torch.from_numpy(
        image
    ).unsqueeze(0)

    tensor = tensor.to(DEVICE)

    return tensor


# ============================================================
# FEATURE EXTRACTION
# ============================================================

def extract_image_features(image_path: str):

    image_tensor = preprocess_image(
        image_path
    )

    with torch.no_grad():

        feature_map = FEATURE_EXTRACTOR.extract_features(
            image_tensor
        )

    return feature_map


# ============================================================
# FEATURE MAP -> PATCHES
# ============================================================

def feature_map_to_patches(feature_map):

    """
    Converts:

        [1, C, H, W]

    into:

        [H*W, C]

    For the current multi-scale extractor:

        [1, 384, 14, 14]

    becomes:

        [196, 384]
    """

    if feature_map.dim() != 4:
        raise ValueError(
            "Expected feature map with shape [B, C, H, W]"
        )

    # Remove batch dimension
    feature_map = feature_map.squeeze(0)

    # C,H,W -> H,W,C
    feature_map = feature_map.permute(
        1,
        2,
        0
    )

    # H,W,C -> H*W,C
    patches = feature_map.reshape(
        -1,
        feature_map.shape[-1]
    )

    return patches


# ============================================================
# FEATURE NORMALIZATION
# ============================================================

def normalize_features(features):

    norms = np.linalg.norm(
        features,
        axis=1,
        keepdims=True
    )

    norms = np.maximum(
        norms,
        1e-12
    )

    return features / norms


# ============================================================
# SAVE FEATURE BANK
# ============================================================

def save_feature_bank(
    category: str,
    features: np.ndarray
):

    category_dir = (
        FEATURE_BANK_DIR / category
    )

    category_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    feature_file = (
        category_dir / "features.npy"
    )

    np.save(
        feature_file,
        features
    )

    return feature_file


# ============================================================
# LOAD FEATURE BANK
# ============================================================

def load_feature_bank(category: str):

    feature_file = (
        FEATURE_BANK_DIR
        / category
        / "features.npy"
    )

    if not feature_file.exists():

        raise FileNotFoundError(
            f"Feature bank not found for category "
            f"'{category}': {feature_file}"
        )

    features = np.load(
        feature_file
    )

    if features.ndim != 2:

        raise ValueError(
            f"Invalid feature bank shape: "
            f"{features.shape}"
        )

    return features


# ============================================================
# PATCHCORE DISTANCE
# ============================================================

def calculate_patchcore_score(
    query_features: np.ndarray,
    memory_bank: np.ndarray
):

    """
    PatchCore-style nearest-neighbour anomaly score.

    Query:
        patches from uploaded image

    Memory bank:
        patches from normal training images

    We use cosine distance.

    Higher score = more anomalous.
    """

    query_features = normalize_features(
        query_features.astype(np.float32)
    )

    memory_bank = normalize_features(
        memory_bank.astype(np.float32)
    )

    # --------------------------------------------------------
    # Calculate cosine similarity
    # --------------------------------------------------------

    similarities = (
        query_features @ memory_bank.T
    )

    # --------------------------------------------------------
    # For every query patch find nearest normal patch
    # --------------------------------------------------------

    max_similarity = np.max(
        similarities,
        axis=1
    )

    # cosine distance
    distances = 1.0 - max_similarity

    distances = np.maximum(
        distances,
        0.0
    )

    # --------------------------------------------------------
    # Sort patch anomaly distances
    # --------------------------------------------------------

    sorted_distances = np.sort(
        distances
    )[::-1]

    number_of_patches = len(
        sorted_distances
    )

    # --------------------------------------------------------
    # Top 1% patches
    # --------------------------------------------------------

    top_count = max(
        1,
        int(np.ceil(
            number_of_patches * 0.01
        ))
    )

    top_distances = (
        sorted_distances[:top_count]
    )

    # --------------------------------------------------------
    # Additional statistics
    # --------------------------------------------------------

    max_distance = float(
        np.max(distances)
    )

    mean_distance = float(
        np.mean(distances)
    )

    top_5_count = max(
        1,
        int(np.ceil(
            number_of_patches * 0.05
        ))
    )

    top_5_distance = float(
        np.mean(
            sorted_distances[:top_5_count]
        )
    )

    top_1_distance = float(
        np.mean(
            sorted_distances[:top_count]
        )
    )

    # --------------------------------------------------------
    # Final anomaly score
    # --------------------------------------------------------

    # Main score is dominated by the most anomalous patches.
    anomaly_score = float(
        0.65 * top_1_distance
        + 0.25 * top_5_distance
        + 0.10 * mean_distance
    )

    return {
        "anomaly_score": anomaly_score,
        "max_distance": max_distance,
        "mean_distance": mean_distance,
        "top_5_distance": top_5_distance,
        "top_1_distance": top_1_distance,
        "top_patch_count": int(top_count),
        "total_patch_count": int(number_of_patches)
    }


# ============================================================
# PREDICTION
# ============================================================

def predict_with_feature_bank(
    image_path: str,
    category: str
):

    # --------------------------------------------------------
    # Extract multi-scale features
    # --------------------------------------------------------

    feature_map = extract_image_features(
        image_path
    )

    # --------------------------------------------------------
    # Convert feature map to patches
    # --------------------------------------------------------

    query_features = feature_map_to_patches(
        feature_map
    )

    query_features = (
        query_features
        .detach()
        .cpu()
        .numpy()
        .astype(np.float32)
    )

    # --------------------------------------------------------
    # Load category memory bank
    # --------------------------------------------------------

    memory_bank = load_feature_bank(
        category
    )

    # --------------------------------------------------------
    # Check feature dimensions
    # --------------------------------------------------------

    if query_features.shape[1] != memory_bank.shape[1]:

        raise ValueError(
            "Feature dimension mismatch. "
            f"Query={query_features.shape[1]}, "
            f"MemoryBank={memory_bank.shape[1]}. "
            "Rebuild the feature banks using the current "
            "PatchCore extractor."
        )

    # --------------------------------------------------------
    # Calculate score
    # --------------------------------------------------------

    result = calculate_patchcore_score(
        query_features,
        memory_bank
    )

    # --------------------------------------------------------
    # Add metadata
    # --------------------------------------------------------

    result.update({

        "category": category,

        "model": "PatchCore-Style Multi-Scale ResNet18",

        "device": str(DEVICE),

        "feature_dimension": int(
            query_features.shape[1]
        ),

        "query_patch_count": int(
            query_features.shape[0]
        ),

        "memory_bank_patch_count": int(
            memory_bank.shape[0]
        )
    })

    return result