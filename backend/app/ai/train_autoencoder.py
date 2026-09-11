from pathlib import Path

import cv2
import numpy as np
import torch

from torch import nn
from torch.utils.data import Dataset, DataLoader

from app.ai.autoencoder import ConvAutoencoder


# ==========================================
# PATHS
# ==========================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

DATASET_DIR = (
    PROJECT_ROOT
    / "dataset"
    / "mvtec_ad"
    / "bottle"
    / "train"
    / "good"
)

MODEL_DIR = (
    PROJECT_ROOT
    / "models"
)

MODEL_DIR.mkdir(
    exist_ok=True
)

MODEL_PATH = (
    MODEL_DIR
    / "bottle_autoencoder.pth"
)


# ==========================================
# SETTINGS
# ==========================================

IMAGE_SIZE = 224

BATCH_SIZE = 8

EPOCHS = 20

LEARNING_RATE = 0.0005


# ==========================================
# DATASET
# ==========================================

class MVTecGoodDataset(Dataset):

    def __init__(self, image_dir):

        self.image_paths = sorted(
            image_dir.glob("*.png")
        )

        if len(self.image_paths) == 0:

            raise RuntimeError(
                f"No PNG images found in: "
                f"{image_dir}"
            )

    def __len__(self):

        return len(
            self.image_paths
        )

    def __getitem__(self, index):

        image_path = (
            self.image_paths[index]
        )

        image = cv2.imread(
            str(image_path)
        )

        if image is None:

            raise ValueError(
                f"Unable to read image: "
                f"{image_path}"
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
            )
        )

        image = (
            image.astype(
                np.float32
            ) / 255.0
        )

        image = np.transpose(
            image,
            (2, 0, 1)
        )

        tensor = torch.tensor(
            image,
            dtype=torch.float32
        )

        return tensor


# ==========================================
# TRAINING
# ==========================================

def train():

    print(
        "\n======================================"
    )

    print(
        " VisionInspect AI - Model Training"
    )

    print(
        "======================================\n"
    )

    print(
        "Dataset:"
    )

    print(
        DATASET_DIR
    )

    if not DATASET_DIR.exists():

        raise FileNotFoundError(
            f"Dataset folder not found:\n"
            f"{DATASET_DIR}"
        )

    dataset = MVTecGoodDataset(
        DATASET_DIR
    )

    print(
        f"\nGood training images: "
        f"{len(dataset)}"
    )

    dataloader = DataLoader(
        dataset,
        batch_size=BATCH_SIZE,
        shuffle=True,
        num_workers=0
    )

    device = torch.device(
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )

    print(
        f"Training device: {device}"
    )

    model = ConvAutoencoder().to(
        device
    )

    criterion = nn.MSELoss()

    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=LEARNING_RATE,
        weight_decay=1e-5
    )

    print(
        "\nStarting training...\n"
    )

    best_loss = float("inf")

    for epoch in range(EPOCHS):

        model.train()

        total_loss = 0.0

        for images in dataloader:

            images = images.to(
                device
            )

            optimizer.zero_grad()

            reconstructed = model(
                images
            )

            loss = criterion(
                reconstructed,
                images
            )

            loss.backward()

            optimizer.step()

            total_loss += (
                loss.item()
                * images.size(0)
            )

        epoch_loss = (
            total_loss
            / len(dataset)
        )

        print(
            f"Epoch "
            f"[{epoch + 1}/{EPOCHS}] "
            f"Loss: "
            f"{epoch_loss:.6f}"
        )

        if epoch_loss < best_loss:

            best_loss = epoch_loss

            torch.save(
                model.state_dict(),
                MODEL_PATH
            )

            print(
                "  ✓ Best model saved"
            )

    print(
        "\n======================================"
    )

    print(
        " Training Completed!"
    )

    print(
        "======================================"
    )

    print(
        "\nBest training loss:"
    )

    print(
        f"{best_loss:.6f}"
    )

    print(
        "\nModel saved at:"
    )

    print(
        MODEL_PATH
    )

    print()


# ==========================================
# RUN
# ==========================================

if __name__ == "__main__":

    train()