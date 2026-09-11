from app.services.dataset_service import (
    check_dataset,
    get_sample_image,
    load_image,
    preprocess_image
)


print("\n======================================")
print("       MVTec AD Dataset Test")
print("======================================\n")


# Check dataset

result = check_dataset()

print("Dataset Available:", result["available"])


if not result["available"]:

    print(result["message"])

else:

    print(
        "Dataset Path:",
        result["dataset_path"]
    )

    print(
        "Categories:",
        result["category_count"]
    )

    print("\nAvailable Categories:")

    for category in result["categories"]:
        print(" -", category)


    # --------------------------------------------------------
    # Test sample image
    # --------------------------------------------------------

    sample_category = result["categories"][0]

    print(
        f"\nTesting category: {sample_category}"
    )


    sample_image = get_sample_image(
        sample_category
    )


    if sample_image is None:

        print(
            "No sample image found."
        )

    else:

        print(
            "Sample image:",
            sample_image
        )


        # Load image

        image = load_image(
            sample_image
        )

        print(
            "Original image shape:",
            image.shape
        )


        # Preprocess

        processed = preprocess_image(
            image
        )

        print(
            "Processed image shape:",
            processed.shape
        )

        print(
            "Pixel value range:",
            processed.min(),
            "to",
            processed.max()
        )


print("\n======================================")
print("             Test Complete")
print("======================================")