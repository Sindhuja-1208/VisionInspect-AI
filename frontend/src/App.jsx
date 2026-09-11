import { useState } from "react";
import "./App.css";
import { loginUser } from "./services/api";
import Dashboard from "./Dashboard";

function App() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const [isLoggedIn, setIsLoggedIn] = useState(
    !!localStorage.getItem("access_token")
  );

  const handleLogin = async (event) => {
    event.preventDefault();

    setError("");

    if (!email || !password || !role) {
      setError("Please fill all fields.");
      return;
    }

    try {
      setLoading(true);

      const data = await loginUser(email, password);

      if (data.user.role !== role) {
        setError("Selected role does not match your account.");
        return;
      }

      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("user", JSON.stringify(data.user));

      setIsLoggedIn(true);

    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // If already logged in, show Dashboard
  if (isLoggedIn) {
    return <Dashboard />;
  }

  return (
    <div className="login-page">

      <div className="login-card">

        <div className="logo-section">

          <div className="logo-icon">
            VI
          </div>

          <h1>
            VisionInspect AI
          </h1>

          <p>
            Manufacturing Quality Inspection System
          </p>

        </div>


        <form
          className="login-form"
          onSubmit={handleLogin}
        >

          <h2>
            Welcome Back
          </h2>

          <p className="login-subtitle">
            Sign in to access the inspection dashboard
          </p>


          {error && (
            <div className="error-message">
              {error}
            </div>
          )}


          <label>
            Email Address
          </label>

          <input
            type="email"
            placeholder="Enter your email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />


          <label>
            Password
          </label>

          <input
            type="password"
            placeholder="Enter your password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />


          <label>
            Role
          </label>

          <select
            value={role}
            onChange={(e) => setRole(e.target.value)}
          >

            <option value="">
              Select your role
            </option>

            <option value="Quality Engineer">
              Quality Engineer
            </option>

            <option value="Factory Supervisor">
              Factory Supervisor
            </option>

          </select>


          <button
            type="submit"
            className="login-button"
            disabled={loading}
          >
            {loading
              ? "Signing in..."
              : "Login"}
          </button>


          <p className="register-text">
            Don't have an account?{" "}
            <span>
              Register
            </span>
          </p>

        </form>

      </div>

    </div>
  );
}

export default App;