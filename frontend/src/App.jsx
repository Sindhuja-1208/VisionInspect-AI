import { useState } from "react";
import "./App.css";

import { loginUser } from "./services/api";

import Dashboard from "./Dashboard";
import Analytics from "./Analytics";


function App() {

  // ============================================================
  // LOGIN STATE
  // ============================================================

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("");

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);


  // ============================================================
  // LOGIN STATUS
  // ============================================================

  const [isLoggedIn, setIsLoggedIn] =
    useState(
      !!localStorage.getItem(
        "access_token"
      )
    );


  // ============================================================
  // CURRENT PAGE
  // ============================================================

  const [currentPage, setCurrentPage] =
    useState("dashboard");


  // ============================================================
  // LOGIN
  // ============================================================

  const handleLogin = async (event) => {

    event.preventDefault();

    setError("");


    if (
      !email ||
      !password ||
      !role
    ) {

      setError(
        "Please fill all fields."
      );

      return;
    }


    try {

      setLoading(true);


      const data =
        await loginUser(
          email,
          password
        );


      if (
        data.user.role !== role
      ) {

        setError(
          "Selected role does not match your account."
        );

        return;
      }


      localStorage.setItem(
        "access_token",
        data.access_token
      );


      localStorage.setItem(
        "user",
        JSON.stringify(
          data.user
        )
      );


      setIsLoggedIn(true);

      setCurrentPage(
        "dashboard"
      );


    } catch (err) {

      setError(
        err.message
      );

    } finally {

      setLoading(false);

    }

  };


  // ============================================================
  // LOGOUT
  // ============================================================

  const handleLogout = () => {

    localStorage.clear();

    setIsLoggedIn(false);

    setCurrentPage(
      "dashboard"
    );

  };


  // ============================================================
  // IF LOGGED IN
  // ============================================================

  if (isLoggedIn) {

    return (

      <div className="app-container">


        {/* ==================================================
            NAVIGATION
            ================================================== */}

        <nav className="app-navigation">


          {/* BRAND */}

          <div className="app-nav-brand">

            <div className="app-nav-logo">
              VI
            </div>

            <div>

              <strong>
                VisionInspect
              </strong>

              <span>
                AI
              </span>

            </div>

          </div>


          {/* NAVIGATION BUTTONS */}

          <div className="app-nav-links">


            <button
              className={
                currentPage === "dashboard"
                  ? "nav-button active"
                  : "nav-button"
              }
              onClick={() =>
                setCurrentPage(
                  "dashboard"
                )
              }
            >
              Dashboard
            </button>


            <button
              className={
                currentPage === "analytics"
                  ? "nav-button active"
                  : "nav-button"
              }
              onClick={() =>
                setCurrentPage(
                  "analytics"
                )
              }
            >
              Analytics
            </button>


          </div>


          {/* LOGOUT */}

          <button
            className="app-logout-button"
            onClick={
              handleLogout
            }
          >
            Logout
          </button>


        </nav>


        {/* ==================================================
            PAGE CONTENT
            ================================================== */}

        <main className="app-page-content">

          {currentPage ===
            "dashboard" && (

            <Dashboard />

          )}


          {currentPage ===
            "analytics" && (

            <Analytics />

          )}

        </main>


      </div>

    );

  }


  // ============================================================
  // LOGIN PAGE
  // ============================================================

  return (

    <div className="login-page">

      <div className="login-card">


        {/* ==================================================
            LOGO
            ================================================== */}

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


        {/* ==================================================
            LOGIN FORM
            ================================================== */}

        <form
          className="login-form"
          onSubmit={
            handleLogin
          }
        >

          <h2>
            Welcome Back
          </h2>

          <p className="login-subtitle">
            Sign in to access the
            inspection dashboard
          </p>


          {/* ERROR */}

          {error && (

            <div className="error-message">

              {error}

            </div>

          )}


          {/* EMAIL */}

          <label>
            Email Address
          </label>

          <input
            type="email"
            placeholder="Enter your email"
            value={email}
            onChange={(event) =>
              setEmail(
                event.target.value
              )
            }
          />


          {/* PASSWORD */}

          <label>
            Password
          </label>

          <input
            type="password"
            placeholder="Enter your password"
            value={password}
            onChange={(event) =>
              setPassword(
                event.target.value
              )
            }
          />


          {/* ROLE */}

          <label>
            Role
          </label>

          <select
            value={role}
            onChange={(event) =>
              setRole(
                event.target.value
              )
            }
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


          {/* LOGIN BUTTON */}

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