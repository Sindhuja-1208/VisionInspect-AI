import { useEffect, useState } from "react";
import UploadInspection from "./UploadInspection";
import "./Dashboard.css";

function Dashboard() {
  const [inspections, setInspections] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedInspectionId, setSelectedInspectionId] = useState(null);

  const user = JSON.parse(localStorage.getItem("user") || "{}");
  const token = localStorage.getItem("access_token");

  // ============================================================
  // BACKEND URL
  // ============================================================

  const API_BASE_URL = "http://127.0.0.1:8000";

  // ============================================================
  // FETCH INSPECTIONS
  // ============================================================

  const fetchInspections = async () => {
    try {
      setLoading(true);

      const response = await fetch(`${API_BASE_URL}/inspections/`, {
        method: "GET",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.status === 401) {
        localStorage.clear();
        window.location.reload();
        return;
      }

      if (!response.ok) {
        throw new Error("Failed to fetch inspections");
      }

      const data = await response.json();

      if (Array.isArray(data)) {
        setInspections(data);
      } else {
        setInspections([]);
      }
    } catch (error) {
      console.error("Failed to fetch inspections:", error);
      setInspections([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!token) {
      localStorage.clear();
      window.location.reload();
      return;
    }

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
  // BASIC STATISTICS
  // ============================================================

  const totalInspections = inspections.length;

  const normalInspections = inspections.filter(
    (item) =>
      String(item.result || "").toUpperCase() === "NORMAL"
  ).length;

  const defectiveInspections = inspections.filter((item) => {
    const result = String(item.result || "").toUpperCase();

    return result === "DEFECT" || result === "DEFECTIVE";
  }).length;

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
    zipper: 0.120682,
  };

  // ============================================================
  // CATEGORY FORMATTER
  // ============================================================

  const formatCategory = (value) => {
    if (!value) {
      return "Unknown";
    }

    return String(value)
      .replace(/_/g, " ")
      .replace(/\b\w/g, (char) => char.toUpperCase());
  };

  // ============================================================
  // SEVERITY CLASS
  // ============================================================

  const getSeverityClass = (level) => {
    if (!level) {
      return "";
    }

    switch (String(level).toLowerCase()) {
      case "critical":
        return "severity-critical";

      case "high":
        return "severity-high";

      case "medium":
        return "severity-medium";

      case "low":
        return "severity-low";

      default:
        return "";
    }
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
          MAIN
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
            DASHBOARD SUMMARY STATISTICS
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
            UPLOAD INSPECTION
            ==================================================== */}

        <UploadInspection
          onUploadSuccess={fetchInspections}
        />


        {/* ====================================================
            QUICK QUALITY SUMMARY
            ==================================================== */}

        <section className="dashboard-summary-section">

          <div className="section-header">

            <div>

              <div className="section-eyebrow">
                QUALITY OVERVIEW
              </div>

              <h2>
                Inspection Summary
              </h2>

              <p>
                Current manufacturing quality inspection overview
              </p>

            </div>

          </div>


          <div className="dashboard-summary-grid">

            <div className="summary-item">

              <span>
                TOTAL INSPECTIONS
              </span>

              <strong>
                {totalInspections}
              </strong>

            </div>


            <div className="summary-item">

              <span>
                PASSED PRODUCTS
              </span>

              <strong>
                {normalInspections}
              </strong>

            </div>


            <div className="summary-item">

              <span>
                DEFECTIVE PRODUCTS
              </span>

              <strong>
                {defectiveInspections}
              </strong>

            </div>


            <div className="summary-item">

              <span>
                AI ENGINE
              </span>

              <strong>
                PatchCore
              </strong>

            </div>

          </div>

        </section>


        {/* ====================================================
            INSPECTION HISTORY
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
              </span>{" "}
              inspections

            </div>

          </div>


          {/* ==================================================
              LOADING
              ================================================== */}

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


          {/* ==================================================
              EMPTY
              ================================================== */}

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
                  Upload a product image to begin AI inspection.
                </p>

              </div>

            )}


          {/* ==================================================
              INSPECTION RESULTS
              ================================================== */}

          {!loading &&
            inspections.length > 0 && (

              <div className="inspection-results">

                {inspections.map((inspection) => {

                  // ==================================================
                  // ID
                  // ==================================================

                  const inspectionId =
                    inspection.id ||
                    inspection._id ||
                    inspection.inspection_id;


                  // ==================================================
                  // FILE NAME
                  // ==================================================

                  let filename = "";

                  if (inspection.filename) {

                    filename = inspection.filename;

                  } else if (inspection.image_path) {

                    filename = String(
                      inspection.image_path
                    )
                      .split("\\")
                      .pop()
                      .split("/")
                      .pop();

                  }


                  // ==================================================
                  // IMAGE URL
                  // ==================================================

                  const imageUrl = filename
                    ? `${API_BASE_URL}/uploads/${encodeURIComponent(
                        filename
                      )}`
                    : null;


                  // ==================================================
                  // RESULT
                  // ==================================================

                  const result = String(
                    inspection.result || ""
                  ).toUpperCase();

                  const isNormal =
                    result === "NORMAL";

                  const isDefect =
                    result === "DEFECT" ||
                    result === "DEFECTIVE";


                  // ==================================================
                  // SELECTED
                  // ==================================================

                  const isSelected =
                    String(selectedInspectionId) ===
                    String(inspectionId);


                  // ==================================================
                  // ANOMALY SCORE
                  // ==================================================

                  const score =
                    inspection.anomaly_score !== null &&
                    inspection.anomaly_score !== undefined &&
                    Number.isFinite(
                      Number(inspection.anomaly_score)
                    )
                      ? Number(inspection.anomaly_score)
                      : null;


                  // ==================================================
                  // CATEGORY
                  // ==================================================

                  const category =
                    inspection.category || "Unknown";

                  const formattedCategory =
                    formatCategory(category);


                  // ==================================================
                  // THRESHOLD
                  // ==================================================

                  const threshold =
                    inspection.threshold !== undefined &&
                    inspection.threshold !== null &&
                    Number.isFinite(
                      Number(inspection.threshold)
                    )
                      ? Number(inspection.threshold)
                      : categoryThresholds[
                          String(category).toLowerCase()
                        ];


                  // ==================================================
                  // QUALITY ASSESSMENT
                  // ==================================================

                  const assessment =
                    inspection.quality_assessment || {};


                  // ==================================================
                  // SEVERITY SCORE
                  // ==================================================

                  const severityScore =
                    assessment.severity_score !== undefined &&
                    assessment.severity_score !== null &&
                    Number.isFinite(
                      Number(assessment.severity_score)
                    )
                      ? Number(assessment.severity_score)
                      : null;


                  // ==================================================
                  // SEVERITY LEVEL
                  // ==================================================

                  const severityLevel =
                    assessment.severity_level ||
                    (isNormal ? "Low" : "Pending");


                  // ==================================================
                  // QUALITY RISK
                  // ==================================================

                  const qualityRisk =
                    assessment.quality_risk ||
                    assessment.risk_level ||
                    (isNormal ? "Low" : "Pending");


                  // ==================================================
                  // QUALITY STATUS
                  // ==================================================

                  const qualityStatus =
                    assessment.quality_status ||
                    (isNormal
                      ? "PASS"
                      : isDefect
                      ? "FAIL"
                      : "REVIEW");


                  // ==================================================
                  // RECOMMENDED ACTION
                  // ==================================================

                  const recommendedAction =
                    assessment.recommended_action ||
                    (isNormal
                      ? "Product meets the current quality inspection criteria."
                      : "Quality inspection required.");


                  // ==================================================
                  // DEFECT TYPE
                  // ==================================================

                  const defectType =
                    assessment.defect_type ||
                    (isNormal
                      ? "No defect detected"
                      : "Visual Anomaly");


                  // ==================================================
                  // SIZE SCORE
                  // ==================================================

                  const sizeScore =
                    assessment.size_score !== undefined &&
                    assessment.size_score !== null &&
                    Number.isFinite(
                      Number(assessment.size_score)
                    )
                      ? Number(assessment.size_score)
                      : 0;


                  // ==================================================
                  // LOCATION SCORE
                  // ==================================================

                  const locationScore =
                    assessment.location_score !== undefined &&
                    assessment.location_score !== null &&
                    Number.isFinite(
                      Number(assessment.location_score)
                    )
                      ? Number(assessment.location_score)
                      : 0;


                  // ==================================================
                  // DEFECT TYPE SCORE
                  // ==================================================

                  const defectTypeScore =
                    assessment.defect_type_score !== undefined &&
                    assessment.defect_type_score !== null &&
                    Number.isFinite(
                      Number(assessment.defect_type_score)
                    )
                      ? Number(assessment.defect_type_score)
                      : 0;


                  // ==================================================
                  // CONFIDENCE SCORE
                  // ==================================================

                  const confidenceScore =
                    assessment.confidence_score !== undefined &&
                    assessment.confidence_score !== null &&
                    Number.isFinite(
                      Number(assessment.confidence_score)
                    )
                      ? Number(assessment.confidence_score)
                      : 0;


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


                  // ==================================================
                  // RENDER CARD
                  // ==================================================

                  return (

                    <article
                      className={cardClass}
                      key={
                        inspectionId ||
                        `${filename}-${inspection.created_at}`
                      }
                      onClick={() =>
                        setSelectedInspectionId(
                          inspectionId
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
                            inspectionId
                          );

                        }

                      }}
                    >

                      {/* ==================================================
                          IMAGE
                          ================================================== */}

                      <div className="result-image-column">

                        <div className="result-image-container">

                          {imageUrl ? (

                            <img
                              src={imageUrl}
                              alt={`Inspected ${formattedCategory}`}
                              className="result-image"
                              onError={(event) => {

                                event.currentTarget.style.display =
                                  "none";

                                const parent =
                                  event.currentTarget.parentElement;

                                if (parent) {

                                  parent.classList.add(
                                    "image-load-error"
                                  );

                                }

                              }}
                            />

                          ) : (

                            <div className="image-placeholder">
                              No Image
                            </div>

                          )}


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


                      {/* ==================================================
                          DETAILS
                          ================================================== */}

                      <div className="result-details">


                        {/* TITLE */}

                        <div className="result-title-row">

                          <div>

                            <div className="inspection-number">
                              INSPECTION #{inspectionId}
                            </div>

                            <h3>
                              {formattedCategory}
                            </h3>

                            <p className="filename">
                              {filename}
                            </p>

                          </div>


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


                        {/* BASIC RESULT INFO */}

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
                              {result || "PENDING"}
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
                              {formattedCategory}
                            </strong>

                          </div>


                          <div className="result-info-box">

                            <span>
                              STATUS
                            </span>

                            <strong className="completed-status">

                              ●{" "}
                              {inspection.status ||
                                "completed"}

                            </strong>

                          </div>

                        </div>


                        {/* MODEL SUMMARY */}

                        <div className="model-summary">

                          <div>

                            <span>
                              PRODUCT
                            </span>

                            <strong>
                              {formattedCategory}
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

                              {threshold !== undefined &&
                              threshold !== null &&
                              Number.isFinite(
                                Number(threshold)
                              )
                                ? Number(
                                    threshold
                                  ).toFixed(6)
                                : "—"}

                            </strong>

                          </div>

                        </div>


                        {/* ==================================================
                            QUALITY ASSESSMENT
                            ================================================== */}

                        <div className="quality-assessment-panel">

                          <div className="quality-assessment-header">

                            <div>

                              <h3>
                                Quality Assessment
                              </h3>

                              <p>
                                AI-based severity
                                and quality-risk
                                evaluation
                              </p>

                            </div>


                            <div
                              className={`severity-badge ${getSeverityClass(
                                severityLevel
                              )}`}
                            >
                              {severityLevel}
                            </div>

                          </div>


                          {/* SEVERITY SCORE */}

                          <div className="severity-score-section">

                            <div className="severity-score-main">

                              <span>
                                SEVERITY SCORE
                              </span>

                              <strong>

                                {severityScore !== null
                                  ? severityScore.toFixed(2)
                                  : "—"}

                              </strong>

                              <small>
                                / 100
                              </small>

                            </div>


                            <div className="severity-score-bar">

                              <div
                                className="severity-score-fill"
                                style={{
                                  width:
                                    severityScore !== null
                                      ? `${Math.min(
                                          Math.max(
                                            severityScore,
                                            0
                                          ),
                                          100
                                        )}%`
                                      : "0%",
                                }}
                              ></div>

                            </div>

                          </div>


                          {/* ASSESSMENT DETAILS */}

                          <div className="quality-assessment-grid">

                            <div className="assessment-item">

                              <span>
                                QUALITY RISK
                              </span>

                              <strong>
                                {qualityRisk}
                              </strong>

                            </div>


                            <div className="assessment-item">

                              <span>
                                QUALITY STATUS
                              </span>

                              <strong>
                                {qualityStatus}
                              </strong>

                            </div>


                            <div className="assessment-item">

                              <span>
                                DEFECT TYPE
                              </span>

                              <strong>
                                {defectType}
                              </strong>

                            </div>


                            <div className="assessment-item">

                              <span>
                                SIZE SCORE
                              </span>

                              <strong>
                                {sizeScore.toFixed(2)}
                              </strong>

                            </div>


                            <div className="assessment-item">

                              <span>
                                LOCATION SCORE
                              </span>

                              <strong>
                                {locationScore.toFixed(2)}
                              </strong>

                            </div>


                            <div className="assessment-item">

                              <span>
                                DEFECT TYPE SCORE
                              </span>

                              <strong>
                                {defectTypeScore.toFixed(2)}
                              </strong>

                            </div>


                            <div className="assessment-item">

                              <span>
                                CONFIDENCE SCORE
                              </span>

                              <strong>
                                {confidenceScore.toFixed(2)}
                              </strong>

                            </div>

                          </div>


                          {/* ASSESSMENT REASON */}

                          {assessment.assessment_reason && (

                            <div className="assessment-reason-box">

                              <span>
                                ASSESSMENT REASON
                              </span>

                              <p>
                                {
                                  assessment.assessment_reason
                                }
                              </p>

                            </div>

                          )}


                          {/* RECOMMENDED ACTION */}

                          <div className="recommended-action-box">

                            <div className="recommended-action-icon">
                              !
                            </div>

                            <div>

                              <span>
                                RECOMMENDED ACTION
                              </span>

                              <strong>
                                {
                                  recommendedAction
                                }
                              </strong>

                            </div>

                          </div>

                        </div>


                        {/* ==================================================
                            RESULT EXPLANATION
                            ================================================== */}

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

                                Potential Defect
                                Detected

                              </div>

                              <p>
                                The PatchCore AI
                                model detected an
                                abnormal visual
                                pattern above the
                                calibrated category
                                threshold. Further
                                quality inspection is
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

                                Quality Check
                                Passed

                              </div>

                              <p>
                                The PatchCore AI
                                model found the
                                product visual
                                pattern to be within
                                the expected normal
                                range for this
                                category.
                              </p>
                            </>

                          )}

                        </div>


                        {/* ==================================================
                            TECHNICAL INFORMATION
                            ================================================== */}

                        <div className="ai-technical-info">

                          <div>

                            <span>
                              AI MODEL
                            </span>

                            <strong>
                              {inspection.model ||
                                "PatchCore-Style Multi-Scale ResNet18"}
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


                          <div>

                            <span>
                              PROCESSING TIME
                            </span>

                            <strong>

                              {inspection.processing_time_seconds !==
                                undefined &&
                              inspection.processing_time_seconds !==
                                null
                                ? `${inspection.processing_time_seconds}s`
                                : "—"}

                            </strong>

                          </div>

                        </div>

                      </div>

                    </article>

                  );
                })}

              </div>

            )}

        </section>

      </main>

    </div>
  );
}

export default Dashboard;