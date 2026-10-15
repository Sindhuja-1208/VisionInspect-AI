import { useCallback, useEffect, useState } from "react";
import { API_BASE_URL } from "./services/api";
import "./SupervisorDashboard.css";

export default function SupervisorDashboard() {
  const [summary, setSummary] = useState(null);
  const [trends, setTrends] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadData = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const token = localStorage.getItem("access_token");
      if (!token) throw new Error("Please log in again.");

      const headers = { Authorization: `Bearer ${token}` };
      const [summaryResponse, trendsResponse] = await Promise.all([
        fetch(`${API_BASE_URL}/analytics/summary`, { headers }),
        fetch(`${API_BASE_URL}/analytics/trends`, { headers }),
      ]);

      if (summaryResponse.status === 401 || trendsResponse.status === 401) {
        throw new Error("Session expired. Please log in again.");
      }
      if (!summaryResponse.ok || !trendsResponse.ok) {
        throw new Error("Could not load production data. Please refresh.");
      }

      const [summaryData, trendsData] = await Promise.all([
        summaryResponse.json(),
        trendsResponse.json(),
      ]);

      setSummary(summaryData);
      setTrends(trendsData);
    } catch (err) {
      setError(err.message || "Unable to load production data.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  if (loading) {
    return <div className="supervisor-page"><p>Loading production overview...</p></div>;
  }

  if (error) {
    return (
      <div className="supervisor-page">
        <div className="supervisor-error">
          <h2>Production data unavailable</h2>
          <p>{error}</p>
          <button onClick={loadData}>Retry</button>
        </div>
      </div>
    );
  }

  const total = Number(summary?.total_inspections || 0);
  const normal = Number(summary?.normal_products || 0);
  const defects = Number(summary?.defects_detected || 0);
  const defectRate = Number(summary?.defect_rate || 0);
  const severity = summary?.severity || {};
  const recent = summary?.recent_inspections || [];
  const daily = trends?.daily_trend || [];
  const categories = trends?.category_trend || [];

  const formatCategory = (value) =>
    String(value || "Unknown").replaceAll("_", " ");

  const formatDate = (value) => {
    if (value == null) return "—";
    const date = typeof value === "number"
      ? new Date(value < 1e12 ? value * 1000 : value)
      : new Date(value);
    return Number.isNaN(date.getTime())
      ? String(value)
      : date.toLocaleDateString();
  };

  return (
    <div className="supervisor-page">
      <header className="supervisor-header">
        <div>
          <span className="supervisor-eyebrow">VISIONINSPECT AI / OPERATIONS</span>
          <h1>Production Overview</h1>
          <p>Monitor inspection output, product quality and defect activity.</p>
        </div>
        <button className="supervisor-refresh" onClick={loadData}>
          Refresh data
        </button>
      </header>

      <section className="supervisor-kpis">
        <article className="supervisor-kpi">
          <span>Total inspections</span>
          <strong>{total}</strong>
          <small>Inspections recorded for this account</small>
        </article>
        <article className="supervisor-kpi">
          <span>Normal products</span>
          <strong>{normal}</strong>
          <small>{Number(summary?.normal_rate || 0)}% normal rate</small>
        </article>
        <article className="supervisor-kpi">
          <span>Defects detected</span>
          <strong>{defects}</strong>
          <small>{defectRate}% defect rate</small>
        </article>
        <article className="supervisor-kpi">
          <span>Average severity</span>
          <strong>{Number(summary?.average_severity_score || 0).toFixed(1)}</strong>
          <small>Score across assessed inspections</small>
        </article>
      </section>

      <section className="supervisor-panel">
        <div className="supervisor-section-heading">
          <div>
            <h2>Quality risk monitor</h2>
            <p>Severity counts from available quality assessments</p>
          </div>
          <span className="supervisor-status">
            {summary?.overall_quality_status || "Status unavailable"}
          </span>
        </div>
        <div className="supervisor-risk-grid">
          {[
            ["Critical", severity.critical, "critical"],
            ["High", severity.high, "high"],
            ["Medium", severity.medium, "medium"],
            ["Low", severity.low, "low"],
            ["Pending", severity.pending, "pending"],
          ].map(([label, count, tone]) => (
            <div className={`supervisor-risk ${tone}`} key={label}>
              <span>{label}</span>
              <strong>{Number(count || 0)}</strong>
            </div>
          ))}
        </div>
      </section>

      <section className="supervisor-panel">
        <div className="supervisor-section-heading">
          <div>
            <h2>Daily production trend</h2>
            <p>Inspection volume and defect counts by date</p>
          </div>
        </div>
        {daily.length === 0 ? (
          <p className="supervisor-empty">No daily trend data available yet.</p>
        ) : (
          <div className="supervisor-table-wrap">
            <table className="supervisor-table">
              <thead>
                <tr>
                  <th>Date</th><th>Inspections</th><th>Normal</th>
                  <th>Defects</th><th>Defect rate</th>
                </tr>
              </thead>
              <tbody>
                {daily.slice(-10).reverse().map((item) => (
                  <tr key={item.date}>
                    <td>{formatDate(item.date)}</td>
                    <td>{item.total}</td>
                    <td>{item.normal}</td>
                    <td>{item.defect}</td>
                    <td>{Number(item.defect_rate || 0)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="supervisor-panel">
        <div className="supervisor-section-heading">
          <div>
            <h2>Product category performance</h2>
            <p>Compare inspection volumes and defect rates by category</p>
          </div>
        </div>
        {categories.length === 0 ? (
          <p className="supervisor-empty">No category data available yet.</p>
        ) : (
          <div className="supervisor-table-wrap">
            <table className="supervisor-table">
              <thead>
                <tr>
                  <th>Category</th><th>Inspections</th>
                  <th>Normal</th><th>Defects</th><th>Defect rate</th>
                </tr>
              </thead>
              <tbody>
                {categories.map((item) => (
                  <tr key={item.category}>
                    <td className="supervisor-category">
                      {formatCategory(item.category)}
                    </td>
                    <td>{item.total}</td>
                    <td>{item.normal}</td>
                    <td>{item.defect}</td>
                    <td>
                      <div className="supervisor-rate">
                        <span>{Number(item.defect_rate || 0)}%</span>
                        <div className="supervisor-rate-track">
                          <div
                            className="supervisor-rate-fill"
                            style={{
                              width: `${Math.min(100, Math.max(0, Number(item.defect_rate) || 0))}%`,
                            }}
                          />
                        </div>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="supervisor-panel">
        <div className="supervisor-section-heading">
          <div>
            <h2>Recent inspections</h2>
            <p>Latest recorded quality outcomes</p>
          </div>
        </div>
        {recent.length === 0 ? (
          <p className="supervisor-empty">
            No inspections recorded yet. Complete an inspection to populate this table.
          </p>
        ) : (
          <div className="supervisor-table-wrap">
            <table className="supervisor-table">
              <thead>
                <tr>
                  <th>Category</th><th>Result</th><th>Severity</th>
                  <th>Anomaly score</th><th>Date</th>
                </tr>
              </thead>
              <tbody>
                {recent.map((item) => (
                  <tr key={item.id}>
                    <td className="supervisor-category">{formatCategory(item.category)}</td>
                    <td>
                      <span className={`supervisor-result ${
                        String(item.result).toUpperCase() === "NORMAL" ? "pass" : "review"
                      }`}>
                        {item.result || "Pending"}
                      </span>
                    </td>
                    <td>{item.severity_level || "Pending"}</td>
                    <td>{Number(item.anomaly_score || 0).toFixed(4)}</td>
                    <td>{formatDate(item.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <p className="supervisor-footnote">
        Figures reflect inspections available to the signed-in account; they are not
        a consolidated view of every factory user.
      </p>
    </div>
  );
}
