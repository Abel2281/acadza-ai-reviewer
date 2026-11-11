import type { Metrics, QueueGroup, Result, SingleResultDetail, AuditEntry, Edit } from "../types";

const API_BASE = `${import.meta.env.VITE_API_BASE_URL ?? ""}/api`;

export async function fetchHealth(): Promise<any> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error("Failed to fetch health check");
  return res.json();
}

export async function fetchMetrics(): Promise<Metrics> {
  const res = await fetch(`${API_BASE}/metrics`);
  if (!res.ok) throw new Error("Failed to fetch metrics");
  return res.json();
}

export async function fetchQueue(): Promise<QueueGroup[]> {
  const res = await fetch(`${API_BASE}/queue`);
  if (!res.ok) throw new Error("Failed to fetch queue");
  return res.json();
}

export async function fetchResults(): Promise<Result[]> {
  const res = await fetch(`${API_BASE}/results`);
  if (!res.ok) throw new Error("Failed to fetch results");
  return res.json();
}

export async function fetchResultDetail(reportId: string): Promise<SingleResultDetail> {
  const res = await fetch(`${API_BASE}/results/${reportId}`);
  if (!res.ok) throw new Error(`Failed to fetch result detail for ${reportId}`);
  return res.json();
}

export async function approveAction(reportId: string, facultyName: string, reason?: string) {
  const res = await fetch(`${API_BASE}/actions/${reportId}/approve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: jsonStringify({ faculty_name: facultyName, reason })
  });
  if (!res.ok) throw new Error(await responseError(res, "Approval failed"));
  return res.json();
}

export async function editAction(reportId: string, facultyName: string, edit: Edit, reason?: string) {
  const res = await fetch(`${API_BASE}/actions/${reportId}/edit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: jsonStringify({ faculty_name: facultyName, edit, reason })
  });
  if (!res.ok) throw new Error(await responseError(res, "Edit action failed"));
  return res.json();
}

export async function rejectAction(reportId: string, facultyName: string, reason: string) {
  const res = await fetch(`${API_BASE}/actions/${reportId}/reject`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: jsonStringify({ faculty_name: facultyName, reason })
  });
  if (!res.ok) throw new Error(await responseError(res, "Rejection failed"));
  return res.json();
}

export async function fetchAuditLogs(reportId?: string): Promise<AuditEntry[]> {
  const url = reportId ? `${API_BASE}/audit/${reportId}` : `${API_BASE}/audit`;
  const res = await fetch(url);
  if (!res.ok) throw new Error("Failed to fetch audit logs");
  return res.json();
}

function jsonStringify(obj: any): string {
  return JSON.stringify(obj);
}

async function responseError(response: Response, fallback: string): Promise<string> {
  try {
    const body = await response.json();
    return body.detail || fallback;
  } catch {
    return fallback;
  }
}
