
import { useState } from "react";
import "./App.css";
import { loginUser, registerUser } from "./services/api";
import Dashboard from "./Dashboard";
import Analytics from "./Analytics";
import SupervisorDashboard from "./SupervisorDashboard";

function App() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);
  const [isRegistering, setIsRegistering] = useState(false);

  const [isLoggedIn, setIsLoggedIn] = useState(
    !!localStorage.getItem("access_token")
  );

  const getSavedUser = () => {
    try {
      return JSON.parse(localStorage.getItem("user") || "null");
    } catch {
      return null;
    }
  };

  const [currentPage, setCurrentPage] = useState(() =>
    getSavedUser()?.role === "Factory Supervisor"
      ? "production"
      : "dashboard"
  );

  // LOGIN
  const handleLogin = async (event) => {
    event.preventDefault();
    setError("");
    setSuccess("");

    if (!email.trim() || !password || !role) {
      setError("Please fill all fields.");
      return;
    }

    try {
      setLoading(true);
      const data = await loginUser(email.trim(), password);

      if (data.user.role !== role) {
        setError("Selected role does not match your account.");
        return;
      }

      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("user", JSON.stringify(data.user));

      setCurrentPage(
        data.user.role === "Factory Supervisor"
          ? "production"
          : "dashboard"
      );
      setIsLoggedIn(true);
    } catch (err) {
      setError(err.message || "Login failed.");
    } finally {
      setLoading(false);
    }
  };

  // REGISTER
  const handleRegister = async (event) => {
    event.preventDefault();
    setError("");
    setSuccess("");

    if (!name.trim() || !email.trim() || !password || !role) {
      setError("Please fill all fields.");
      return;
    }

    if (password.length < 8) {
      setError("Password must contain at least 8 characters.");
      return;
    }

    try {
      setLoading(true);
      await registerUser(name.trim(), email.trim(), password, role);

      setIsRegistering(false);
      setName("");
      setPassword("");
      setRole("");
      setSuccess("Registration successful! Please log in.");
    } catch (err) {
      setError(err.message || "Registration failed.");
    } finally {
      setLoading(false);
    }
  };

  // LOGOUT
  const handleLogout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user");

    setIsLoggedIn(false);
    setCurrentPage("dashboard");
    setName("");
    setEmail("");
    setPassword("");
    setRole("");
    setError("");
    setSuccess("");
    setIsRegistering(false);
  };

  // APPLICATION
  if (isLoggedIn) {
    const user = getSavedUser();
    const isSupervisor = user?.role === "Factory Supervisor";

    // Handle an invalid or missing saved user safely.
    if (!user) {
      localStorage.removeItem("access_token");
      setIsLoggedIn(false);
      return null;
    }

    return (
      <div className="app-container">
        <header className="app-navigation">
          <div className="app-nav-brand">
            <div className="app-nav-logo">✦</div>
            <div className="app-brand-text">
              <strong>VisionInspect AI</strong>
              <span>Intelligent Manufacturing Quality Inspection</span>
            </div>
          </div>

          <div className="app-nav-links">
            <button
              className={
                currentPage === (isSupervisor ? "production" : "dashboard")
                  ? "nav-button active"
                  : "nav-button"
              }
              onClick={() => setCurrentPage(isSupervisor ? "production" : "dashboard")}
            >
              {isSupervisor ? "Production Overview" : "Dashboard"}
            </button>

            <button
              className={
                currentPage === "analytics" ? "nav-button active" : "nav-button"
              }
              onClick={() => setCurrentPage("analytics")}
            >
              Analytics
            </button>
          </div>

          <div className="app-nav-user">
            <strong>{user.name}</strong>
            <small>{user.role}</small>
          </div>

          <button className="app-logout-button" onClick={handleLogout}>
            Logout
          </button>
        </header>
        <main className="app-page-content">
          {isSupervisor && currentPage === "production" && (
            <SupervisorDashboard />
          )}

          {!isSupervisor && currentPage === "dashboard" && (
            <Dashboard />
          )}

          {currentPage === "analytics" && <Analytics />}
        </main>
      </div>
    );
  }

  // LOGIN AND REGISTRATION
  return (
    <div className="login-page">
      <div className="login-card">
        <div className="logo-section">
          <div className="logo-icon">VI</div>
          <h1>VisionInspect AI</h1>
          <p>Manufacturing Quality Inspection System</p>
        </div>

        <form
          className="login-form"
          onSubmit={isRegistering ? handleRegister : handleLogin}
        >
          <h2>{isRegistering ? "Create Your Account" : "Welcome Back"}</h2>

          <p className="login-subtitle">
            {isRegistering
              ? "Register to access VisionInspect AI"
              : "Sign in to access your dashboard"}
          </p>

          {error && <div className="error-message">{error}</div>}
          {success && <div className="success-message">{success}</div>}

          {isRegistering && (
            <>
              <label htmlFor="register-name">Full Name</label>
              <input
                id="register-name"
                type="text"
                placeholder="Enter your full name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            </>
          )}

          <label htmlFor="email">Email Address</label>
          <input
            id="email"
            type="email"
            placeholder="Enter your email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />

          <label htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            placeholder={isRegistering ? "At least 8 characters" : "Enter your password"}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            minLength={isRegistering ? 8 : undefined}
            required
          />

          <label htmlFor="role">Role</label>
          <select
            id="role"
            value={role}
            onChange={(e) => setRole(e.target.value)}
            required
          >
            <option value="">Select your role</option>
            <option value="Quality Engineer">Quality Engineer</option>
            <option value="Factory Supervisor">Factory Supervisor</option>
          </select>

          <button
            type="submit"
            className="login-button"
            disabled={loading}
          >
            {loading
              ? "Please wait..."
              : isRegistering
                ? "Create Account"
                : "Login"}
          </button>

          <p className="register-text">
            {isRegistering
              ? "Already have an account? "
              : "Don't have an account? "}
            <span
              role="button"
              tabIndex={0}
              style={{ cursor: "pointer", fontWeight: "bold" }}
              onClick={() => {
                if (loading) return;
                setIsRegistering(!isRegistering);
                setError("");
                setSuccess("");
              }}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  if (loading) return;
                  setIsRegistering(!isRegistering);
                  setError("");
                  setSuccess("");
                }
              }}
            >
              {isRegistering ? "Login" : "Register"}
            </span>
          </p>
        </form>
      </div>
    </div>
  );
}

export default App;



