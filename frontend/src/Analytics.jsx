import React, { useEffect, useState } from "react";
import "./Analytics.css";

const API_BASE_URL = "http://localhost:8000";

export default function Analytics() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadAnalytics = async () => {
    try {
      setLoading(true);
      setError("");

      const token = localStorage.getItem("access_token");

      if (!token) {
        throw new Error(
          "Authentication token not found. Please login again."
        );
      }

      const response = await fetch(
        `${API_BASE_URL}/analytics/summary`,
        {
          method: "GET",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        }
      );

      if (response.status === 401) {
        localStorage.removeItem("access_token");

        throw new Error(
          "Session expired or authentication failed. Please login again."
        );
      }

      if (!response.ok) {
        let message = `Analytics request failed: ${response.status}`;

        try {
          const errorData = await response.json();

          if (errorData.detail) {
            message = errorData.detail;
          }
        } catch {
          // Keep default error message
        }

        throw new Error(message);
      }

      const result = await response.json();

      setData(result);
    } catch (err) {
      console.error("Analytics error:", err);

      setError(
        err?.message || "Failed to load analytics"
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAnalytics();
  }, []);

  /* ============================================================
     LOADING
     ============================================================ */

  if (loading) {
    return (
      <div className="analytics-page">
        <div className="analytics-loading">
          <div className="loading-spinner"></div>

          <h2>Loading Production Analytics</h2>

          <p>
            Processing inspection quality data...
          </p>
        </div>
      </div>
    );
  }

  /* ============================================================
     ERROR
     ============================================================ */

  if (error) {
    return (
      <div className="analytics-page">
        <div className="analytics-error">
          <div className="error-icon">!</div>

          <h2>Unable to Load Analytics</h2>

          <p>{error}</p>

          <button
            className="retry-button"
            onClick={loadAnalytics}
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  /* ============================================================
     EMPTY
     ============================================================ */

  if (!data) {
    return (
      <div className="analytics-page">
        <div className="analytics-empty">
          <div className="analytics-empty-icon">
            ◇
          </div>

          <h3>No Analytics Data</h3>

          <p>
            Complete an inspection to generate
            production analytics.
          </p>
        </div>
      </div>
    );
  }

  /* ============================================================
     BASIC DATA
     ============================================================ */

  const totalInspections = Number(
    data.total_inspections ?? 0
  );

  const normalInspections = Number(
    data.normal_products ?? 0
  );

  const defectInspections = Number(
    data.defects_detected ?? 0
  );

  const normalRate = Number(
    data.normal_rate ?? 0
  );

  const defectRate = Number(
    data.defect_rate ?? 0
  );

  const averageSeverity = Number(
    data.average_severity_score ?? 0
  );

  const severity = data.severity || {};

  const criticalCount = Number(
    severity.critical ?? 0
  );

  const highCount = Number(
    severity.high ?? 0
  );

  const mediumCount = Number(
    severity.medium ?? 0
  );

  const lowCount = Number(
    severity.low ?? 0
  );

  const pendingCount = Number(
    severity.pending ?? 0
  );

  /* ============================================================
     CATEGORY DATA
     ============================================================ */

  const categoryCounts =
    data.category_counts || {};

  const categoryDefects =
    data.category_defects || {};

  const categoryDefectRates =
    data.category_defect_rates || {};

  const categoryAverageSeverity =
    data.category_average_severity || {};

  /* ============================================================
     SEVERITY
     ============================================================ */

  const severityRows = [
    {
      name: "Critical",
      value: criticalCount,
      className: "critical",
    },
    {
      name: "High",
      value: highCount,
      className: "high",
    },
    {
      name: "Medium",
      value: mediumCount,
      className: "medium",
    },
    {
      name: "Low",
      value: lowCount,
      className: "low",
    },
    {
      name: "Pending",
      value: pendingCount,
      className: "pending",
    },
  ];

  const severityTotal =
    criticalCount +
    highCount +
    mediumCount +
    lowCount +
    pendingCount;

  const maxSeverityValue = Math.max(
    ...severityRows.map(
      (item) => item.value
    ),
    1
  );

  /* ============================================================
     CATEGORY ROWS

     IMPORTANT:
     No useMemo here.

     This avoids the React Hooks ordering problem.
     ============================================================ */

  const categoryRows = Object.entries(
    categoryCounts
  )
    .map(([category, count]) => {
      const inspections = Number(
        count ?? 0
      );

      const defects = Number(
        categoryDefects[category] ?? 0
      );

      const categoryRate = Number(
        categoryDefectRates[category] ?? 0
      );

      const categorySeverity = Number(
        categoryAverageSeverity[category] ?? 0
      );

      return {
        category,
        inspections,
        defects,
        defectRate: categoryRate,
        severity: categorySeverity,
      };
    })
    .sort(
      (a, b) =>
        b.defectRate - a.defectRate
    );

  const highestDefectCategory =
    categoryRows.length > 0
      ? categoryRows[0]
      : null;

  /* ============================================================
     RENDER
     ============================================================ */

  return (
    <div className="analytics-page">

      {/* ========================================================
          HEADER
          ======================================================== */}

      <header className="analytics-header">

        <div className="analytics-header-content">

          <div className="section-eyebrow">
            PRODUCTION MONITORING
          </div>

          <h1>
            Production Analytics
          </h1>

          <p>
            AI-powered manufacturing quality
            inspection analytics and defect monitoring.
          </p>

        </div>

        <button
          className="refresh-button"
          onClick={loadAnalytics}
        >
          <span className="refresh-icon">
            ↻
          </span>

          Refresh
        </button>

      </header>


      {/* ========================================================
          KPI CARDS
          ======================================================== */}

      <section className="analytics-kpi-grid">

        {/* TOTAL */}

        <div className="analytics-kpi-card total-kpi">

          <div className="kpi-top">

            <div className="kpi-icon">
              ◈
            </div>

            <span className="kpi-label">
              TOTAL
            </span>

          </div>

          <div className="kpi-value">
            {totalInspections}
          </div>

          <div className="kpi-title">
            Total Inspections
          </div>

          <div className="kpi-description">
            All processed products
          </div>

        </div>


        {/* NORMAL */}

        <div className="analytics-kpi-card normal-kpi">

          <div className="kpi-top">

            <div className="kpi-icon">
              ✓
            </div>

            <span className="kpi-label">
              PASS
            </span>

          </div>

          <div className="kpi-value">
            {normalInspections}
          </div>

          <div className="kpi-title">
            Normal Products
          </div>

          <div className="kpi-description">
            {normalRate.toFixed(1)}% of inspections
          </div>

        </div>


        {/* DEFECT */}

        <div className="analytics-kpi-card defect-kpi">

          <div className="kpi-top">

            <div className="kpi-icon">
              !
            </div>

            <span className="kpi-label">
              ALERT
            </span>

          </div>

          <div className="kpi-value">
            {defectInspections}
          </div>

          <div className="kpi-title">
            Defects Detected
          </div>

          <div className="kpi-description">
            {defectRate.toFixed(1)}% defect rate
          </div>

        </div>


        {/* SEVERITY */}

        <div className="analytics-kpi-card severity-kpi">

          <div className="kpi-top">

            <div className="kpi-icon">
              ◉
            </div>

            <span className="kpi-label">
              QUALITY
            </span>

          </div>

          <div className="kpi-value">
            {averageSeverity.toFixed(1)}
          </div>

          <div className="kpi-title">
            Average Severity
          </div>

          <div className="kpi-description">
            Quality severity score / 100
          </div>

        </div>

      </section>


      {/* ========================================================
          QUALITY + SEVERITY
          ======================================================== */}

      <section className="analytics-two-column">


        {/* ======================================================
            QUALITY OVERVIEW
            ====================================================== */}

        <div className="analytics-panel quality-overview-panel">

          <div className="analytics-panel-header">

            <div>

              <div className="section-eyebrow">
                QUALITY PERFORMANCE
              </div>

              <h2>
                Quality Overview
              </h2>

              <p>
                Overall production inspection performance.
              </p>

            </div>

          </div>


          <div className="quality-overview-content">


            {/* QUALITY RING */}

            <div
              className="quality-ring"
              style={{
                background: `conic-gradient(
                  #16a34a 0deg,
                  #16a34a ${Math.min(
                    100,
                    Math.max(0, normalRate)
                  ) * 3.6}deg,
                  #e9eef5 ${
                    Math.min(
                      100,
                      Math.max(0, normalRate)
                    ) * 3.6
                  }deg,
                  #e9eef5 360deg
                )`,
              }}
            >

              <div className="quality-ring-inner">

                <strong>
                  {normalRate.toFixed(1)}%
                </strong>

                <span>
                  PASS RATE
                </span>

              </div>

            </div>


            {/* QUALITY METRICS */}

            <div className="quality-metrics">


              {/* NORMAL */}

              <div className="quality-metric">

                <div className="metric-heading">

                  <span className="metric-dot normal-dot"></span>

                  <span>
                    Normal Products
                  </span>

                  <strong>
                    {normalRate.toFixed(1)}%
                  </strong>

                </div>

                <div className="metric-bar">

                  <div
                    className="metric-fill normal-fill"
                    style={{
                      width: `${Math.min(
                        100,
                        Math.max(
                          0,
                          normalRate
                        )
                      )}%`,
                    }}
                  />

                </div>

                <small>
                  {normalInspections} products passed
                </small>

              </div>


              {/* DEFECT */}

              <div className="quality-metric">

                <div className="metric-heading">

                  <span className="metric-dot defect-dot"></span>

                  <span>
                    Defective Products
                  </span>

                  <strong>
                    {defectRate.toFixed(1)}%
                  </strong>

                </div>

                <div className="metric-bar">

                  <div
                    className="metric-fill defect-fill"
                    style={{
                      width: `${Math.min(
                        100,
                        Math.max(
                          0,
                          defectRate
                        )
                      )}%`,
                    }}
                  />

                </div>

                <small>
                  {defectInspections} products require attention
                </small>

              </div>

            </div>

          </div>


          {/* QUALITY FOOTER */}

          <div className="quality-overview-footer">

            <div>

              <span>
                TOTAL PROCESSED
              </span>

              <strong>
                {totalInspections}
              </strong>

            </div>

            <div>

              <span>
                PASS RATE
              </span>

              <strong>
                {normalRate.toFixed(1)}%
              </strong>

            </div>

            <div>

              <span>
                DEFECT RATE
              </span>

              <strong>
                {defectRate.toFixed(1)}%
              </strong>

            </div>

          </div>

        </div>


        {/* ======================================================
            SEVERITY DISTRIBUTION
            ====================================================== */}

        <div className="analytics-panel severity-panel">

          <div className="analytics-panel-header">

            <div>

              <div className="section-eyebrow">
                RISK ANALYSIS
              </div>

              <h2>
                Severity Distribution
              </h2>

              <p>
                Quality risk levels across inspections.
              </p>

            </div>

          </div>


          <div className="severity-chart">

            {severityRows.map((item) => {

              const percentage =
                severityTotal > 0
                  ? (item.value /
                      severityTotal) *
                    100
                  : 0;

              const barWidth =
                (item.value /
                  maxSeverityValue) *
                100;

              return (
                <div
                  className="severity-row"
                  key={item.name}
                >

                  <div className="severity-row-header">

                    <div className="severity-name">

                      <span
                        className={`severity-indicator ${item.className}`}
                      ></span>

                      <strong>
                        {item.name}
                      </strong>

                    </div>

                    <div className="severity-numbers">

                      <strong>
                        {item.value}
                      </strong>

                      <span>
                        {percentage.toFixed(1)}%
                      </span>

                    </div>

                  </div>

                  <div className="severity-bar">

                    <div
                      className={`severity-fill ${item.className}`}
                      style={{
                        width: `${Math.min(
                          100,
                          Math.max(
                            0,
                            barWidth
                          )
                        )}%`,
                      }}
                    />

                  </div>

                </div>
              );
            })}

          </div>


          <div className="severity-summary">

            <div>

              <span>
                TOTAL ASSESSED
              </span>

              <strong>
                {severityTotal}
              </strong>

            </div>

            <div>

              <span>
                HIGH + CRITICAL
              </span>

              <strong>
                {criticalCount +
                  highCount}
              </strong>

            </div>

          </div>

        </div>

      </section>


      {/* ========================================================
          CATEGORY ANALYTICS
          ======================================================== */}

      <section className="analytics-panel category-panel">

        <div className="analytics-panel-header category-header">

          <div>

            <div className="section-eyebrow">
              CATEGORY ANALYSIS
            </div>

            <h2>
              Category-wise Production Quality
            </h2>

            <p>
              Inspection volume, defect frequency and
              severity across product categories.
            </p>

          </div>


          {highestDefectCategory && (

            <div className="category-highlight">

              <span>
                HIGHEST DEFECT RATE
              </span>

              <strong>
                {formatCategory(
                  highestDefectCategory.category
                )}
              </strong>

              <small>
                {highestDefectCategory.defectRate.toFixed(
                  1
                )}%
              </small>

            </div>

          )}

        </div>


        {categoryRows.length === 0 ? (

          <div className="analytics-empty inline-empty">

            <div className="analytics-empty-icon">
              ◇
            </div>

            <h3>
              No Category Data
            </h3>

            <p>
              Category analytics will appear after inspections.
            </p>

          </div>

        ) : (

          <div className="category-visual-list">

            {categoryRows.map((item) => {

              const inspectionPercentage =
                totalInspections > 0
                  ? (item.inspections /
                      totalInspections) *
                    100
                  : 0;

              const defectPercentage =
                Math.min(
                  100,
                  Math.max(
                    0,
                    item.defectRate
                  )
                );

              return (

                <div
                  className="category-visual-row"
                  key={item.category}
                >

                  {/* CATEGORY */}

                  <div className="category-name-cell">

                    <div className="category-symbol">
                      ◈
                    </div>

                    <div>

                      <strong>
                        {formatCategory(
                          item.category
                        )}
                      </strong>

                      <span>
                        {item.inspections} inspections
                      </span>

                    </div>

                  </div>


                  {/* VOLUME */}

                  <div className="category-volume">

                    <div className="category-value-line">

                      <span>
                        Inspection Volume
                      </span>

                      <strong>
                        {inspectionPercentage.toFixed(
                          1
                        )}%
                      </strong>

                    </div>

                    <div className="category-mini-bar">

                      <div
                        className="category-volume-fill"
                        style={{
                          width: `${Math.min(
                            100,
                            inspectionPercentage
                          )}%`,
                        }}
                      />

                    </div>

                  </div>


                  {/* DEFECTS */}

                  <div className="category-defect-info">

                    <span>
                      DEFECTS
                    </span>

                    <strong>
                      {item.defects}
                    </strong>

                  </div>


                  {/* DEFECT RATE */}

                  <div className="category-rate-info">

                    <div>

                      <span>
                        DEFECT RATE
                      </span>

                      <strong>
                        {item.defectRate.toFixed(
                          1
                        )}%
                      </strong>

                    </div>

                    <div className="category-rate-bar">

                      <div
                        className="category-rate-fill"
                        style={{
                          width: `${defectPercentage}%`,
                        }}
                      />

                    </div>

                  </div>


                  {/* SEVERITY */}

                  <div className="category-severity-info">

                    <span>
                      AVG SEVERITY
                    </span>

                    <strong>
                      {item.severity.toFixed(
                        1
                      )}
                    </strong>

                  </div>

                </div>
              );
            })}

          </div>

        )}

      </section>


      {/* ========================================================
          PRODUCTION STATUS
          ======================================================== */}

      <section className="analytics-panel production-status-panel">

        <div className="analytics-panel-header">

          <div>

            <div className="section-eyebrow">
              QUALITY STATUS
            </div>

            <h2>
              Current Production Status
            </h2>

            <p>
              Overall quality condition based on completed inspections.
            </p>

          </div>

          <div className="live-status">

            <span className="live-dot"></span>

            <span>
              LIVE DATA
            </span>

          </div>

        </div>


        <div className="production-status-grid">


          {/* OVERALL */}

          <div className="production-status-card overall-status">

            <div className="status-card-icon">
              ◉
            </div>

            <div>

              <span>
                QUALITY STATUS
              </span>

              <strong>
                {data.overall_quality_status ||
                  "No Inspections"}
              </strong>

            </div>

          </div>


          {/* PASSED */}

          <div className="production-status-card">

            <div className="status-card-icon">
              ✓
            </div>

            <div>

              <span>
                PASSED
              </span>

              <strong>
                {normalInspections}
              </strong>

              <small>
                {normalRate.toFixed(
                  1
                )}% of production
              </small>

            </div>

          </div>


          {/* FAILED */}

          <div className="production-status-card">

            <div className="status-card-icon defect-status-icon">
              !
            </div>

            <div>

              <span>
                FAILED
              </span>

              <strong>
                {defectInspections}
              </strong>

              <small>
                {defectRate.toFixed(
                  1
                )}% of production
              </small>

            </div>

          </div>


          {/* PROCESSED */}

          <div className="production-status-card">

            <div className="status-card-icon">
              ◈
            </div>

            <div>

              <span>
                PROCESSED
              </span>

              <strong>
                {totalInspections}
              </strong>

              <small>
                Total inspections
              </small>

            </div>

          </div>

        </div>

      </section>


      {/* ========================================================
          INSIGHTS
          ======================================================== */}

      <section className="analytics-insights">


        <div className="insight-item normal-insight">

          <div className="insight-icon">
            ✓
          </div>

          <div>

            <span>
              QUALITY PERFORMANCE
            </span>

            <strong>
              {normalRate.toFixed(1)}% Normal
            </strong>

            <p>
              Products currently meeting expected
              quality inspection criteria.
            </p>

          </div>

        </div>


        <div className="insight-item defect-insight">

          <div className="insight-icon">
            !
          </div>

          <div>

            <span>
              DEFECT MONITORING
            </span>

            <strong>
              {defectInspections} Defects Detected
            </strong>

            <p>
              Defective products identified through
              AI-powered visual inspection.
            </p>

          </div>

        </div>


        <div className="insight-item severity-insight">

          <div className="insight-icon">
            ◉
          </div>

          <div>

            <span>
              SEVERITY MONITORING
            </span>

            <strong>
              {criticalCount + highCount} High-Risk
            </strong>

            <p>
              Combined critical and high severity
              inspection assessments.
            </p>

          </div>

        </div>

      </section>


      {/* ========================================================
          FOOTER
          ======================================================== */}

      <footer className="analytics-footer">

        <div>

          <strong>
            VisionInspect AI
          </strong>

          <span>
            Manufacturing Quality Intelligence
          </span>

        </div>

        <div>

          <span>
            PatchCore-based Quality Inspection
          </span>

        </div>

      </footer>

    </div>
  );
}


/* ================================================================
   CATEGORY FORMATTER
   ================================================================ */

function formatCategory(category) {
  if (!category) {
    return "Unknown";
  }

  return String(category)
    .replace(/_/g, " ")
    .replace(/\b\w/g, (letter) =>
      letter.toUpperCase()
    );
}