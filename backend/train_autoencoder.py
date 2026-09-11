from pathlib import Path

import cv2
import numpy as np

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

from app.services.anomaly_model import ConvAutoencoder


# =====================================================
# CONFIGURATION
# =====================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATASET_DIR = (
    PROJECT_ROOT
    / "dataset"
    / "mvtec_ad"
)

MODEL_DIR = (
    PROJECT_ROOT
    / "models"
)

MODEL_DIR.mkdir(
    parents=True,
    exist_ok=True
)


CATEGORY = "bottle"

IMAGE_SIZE = 128

BATCH_SIZE = 8

EPOCHS = 10

LEARNING_RATE = 0.001

MODEL_PATH = (
    MODEL_DIR
    / "bottle_autoencoder.pth"
)


# =====================================================
# DATASET
# =====================================================

class MVTecGoodDataset(Dataset):

    def __init__(self, image_paths):

        self.image_paths = image_paths


    def __len__(self):

        return len(
            self.image_paths
        )


    def __getitem__(self, index):

        image_path = self.image_paths[index]

        image = cv2.imread(
            str(image_path)
        )

        if image is None:

            raise ValueError(
                f"Unable to read image: {image_path}"
            )

        # BGR → RGB

        image = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2RGB
        )

        # Resize

        image = cv2.resize(
            image,
            (IMAGE_SIZE, IMAGE_SIZE)
        )

        # Normalize 0 → 1

        image = (
            image.astype(
                np.float32
            )
            / 255.0
        )

        # HWC → CHW

        image = np.transpose(
            image,
            (2, 0, 1)
        )

        tensor = torch.tensor(
            image,
            dtype=torch.float32
        )

        return tensor


# =====================================================
# FIND GOOD TRAINING IMAGES
# =====================================================

good_dir = (
    DATASET_DIR
    / CATEGORY
    / "train"
    / "good"
)


if not good_dir.exists():

    raise FileNotFoundError(
        f"Training folder not found:\n{good_dir}"
    )


image_paths = sorted(
    good_dir.glob("*.png")
)


print("\n======================================")
print("     MVTec Autoencoder Training")
print("======================================\n")

print(
    "Category:",
    CATEGORY
)

print(
    "Training folder:",
    good_dir
)

print(
    "Good images found:",
    len(image_paths)
)


if len(image_paths) == 0:

    raise ValueError(
        "No training images found."
    )


# =====================================================
# DATASET + DATALOADER
# =====================================================

dataset = MVTecGoodDataset(
    image_paths
)


dataloader = DataLoader(
    dataset,
    batch_size=BATCH_SIZE,
    shuffle=True
)


# =====================================================
# DEVICE
# =====================================================

device = torch.device(
    "cuda"
    if torch.cuda.is_available()
    else "cpu"
)


print(
    "Device:",
    device
)


# =====================================================
# MODEL
# =====================================================

model = ConvAutoencoder()

model = model.to(device)


# =====================================================
# LOSS + OPTIMIZER
# =====================================================

criterion = nn.MSELoss()

optimizer = torch.optim.Adam(
    model.parameters(),
    lr=LEARNING_RATE
)


# =====================================================
# TRAINING
# =====================================================

model.train()


for epoch in range(EPOCHS):

    total_loss = 0.0


    for images in dataloader:

        images = images.to(
            device
        )


        # Forward pass

        reconstructed = model(
            images
        )


        # Reconstruction loss

        loss = criterion(
            reconstructed,
            images
        )


        # Backpropagation

        optimizer.zero_grad()

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
        f"{epoch + 1}/{EPOCHS} "
        f"- Loss: "
        f"{epoch_loss:.6f}"
    )


# =====================================================
# SAVE MODEL
# =====================================================

torch.save(
    model.state_dict(),
    MODEL_PATH
)


print("\n======================================")
print("       Training Completed")
print("======================================\n")

print(
    "Model saved at:"
)

print(
    MODEL_PATH
)

print(
    "\nYou can now use this model "
    "for anomaly detection."
)