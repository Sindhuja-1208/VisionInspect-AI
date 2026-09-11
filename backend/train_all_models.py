from pathlib import Path
import time
import cv2
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

from app.ai.autoencoder import ConvAutoencoder


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATASET_DIR = PROJECT_ROOT / "dataset" / "mvtec_ad"
MODEL_DIR = PROJECT_ROOT / "models"

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

IMAGE_SIZE = 224
BATCH_SIZE = 8
EPOCHS = 10
LEARNING_RATE = 0.001

device = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

MODEL_DIR.mkdir(exist_ok=True)


# ============================================================
# DATASET
# ============================================================

class MVTecGoodDataset(Dataset):

    def __init__(self, image_paths):
        self.image_paths = image_paths

    def __len__(self):
        return len(self.image_paths)

    def __getitem__(self, index):

        image_path = self.image_paths[index]

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
            (IMAGE_SIZE, IMAGE_SIZE)
        )

        image = image.astype(
            np.float32
        ) / 255.0

        image = np.transpose(
            image,
            (2, 0, 1)
        )

        tensor = torch.tensor(
            image,
            dtype=torch.float32
        )

        return tensor


# ============================================================
# TRAIN ONE CATEGORY
# ============================================================

def train_category(category):

    print("\n" + "=" * 70)
    print(f"TRAINING CATEGORY: {category.upper()}")
    print("=" * 70)

    category_dir = (
        DATASET_DIR
        / category
        / "train"
        / "good"
    )

    if not category_dir.exists():

        print(
            f"ERROR: Training directory not found:"
            f"\n{category_dir}"
        )

        return False

    image_paths = sorted(
        category_dir.glob("*.png")
    )

    if len(image_paths) == 0:

        print(
            f"ERROR: No PNG images found for {category}"
        )

        return False

    print(
        f"Training images: {len(image_paths)}"
    )

    dataset = MVTecGoodDataset(
        image_paths
    )

    dataloader = DataLoader(
        dataset,
        batch_size=BATCH_SIZE,
        shuffle=True,
        num_workers=0
    )

    model = ConvAutoencoder().to(device)

    criterion = nn.MSELoss()

    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=LEARNING_RATE
    )

    best_loss = float("inf")

    model_path = (
        MODEL_DIR
        / f"{category}_autoencoder.pth"
    )

    start_time = time.time()

    for epoch in range(EPOCHS):

        model.train()

        running_loss = 0.0

        for images in dataloader:

            images = images.to(device)

            optimizer.zero_grad()

            reconstructed = model(images)

            loss = criterion(
                reconstructed,
                images
            )

            loss.backward()

            optimizer.step()

            running_loss += (
                loss.item()
                * images.size(0)
            )

        epoch_loss = (
            running_loss
            / len(dataset)
        )

        print(
            f"Epoch [{epoch + 1:02d}/{EPOCHS}] "
            f"Loss: {epoch_loss:.6f}"
        )

        if epoch_loss < best_loss:

            best_loss = epoch_loss

            torch.save(
                model.state_dict(),
                model_path
            )

    elapsed = time.time() - start_time

    print("\nTraining completed!")

    print(
        f"Category: {category}"
    )

    print(
        f"Best Loss: {best_loss:.6f}"
    )

    print(
        f"Model saved: {model_path}"
    )

    print(
        f"Training time: {elapsed / 60:.2f} minutes"
    )

    return True


# ============================================================
# TRAIN ALL CATEGORIES
# ============================================================

def main():

    print("=" * 70)
    print("VISIONINSPECT AI - MVTec AD MODEL TRAINING")
    print("=" * 70)

    print(
        f"Dataset: {DATASET_DIR}"
    )

    print(
        f"Device: {device}"
    )

    print(
        f"Categories: {len(CATEGORIES)}"
    )

    print(
        f"Epochs per category: {EPOCHS}"
    )

    print("=" * 70)

    overall_start = time.time()

    successful = []
    failed = []

    for index, category in enumerate(
        CATEGORIES,
        start=1
    ):

        print(
            f"\n\nCATEGORY {index}/{len(CATEGORIES)}"
        )

        try:

            success = train_category(
                category
            )

            if success:
                successful.append(category)
            else:
                failed.append(category)

        except Exception as error:

            print(
                f"\nERROR while training {category}:"
            )

            print(error)

            failed.append(category)

    total_time = (
        time.time()
        - overall_start
    )

    print("\n\n" + "=" * 70)
    print("TRAINING SUMMARY")
    print("=" * 70)

    print(
        f"Successful: {len(successful)}"
    )

    print(
        f"Failed: {len(failed)}"
    )

    print(
        f"Total training time: "
        f"{total_time / 60:.2f} minutes"
    )

    print("\nSuccessful categories:")

    for category in successful:
        print(
            f"  ✓ {category}"
        )

    if failed:

        print("\nFailed categories:")

        for category in failed:
            print(
                f"  ✗ {category}"
            )

    print("\nModel directory:")

    print(MODEL_DIR)

    print("=" * 70)


if __name__ == "__main__":
    main()