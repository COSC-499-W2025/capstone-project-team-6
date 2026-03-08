import { useEffect, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { getTaskStatus } from "../services/analysisApi";

export default function AnalyzePage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();

  const taskIdFromNav = location.state?.taskId ?? sessionStorage.getItem("analyze_task_id") ?? null;
  const projectType = location.state?.projectType ?? sessionStorage.getItem("analyze_project_type") ?? null;
  const analysisType = location.state?.analysisType ?? sessionStorage.getItem("analyze_analysis_type") ?? null;
  const projectName = location.state?.projectName ?? sessionStorage.getItem("analyze_project_name") ?? null;

  const [status, setStatus] = useState("starting");
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState("");
  const [analysisPhase, setAnalysisPhase] = useState(null);

  const pollTimerRef = useRef(null);
  const cancelledRef = useRef(false);

  useEffect(() => {
    cancelledRef.current = false;

    if (!user?.token) {
      setStatus("failed");
      setError("Missing auth token. Please log in again.");
      return;
    }

    if (!taskIdFromNav) {
      setStatus("failed");
      setError("Missing task. Please go back to Upload and click Analyze again.");
      return;
    }

    setStatus("running");
    setProgress(0);
    setError("");

    beginPolling(taskIdFromNav);

    return () => {
      cancelledRef.current = true;
      if (pollTimerRef.current) clearInterval(pollTimerRef.current);
    };
  }, [user?.token, taskIdFromNav]);

  function beginPolling(id) {
    pollOnce(id);
    pollTimerRef.current = setInterval(() => {
      pollOnce(id);
    }, 1000);
  }

  async function pollOnce(id) {
    try {
      const data = await getTaskStatus(id, user.token);

      if (cancelledRef.current) return;

      const p = typeof data.progress === "number" ? data.progress : 0;
      setProgress(Math.max(0, Math.min(100, p)));
      setAnalysisPhase(data.analysis_phase || null);

      const s = (data.status || "").toLowerCase();
      if (s === "completed") {
        setStatus("completed");
        setProgress(100);
        clearInterval(pollTimerRef.current);
        const analysisUuid = data?.result?.analysis_uuid;
        if (analysisUuid) {
          sessionStorage.setItem("portfolio_id", analysisUuid);
        }
        sessionStorage.removeItem("analyze_task_id");
        sessionStorage.removeItem("analyze_project_type");
        sessionStorage.removeItem("analyze_analysis_type");
        sessionStorage.removeItem("analyze_project_name");

        if (data?.result?.duplicate === true) {
          navigate("/upload", { state: { duplicateMessage: "This project has already been analyzed. You can view it in your projects." } });
        } else {
          navigate("/projects");
        }
      } else if (s === "failed") {
        setStatus("failed");
        setError(data.error || "Analysis failed");
        clearInterval(pollTimerRef.current);
      } else {
        setStatus("running");
      }
    } catch (e) {
      if (cancelledRef.current) return;
      setError(e?.message ?? "Polling error");
    }
  }

  const isDone = status === "completed";
  const isFailed = status === "failed";

  const projectTypeLabel = projectType === "multiple" ? "Multi-Project" : "Single Project";
  const analysisTypeLabel = analysisType === "llm" ? "LLM Analysis" : "Non-LLM Analysis";

  const statusLabel =
    status === "starting" ? "Starting…"
    : status === "running" ? "Running…"
    : status === "completed" ? "Completed"
    : "Failed";

  const statusColor =
    status === "completed" ? "#16a34a"
    : status === "failed" ? "#dc2626"
    : "#4f46e5";

  const phaseMessage =
    analysisPhase === "non_llm" ? "Running non-LLM analysis…"
    : analysisPhase === "llm" ? "Running LLM analysis…"
    : null;

  return (
    <div style={{ minHeight: "100vh", backgroundColor: "#fafafa" }}>

      <div style={{ maxWidth: 720, margin: "0 auto", padding: "48px 32px" }}>
        {/* Header */}
        <div style={{ marginBottom: 40 }}>
          <h1 style={{
            fontSize: 36,
            fontWeight: 600,
            margin: "0 0 8px 0",
            color: "#1a1a1a",
            letterSpacing: "-0.5px",
          }}>
            Analyzing Project
          </h1>
          <p style={{ fontSize: 16, color: "#737373", margin: 0 }}>
            Your project is being processed. This page will update automatically.
          </p>
        </div>

        {/* Project name card */}
        {projectName && (
          <div style={{
            backgroundColor: "white",
            borderRadius: 12,
            border: "1px solid #e5e5e5",
            padding: "20px 24px",
            marginBottom: 20,
            display: "flex",
            alignItems: "center",
            gap: 14,
          }}>
            <span style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              width: 40,
              height: 40,
              backgroundColor: "#f5f3ff",
              borderRadius: 10,
              fontSize: 18,
            }}>
              📂
            </span>
            <div>
              <div style={{ fontSize: 13, color: "#737373", fontWeight: 500, marginBottom: 2 }}>
                Project Name
              </div>
              <div style={{ fontSize: 16, fontWeight: 600, color: "#1a1a1a" }}>
                {projectName}
              </div>
            </div>
          </div>
        )}

        {/* Info badges */}
        <div style={{ display: "flex", gap: 12, marginBottom: 24, flexWrap: "wrap" }}>
          <span style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 6,
            padding: "6px 14px",
            backgroundColor: "#f0fdf4",
            color: "#15803d",
            borderRadius: 20,
            fontSize: 13,
            fontWeight: 500,
            border: "1px solid #bbf7d0",
          }}>
            📁 {projectTypeLabel}
          </span>
          <span style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 6,
            padding: "6px 14px",
            backgroundColor: analysisType === "llm" ? "#eff6ff" : "#faf5ff",
            color: analysisType === "llm" ? "#1d4ed8" : "#7e22ce",
            borderRadius: 20,
            fontSize: 13,
            fontWeight: 500,
            border: `1px solid ${analysisType === "llm" ? "#bfdbfe" : "#e9d5ff"}`,
          }}>
            {analysisType === "llm" ? "🤖" : "⚙️"} {analysisTypeLabel}
          </span>
        </div>

        {/* Main card */}
        <div style={{
          backgroundColor: "white",
          borderRadius: 16,
          border: "1px solid #e5e5e5",
          padding: 32,
          marginBottom: 24,
        }}>
          {/* Status row */}
          <div style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: 24,
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              {status === "running" && (
                <span style={{
                  display: "inline-block",
                  width: 10,
                  height: 10,
                  borderRadius: "50%",
                  backgroundColor: "#4f46e5",
                  animation: "pulse 1.5s ease-in-out infinite",
                }} />
              )}
              {status === "completed" && <span style={{ fontSize: 18 }}>✅</span>}
              {status === "failed" && <span style={{ fontSize: 18 }}>❌</span>}
              {status === "starting" && <span style={{ fontSize: 18 }}>⏳</span>}
              <span style={{
                fontSize: 16,
                fontWeight: 600,
                color: statusColor,
              }}>
                {statusLabel}
              </span>
            </div>
            <span style={{
              fontSize: 24,
              fontWeight: 600,
              color: "#1a1a1a",
              letterSpacing: "-0.5px",
            }}>
              {progress}%
            </span>
          </div>

          {/* Progress bar */}
          <div style={{
            height: 8,
            background: "#f5f5f5",
            borderRadius: 8,
            overflow: "hidden",
            marginBottom: 20,
          }}>
            <div style={{
              height: "100%",
              width: `${progress}%`,
              background: isFailed
                ? "#dc2626"
                : "linear-gradient(90deg, #4f46e5, #7c3aed)",
              borderRadius: 8,
              transition: "width 250ms linear",
            }} />
          </div>

          {/* Phase info */}
          {status === "running" && phaseMessage && (
            <div style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              padding: "10px 16px",
              backgroundColor: "#f5f3ff",
              borderRadius: 8,
              marginBottom: 16,
            }}>
              <span style={{ fontSize: 14 }}>🔍</span>
              <span style={{ fontSize: 14, color: "#5b21b6", fontWeight: 500 }}>
                {phaseMessage}
              </span>
            </div>
          )}

          {/* Error message */}
          {error && (
            <div style={{
              padding: "12px 16px",
              backgroundColor: isFailed ? "#fef2f2" : "#fffbeb",
              border: `1px solid ${isFailed ? "#fecaca" : "#fde68a"}`,
              borderRadius: 8,
              color: isFailed ? "#991b1b" : "#92400e",
              fontSize: 14,
            }}>
              <strong>{isFailed ? "Error: " : "Warning: "}</strong>
              {error}
            </div>
          )}
        </div>

        {/* Action buttons */}
        <div style={{ display: "flex", gap: 12 }}>
          <button
            onClick={() => navigate("/dashboard")}
            style={{
              padding: "10px 20px",
              backgroundColor: "white",
              color: "#1a1a1a",
              border: "1px solid #e5e5e5",
              borderRadius: 8,
              cursor: "pointer",
              fontSize: 14,
              fontWeight: 500,
              transition: "all 0.2s",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = "#f5f5f5";
              e.currentTarget.style.borderColor = "#d4d4d4";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = "white";
              e.currentTarget.style.borderColor = "#e5e5e5";
            }}
          >
            ← Back to Dashboard
          </button>

          <button
            onClick={() => navigate("/projects")}
            disabled={!isDone}
            style={{
              padding: "10px 20px",
              backgroundColor: isDone ? "#1a1a1a" : "#d4d4d4",
              color: isDone ? "white" : "#a3a3a3",
              border: "none",
              borderRadius: 8,
              cursor: isDone ? "pointer" : "not-allowed",
              fontSize: 14,
              fontWeight: 500,
              transition: "all 0.2s",
            }}
            onMouseEnter={(e) => {
              if (isDone) e.currentTarget.style.backgroundColor = "#333";
            }}
            onMouseLeave={(e) => {
              if (isDone) e.currentTarget.style.backgroundColor = "#1a1a1a";
            }}
          >
            Go to Projects →
          </button>

          {isFailed && (
            <button
              onClick={() => taskIdFromNav && beginPolling(taskIdFromNav)}
              style={{
                padding: "10px 20px",
                backgroundColor: "#fef2f2",
                color: "#dc2626",
                border: "1px solid #fecaca",
                borderRadius: 8,
                cursor: "pointer",
                fontSize: 14,
                fontWeight: 500,
                transition: "all 0.2s",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = "#fee2e2";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = "#fef2f2";
              }}
            >
              ↻ Retry
            </button>
          )}
        </div>
      </div>

      {/* Pulse animation */}
      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.4; }
        }
      `}</style>
    </div>
  );
}

