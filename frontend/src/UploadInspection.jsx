import { useRef, useState } from "react";

const API_BASE_URL = "http://127.0.0.1:8000";

const CATEGORIES = [
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
];

function UploadInspection({ onUploadSuccess }) {
  const fileInputRef = useRef(null);

  const [selectedFile, setSelectedFile] = useState(null);
  const [category, setCategory] = useState("bottle");
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState("");
  const [messageType, setMessageType] = useState("");
  const [preview, setPreview] = useState(null);

  const formatCategory = (value) => {
    return value
      .replace("_", " ")
      .replace(/\b\w/g, (char) => char.toUpperCase());
  };

  const handleFileChange = (event) => {
    const file = event.target.files?.[0];

    if (!file) {
      return;
    }

    const allowedTypes = [
      "image/jpeg",
      "image/png",
      "image/bmp",
    ];

    if (!allowedTypes.includes(file.type)) {
      setMessage(
        "Please select a JPG, PNG or BMP image."
      );
      setMessageType("error");
      setSelectedFile(null);
      setPreview(null);
      return;
    }

    setSelectedFile(file);
    setMessage("");
    setMessageType("");

    const imageUrl = URL.createObjectURL(file);
    setPreview(imageUrl);
  };

  const openFilePicker = () => {
    fileInputRef.current?.click();
  };

  const clearSelection = () => {
    setSelectedFile(null);
    setPreview(null);
    setMessage("");
    setMessageType("");

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setMessage("Please select a product image first.");
      setMessageType("error");
      return;
    }

    const token = localStorage.getItem("access_token");

    if (!token) {
      setMessage(
        "Authentication token not found. Please login again."
      );
      setMessageType("error");
      return;
    }

    setUploading(true);
    setMessage("");
    setMessageType("");

    const formData = new FormData();

    formData.append("file", selectedFile);
    formData.append("category", category);

    try {
      const response = await fetch(
        `${API_BASE_URL}/inspections/upload`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
          },
          body: formData,
        }
      );

      const data = await response.json();

      if (response.status === 401) {
        localStorage.clear();
        window.location.reload();
        return;
      }

      if (!response.ok) {
        throw new Error(
          data.detail || "Inspection failed."
        );
      }

      setMessage(
        `Inspection completed successfully — ${data.result}`
      );
      setMessageType("success");

      clearSelection();

      if (onUploadSuccess) {
        onUploadSuccess();
      }
    } catch (error) {
      console.error("Upload error:", error);

      setMessage(
        error.message || "Unable to complete inspection."
      );
      setMessageType("error");
    } finally {
      setUploading(false);
    }
  };

  return (
    <section className="upload-section">

      {/* HEADER */}
      <div className="upload-header">

        <div className="upload-title-area">

          <div className="upload-title-icon">
            ✦
          </div>

          <div>
            <h2>
              Product Image Inspection
            </h2>

            <p>
              Upload a product image to perform
              AI-powered quality inspection.
            </p>
          </div>

        </div>

        <div className="upload-ai-status">
          <span className="status-dot"></span>
          PatchCore AI Ready
        </div>

      </div>


      {/* CATEGORY */}
      <div className="category-selector">

        <div className="category-label-row">

          <label htmlFor="product-category">
            Product Category
          </label>

          <span>
            AI Model Selection
          </span>

        </div>

        <div className="category-select-wrapper">

          <span className="category-icon">
            ◈
          </span>

          <select
            id="product-category"
            value={category}
            onChange={(event) =>
              setCategory(event.target.value)
            }
            disabled={uploading}
          >
            {CATEGORIES.map((item) => (
              <option
                key={item}
                value={item}
              >
                {formatCategory(item)}
              </option>
            ))}
          </select>

          <span className="select-arrow">
            ▾
          </span>

        </div>

        <p className="category-help">
          The selected category determines which
          trained PatchCore AI model and calibrated
          threshold are used for inspection.
        </p>

      </div>


      {/* UPLOAD AREA */}
      <div className="upload-box">

        {!selectedFile ? (

          <div className="upload-empty">

            <div className="upload-main-icon">
              ↑
            </div>

            <h3>
              Upload Product Image
            </h3>

            <p>
              Select a clear image of the product
              you want to inspect.
            </p>

            <button
              type="button"
              className="choose-image-button"
              onClick={openFilePicker}
              disabled={uploading}
            >
              <span>＋</span>
              Choose Image
            </button>

            <span className="upload-format">
              Supported formats: JPG, PNG, BMP
            </span>

          </div>

        ) : (

          <div className="selected-image-area">

            {/* IMAGE PREVIEW */}
            <div
              className="selected-image-preview"
              style={{
                overflow: "hidden",
                padding: 0,
                display: "flex",
                alignItems: "stretch",
                justifyContent: "stretch",
              }}
            >

              {preview && (
                <img
                  src={preview}
                  alt="Selected product"
                  style={{
                    width: "100%",
                    height: "100%",
                    display: "block",
                    objectFit: "contain",
                    objectPosition: "center",
                    borderRadius: "inherit",
                    background: "#f1f4f8",
                  }}
                />
              )}

            </div>


            {/* FILE INFO */}
            <div className="selected-image-info">

              <div className="selected-ready-label">
                ✓ IMAGE READY FOR INSPECTION
              </div>

              <h3>
                Product Image Selected
              </h3>

              <p className="selected-file-name">
                {selectedFile.name}
              </p>

              <p className="selected-file-size">
                {(selectedFile.size / 1024).toFixed(1)} KB
                {" • "}
                {formatCategory(category)}
              </p>


              <div className="upload-actions">

                <button
                  type="button"
                  className="change-image-button"
                  onClick={openFilePicker}
                  disabled={uploading}
                >
                  Change Image
                </button>

                <button
                  type="button"
                  className="upload-image-button"
                  onClick={handleUpload}
                  disabled={uploading}
                >
                  {uploading ? (
                    <>
                      <span className="button-spinner"></span>
                      Inspecting...
                    </>
                  ) : (
                    <>
                      ✦ Inspect with AI
                    </>
                  )}
                </button>

              </div>

            </div>

          </div>

        )}

        <input
          ref={fileInputRef}
          type="file"
          accept=".jpg,.jpeg,.png,.bmp,image/jpeg,image/png,image/bmp"
          onChange={handleFileChange}
          style={{ display: "none" }}
        />

      </div>


      {/* PROGRESS */}
      {uploading && (
        <div className="upload-progress">

          <div className="spinner"></div>

          <div>
            <strong>
              AI inspection in progress...
            </strong>

            <p>
              PatchCore is analyzing the selected
              product image against the learned
              normal-product feature patterns.
            </p>
          </div>

        </div>
      )}


      {/* MESSAGE */}
      {message && (
        <div
          className={`upload-message ${
            messageType === "success"
              ? "success-message"
              : "error-message"
          }`}
        >

          <span>
            {messageType === "success" ? "✓" : "!"}
          </span>

          {message}

        </div>
      )}

    </section>
  );
}

export default UploadInspection;