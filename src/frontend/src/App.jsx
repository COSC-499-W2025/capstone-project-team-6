import React, { useState, useEffect } from "react";
import Dashboard from "./Dashboard.jsx";

function App() {
  const [mode, setMode] = useState("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [loggedIn, setLoggedIn] = useState(false);

  useEffect(() => {
    const savedUser = localStorage.getItem("username");
    if (savedUser) {
      setUsername(savedUser);
      setLoggedIn(true);
    }
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage("Loading...");

    const endpoint =
      mode === "login"
        ? "http://localhost:8080/login"
        : "http://localhost:8080/signup";

    try {
      const res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Request failed");

      setMessage("");
      setLoggedIn(true);
      localStorage.setItem("username", username);
    } catch (err) {
      setMessage(err.message || "Something went wrong");
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("username");
    setUsername("");
    setPassword("");
    setLoggedIn(false);
    setMessage("");
  };

  if (loggedIn) {
    return <Dashboard username={username} onLogout={handleLogout} />;
  }

  return (
    <div
      style={{
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        minHeight: "100vh",
        background: "linear-gradient(135deg, #6EE7B7 0%, #3B82F6 100%)",
        fontFamily: "Inter, Arial, sans-serif",
      }}
    >
      <div
        style={{
          backgroundColor: "white",
          padding: "40px 30px",
          borderRadius: "16px",
          boxShadow: "0 4px 20px rgba(0,0,0,0.1)",
          width: "320px",
          textAlign: "center",
        }}
      >
        <h2 style={{ marginBottom: "24px", color: "#111827" }}>
          {mode === "login" ? "Welcome" : "Create an Account"}
        </h2>

        <form onSubmit={handleSubmit}>
          <input
            type="text"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            style={{
              width: "100%",
              padding: "10px 12px",
              marginBottom: "12px",
              borderRadius: "8px",
              border: "1px solid #d1d5db",
              fontSize: "15px",
            }}
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            style={{
              width: "100%",
              padding: "10px 12px",
              marginBottom: "16px",
              borderRadius: "8px",
              border: "1px solid #d1d5db",
              fontSize: "15px",
            }}
          />
          <button
            type="submit"
            style={{
              width: "100%",
              padding: "10px",
              backgroundColor: "#3B82F6",
              color: "white",
              border: "none",
              borderRadius: "8px",
              fontSize: "15px",
              cursor: "pointer",
              fontWeight: 500,
              transition: "background 0.2s ease",
            }}
            onMouseOver={(e) => (e.target.style.backgroundColor = "#2563EB")}
            onMouseOut={(e) => (e.target.style.backgroundColor = "#3B82F6")}
          >
            {mode === "login" ? "Login" : "Sign Up"}
          </button>
        </form>

        <p style={{ marginTop: "14px", color: "#374151" }}>{message}</p>

        <button
          onClick={() => setMode(mode === "login" ? "signup" : "login")}
          style={{
            marginTop: "18px",
            background: "none",
            border: "none",
            color: "#2563EB",
            cursor: "pointer",
            fontSize: "14px",
            textDecoration: "underline",
          }}
        >
          {mode === "login"
            ? "Don't have an account? Sign up"
            : "Already have an account? Log in"}
        </button>
      </div>
    </div>
  );
}

export default App;
