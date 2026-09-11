from app.services.image_service import (
    load_image,
    get_image_quality,
    preprocess_image
)

from app.services.dataset_service import (
    get_sample_image
)


print("\n======================================")
print("      Image Processing Test")
print("======================================\n")


# Get a sample image from MVTec AD
sample_image = get_sample_image("bottle")


if sample_image is None:

    print("ERROR: Sample image not found.")

else:

    print("Sample image:")
    print(sample_image)

    # Load image
    image = load_image(sample_image)

    print("\nOriginal image:")
    print("Shape:", image.shape)

    # Image quality analysis
    quality = get_image_quality(image)

    print("\nImage Quality:")
    print("Width:", quality["width"])
    print("Height:", quality["height"])
    print("Brightness:", quality["brightness"])
    print("Sharpness:", quality["sharpness"])

    # Preprocessing
    processed = preprocess_image(image)

    print("\nAfter preprocessing:")
    print("Shape:", processed.shape)
    print(
        "Minimum pixel value:",
        processed.min()
    )
    print(
        "Maximum pixel value:",
        processed.max()
    )


print("\n======================================")
print("          Test Complete")
print("======================================")