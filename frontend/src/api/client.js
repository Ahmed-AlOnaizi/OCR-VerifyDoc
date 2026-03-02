import axios from "axios";

const API_BASE = "/api";

const client = axios.create({ baseURL: API_BASE });

// --- Users ---
export const listUsers = () => client.get("/users").then((r) => r.data);

export const createUser = (data) =>
  client.post("/users", data).then((r) => r.data);

export const getUser = (id) => client.get(`/users/${id}`).then((r) => r.data);

// --- Documents ---
export const listDocuments = (userId) =>
  client.get(`/users/${userId}/documents`).then((r) => r.data);

export const uploadDocument = (userId, file, docType) => {
  const form = new FormData();
  form.append("file", file);
  form.append("doc_type", docType);
  return client.post(`/users/${userId}/documents`, form).then((r) => r.data);
};

// --- Verification ---
export const startVerification = (userId) =>
  client.post(`/users/${userId}/verify`).then((r) => r.data);

export const getJob = (jobId) =>
  client.get(`/jobs/${jobId}`).then((r) => r.data);

export const getLatestVerification = (userId) =>
  client.get(`/users/${userId}/verification-latest`).then((r) => r.data);

// --- SSE ---
export const subscribeToJob = (jobId, onEvent, onError) => {
  const url = `${API_BASE}/jobs/${jobId}/events`;
  const source = new EventSource(url);

  source.addEventListener("progress", (e) => {
    const data = JSON.parse(e.data);
    onEvent(data);
    if (data.status === "completed" || data.status === "failed") {
      source.close();
    }
  });

  source.addEventListener("error", (e) => {
    if (onError) onError(e);
    source.close();
  });

  return source;
};
