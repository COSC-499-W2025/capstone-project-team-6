export async function startAnalysisRequest(token, uploadId) {
  const res = await fetch(`/api/analysis/uploads/${uploadId}/start`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({}),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Start failed (${res.status}): ${text}`);
  }

  const data = await res.json();
  if (!data.task_id) throw new Error("Start failed: no task_id returned");
  return data; // { task_id, status_url, ... }
}

export async function getTaskStatus(taskId, token) {
  const res = await fetch(`/api/tasks/${taskId}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Status failed (${res.status}): ${text}`);
  }

  return await res.json(); // expects { status, progress, error, result, ... }
}

export async function cleanupUploadRequest(token, uploadId) {
  const res = await fetch(`/api/analysis/uploads/${uploadId}/cleanup`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Cleanup failed (${res.status}): ${text}`);
  }

  return await res.json();
}
