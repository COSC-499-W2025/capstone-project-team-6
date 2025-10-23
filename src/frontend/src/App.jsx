import React, { useState } from "react";

function App() {
  const [mode, setMode] = useState("login"); // "login" or "signup"
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");

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
      setMessage(data.message);
    } catch (err) {
      setMessage(err.message || "Something went wrong");
    }
  };

  return (
    <div style={{ width: "300px", margin: "100px auto", textAlign: "center" }}>
      <h2>{mode === "login" ? "Login" : "Sign Up"}</h2>

      <form onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          style={{ width: "100%", padding: "8px", marginBottom: "10px" }}
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          style={{ width: "100%", padding: "8px", marginBottom: "10px" }}
        />

        <button type="submit" style={{ width: "100%", padding: "8px" }}>
          {mode === "login" ? "Login" : "Sign Up"}
        </button>
      </form>

      <p style={{ marginTop: "10px" }}>{message}</p>

      <button
        onClick={() => setMode(mode === "login" ? "signup" : "login")}
        style={{
          marginTop: "10px",
          background: "none",
          border: "none",
          color: "blue",
          cursor: "pointer",
          textDecoration: "underline",
        }}
      >
        {mode === "login"
          ? "Don't have an account? Sign up"
          : "Already have an account? Log in"}
      </button>
    </div>
  );
}

export default App;
