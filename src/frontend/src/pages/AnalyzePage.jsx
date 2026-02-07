import { useEffect, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext"; 
import {startAnalysisRequest, getTaskStatus, cleanupUploadRequest  } from "../services/analysisApi";


//const API_BASE = ""; 

export default function AnalyzePage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();
  

  const uploadId = sessionStorage.getItem("upload_id");
  const zipPath =
    uploadId
      ? `(loaded from database) upload_id=${uploadId}`
      : "(missing upload_id — please upload a zip first)";

  const [status, setStatus] = useState("starting"); // starting | running | completed | failed
  const [progress, setProgress] = useState(0);
  const [taskId, setTaskId] = useState(null);
  const [error, setError] = useState("");

  const pollTimerRef = useRef(null);
  const cancelledRef = useRef(false);

  useEffect(() => {
    cancelledRef.current = false;

    // If user isn't ready yet, don't start.
    if (!user?.token) {
      setStatus("failed");
      setError("Missing auth token. Please log in again.");
      return;
    }
        if (!uploadId) {
      setStatus("failed");
      setError("Missing upload_id. Please upload a zip first (Upload page should store upload_id in sessionStorage).");
      return;
    }

    startAnalysis();

    return () => {
      cancelledRef.current = true;
      if (pollTimerRef.current) clearInterval(pollTimerRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user?.token]);

  async function startAnalysis() {
    try {
      setStatus("starting");
      setError("");
      const data = await startAnalysisRequest(user.token, uploadId);
      console.log("startAnalysis response:", data);

      if (!data.task_id) throw new Error("Start failed: no task_id returned");
      if (cancelledRef.current) return;

      setTaskId(data.task_id);
      setStatus("running");
      setProgress(0);

      beginPolling(data.task_id);
    } catch (e) {
      if (cancelledRef.current) return;
      setStatus("failed");
      setError(e?.message ?? "Unknown error starting analysis");
    }
  }

  function beginPolling(id) {
    // poll immediately once, then every 1s
    pollOnce(id);

    pollTimerRef.current = setInterval(() => {
      pollOnce(id);
    }, 1000);
  }

  async function pollOnce(id) {
    try {
      const data = await getTaskStatus(id, user.token);
      console.log("task status:", data.status, data.progress);


      if (cancelledRef.current) return;

      const p = typeof data.progress === "number" ? data.progress : 0;
      setProgress(Math.max(0, Math.min(100, p)));

      const s = (data.status || "").toLowerCase();
      if (s === "completed") {
        setStatus("completed");
        setProgress(100);
        clearInterval(pollTimerRef.current);
        const analysisUuid = data?.result?.analysis_uuid;
        if (analysisUuid) {
          sessionStorage.setItem("portfolio_id", analysisUuid);
        }

        try {
          await cleanupUploadRequest(user.token, uploadId);
        } catch (cleanupErr) {
          // Cleanup failing shouldn't block redirect, but we show a warning
          console.warn("Cleanup failed:", cleanupErr);
          setError(cleanupErr?.message ?? "Cleanup failed (zip may not have been deleted).");
        }
         navigate("/projects");
        return;


      } else if (s === "failed") {
        setStatus("failed");
        setError(data.error || "Analysis failed");
        clearInterval(pollTimerRef.current);
      } else {
        setStatus("running");
      }
    } catch (e) {
      if (cancelledRef.current) return;
      // If polling fails temporarily, keep running but show last error
      setError(e?.message ?? "Polling error");
    }
  }

  const isDone = status === "completed";
  const isFailed = status === "failed";

  return (
    <div style={{ padding: 24, maxWidth: 720 }}>
      <h1>Analyzing Project</h1>

      <div style={{ marginTop: 12, marginBottom: 18 }}>
        <div style={{ fontSize: 14, opacity: 0.8 }}>Project path</div>
        <div style={{ fontFamily: "monospace", marginTop: 6 }}>{zipPath}</div>
      </div>

      <div style={{ marginTop: 12 }}>
        <div style={{ marginBottom: 8 }}>
          Status:{" "}
          <b>
            {status === "starting"
              ? "Starting…"
              : status === "running"
              ? "Running…"
              : status === "completed"
              ? "Completed"
              : "Failed"}
          </b>
        </div>

        {/* Progress bar */}
        <div
          style={{
            height: 14,
            background: "#e5e5e5",
            borderRadius: 8,
            overflow: "hidden",
          }}
        >
          <div
            style={{
              height: "100%",
              width: `${progress}%`,
              background: "#4f46e5",
              transition: "width 250ms linear",
            }}
          />
        </div>

        <div style={{ marginTop: 8, fontSize: 13, opacity: 0.8 }}>
          {taskId ? `Task: ${taskId}` : ""}
          {taskId ? " · " : ""}
          {`${progress}%`}
        </div>

        {error ? (
          <div style={{ marginTop: 12, color: "#b91c1c" }}>
            {isFailed ? "Error: " : "Warning: "}
            {error}
          </div>
        ) : null}
      </div>

      {/* Buttons */}
      <div style={{ display: "flex", gap: 12, marginTop: 24 }}>
        <button onClick={() => navigate("/dashboard")}>Exit</button>

        <button
          onClick={() => navigate("/projects")}
          disabled={!isDone}
          title={!isDone ? "Wait for analysis to complete" : ""}
        >
          Go to Projects
        </button>


        {/* Optional: retry if failed */}
        {isFailed ? (
          <button onClick={startAnalysis}>Retry</button>
        ) : null}
      </div>
    </div>
  );
}

