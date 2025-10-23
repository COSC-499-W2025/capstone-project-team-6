import React from "react";

function Dashboard({ username, onLogout }) {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        minHeight: "100vh",
        background:
          "linear-gradient(135deg, #60a5fa 0%, #a78bfa 100%)",
        fontFamily: "Inter, Arial, sans-serif",
        color: "#111827",
      }}
    >
      <div
        style={{
          backgroundColor: "white",
          padding: "40px 30px",
          borderRadius: "16px",
          boxShadow: "0 4px 20px rgba(0,0,0,0.1)",
          width: "360px",
          textAlign: "center",
        }}
      >
        <h2 style={{ marginBottom: "16px" }}>Welcome, {username}</h2>
        <p style={{ color: "#4B5563", marginBottom: "30px" }}>
          You’ve successfully logged in.          </p>

        <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          <button
            onClick={() => alert("Consent form page here")}
            style={{
              padding: "10px",
              backgroundColor: "#2563EB",
              color: "white",
              border: "none",
              borderRadius: "8px",
              fontSize: "15px",
              cursor: "pointer",
              transition: "background 0.2s",
            }}
            onMouseOver={(e) => (e.target.style.backgroundColor = "#1D4ED8")}
            onMouseOut={(e) => (e.target.style.backgroundColor = "#2563EB")}
          >
            Fill out Consent form to Proceed
          </button>

          <button
            onClick={() => alert("File upload here")}
            style={{
              padding: "10px",
              backgroundColor: "#10B981",
              color: "white",
              border: "none",
              borderRadius: "8px",
              fontSize: "15px",
              cursor: "pointer",
              transition: "background 0.2s",
            }}
            onMouseOver={(e) => (e.target.style.backgroundColor = "#059669")}
            onMouseOut={(e) => (e.target.style.backgroundColor = "#10B981")}
          >
            Upload Project Files
          </button>

          <button
            onClick={onLogout}
            style={{
              marginTop: "20px",
              padding: "10px",
              backgroundColor: "#EF4444",
              color: "white",
              border: "none",
              borderRadius: "8px",
              fontSize: "15px",
              cursor: "pointer",
              transition: "background 0.2s",
            }}
            onMouseOver={(e) => (e.target.style.backgroundColor = "#DC2626")}
            onMouseOut={(e) => (e.target.style.backgroundColor = "#EF4444")}
          >
            Logout
          </button>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
