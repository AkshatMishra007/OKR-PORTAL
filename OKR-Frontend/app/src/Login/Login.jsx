import { useState } from "react";
import "./Login.css";
import { useNavigate } from "react-router-dom";
import {API_URL} from "../Config/ApiEndpoint";
import logo from "../logo.svg";

function Login() {
  const [username_or_email, setUsernameOrEmail] = useState("");
  const [password, setPassword] = useState("");

  const navigate = useNavigate();

  const handleLogin = async (event) => {
    event.preventDefault();

    try {
      const response = await fetch(
        `${API_URL}/api/auth/login`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Accept": "application/json"
          },
          body: JSON.stringify({ username_or_email, password }),
        }
      );
    console.log("Login response status:", response);
      const data = await response.json();
      console.log("Login response data:", data);
      if (data.access_token) {
        // Login successful
        localStorage.setItem("token", data.access_token);
        localStorage.setItem("refresh_token", data.refresh_token);
        navigate("/my-okr");
      } else {
        // Login failed
        alert("Invalid email or password");
      }
    } catch (error) {
      console.error("Error fetching user data:", error);
      alert("Something went wrong while logging in");
    }
  };

  return (
    <div id="page-login">
      <div className="login-box">

        <div className="login-logo">
          <div id="login-logo-img">
            <img src={logo} alt="Logo" />
          </div>

          <h1>
            OKR <span>Portal</span>
          </h1>

          <p>Objectives &amp; Key Results Platform</p>
        </div>

        <form onSubmit={handleLogin}>

          <div className="form-field">
            <label className="form-label" htmlFor="login-email">
              Username/Email
            </label>

            <input
              type="text"
              className="form-input"
              placeholder="Enter your email"
              id="login-email"
              value={username_or_email}
              onChange={(event) => setUsernameOrEmail(event.target.value)}
              required
            />
          </div>

          <div className="form-field">
            <label className="form-label" htmlFor="login-pass">
              Password
            </label>

            <input
              type="password"
              className="form-input"
              placeholder="Enter password"
              id="login-pass"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
          </div>

          <button type="submit" className="btn-primary">
            Sign In
          </button>

        </form>

        <p className="login-footer">
          Forgot password?{" "}
          <a href="/forgot-password">Reset here</a>
        </p>

      </div>
    </div>
  );
}

export default Login;