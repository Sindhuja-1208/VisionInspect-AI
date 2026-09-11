from pathlib import Path
import random
import time

import numpy as np

from app.ai.patchcore_model import (
    extract_image_features,
    feature_map_to_patches,
    normalize_features,
    save_feature_bank,
)


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATASET_DIR = (
    PROJECT_ROOT
    / "dataset"
    / "mvtec_ad"
)


# ============================================================
# CATEGORIES
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
# SETTINGS
# ============================================================

MAX_IMAGES_PER_CATEGORY = 100

RANDOM_SEED = 42

random.seed(RANDOM_SEED)


# ============================================================
# GET GOOD TRAINING IMAGES
# ============================================================

def get_good_images(category):

    good_dir = (
        DATASET_DIR
        / category
        / "train"
        / "good"
    )

    if not good_dir.exists():

        raise FileNotFoundError(
            f"Good training directory not found:\n"
            f"{good_dir}"
        )

    images = sorted(
        list(good_dir.glob("*.png"))
    )

    if not images:

        raise FileNotFoundError(
            f"No PNG images found in:\n"
            f"{good_dir}"
        )

    # Shuffle deterministically
    random.shuffle(images)

    # Limit number of images
    images = images[
        :MAX_IMAGES_PER_CATEGORY
    ]

    return images


# ============================================================
# BUILD ONE FEATURE BANK
# ============================================================

def build_feature_bank(category):

    print()
    print("=" * 80)
    print(
        f"BUILDING MULTI-SCALE FEATURE BANK: "
        f"{category.upper()}"
    )
    print("=" * 80)

    start_time = time.time()

    image_files = get_good_images(
        category
    )

    print(
        f"Normal images selected: "
        f"{len(image_files)}"
    )

    all_features = []

    successful_images = 0

    failed_images = 0

    # --------------------------------------------------------
    # Process images
    # --------------------------------------------------------

    for index, image_path in enumerate(
        image_files,
        start=1
    ):

        try:

            # ----------------------------------------------
            # Extract multi-scale feature map
            #
            # Expected:
            #
            # [1, 384, 14, 14]
            # ----------------------------------------------

            feature_map = extract_image_features(
                str(image_path)
            )

            # ----------------------------------------------
            # Convert to patches
            #
            # Expected:
            #
            # 196 x 384
            # ----------------------------------------------

            patches = feature_map_to_patches(
                feature_map
            )

            # ----------------------------------------------
            # Move to NumPy
            # ----------------------------------------------

            patches = (
                patches
                .detach()
                .cpu()
                .numpy()
                .astype(np.float32)
            )

            # ----------------------------------------------
            # Normalize each patch
            # ----------------------------------------------

            patches = normalize_features(
                patches
            )

            # ----------------------------------------------
            # Validate shape
            # ----------------------------------------------

            if patches.ndim != 2:

                raise ValueError(
                    f"Unexpected patch shape: "
                    f"{patches.shape}"
                )

            if patches.shape[1] != 384:

                raise ValueError(
                    f"Expected 384 features, "
                    f"got {patches.shape[1]}"
                )

            # ----------------------------------------------
            # Add to feature bank
            # ----------------------------------------------

            all_features.append(
                patches
            )

            successful_images += 1

            print(
                f"[{index:3d}/{len(image_files):3d}] "
                f"{image_path.name} -> "
                f"{patches.shape[0]} patches "
                f"x {patches.shape[1]} features"
            )

        except Exception as error:

            failed_images += 1

            print(
                f"[{index:3d}/{len(image_files):3d}] "
                f"{image_path.name} -> FAILED"
            )

            print(
                f"    Error: {error}"
            )

    # --------------------------------------------------------
    # Validate
    # --------------------------------------------------------

    if not all_features:

        raise RuntimeError(
            f"No features were generated "
            f"for category: {category}"
        )

    # --------------------------------------------------------
    # Combine all patches
    # --------------------------------------------------------

    feature_bank = np.vstack(
        all_features
    ).astype(np.float32)

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    saved_path = save_feature_bank(
        category,
        feature_bank
    )

    elapsed = (
        time.time() - start_time
    )

    print()
    print(
        "Feature bank created successfully."
    )

    print(
        f"Category:       {category}"
    )

    print(
        f"Images used:    {successful_images}"
    )

    print(
        f"Failed images:  {failed_images}"
    )

    print(
        f"Total patches:  {feature_bank.shape[0]}"
    )

    print(
        f"Feature size:   {feature_bank.shape[1]}"
    )

    print(
        f"Saved to:       {saved_path}"
    )

    print(
        f"Time:            {elapsed:.2f} seconds"
    )

    return {
        "category": category,
        "success": True,
        "images": successful_images,
        "failed": failed_images,
        "patches": feature_bank.shape[0],
        "feature_size": feature_bank.shape[1],
        "time": elapsed,
    }


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 80)
    print(
        "VISIONINSPECT AI"
    )
    print(
        "MULTI-SCALE PATCHCORE FEATURE BANK BUILDER"
    )
    print("=" * 80)

    print()
    print(
        f"Dataset directory:\n{DATASET_DIR}"
    )

    print()
    print(
        f"Categories: {len(CATEGORIES)}"
    )

    print(
        f"Maximum images/category: "
        f"{MAX_IMAGES_PER_CATEGORY}"
    )

    print()
    print(
        "Feature configuration:"
    )

    print(
        "  ResNet18 layer2 + layer3"
    )

    print(
        "  Feature dimensions: 384"
    )

    print(
        "  Spatial grid: 14 x 14"
    )

    print(
        "  Patches/image: 196"
    )

    print()
    print(
        "Existing feature banks will be replaced "
        "with the new multi-scale feature banks."
    )

    print()

    overall_start = time.time()

    successful = []

    failed = []

    # --------------------------------------------------------
    # Build every category
    # --------------------------------------------------------

    for category in CATEGORIES:

        try:

            result = build_feature_bank(
                category
            )

            successful.append(
                result
            )

        except Exception as error:

            print()
            print(
                f"FAILED CATEGORY: "
                f"{category}"
            )

            print(
                f"Error: {error}"
            )

            failed.append(
                {
                    "category": category,
                    "error": str(error)
                }
            )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    total_time = (
        time.time() - overall_start
    )

    print()
    print("=" * 80)
    print(
        "MULTI-SCALE FEATURE BANK BUILD SUMMARY"
    )
    print("=" * 80)

    print(
        f"Successful: "
        f"{len(successful)}/{len(CATEGORIES)}"
    )

    print(
        f"Failed:     "
        f"{len(failed)}/{len(CATEGORIES)}"
    )

    print(
        f"Total time: "
        f"{total_time / 60:.2f} minutes"
    )

    print()

    if successful:

        print(
            "SUCCESSFUL CATEGORIES:"
        )

        for item in successful:

            print(
                f"  [OK] "
                f"{item['category']} "
                f"-> "
                f"{item['patches']} patches, "
                f"{item['feature_size']} features"
            )

    print()

    if failed:

        print(
            "FAILED CATEGORIES:"
        )

        for item in failed:

            print(
                f"  [FAILED] "
                f"{item['category']}"
            )

            print(
                f"      {item['error']}"
            )

    print()

    if len(successful) == len(CATEGORIES):

        print(
            "ALL 15 CATEGORY FEATURE BANKS "
            "CREATED SUCCESSFULLY."
        )

    else:

        print(
            "WARNING: Some feature banks failed."
        )

    print()
    print(
        "Feature bank building completed."
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()