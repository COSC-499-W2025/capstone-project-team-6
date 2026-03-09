import { useEffect, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext"; 
//import {startAnalysisRequest, getTaskStatus, cleanupUploadRequest  } from "../services/analysisApi";
import { getTaskStatus } from "../services/analysisApi";


//const API_BASE = ""; 

export default function AnalyzePage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();
  

  // Support both single taskId and multiple taskIds
  const taskIdsFromNav = location.state?.taskIds ?? (location.state?.taskId ? [location.state.taskId] : null)
    ?? (() => {
      try {
        const stored = sessionStorage.getItem("analyze_task_ids");
        return stored ? JSON.parse(stored) : null;
      } catch {
        return null;
      }
    })()
    ?? (sessionStorage.getItem("analyze_task_id") ? [sessionStorage.getItem("analyze_task_id")] : null);
  const isMultiTask = Array.isArray(taskIdsFromNav) && taskIdsFromNav.length > 1;
  const displayInfo = taskIdsFromNav?.length
    ? (isMultiTask ? `${taskIdsFromNav.length} tasks` : `Task: ${taskIdsFromNav[0]}`)
    : "(missing taskId — please upload and analyze again)";

  const [status, setStatus] = useState("starting"); // starting | running | completed | failed
  const [progress, setProgress] = useState(0);
  const [taskId, setTaskId] = useState(null);
  const [taskStatuses, setTaskStatuses] = useState({}); // { taskId: "running"|"completed"|"failed" }
  const [error, setError] = useState("");
  const [analysisPhase, setAnalysisPhase] = useState(null); // "non_llm" | "llm" | null

  const pollTimerRef = useRef(null);
  const cancelledRef = useRef(false);

  useEffect(() => {
    cancelledRef.current = false;

    if (!user?.token) {
      setStatus("failed");
      setError("Missing auth token. Please log in again.");
      return;
    }

    if (!taskIdsFromNav || taskIdsFromNav.length === 0) {
      setStatus("failed");
      setError("Missing taskId. Please go back to Upload and click Analyze again.");
      return;
    }

    setTaskId(taskIdsFromNav[0]);
    setStatus("running");
    setProgress(0);
    setError("");
    setTaskStatuses({});

    beginPolling(taskIdsFromNav);

    return () => {
      cancelledRef.current = true;
      if (pollTimerRef.current) clearInterval(pollTimerRef.current);
    };
  }, [user?.token, taskIdsFromNav ? taskIdsFromNav.join(",") : null]);

  function beginPolling(ids) {
    const idList = Array.isArray(ids) ? ids : [ids];
    pollAllOnce(idList);
    pollTimerRef.current = setInterval(() => pollAllOnce(idList), 1000);
  }

  async function pollAllOnce(idList) {
    if (!idList?.length || !user?.token) return;
    const results = await Promise.all(
      idList.map(async (id) => {
        try {
          return await getTaskStatus(id, user.token);
        } catch (e) {
          return { status: "failed", error: e?.message ?? "Polling error", taskId: id };
        }
      })
    );

    if (cancelledRef.current) return;

    const statusMap = {};
    let completedCount = 0;
    let failedCount = 0;
    let anyDuplicate = false;
    let lastAnalysisUuid = null;
    let lastError = null;
    let maxProgress = 0;

    for (let i = 0; i < idList.length; i++) {
      const data = results[i];
      const id = idList[i];
      const s = (data?.status || "").toLowerCase();
      statusMap[id] = s;

      if (s === "completed") {
        completedCount++;
        if (data?.result?.duplicate === true) anyDuplicate = true;
        if (data?.result?.analysis_uuid) lastAnalysisUuid = data.result.analysis_uuid;
        const p = typeof data?.progress === "number" ? data.progress : 100;
        maxProgress = Math.max(maxProgress, p);
      } else if (s === "failed") {
        failedCount++;
        lastError = data?.error || "Analysis failed";
      } else {
        const p = typeof data?.progress === "number" ? data.progress : 0;
        maxProgress = Math.max(maxProgress, p);
      }
      if (data?.analysis_phase) setAnalysisPhase(data.analysis_phase);
    }

    setTaskStatuses(statusMap);
    setProgress(idList.length > 1 ? Math.round((completedCount / idList.length) * 100) : maxProgress);

    const allTerminal = completedCount + failedCount === idList.length;

    if (allTerminal) {
      clearInterval(pollTimerRef.current);
      sessionStorage.removeItem("analyze_task_id");
      sessionStorage.removeItem("analyze_task_ids");
      if (lastAnalysisUuid) sessionStorage.setItem("portfolio_id", lastAnalysisUuid);

      if (anyDuplicate && idList.length === 1) {
        navigate("/upload", { state: { duplicateMessage: "This project has already been analyzed. You can view it in your projects." } });
        return;
      }

      setStatus("completed");
      setProgress(100);
      if (failedCount > 0 && completedCount === 0) {
        setStatus("failed");
        setError(lastError || "All analyses failed");
      } else {
        navigate("/projects");
      }
    } else if (failedCount > 0) {
      setError(lastError || "Some analyses failed");
    } else {
      setStatus("running");
    }
  }

  const isDone = status === "completed";
  const isFailed = status === "failed";

  return (
    <div style={{ padding: 24, maxWidth: 720 }}>
      <h1>Analyzing Project</h1>

      <div style={{ marginTop: 12, marginBottom: 18 }}>
        <div style={{ fontSize: 14, opacity: 0.8 }}>Project path</div>
        <div style={{ fontFamily: "monospace", marginTop: 6 }}>{displayInfo}</div>
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
          {isMultiTask
            ? `${Object.values(taskStatuses).filter((s) => s === "completed").length}/${taskIdsFromNav?.length ?? 0} completed · ${progress}%`
            : taskId
            ? `Task: ${taskId} · ${progress}%`
            : `${progress}%`}
        </div>

        {status === "running" && analysisPhase && (
          <div style={{ marginTop: 8, fontSize: 13, color: "#4f46e5" }}>
            Type of analysis: {analysisPhase === "llm" ? "LLM" : "non-LLM"}
            {analysisPhase === "non_llm" && " — Completing non-LLM analysis"}
            {analysisPhase === "llm" && " — Running LLM analysis"}
          </div>
        )}

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


        {isFailed ? (
          <button onClick={() => taskIdsFromNav && beginPolling(taskIdsFromNav)}>Retry</button>
        ) : null}

      </div>
    </div>
  );
}

