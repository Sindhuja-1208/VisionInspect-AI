import { useEffect, useState } from "react";
import UploadInspection from "./UploadInspection";
import "./Dashboard.css";

function Dashboard() {
  const [inspections, setInspections] = useState([]);
  const [loading, setLoading] = useState(true);

  // Selected inspection card
  const [selectedInspectionId, setSelectedInspectionId] = useState(null);

  const user = JSON.parse(
    localStorage.getItem("user") || "{}"
  );

  const token = localStorage.getItem("access_token");

  // ============================================================
  // FETCH INSPECTIONS
  // ============================================================

  const fetchInspections = async () => {
    try {
      const response = await fetch(
        "http://127.0.0.1:8000/inspections/",
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (response.status === 401) {
        localStorage.clear();
        window.location.reload();
        return;
      }

      if (!response.ok) {
        throw new Error("Failed to fetch inspections");
      }

      const data = await response.json();

      setInspections(data);
    } catch (error) {
      console.error(
        "Failed to fetch inspections:",
        error
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInspections();
  }, []);

  // ============================================================
  // LOGOUT
  // ============================================================

  const handleLogout = () => {
    localStorage.clear();
    window.location.reload();
  };

  // ============================================================
  // STATISTICS
  // IMPORTANT:
  // Backend returns "DEFECT", NOT "DEFECTIVE"
  // ============================================================

  const totalInspections = inspections.length;

  const normalInspections = inspections.filter(
    (item) => item.result === "NORMAL"
  ).length;

  const defectiveInspections = inspections.filter(
    (item) =>
      item.result === "DEFECT" ||
      item.result === "DEFECTIVE"
  ).length;

  const aiInspections = inspections.length;

  // ============================================================
  // CATEGORY THRESHOLDS
  // ============================================================

  const categoryThresholds = {
    bottle: 0.079466,
    cable: 0.209822,
    capsule: 0.123271,
    carpet: 0.106577,
    grid: 0.112386,
    hazelnut: 0.231549,
    leather: 0.101448,
    metal_nut: 0.181667,
    pill: 0.180071,
    screw: 0.160719,
    tile: 0.194956,
    toothbrush: 0.198892,
    transistor: 0.167431,
    wood: 0.226569,
    zipper: 0.120682
  };

  // ============================================================
  // RENDER
  // ============================================================

  return (
    <div className="dashboard-page">

      {/* ======================================================
          HEADER
          ====================================================== */}

      <header className="dashboard-header">

        <div className="header-brand">

          <div className="brand-icon">
            ✦
          </div>

          <div className="brand-text">

            <h1>
              VisionInspect <span>AI</span>
            </h1>

            <p>
              Intelligent Manufacturing Quality Inspection
            </p>

          </div>

        </div>


        <div className="user-area">

          <div className="user-info">

            <strong>
              {user.name || "Quality Engineer"}
            </strong>

            <span>
              {user.role || "Quality Engineer"}
            </span>

          </div>

          <button
            className="logout-button"
            onClick={handleLogout}
          >
            Logout
          </button>

        </div>

      </header>


      {/* ======================================================
          MAIN CONTENT
          ====================================================== */}

      <main className="dashboard-content">


        {/* ====================================================
            WELCOME
            ==================================================== */}

        <section className="welcome-section">

          <div className="welcome-left">

            <div className="section-eyebrow">
              AI QUALITY CONTROL CENTER
            </div>

            <h2>
              Welcome back,{" "}
              <span>
                {user.name || "Quality Engineer"}
              </span>
            </h2>

            <p>
              Monitor product quality, detect anomalies,
              and review AI-powered inspection results.
            </p>

          </div>


          <div className="system-status">

            <div className="status-dot"></div>

            <div>

              <strong>
                AI System Online
              </strong>

              <span>
                PatchCore Engine Active
              </span>

            </div>

          </div>

        </section>


        {/* ====================================================
            STATISTICS
            ==================================================== */}

        <section className="stats-grid">


          {/* TOTAL */}

          <div className="stat-card total-card">

            <div className="stat-card-top">

              <div className="stat-icon total-icon">
                ◈
              </div>

              <span className="stat-badge total-badge">
                ALL
              </span>

            </div>

            <div className="stat-card-label">
              Total Inspections
            </div>

            <div className="stat-number">
              {totalInspections}
            </div>

            <div className="stat-description">
              Products inspected
            </div>

          </div>


          {/* NORMAL */}

          <div className="stat-card normal-card">

            <div className="stat-card-top">

              <div className="stat-icon normal-icon">
                ✓
              </div>

              <span className="stat-badge normal-badge">
                PASS
              </span>

            </div>

            <div className="stat-card-label">
              Normal Products
            </div>

            <div className="stat-number">
              {normalInspections}
            </div>

            <div className="stat-description">
              Quality check passed
            </div>

          </div>


          {/* DEFECT */}

          <div className="stat-card defect-card">

            <div className="stat-card-top">

              <div className="stat-icon defect-icon">
                !
              </div>

              <span className="stat-badge defect-badge">
                ALERT
              </span>

            </div>

            <div className="stat-card-label">
              Defects Detected
            </div>

            <div className="stat-number">
              {defectiveInspections}
            </div>

            <div className="stat-description">
              Requires attention
            </div>

          </div>


          {/* AI */}

          <div className="stat-card ai-card">

            <div className="stat-card-top">

              <div className="stat-icon ai-icon">
                ✦
              </div>

              <span className="stat-badge ai-badge">
                AI
              </span>

            </div>

            <div className="stat-card-label">
              AI Inspections
            </div>

            <div className="stat-number">
              {aiInspections}
            </div>

            <div className="stat-description">
              PatchCore powered
            </div>

          </div>

        </section>


        {/* ====================================================
            UPLOAD
            ==================================================== */}

        <UploadInspection
          onUploadSuccess={fetchInspections}
        />


        {/* ====================================================
            RESULTS
            ==================================================== */}

        <section className="inspection-section">

          <div className="section-header">

            <div>

              <div className="section-eyebrow">
                INSPECTION HISTORY
              </div>

              <h2>
                AI Inspection Results
              </h2>

              <p>
                Detailed analysis from your product inspections
              </p>

            </div>


            <div className="result-count">

              <span>
                {totalInspections}
              </span>

              inspections

            </div>

          </div>


          {/* LOADING */}

          {loading && (

            <div className="empty-state">

              <div className="loading-spinner"></div>

              <h3>
                Loading inspections...
              </h3>

              <p>
                Retrieving AI inspection records.
              </p>

            </div>

          )}


          {/* EMPTY */}

          {!loading &&
            inspections.length === 0 && (

              <div className="empty-state">

                <div className="empty-icon">
                  ◇
                </div>

                <h3>
                  No inspections yet
                </h3>

                <p>
                  Upload a product image to begin
                  AI inspection.
                </p>

              </div>

            )}


          {/* RESULTS */}

          {!loading &&
            inspections.length > 0 && (

              <div className="inspection-results">

                {inspections.map(
                  (inspection) => {

                    const filename =
                      inspection.image_path
                        ? inspection.image_path
                            .split("\\")
                            .pop()
                            .split("/")
                            .pop()
                        : "";

                    const imageUrl =
                      filename
                        ? `http://127.0.0.1:8000/uploads/${filename}`
                        : null;


                    // ==================================================
                    // RESULT TYPE
                    // ==================================================

                    const isNormal =
                      inspection.result === "NORMAL";

                    const isDefect =
                      inspection.result === "DEFECT" ||
                      inspection.result === "DEFECTIVE";


                    // ==================================================
                    // SELECTED CARD
                    // ==================================================

                    const isSelected =
                      String(selectedInspectionId) ===
                      String(inspection.id);


                    // ==================================================
                    // SCORE
                    // ==================================================

                    const score =
                      inspection.anomaly_score !== null &&
                      inspection.anomaly_score !== undefined
                        ? Number(
                            inspection.anomaly_score
                          )
                        : null;


                    // ==================================================
                    // CATEGORY
                    // ==================================================

                    const category =
                      inspection.category ||
                      "Unknown";


                    const threshold =
                      categoryThresholds[
                        category
                      ];


                    // ==================================================
                    // CARD CLASS
                    // ==================================================

                    let cardClass =
                      "inspection-result-card";

                    if (isDefect) {
                      cardClass +=
                        " inspection-defect";
                    } else if (isNormal) {
                      cardClass +=
                        " inspection-normal";
                    }

                    if (isSelected && isNormal) {
                      cardClass +=
                        " inspection-selected-normal";
                    }

                    if (isSelected && isDefect) {
                      cardClass +=
                        " inspection-selected-defect";
                    }


                    return (

                      <article
                        className={cardClass}
                        key={inspection.id}

                        onClick={() =>
                          setSelectedInspectionId(
                            inspection.id
                          )
                        }

                        tabIndex={0}

                        onKeyDown={(event) => {

                          if (
                            event.key === "Enter" ||
                            event.key === " "
                          ) {
                            event.preventDefault();

                            setSelectedInspectionId(
                              inspection.id
                            );
                          }

                        }}

                      >


                        {/* =================================
                            IMAGE
                            ================================= */}

                        <div className="result-image-column">

                          <div className="result-image-container">

                            {imageUrl ? (

                              <img
                                src={imageUrl}
                                alt="Inspected product"
                                className="result-image"
                              />

                            ) : (

                              <div className="image-placeholder">
                                No Image
                              </div>

                            )}


                            {/* IMAGE STATUS */}

                            {isDefect && (

                              <div className="image-defect-badge">
                                ! DEFECT
                              </div>

                            )}

                            {isNormal && (

                              <div className="image-normal-badge">
                                ✓ NORMAL
                              </div>

                            )}

                          </div>

                        </div>


                        {/* =================================
                            DETAILS
                            ================================= */}

                        <div className="result-details">


                          {/* TITLE */}

                          <div className="result-title-row">

                            <div>

                              <div className="inspection-number">
                                INSPECTION #{inspection.id}
                              </div>

                              <h3>
                                {category
                                  .replace("_", " ")
                                  .replace(
                                    /\b\w/g,
                                    (char) =>
                                      char.toUpperCase()
                                  )}
                              </h3>

                              <p className="filename">
                                {filename}
                              </p>

                            </div>


                            {/* TOP STATUS */}

                            {isDefect && (

                              <span className="result-defective">
                                ! DEFECT
                              </span>

                            )}

                            {isNormal && (

                              <span className="result-normal">
                                ✓ NORMAL
                              </span>

                            )}

                          </div>


                          {/* =================================
                              INFO GRID
                              ================================= */}

                          <div className="result-info-grid">


                            <div
                              className={`result-info-box ${
                                isDefect
                                  ? "info-defect"
                                  : isNormal
                                  ? "info-normal"
                                  : ""
                              }`}
                            >

                              <span>
                                AI RESULT
                              </span>

                              <strong>
                                {inspection.result ||
                                  "PENDING"}
                              </strong>

                            </div>


                            <div className="result-info-box">

                              <span>
                                ANOMALY SCORE
                              </span>

                              <strong className="score-value">

                                {score !== null
                                  ? score.toFixed(6)
                                  : "—"}

                              </strong>

                            </div>


                            <div className="result-info-box">

                              <span>
                                CATEGORY
                              </span>

                              <strong>
                                {category
                                  .replace("_", " ")
                                  .replace(
                                    /\b\w/g,
                                    (char) =>
                                      char.toUpperCase()
                                  )}
                              </strong>

                            </div>


                            <div className="result-info-box">

                              <span>
                                STATUS
                              </span>

                              <strong className="completed-status">
                                ● {inspection.status || "completed"}
                              </strong>

                            </div>

                          </div>


                          {/* =================================
                              MODEL INFO
                              ================================= */}

                          <div className="model-summary">


                            <div>

                              <span>
                                PRODUCT
                              </span>

                              <strong>
                                {category
                                  .replace("_", " ")
                                  .replace(
                                    /\b\w/g,
                                    (char) =>
                                      char.toUpperCase()
                                  )}
                              </strong>

                            </div>


                            <div>

                              <span>
                                DETECTION
                              </span>

                              <strong>
                                PatchCore
                              </strong>

                            </div>


                            <div>

                              <span>
                                THRESHOLD
                              </span>

                              <strong>
                                {threshold
                                  ? threshold.toFixed(6)
                                  : "—"}
                              </strong>

                            </div>

                          </div>


                          {/* =================================
                              EXPLANATION
                              ================================= */}

                          <div
                            className={`score-explanation ${
                              isDefect
                                ? "explanation-defect"
                                : isNormal
                                ? "explanation-normal"
                                : ""
                            }`}
                          >

                            {isDefect && (

                              <>

                                <div className="explanation-title">

                                  <span className="explanation-icon">
                                    !
                                  </span>

                                  Potential Defect Detected

                                </div>

                                <p>
                                  The PatchCore AI model detected
                                  an abnormal visual pattern above
                                  the calibrated category threshold.
                                  Further quality inspection is
                                  recommended.
                                </p>

                              </>

                            )}


                            {isNormal && (

                              <>

                                <div className="explanation-title">

                                  <span className="explanation-icon">
                                    ✓
                                  </span>

                                  Quality Check Passed

                                </div>

                                <p>
                                  The PatchCore AI model found
                                  the product visual pattern to be
                                  within the expected normal range
                                  for this category.
                                </p>

                              </>

                            )}

                          </div>


                          {/* =================================
                              TECHNICAL INFORMATION
                              ================================= */}

                          <div className="ai-technical-info">


                            <div>

                              <span>
                                AI MODEL
                              </span>

                              <strong>
                                PatchCore-Style Multi-Scale ResNet18
                              </strong>

                            </div>


                            <div>

                              <span>
                                DETECTION METHOD
                              </span>

                              <strong>
                                Feature Memory Bank
                              </strong>

                            </div>


                            <div>

                              <span>
                                INPUT
                              </span>

                              <strong>
                                224 × 224
                              </strong>

                            </div>

                          </div>


                        </div>

                      </article>

                    );

                  }
                )}

              </div>

            )}

        </section>

      </main>

    </div>
  );
}

export default Dashboard;