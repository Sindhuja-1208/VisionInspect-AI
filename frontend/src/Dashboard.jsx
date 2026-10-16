
import UploadInspection from "./UploadInspection";
import "./Dashboard.css";

function Dashboard() {
  let user = {};

  try {
    user = JSON.parse(localStorage.getItem("user") || "{}");
  } catch {
    user = {};
  }

  return (
    <div className="dashboard-page">
      <main className="dashboard-content">
        <section className="welcome-section">
          <div className="welcome-left">
            <div className="section-eyebrow">
              AI QUALITY CONTROL CENTER
            </div>

            <h2>
              Welcome back,{" "}
              <span>{user.name || "Quality Engineer"}</span>
            </h2>

            <p>
              Inspect product images, detect visual anomalies,
              and evaluate manufacturing quality using AI.
            </p>
          </div>

          <div className="system-status">
            <div className="status-dot" />
            <div>
              <strong>AI System</strong>
              <span>PatchCore Inspection Engine</span>
            </div>
          </div>
        </section>

        <UploadInspection />
      </main>
    </div>
  );
}

export default Dashboard;
